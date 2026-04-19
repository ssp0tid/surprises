use crate::models::Shell;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ShellmemError {
    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),

    #[error("Parse error for shell {shell}: {message}")]
    Parse { shell: Shell, message: String },

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Not found: id {0}")]
    NotFound(i64),

    #[error("Invalid timestamp: {0}")]
    InvalidTimestamp(String),

    #[error("Sync error: {0}")]
    Sync(String),

    #[error("Export error: {0}")]
    Export(String),

    #[error("Config error: {0}")]
    Config(String),
}