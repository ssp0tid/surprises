use std::fs::{File, Metadata};
use std::io::{BufRead, BufReader, Read, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum LogFileError {
    #[error("File not found: {0}")]
    FileNotFound(PathBuf),
    #[error("Permission denied: {0}")]
    PermissionDenied(PathBuf),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Invalid line number: {line}")]
    InvalidLineNumber { line: u64 },
    #[error("File changed during read")]
    FileChanged,
    #[error("UTF-8 error at line {line}")]
    Utf8Error { line: u64, context: String },
}

/// Metadata about the log file.
#[derive(Debug, Clone)]
pub struct FileMetadata {
    pub path: PathBuf,
    pub size: u64,
    pub inode: u64,
    pub modified: Option<std::time::SystemTime>,
    pub is_append_only: bool,
}

impl FileMetadata {
    pub fn from_metadata(path: PathBuf, meta: &Metadata) -> Self {
        let inode = meta
            .inode()
            .try_into()
            .unwrap_or(0);

        Self {
            path,
            size: meta.len(),
            inode,
            modified: meta.modified().ok(),
            is_append_only: false,
        }
    }
}

/// Line index for efficient line offset caching.
///
/// Stores byte offsets for each line to enable random access without
/// scanning from the start.
#[derive(Debug, Clone)]
pub struct LineIndex {
    offsets: Vec<u64>,
    total_lines: u64,
    total_bytes: u64,
}

impl LineIndex {
    pub fn new() -> Self {
        Self {
            offsets: Vec::new(),
            total_lines: 0,
            total_bytes: 0,
        }
    }

    pub fn from_offsets(offsets: Vec<u64>, total_bytes: u64) -> Self {
        let total_lines = offsets.len() as u64;
        Self {
            offsets,
            total_lines,
            total_bytes,
        }
    }

    pub fn get_offset(&self, line_num: u64) -> Option<u64> {
        self.offsets.get(line_num as usize).copied()
    }

    pub fn get_range(&self, start: u64, count: u64) -> Vec<u64> {
        let start = start as usize;
        let end = (start + count as usize).min(self.offsets.len());
        self.offsets[start..end].to_vec()
    }

    pub fn total_lines(&self) -> u64 {
        self.total_lines
    }

    pub fn total_bytes(&self) -> u64 {
        self.total_bytes
    }

    pub fn is_empty(&self) -> bool {
        self.total_lines == 0
    }
}

impl Default for LineIndex {
    fn default() -> Self {
        Self::new()
    }
}

/// Log file with streaming I/O.
///
/// Uses pread(2)/read(2) instead of mmap(2) per plan section 11.1:
/// "Do NOT use mmap for files that may change!"
#[derive(Debug)]
pub struct LogFile {
    path: PathBuf,
    file: File,
    index: Arc<std::sync::RwLock<LineIndex>>,
    metadata: Arc<std::sync::RwLock<Option<FileMetadata>>>,
    size: Arc<AtomicU64>,
    line_count: Arc<AtomicU64>,
    is_static: bool,
}

impl LogFile {
    pub fn open(path: impl Into<PathBuf>) -> Result<Self, LogFileError> {
        let path: PathBuf = path.into();

        if !path.exists() {
            return Err(LogFileError::FileNotFound(path));
        }

        let file = File::open(&path)?;

        let meta = std::fs::metadata(&path)?;
        let file_meta = FileMetadata::from_metadata(path.clone(), &meta);
        let file_size = meta.len();

        let index = Arc::new(std::sync::RwLock::new(LineIndex::new()));
        let metadata = Arc::new(std::sync::RwLock::new(Some(file_meta)));
        let size = Arc::new(AtomicU64::new(file_size));
        let line_count = Arc::new(AtomicU64::new(0));

        let mut log_file = Self {
            path,
            file,
            index,
            metadata,
            size: size.clone(),
            line_count: line_count.clone(),
            is_static: false,
        };

        log_file.build_index()?;

        Ok(log_file)
    }

    pub fn open_static(path: impl Into<PathBuf>) -> Result<Self, LogFileError> {
        let mut file = Self::open(path)?;
        file.is_static = true;
        Ok(file)
    }

    fn build_index(&mut self) -> Result<(), LogFileError> {
        let mut reader = BufReader::new(&self.file);
        let mut offsets = Vec::new();
        let mut offset: u64 = 0;
        let mut line_start = true;
        let mut buffer = String::new();

        loop {
            buffer.clear();
            let n = reader.read_line(&mut buffer)?;
            if n == 0 {
                break;
            }

            if line_start {
                offsets.push(offset);
                line_start = false;
            }

            offset += n as u64;

            if buffer.ends_with('\n') {
                line_start = true;
            }
        }

        let total_bytes = self.file.metadata()?.len();
        let line_count = offsets.len() as u64;

        let index = LineIndex::from_offsets(offsets, total_bytes);
        *self.index.write().unwrap() = index;
        self.line_count.store(line_count, Ordering::SeqCst);
        self.size.store(total_bytes, Ordering::SeqCst);

        Ok(())
    }

    pub fn read_line(&self, line_num: u64) -> Result<String, LogFileError> {
        let offset = {
            let index = self.index.read().unwrap();
            index.get_offset(line_num).ok_or_else(|| LogFileError::InvalidLineNumber { line: line_num })?
        };

        let mut file = File::open(&self.path)?;
        file.seek(SeekFrom::Start(offset))?;

        let mut reader = BufReader::new(file);
        let mut line = String::new();
        reader.read_line(&mut line)?;

        if line.ends_with('\n') {
            line.pop();
            if line.ends_with('\r') {
                line.pop();
            }
        }

        Ok(line)
    }

    pub fn read_lines(&self, start: u64, count: usize) -> Result<Vec<String>, LogFileError> {
        let mut lines = Vec::with_capacity(count);

        for i in 0..count {
            match self.read_line(start + i as u64) {
                Ok(line) => lines.push(line),
                Err(LogFileError::InvalidLineNumber { .. }) => break,
                Err(e) => return Err(e),
            }
        }

        Ok(lines)
    }

    pub fn refresh(&mut self) -> Result<bool, LogFileError> {
        let current_meta = std::fs::metadata(&self.path)?;
        let current_size = current_meta.len();

        let previous_size = self.size.load(Ordering::SeqCst);

        if current_size == previous_size {
            return Ok(false);
        }

        let previous_inode = self.metadata.read().unwrap()
            .as_ref()
            .map(|m| m.inode)
            .unwrap_or(0);

        let new_inode = current_meta.inode().try_into().unwrap_or(0);

        if previous_inode != new_inode {
            self.path = self.path.clone();
            self.file = File::open(&self.path)?;
            self.file.seek(SeekFrom::Start(0))?;
        }

        self.build_index()?;

        Ok(true)
    }

    pub fn is_binary(&self) -> Result<bool, LogFileError> {
        let mut file = File::open(&self.path)?;

        let mut buffer = [0u8; 8192];
        let n = file.read(&mut buffer)?;

        for &byte in &buffer[..n] {
            if byte == 0 {
                return Ok(true);
            }
            if byte < 0x09 || (0x0e <= byte && byte < 0x20) {
                if byte != 0x0A && byte != 0x0D && byte != 0x09 {
                    return Ok(true);
                }
            }
        }

        Ok(false)
    }

    pub fn is_empty(&self) -> bool {
        self.line_count.load(Ordering::SeqCst) == 0
    }

    pub fn total_lines(&self) -> u64 {
        self.line_count.load(Ordering::SeqCst)
    }

    pub fn total_bytes(&self) -> u64 {
        self.size.load(Ordering::SeqCst)
    }

    pub fn metadata(&self) -> Option<FileMetadata> {
        self.metadata.read().unwrap().clone()
    }

    pub fn path(&self) -> &PathBuf {
        &self.path
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_line_index() {
        let index = LineIndex::from_offsets(vec![0, 10, 20], 30);
        assert_eq!(index.total_lines(), 3);
        assert_eq!(index.get_offset(0), Some(0));
        assert_eq!(index.get_offset(1), Some(10));
        assert_eq!(index.get_offset(2), Some(20));
        assert_eq!(index.get_offset(3), None);
    }

    #[test]
    fn test_read_lines() {
        let mut file = NamedTempFile::new().unwrap();
        writeln!(file, "Line 1").unwrap();
        writeln!(file, "Line 2").unwrap();
        writeln!(file, "Line 3").unwrap();

        let log_file = LogFile::open(file.path()).unwrap();
        let lines = log_file.read_lines(0, 2).unwrap();

        assert_eq!(lines.len(), 2);
        assert_eq!(lines[0], "Line 1");
        assert_eq!(lines[1], "Line 2");
    }

    #[test]
    fn test_read_single_line() {
        let mut file = NamedTempFile::new().unwrap();
        writeln!(file, "Line 1").unwrap();
        writeln!(file, "Line 2").unwrap();

        let log_file = LogFile::open(file.path()).unwrap();
        let line = log_file.read_line(1).unwrap();
        assert_eq!(line, "Line 2");
    }

    #[test]
    fn test_empty_file() {
        let file = NamedTempFile::new().unwrap();
        let log_file = LogFile::open(file.path()).unwrap();
        assert!(log_file.is_empty());
    }

    #[test]
    fn test_is_binary() {
        let mut file = NamedTempFile::new().unwrap();
        write!(file, "Hello\x00World").unwrap();

        let log_file = LogFile::open(file.path()).unwrap();
        assert!(log_file.is_binary().unwrap());
    }

    #[test]
    fn test_is_text() {
        let mut file = NamedTempFile::new().unwrap();
        writeln!(file, "Hello World").unwrap();

        let log_file = LogFile::open(file.path()).unwrap();
        assert!(!log_file.is_binary().unwrap());
    }
}