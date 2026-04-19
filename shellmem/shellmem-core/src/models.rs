use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Shell {
    Bash,
    Zsh,
    Fish,
}

impl Default for Shell {
    fn default() -> Self {
        Shell::Bash
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tag {
    pub id: i64,
    pub name: String,
    pub color: String,
}

impl Default for Tag {
    fn default() -> Self {
        Tag {
            id: 0,
            name: String::new(),
            color: String::from("#808080"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Command {
    pub id: i64,
    pub command: String,
    pub shell: Shell,
    pub timestamp: DateTime<Utc>,
    pub duration_ms: Option<i64>,
    pub working_dir: Option<String>,
    pub exit_status: Option<i32>,
    pub is_favorite: bool,
    pub tags: Vec<Tag>,
    pub hash: String,
    pub source_file: Option<String>,
    pub source_id: Option<i64>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub is_deleted: bool,
}

impl Default for Command {
    fn default() -> Self {
        let now = Utc::now();
        Command {
            id: 0,
            command: String::new(),
            shell: Shell::default(),
            timestamp: now,
            duration_ms: None,
            working_dir: None,
            exit_status: None,
            is_favorite: false,
            tags: Vec::new(),
            hash: String::new(),
            source_file: None,
            source_id: None,
            created_at: now,
            updated_at: now,
            is_deleted: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewCommand {
    pub command: String,
    pub shell: Shell,
    pub timestamp: DateTime<Utc>,
    pub duration_ms: Option<i64>,
    pub working_dir: Option<String>,
    pub exit_status: Option<i32>,
    pub is_favorite: bool,
    pub tags: Vec<Tag>,
    pub hash: String,
    pub source_file: Option<String>,
    pub source_id: Option<i64>,
}

impl Default for NewCommand {
    fn default() -> Self {
        NewCommand {
            command: String::new(),
            shell: Shell::default(),
            timestamp: Utc::now(),
            duration_ms: None,
            working_dir: None,
            exit_status: None,
            is_favorite: false,
            tags: Vec::new(),
            hash: String::new(),
            source_file: None,
            source_id: None,
        }
    }
}

impl From<NewCommand> for Command {
    fn from(new: NewCommand) -> Self {
        let now = Utc::now();
        Command {
            id: 0,
            command: new.command,
            shell: new.shell,
            timestamp: new.timestamp,
            duration_ms: new.duration_ms,
            working_dir: new.working_dir,
            exit_status: new.exit_status,
            is_favorite: new.is_favorite,
            tags: new.tags,
            hash: new.hash,
            source_file: new.source_file,
            source_id: new.source_id,
            created_at: now,
            updated_at: now,
            is_deleted: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SearchOptions {
    pub query: Option<String>,
    pub shell: Option<Shell>,
    pub from_date: Option<DateTime<Utc>>,
    pub to_date: Option<DateTime<Utc>>,
    pub tags: Option<Vec<String>>,
    pub favorites_only: bool,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TagWithCommands {
    pub tag: Tag,
    pub commands: Vec<Command>,
}

impl Default for TagWithCommands {
    fn default() -> Self {
        TagWithCommands {
            tag: Tag::default(),
            commands: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DedupeReport {
    pub duplicates_removed: usize,
    pub unique_commands: usize,
    pub total_before: usize,
}

impl Default for DedupeReport {
    fn default() -> Self {
        DedupeReport {
            duplicates_removed: 0,
            unique_commands: 0,
            total_before: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub command: Command,
    pub score: i64,
}

impl Default for SearchResult {
    fn default() -> Self {
        SearchResult {
            command: Command::default(),
            score: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncState {
    pub shell: Shell,
    pub source_file: String,
    pub last_pos: i64,
    pub last_hash: Option<String>,
}

impl Default for SyncState {
    fn default() -> Self {
        SyncState {
            shell: Shell::default(),
            source_file: String::new(),
            last_pos: 0,
            last_hash: None,
        }
    }
}