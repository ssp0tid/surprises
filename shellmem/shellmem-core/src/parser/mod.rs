use std::path::Path;
use thiserror::Error;

pub mod bash;
pub mod fish;
pub mod zsh;

pub use bash::BashParser;
pub use fish::FishParser;
pub use zsh::ZshParser;

pub use crate::models::Shell;

#[derive(Debug, Clone)]
pub struct ParsedCommand {
    pub command: String,
    pub timestamp: i64,
    pub duration_ms: Option<i64>,
    pub working_dir: Option<String>,
    pub exit_status: Option<i32>,
    pub hash: String,
}

#[derive(Debug, Error)]
pub enum ParserError {
    #[error("Parse error for {shell}: {message}")]
    Parse { shell: Shell, message: String },

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub trait Parser {
    fn parse(&self, content: &str) -> Result<Vec<ParsedCommand>, ParserError>;
}

pub fn parse_shell(shell: Shell, content: &str) -> Result<Vec<ParsedCommand>, ParserError> {
    match shell {
        Shell::Bash => BashParser.parse(content),
        Shell::Zsh => ZshParser.parse(content),
        Shell::Fish => FishParser.parse(content),
    }
}

pub fn detect_shell_from_path(path: &Path) -> Option<Shell> {
    let filename = path.file_name()?.to_str()?;
    match filename {
        "bash_history" => Some(Shell::Bash),
        "zsh_history" => Some(Shell::Zsh),
        "fish_history" => Some(Shell::Fish),
        _ => {
            let path_str = path.to_str()?;
            if path_str.contains("bash") && path_str.contains("history") {
                Some(Shell::Bash)
            } else if path_str.contains("zsh") && path_str.contains("history") {
                Some(Shell::Zsh)
            } else if path_str.contains("fish") && path_str.contains("history") {
                Some(Shell::Fish)
            } else {
                None
            }
        }
    }
}