use notify::{
    Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher,
};
use std::path::PathBuf;
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum WatcherError {
    #[error("Failed to create watcher: {0}")]
    WatcherCreate(String),
    #[error("Failed to watch path: {0}")]
    WatchPath(String),
    #[error("Channel error")]
    ChannelError,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FileChange {
    Modified,
    Removed,
    Created,
    Rotated,
}

pub struct FileWatcher {
    watcher: Option<RecommendedWatcher>,
    path: PathBuf,
    last_inode: Arc<Mutex<u64>>,
    last_size: Arc<Mutex<u64>>,
    receiver: Option<Receiver<Result<Event, notify::Error>>>,
    debounce_ms: u64,
}

impl FileWatcher {
    pub fn new(path: impl Into<PathBuf>) -> Result<Self, WatcherError> {
        Self::with_debounce(path, 100)
    }

    pub fn with_debounce(path: impl Into<PathBuf>, debounce_ms: u64) -> Result<Self, WatcherError> {
        let path: PathBuf = path.into();

        let (tx, rx) = channel();

        let watcher = RecommendedWatcher::new(
            move |res| {
                let _ = tx.send(res);
            },
            Config::default().with_poll_interval(Duration::from_millis(debounce_ms)),
        )
        .map_err(|e| WatcherError::WatcherCreate(e.to_string()))?;

        let initial_inode = get_file_inode(&path);
        let initial_size = get_file_size(&path);

        Ok(Self {
            watcher: Some(watcher),
            path: path.clone(),
            last_inode: Arc::new(Mutex::new(initial_inode)),
            last_size: Arc::new(Mutex::new(initial_size)),
            receiver: Some(rx),
            debounce_ms,
        })
    }

    pub fn watch(&mut self) -> Result<(), WatcherError> {
        if let Some(ref mut watcher) = self.watcher {
            watcher
                .watch(&self.path, RecursiveMode::NonRecursive)
                .map_err(|e| WatcherError::WatchPath(e.to_string()))?;
        }
        Ok(())
    }

    pub fn check_events(&mut self) -> Vec<FileChange> {
        let mut changes = Vec::new();

        let rx = match &self.receiver {
            Some(r) => r,
            None => return changes,
        };

        while let Ok(result) = rx.try_recv() {
            if let Ok(event) = result {
                for change in process_event(&event) {
                    changes.push(change);
                }
            }
        }

        if let Some(change) = self.check_rotation() {
            if !changes.contains(&FileChange::Rotated) {
                changes.push(change);
            }
        }

        changes
    }

    fn check_rotation(&self) -> Option<FileChange> {
        let current_inode = get_file_inode(&self.path);
        let mut last_inode = self.last_inode.lock().unwrap();

        if current_inode != *last_inode && current_inode != 0 {
            *last_inode = current_inode;
            return Some(FileChange::Rotated);
        }

        None
    }

    pub fn refresh_metadata(&mut self) {
        let current_inode = get_file_inode(&self.path);
        let current_size = get_file_size(&self.path);

        *self.last_inode.lock().unwrap() = current_inode;
        *self.last_size.lock().unwrap() = current_size;
    }

    pub fn path(&self) -> &PathBuf {
        &self.path
    }

    pub fn is_watching(&self) -> bool {
        self.watcher.is_some()
    }
}

fn get_file_inode(path: &PathBuf) -> u64 {
    std::fs::metadata(path)
        .ok()
        .and_then(|m| m.inode().try_into().ok())
        .unwrap_or(0)
}

fn get_file_size(path: &PathBuf) -> u64 {
    std::fs::metadata(path).ok().map(|m| m.len()).unwrap_or(0)
}

fn process_event(event: &Event) -> Vec<FileChange> {
    let mut changes = Vec::new();

    match event.kind {
        EventKind::Modify(_) => {
            changes.push(FileChange::Modified);
        }
        EventKind::Remove(_) => {
            changes.push(FileChange::Removed);
        }
        EventKind::Create(_) => {
            changes.push(FileChange::Created);
        }
        _ => {}
    }

    changes
}

pub struct AsyncFileWatcher {
    watcher: notify::recommended_watcher::Rx,
    path: PathBuf,
    last_inode: Arc<Mutex<u64>>,
    debounce: Duration,
}

impl AsyncFileWatcher {
    pub fn new(path: impl Into<PathBuf>) -> Result<Self, notify::Error> {
        let path: PathBuf = path.into();
        let (watcher, _) = notify::recommended_watcher(move |_| {})?;

        let initial_inode = get_file_inode(&path);

        Ok(Self {
            watcher,
            path,
            last_inode: Arc::new(Mutex::new(initial_inode)),
            debounce: Duration::from_millis(100),
        })
    }

    pub fn check_rotation(&self) -> bool {
        let current_inode = get_file_inode(&self.path);
        let last_inode = *self.last_inode.lock().unwrap();

        if current_inode != last_inode && current_inode != 0 {
            *self.last_inode.lock().unwrap() = current_inode;
            return true;
        }

        false
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
    fn test_file_watcher_create() {
        let file = NamedTempFile::new().unwrap();
        let watcher = FileWatcher::new(file.path());
        assert!(watcher.is_ok());
    }

    #[test]
    fn test_file_watcher_with_debounce() {
        let file = NamedTempFile::new().unwrap();
        let watcher = FileWatcher::with_debounce(file.path(), 50);
        assert!(watcher.is_ok());
    }

    #[test]
    fn test_rotation_detection() {
        let mut file = NamedTempFile::new().unwrap();
        write!(file, "initial").unwrap();

        let mut watcher = FileWatcher::new(file.path()).unwrap();
        let rotation = watcher.check_rotation();
        assert!(rotation.is_none());

        std::fs::remove_file(file.path()).unwrap();
        let _ = std::io::Write::write(&mut file, b"rotated");

        let rotation = watcher.check_rotation();
        assert!(rotation.is_some());
    }

    #[test]
    fn test_async_watcher() {
        let file = NamedTempFile::new().unwrap();
        let watcher = AsyncFileWatcher::new(file.path());
        assert!(watcher.is_ok());
    }

    #[test]
    fn test_check_inode() {
        let file = NamedTempFile::new().unwrap();
        let inode = get_file_inode(&file.path().to_path_buf());
        assert!(inode > 0);
    }
}