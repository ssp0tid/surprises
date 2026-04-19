use rusqlite::Connection;
use crate::error::ShellmemError;

pub fn run_migrations(conn: &Connection) -> Result<(), ShellmemError> {
    let table_exists: bool = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='commands'",
        [],
        |row| row.get::<_, i32>(0),
    )?;

    if table_exists > 0 {
        return Ok(());
    }

    conn.execute(
        "CREATE TABLE commands (
            id INTEGER PRIMARY KEY,
            command TEXT NOT NULL,
            shell TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_id TEXT,
            timestamp INTEGER NOT NULL,
            duration_ms INTEGER,
            working_dir TEXT,
            exit_status INTEGER,
            is_favorite BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            hash TEXT NOT NULL UNIQUE
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#ffffff'
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE command_tags (
            command_id INTEGER REFERENCES commands(id),
            tag_id INTEGER REFERENCES tags(id),
            PRIMARY KEY (command_id, tag_id)
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE sync_state (
            shell TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            last_pos INTEGER NOT NULL,
            last_hash TEXT
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )",
        [],
    )?;

    conn.execute(
        "CREATE INDEX idx_commands_timestamp ON commands(timestamp DESC)",
        [],
    )?;

    conn.execute(
        "CREATE INDEX idx_commands_hash ON commands(hash)",
        [],
    )?;

    conn.execute(
        "CREATE INDEX idx_commands_favorite ON commands(is_favorite) WHERE is_favorite = TRUE",
        [],
    )?;

    conn.execute(
        "CREATE INDEX idx_command_tags_command ON command_tags(command_id)",
        [],
    )?;

    conn.execute(
        "CREATE INDEX idx_command_tags_tag ON command_tags(tag_id)",
        [],
    )?;

    Ok(())
}