pub mod cli;
pub mod config;
pub mod entropy;
pub mod errors;
pub mod generator;
pub mod storage;
pub mod clipboard;
pub mod output;

pub use cli::Cli;
pub use config::{AppConfig, ClipboardConfig, GeneratorConfig, OutputConfig, StorageConfig};
pub use entropy::{EntropyInfo, Strength};
pub use errors::{PassgenError, Result};
pub use generator::{generate, generate_multiple, generate_with_info};
pub use storage::{PasswordEntry, PasswordHistory, export_csv, export_json, export_txt, history_path};
pub use clipboard::{copy_to_clipboard, clear_clipboard, copy_with_timeout, copy_async};
pub use output::{display_password, display_password_verbose, display_multiple_passwords};

pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}