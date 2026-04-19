use std::path::Path;
use rusqlite::Connection;
use crate::error::ShellmemError;
use crate::models::{Command, DedupeReport, NewCommand, SearchOptions, Tag, SyncState};
use crate::Shell;

mod migrations;
mod sqlite;

pub use sqlite::Database;

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new(path: &Path) -> Result<Self, ShellmemError> {
        let conn = Connection::open(path)?;
        migrations::run_migrations(&conn)?;
        Ok(Self { conn })
    }

    pub fn connection(&self) -> &Connection {
        &self.conn
    }
}

impl HistoryStore for Database {
    fn add_command(&mut self, cmd: NewCommand) -> Result<i64, ShellmemError> {
        sqlite::add_command(self, cmd)
    }

    fn get_command(&self, id: i64) -> Result<Option<Command>, ShellmemError> {
        sqlite::get_command(self, id)
    }

    fn search(&self, options: SearchOptions) -> Result<Vec<Command>, ShellmemError> {
        sqlite::search(self, options)
    }

    fn set_favorite(&self, id: i64, favorite: bool) -> Result<(), ShellmemError> {
        sqlite::set_favorite(self, id, favorite)
    }

    fn add_tag(&self, command_id: i64, tag_id: i64) -> Result<(), ShellmemError> {
        sqlite::add_tag(self, command_id, tag_id)
    }

    fn remove_tag(&self, command_id: i64, tag_id: i64) -> Result<(), ShellmemError> {
        sqlite::remove_tag(self, command_id, tag_id)
    }

    fn set_deleted(&self, id: i64, deleted: bool) -> Result<(), ShellmemError> {
        sqlite::set_deleted(self, id, deleted)
    }

    fn dedupe(&mut self) -> Result<DedupeReport, ShellmemError> {
        sqlite::dedupe(self)
    }

    fn tag_exists(&self, name: &str) -> Result<Option<Tag>, ShellmemError> {
        sqlite::tag_exists(self, name)
    }

    fn create_tag(&self, name: &str, color: &str) -> Result<Tag, ShellmemError> {
        sqlite::create_tag(self, name, color)
    }

    fn get_all_tags(&self) -> Result<Vec<Tag>, ShellmemError> {
        sqlite::get_all_tags(self)
    }

    fn get_commands_by_tag(&self, tag_id: i64) -> Result<Vec<Command>, ShellmemError> {
        sqlite::get_commands_by_tag(self, tag_id)
    }

    fn get_sync_state(&self, shell: Shell) -> Result<Option<SyncState>, ShellmemError> {
        sqlite::get_sync_state(self, shell)
    }

    fn set_sync_state(&self, shell: Shell, source_file: &str, last_pos: i64, last_hash: Option<&str>) -> Result<(), ShellmemError> {
        sqlite::set_sync_state(self, shell, source_file, last_pos, last_hash)
    }
}

pub trait HistoryStore {
    fn add_command(&mut self, cmd: NewCommand) -> Result<i64, ShellmemError>;
    fn get_command(&self, id: i64) -> Result<Option<Command>, ShellmemError>;
    fn search(&self, options: SearchOptions) -> Result<Vec<Command>, ShellmemError>;
    fn set_favorite(&self, id: i64, favorite: bool) -> Result<(), ShellmemError>;
    fn add_tag(&self, command_id: i64, tag_id: i64) -> Result<(), ShellmemError>;
    fn remove_tag(&self, command_id: i64, tag_id: i64) -> Result<(), ShellmemError>;
    fn set_deleted(&self, id: i64, deleted: bool) -> Result<(), ShellmemError>;
    fn dedupe(&mut self) -> Result<DedupeReport, ShellmemError>;
    fn tag_exists(&self, name: &str) -> Result<Option<Tag>, ShellmemError>;
    fn create_tag(&self, name: &str, color: &str) -> Result<Tag, ShellmemError>;
    fn get_all_tags(&self) -> Result<Vec<Tag>, ShellmemError>;
    fn get_commands_by_tag(&self, tag_id: i64) -> Result<Vec<Command>, ShellmemError>;
    fn get_sync_state(&self, shell: Shell) -> Result<Option<SyncState>, ShellmemError>;
    fn set_sync_state(&self, shell: Shell, source_file: &str, last_pos: i64, last_hash: Option<&str>) -> Result<(), ShellmemError>;
}