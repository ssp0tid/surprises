//! Persistence layer for bookmarks.

use crate::bookmarks::BookmarkStore;
use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::path::PathBuf;

/// Error type for bookmark storage operations.
#[derive(Debug, Serialize, Deserialize)]
pub enum StorageError {
    #[serde(rename = "IO error")]
    Io(String),
    #[serde(rename = "Serialization error")]
    Serialization(String),
    #[serde(rename = "Config directory not found")]
    ConfigDirNotFound,
}

impl From<io::Error> for StorageError {
    fn from(err: io::Error) -> Self {
        StorageError::Io(err.to_string())
    }
}

impl From<serde_json::Error> for StorageError {
    fn from(err: serde_json::Error) -> Self {
        StorageError::Serialization(err.to_string())
    }
}

/// Get the config directory path (~/.config/logprobe).
fn get_config_dir() -> Result<PathBuf, StorageError> {
    let config_dir = dirs::config_dir()
        .ok_or(StorageError::ConfigDirNotFound)?
        .join("logprobe");
    Ok(config_dir)
}

/// Get the bookmarks file path.
fn get_bookmarks_path() -> Result<PathBuf, StorageError> {
    Ok(get_config_dir()?.join("bookmarks.json"))
}

/// Load bookmarks from disk.
pub fn load() -> Result<BookmarkStore, StorageError> {
    let path = get_bookmarks_path()?;

    if !path.exists() {
        return Ok(BookmarkStore::new());
    }

    let content = fs::read_to_string(&path)?;
    let store: BookmarkStore = serde_json::from_str(&content)?;
    Ok(store)
}

/// Save bookmarks to disk.
pub fn save(store: &BookmarkStore) -> Result<(), StorageError> {
    let config_dir = get_config_dir()?;
    let path = get_bookmarks_path()?;

    fs::create_dir_all(&config_dir)?;
    let content = serde_json::to_string_pretty(store)?;
    fs::write(&path, content)?;
    Ok(())
}