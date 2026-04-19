use sha2::{Sha256, Digest};

use super::{ParsedCommand, Parser, ParserError, Shell};

pub struct ZshParser;

impl Parser for ZshParser {
    fn parse(&self, content: &str) -> Result<Vec<ParsedCommand>, ParserError> {
        let mut commands = Vec::new();

        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }

            if !line.starts_with(':') {
                continue;
            }

            let remaining = match line.strip_prefix(':') {
                Some(r) => r.trim(),
                None => continue,
            };

            let (time_part, cmd_part) = match remaining.find(';') {
                Some(idx) => remaining.split_at(idx),
                None => continue,
            };

            let cmd = &cmd_part[1..];
            if cmd.is_empty() {
                continue;
            }

            let cmd = unescape_newlines(cmd);

            let (timestamp, duration_ms) = parse_timestamp_and_duration(time_part);

            let hash = calculate_hash(&cmd);

            commands.push(ParsedCommand {
                command: cmd,
                timestamp,
                duration_ms,
                working_dir: None,
                exit_status: None,
                hash,
            });
        }

        Ok(commands)
    }
}

fn parse_timestamp_and_duration(time_part: &str) -> (i64, Option<i64>) {
    let parts: Vec<&str> = time_part.split(':').collect();
    if parts.is_empty() {
        return (chrono::Utc::now().timestamp(), None);
    }

    let timestamp = match parts[0].parse::<i64>() {
        Ok(ts) => ts,
        Err(_) => chrono::Utc::now().timestamp(),
    };

    let duration_ms = if parts.len() > 1 {
        parts[1].parse::<i64>().ok().map(|s| s * 1000)
    } else {
        None
    };

    (timestamp, duration_ms)
}

fn unescape_newlines(s: &str) -> String {
    s.replace("\\n", "\n")
}

fn calculate_hash(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}