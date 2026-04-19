use sha2::{Sha256, Digest};

use super::{ParsedCommand, Parser, ParserError, Shell};

pub struct FishParser;

impl Parser for FishParser {
    fn parse(&self, content: &str) -> Result<Vec<ParsedCommand>, ParserError> {
        let mut commands = Vec::new();
        let mut current_entry: Option<FishEntry> = None;

        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            if trimmed.starts_with("- cmd:") {
                if let Some(entry) = current_entry.take() {
                    if let Some(cmd) = entry.into_parsed_command() {
                        commands.push(cmd);
                    }
                }

                let cmd_value = trimmed.strip_prefix("- cmd:").map(|s| s.trim()).unwrap_or("");
                if cmd_value.is_empty() {
                    continue;
                }

                current_entry = Some(FishEntry {
                    command: cmd_value.to_string(),
                    timestamp: None,
                    cwd: None,
                    status: None,
                });
            } else if let Some(ref mut entry) = current_entry {
                if let Some(val) = trimmed.strip_prefix("when:").map(|s| s.trim()) {
                    entry.timestamp = val.parse().ok();
                } else if let Some(val) = trimmed.strip_prefix("cwd:").map(|s| s.trim()) {
                    entry.cwd = Some(val.to_string());
                } else if let Some(val) = trimmed.strip_prefix("status:").map(|s| s.trim()) {
                    entry.status = val.parse().ok();
                }
            }
        }

        if let Some(entry) = current_entry {
            if let Some(cmd) = entry.into_parsed_command() {
                commands.push(cmd);
            }
        }

        Ok(commands)
    }
}

struct FishEntry {
    command: String,
    timestamp: Option<i64>,
    cwd: Option<String>,
    status: Option<i32>,
}

impl FishEntry {
    fn into_parsed_command(self) -> Option<ParsedCommand> {
        let timestamp = self.timestamp.unwrap_or(chrono::Utc::now().timestamp());
        let hash = calculate_hash(&self.command);

        Some(ParsedCommand {
            command: self.command,
            timestamp,
            duration_ms: None,
            working_dir: self.cwd,
            exit_status: self.status,
            hash,
        })
    }
}

fn calculate_hash(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}