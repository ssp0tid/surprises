use rusqlite::{params, Connection, OptionalExtension};
use crate::error::ShellmemError;
use crate::models::{Command, DedupeReport, NewCommand, SearchOptions, Tag, SyncState};
use crate::Shell;
use crate::storage::Database;

pub fn add_command(db: &mut Database, cmd: NewCommand) -> Result<i64, ShellmemError> {
    let conn = db.connection();
    let now = chrono::Utc::now().timestamp();

    let exists: bool = conn.query_row(
        "SELECT EXISTS(SELECT 1 FROM commands WHERE hash = ?1 AND is_deleted = FALSE)",
        params![cmd.hash],
        |row| row.get(0),
    )?;

    if exists {
        return Ok(0);
    }

    conn.execute(
        "INSERT INTO commands (
            command, shell, source_file, source_id, timestamp, duration_ms,
            working_dir, exit_status, is_favorite, is_deleted, created_at, updated_at, hash
        ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
        params![
            cmd.command,
            shell_to_string(&cmd.shell),
            cmd.source_file,
            cmd.source_id.map(|id| id.to_string()),
            cmd.timestamp.timestamp(),
            cmd.duration_ms,
            cmd.working_dir,
            cmd.exit_status,
            cmd.is_favorite,
            false,
            now,
            now,
            cmd.hash,
        ],
    )?;

    Ok(conn.last_insert_rowid())
}

pub fn get_command(db: &Database, id: i64) -> Result<Option<Command>, ShellmemError> {
    let conn = db.connection();

    let mut stmt = conn.prepare(
        "SELECT id, command, shell, source_file, source_id, timestamp, duration_ms,
                working_dir, exit_status, is_favorite, is_deleted, created_at, updated_at, hash
         FROM commands WHERE id = ?1 AND is_deleted = FALSE"
    )?;

    let command = stmt.query_row(params![id], |row| {
        Ok(Command {
            id: row.get(0)?,
            command: row.get(1)?,
            shell: string_to_shell(&row.get::<_, String>(2)?),
            source_file: row.get(3)?,
            source_id: row.get::<_, Option<String>>(4)?.and_then(|s| s.parse().ok()),
            timestamp: chrono::DateTime::from_timestamp(row.get(5)?, 0).unwrap_or_else(chrono::Utc::now),
            duration_ms: row.get(6)?,
            working_dir: row.get(7)?,
            exit_status: row.get(8)?,
            is_favorite: row.get(9)?,
            is_deleted: row.get(10)?,
            tags: Vec::new(),
            hash: row.get(12)?,
            created_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
            updated_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
        })
    }).optional()?;

    if let Some(mut cmd) = command {
        cmd.tags = get_command_tags(conn, cmd.id)?;
        Ok(Some(cmd))
    } else {
        Ok(None)
    }
}

pub fn search(db: &Database, options: SearchOptions) -> Result<Vec<Command>, ShellmemError> {
    let conn = db.connection();

    let mut sql = String::from(
        "SELECT c.id, c.command, c.shell, c.source_file, c.source_id, c.timestamp,
                c.duration_ms, c.working_dir, c.exit_status, c.is_favorite,
                c.is_deleted, c.created_at, c.updated_at, c.hash
         FROM commands c WHERE c.is_deleted = FALSE"
    );

    let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    if let Some(ref query) = options.query {
        sql.push_str(" AND c.command LIKE ?");
        params_vec.push(Box::new(format!("%{}%", query)));
    }

    if let Some(ref shell) = options.shell {
        sql.push_str(" AND c.shell = ?");
        params_vec.push(Box::new(shell_to_string(shell)));
    }

    if let Some(from_date) = options.from_date {
        sql.push_str(" AND c.timestamp >= ?");
        params_vec.push(Box::new(from_date.timestamp()));
    }

    if let Some(to_date) = options.to_date {
        sql.push_str(" AND c.timestamp <= ?");
        params_vec.push(Box::new(to_date.timestamp()));
    }

    if options.favorites_only {
        sql.push_str(" AND c.is_favorite = TRUE");
    }

    if let Some(ref tag_names) = options.tags {
        if !tag_names.is_empty() {
            sql.push_str(" AND EXISTS (SELECT 1 FROM command_tags ct JOIN tags t ON ct.tag_id = t.id WHERE ct.command_id = c.id AND t.name IN (");
            for (i, _) in tag_names.iter().enumerate() {
                if i > 0 {
                    sql.push_str(", ");
                }
                sql.push_str(&format!("?{}", params_vec.len() + i + 1));
            }
            sql.push_str("))");
            for tag in tag_names {
                params_vec.push(Box::new(tag.clone()));
            }
        }
    }

    sql.push_str(" ORDER BY c.timestamp DESC");

    if let Some(limit) = options.limit {
        sql.push_str(&format!(" LIMIT {}", limit));
    }

    if let Some(offset) = options.offset {
        sql.push_str(&format!(" OFFSET {}", offset));
    }

    let mut stmt = conn.prepare(&sql)?;

    let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|b| b.as_ref()).collect();

    let mut commands: Vec<Command> = stmt.query_map(params_refs.as_slice(), |row| {
        Ok(Command {
            id: row.get(0)?,
            command: row.get(1)?,
            shell: string_to_shell(&row.get::<_, String>(2)?),
            source_file: row.get(3)?,
            source_id: row.get::<_, Option<String>>(4)?.and_then(|s| s.parse().ok()),
            timestamp: chrono::DateTime::from_timestamp(row.get(5)?, 0).unwrap_or_else(chrono::Utc::now),
            duration_ms: row.get(6)?,
            working_dir: row.get(7)?,
            exit_status: row.get(8)?,
            is_favorite: row.get(9)?,
            is_deleted: row.get(10)?,
            tags: Vec::new(),
            hash: row.get(12)?,
            created_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
            updated_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
        })
    })?.collect::<Result<Vec<_>, _>>()?;

    for cmd in &mut commands {
        cmd.tags = get_command_tags(conn, cmd.id)?;
    }

    Ok(commands)
}

pub fn set_favorite(db: &Database, id: i64, favorite: bool) -> Result<(), ShellmemError> {
    let conn = db.connection();
    let now = chrono::Utc::now().timestamp();

    conn.execute(
        "UPDATE commands SET is_favorite = ?1, updated_at = ?2 WHERE id = ?3",
        params![favorite, now, id],
    )?;

    Ok(())
}

pub fn add_tag(db: &Database, command_id: i64, tag_id: i64) -> Result<(), ShellmemError> {
    let conn = db.connection();

    conn.execute(
        "INSERT OR IGNORE INTO command_tags (command_id, tag_id) VALUES (?1, ?2)",
        params![command_id, tag_id],
    )?;

    Ok(())
}

pub fn remove_tag(db: &Database, command_id: i64, tag_id: i64) -> Result<(), ShellmemError> {
    let conn = db.connection();

    conn.execute(
        "DELETE FROM command_tags WHERE command_id = ?1 AND tag_id = ?2",
        params![command_id, tag_id],
    )?;

    Ok(())
}

pub fn set_deleted(db: &Database, id: i64, deleted: bool) -> Result<(), ShellmemError> {
    let conn = db.connection();
    let now = chrono::Utc::now().timestamp();

    conn.execute(
        "UPDATE commands SET is_deleted = ?1, updated_at = ?2 WHERE id = ?3",
        params![deleted, now, id],
    )?;

    Ok(())
}

pub fn dedupe(db: &mut Database) -> Result<DedupeReport, ShellmemError> {
    let conn = db.connection();

    let total_before: usize = conn.query_row(
        "SELECT COUNT(*) FROM commands WHERE is_deleted = FALSE",
        [],
        |row| row.get(0),
    )?;

    conn.execute(
        "DELETE FROM commands WHERE id IN (
            SELECT c1.id FROM commands c1
            WHERE EXISTS (
                SELECT 1 FROM commands c2
                WHERE c2.hash = c1.hash
                  AND c2.id < c1.id
                  AND c2.is_deleted = FALSE
            )
            AND c1.is_deleted = FALSE
        )",
        [],
    )?;

    let duplicates_removed = total_before.saturating_sub(
        conn.query_row(
            "SELECT COUNT(*) FROM commands WHERE is_deleted = FALSE",
            [],
            |row| row.get(0),
        )?,
    );

    let unique_commands = total_before.saturating_sub(duplicates_removed);

    Ok(DedupeReport {
        duplicates_removed,
        unique_commands,
        total_before,
    })
}

pub fn tag_exists(db: &Database, name: &str) -> Result<Option<Tag>, ShellmemError> {
    let conn = db.connection();

    let tag = conn.query_row(
        "SELECT id, name, color FROM tags WHERE name = ?1",
        params![name],
        |row| Ok(Tag {
            id: row.get(0)?,
            name: row.get(1)?,
            color: row.get(2)?,
        }),
    ).optional()?;

    Ok(tag)
}

pub fn create_tag(db: &Database, name: &str, color: &str) -> Result<Tag, ShellmemError> {
    let conn = db.connection();

    conn.execute(
        "INSERT INTO tags (name, color) VALUES (?1, ?2)",
        params![name, color],
    )?;

    let id = conn.last_insert_rowid();

    Ok(Tag {
        id,
        name: name.to_string(),
        color: color.to_string(),
    })
}

pub fn get_all_tags(db: &Database) -> Result<Vec<Tag>, ShellmemError> {
    let conn = db.connection();

    let mut stmt = conn.prepare("SELECT id, name, color FROM tags ORDER BY name")?;

    let tags = stmt.query_map([], |row| {
        Ok(Tag {
            id: row.get(0)?,
            name: row.get(1)?,
            color: row.get(2)?,
        })
    })?.collect::<Result<Vec<_>, _>>()?;

    Ok(tags)
}

pub fn get_commands_by_tag(db: &Database, tag_id: i64) -> Result<Vec<Command>, ShellmemError> {
    let conn = db.connection();

    let mut stmt = conn.prepare(
        "SELECT c.id, c.command, c.shell, c.source_file, c.source_id, c.timestamp,
                c.duration_ms, c.working_dir, c.exit_status, c.is_favorite,
                c.is_deleted, c.created_at, c.updated_at, c.hash
         FROM commands c
         INNER JOIN command_tags ct ON c.id = ct.command_id
         WHERE ct.tag_id = ?1 AND c.is_deleted = FALSE
         ORDER BY c.timestamp DESC"
    )?;

    let commands = stmt.query_map(params![tag_id], |row| {
        Ok(Command {
            id: row.get(0)?,
            command: row.get(1)?,
            shell: string_to_shell(&row.get::<_, String>(2)?),
            source_file: row.get(3)?,
            source_id: row.get::<_, Option<String>>(4)?.and_then(|s| s.parse().ok()),
            timestamp: chrono::DateTime::from_timestamp(row.get(5)?, 0).unwrap_or_else(chrono::Utc::now),
            duration_ms: row.get(6)?,
            working_dir: row.get(7)?,
            exit_status: row.get(8)?,
            is_favorite: row.get(9)?,
            is_deleted: row.get(10)?,
            tags: Vec::new(),
            hash: row.get(12)?,
            created_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
            updated_at: chrono::DateTime::from_timestamp(row.get(11)?, 0).unwrap_or_else(chrono::Utc::now),
        })
    })?.collect::<Result<Vec<_>, _>>()?;

    Ok(commands)
}

pub fn get_sync_state(db: &Database, shell: Shell) -> Result<Option<SyncState>, ShellmemError> {
    let conn = db.connection();

    let state = conn.query_row(
        "SELECT shell, source_file, last_pos, last_hash FROM sync_state WHERE shell = ?1",
        params![shell_to_string(&shell)],
        |row| Ok(SyncState {
            shell: string_to_shell(&row.get::<_, String>(0)?),
            source_file: row.get(1)?,
            last_pos: row.get(2)?,
            last_hash: row.get(3)?,
        }),
    ).optional()?;

    Ok(state)
}

pub fn set_sync_state(
    db: &Database,
    shell: Shell,
    source_file: &str,
    last_pos: i64,
    last_hash: Option<&str>,
) -> Result<(), ShellmemError> {
    let conn = db.connection();

    conn.execute(
        "INSERT OR REPLACE INTO sync_state (shell, source_file, last_pos, last_hash) VALUES (?1, ?2, ?3, ?4)",
        params![shell_to_string(&shell), source_file, last_pos, last_hash],
    )?;

    Ok(())
}

fn get_command_tags(conn: &Connection, command_id: i64) -> Result<Vec<Tag>, ShellmemError> {
    let mut stmt = conn.prepare(
        "SELECT t.id, t.name, t.color FROM tags t
         INNER JOIN command_tags ct ON t.id = ct.tag_id
         WHERE ct.command_id = ?1"
    )?;

    let tags = stmt.query_map(params![command_id], |row| {
        Ok(Tag {
            id: row.get(0)?,
            name: row.get(1)?,
            color: row.get(2)?,
        })
    })?.collect::<Result<Vec<_>, _>>()?;

    Ok(tags)
}

fn shell_to_string(shell: &Shell) -> String {
    match shell {
        Shell::Bash => "bash".to_string(),
        Shell::Zsh => "zsh".to_string(),
        Shell::Fish => "fish".to_string(),
    }
}

fn string_to_shell(s: &str) -> Shell {
    match s {
        "bash" => Shell::Bash,
        "zsh" => Shell::Zsh,
        "fish" => Shell::Fish,
        _ => Shell::Bash,
    }
}