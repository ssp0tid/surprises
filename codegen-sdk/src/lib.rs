pub mod cli;
pub mod parser;
pub mod config;
pub mod introspection;
pub mod utils;

pub use parser::types::ApiSpec;
pub use anyhow::Result;
pub use thiserror::Error;

use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Language {
    TypeScript,
    Python,
    Go,
    Rust,
}

impl std::fmt::Display for Language {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Language::TypeScript => write!(f, "typescript"),
            Language::Python => write!(f, "python"),
            Language::Go => write!(f, "go"),
            Language::Rust => write!(f, "rust"),
        }
    }
}

impl FromStr for Language {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "typescript" | "ts" => Ok(Language::TypeScript),
            "python" | "py" => Ok(Language::Python),
            "go" | "golang" => Ok(Language::Go),
            "rust" | "rs" => Ok(Language::Rust),
            _ => Err(()),
        }
    }
}
