use thiserror::Error;

#[derive(Debug, Error)]
pub enum PassgenError {
    #[error("Invalid length: {0}. Must be between 8 and 128")]
    InvalidLength(usize),
    
    #[error("No character sets selected")]
    NoCharacterSets,
    
    #[error("Not enough unique characters for password: need {0}, have {1}")]
    InsufficientUniqueChars(usize, usize),
    
    #[error("Clipboard error: {0}")]
    ClipboardError(String),
    
    #[error("Storage error: {0}")]
    StorageError(String),
    
    #[error("Encryption error: {0}")]
    EncryptionError(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::Error),
    
    #[error("Base64 decode error: {0}")]
    Base64Error(#[from] base64::DecodeError),
}

pub type Result<T> = std::result::Result<T, PassgenError>;