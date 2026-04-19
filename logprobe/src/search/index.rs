use std::fs::File;
use std::io::{BufRead, BufReader, Error as IoError};
use std::path::Path;
use std::sync::{Arc, RwLock};

use crate::errors::Error;

pub struct LineIndex {
    offsets: Vec<u64>,
    cache: Arc<RwLock<LineIndexCache>>,
}

pub struct LineIndexCache {
    offsets: Vec<u64>,
}

impl LineIndex {
    pub fn new() -> Self {
        Self {
            offsets: Vec::new(),
            cache: Arc::new(RwLock::new(LineIndexCache { offsets: Vec::new() })),
        }
    }

    pub fn get_offset(&self, line_num: u64) -> Result<u64, Error> {
        let idx = line_num as usize;
        if idx >= self.offsets.len() {
            return Err(Error::Io(IoError::new(
                std::io::ErrorKind::InvalidInput,
                format!(
                    "Line {} out of bounds (total lines: {})",
                    line_num,
                    self.offsets.len()
                ),
            )));
        }
        Ok(self.offsets[idx])
    }

    pub fn build_from_file(path: &Path) -> Result<Self, Error> {
        let file = File::open(path)?;
        let reader = BufReader::new(file);

        let mut offsets = vec![0];
        let mut current_offset: u64 = 0;

        for line in reader.lines() {
            let line = line?;
            current_offset += line.len() as u64 + 1;
            offsets.push(current_offset);
        }

        let cache_data = Arc::new(RwLock::new(LineIndexCache {
            offsets: offsets.clone(),
        }));

        Ok(Self {
            offsets,
            cache: cache_data,
        })
    }

    pub fn invalidate(&self) -> Result<(), Error> {
        let mut cache = self.cache.write().map_err(|_| {
            Error::Io(IoError::new(
                std::io::ErrorKind::Other,
                "Failed to acquire write lock on cache",
            ))
        })?;
        cache.offsets.clear();
        Ok(())
    }

    pub fn line_count(&self) -> u64 {
        self.offsets.len() as u64
    }
}

impl Default for LineIndex {
    fn default() -> Self {
        Self::new()
    }
}