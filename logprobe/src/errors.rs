//! Error types for logprobe.

use std::path::PathBuf;
use thiserror::Error;

/// Main error type for logprobe operations.
#[derive(Error, Debug)]
pub enum Error {
    #[error("File not found: {0}")]
    FileNotFound(PathBuf),

    #[error("Permission denied: {0}")]
    PermissionDenied(PathBuf),

    #[error("Invalid regex: {0}")]
    InvalidRegex(String),

    #[error("File changed during read")]
    FileChanged,

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("UTF-8 error at line {line}: {context}")]
    Utf8Error {
        /// The line number where the UTF-8 error occurred.
        line: u64,
        /// Context around the error for debugging.
        context: String,
    },
}