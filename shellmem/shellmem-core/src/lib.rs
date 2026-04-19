pub mod config;
pub mod error;
pub mod models;
pub mod parser;
pub mod search;
pub mod storage;
pub mod sync;

pub use config::Config;
pub use error::ShellmemError;
pub use models::{
    Command, DedupeReport, NewCommand, SearchOptions, SearchResult, Shell, Tag, TagWithCommands,
};
pub use parser::{parse_shell, BashParser, FishParser, Parser, ParsedCommand, ZshParser};
pub use search::SearchEngine;
pub use storage::{Database, HistoryStore};
pub use sync::HistoryWatcher;