use sha2::{Sha256, Digest};

use super::{ParsedCommand, Parser, ParserError, Shell};

pub struct BashParser;

impl Parser for BashParser {
    fn parse(&self, content: &str) -> Result<Vec<ParsedCommand>, ParserError> {
        let mut commands = Vec::new();
        let mut lines = content.lines().peekable();
        let mut pending_timestamp: Option<i64> = None;
        let now = chrono::Utc::now().timestamp();

        while let Some(line) = lines.next() {
            if line.starts_with('#') && line.len() > 1 {
                let ts_str = &line[1..];
                if ts_str.chars().all(|c| c.is_ascii_digit()) {
                    pending_timestamp = ts_str.parse().ok();
                    continue;
                }
            }

            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            if trimmed.starts_with(' ') {
                continue;
            }

            let timestamp = pending_timestamp.unwrap_or(now);
            let hash = calculate_hash(trimmed);

            commands.push(ParsedCommand {
                command: trimmed.to_string(),
                timestamp,
                duration_ms: None,
                working_dir: None,
                exit_status: None,
                hash,
            });

            pending_timestamp = None;
        }

        Ok(commands)
    }
}

fn calculate_hash(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}