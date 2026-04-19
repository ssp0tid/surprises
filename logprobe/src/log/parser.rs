use crate::log::level::{detect_level, Level};
use crate::log::timestamp::{extract_timestamp_from_line, parse_timestamp, Timestamp};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogFormat {
    Json,
    Apache,
    Syslog,
    Iso8601,
    Plaintext,
}

impl LogFormat {
    pub fn name(&self) -> &'static str {
        match self {
            LogFormat::Json => "JSON",
            LogFormat::Apache => "Apache",
            LogFormat::Syslog => "Syslog",
            LogFormat::Iso8601 => "ISO 8601",
            LogFormat::Plaintext => "Plaintext",
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct LogLine {
    pub text: String,
    pub level: Level,
    pub timestamp: Option<Timestamp>,
    pub line_number: u64,
    pub format: Option<LogFormat>,
}

impl LogLine {
    pub fn new(line_number: u64) -> Self {
        Self {
            text: String::new(),
            level: Level::Unknown,
            timestamp: None,
            line_number,
            format: None,
        }
    }

    pub fn with_text(mut self, text: String) -> Self {
        self.text = text;
        self
    }

    pub fn is_empty(&self) -> bool {
        self.text.is_empty()
    }
}

pub fn parse_line(line_number: u64, text: &str) -> LogLine {
    let level = detect_level(text);
    let timestamp = extract_timestamp_from_line(text);
    let format = detect_format(text);

    LogLine {
        text: text.to_string(),
        level,
        timestamp,
        line_number,
        format: Some(format),
    }
}

pub fn detect_format(line: &str) -> LogFormat {
    let line = line.trim();

    if line.is_empty() {
        return LogFormat::Plaintext;
    }

    if line.starts_with('{') || line.starts_with('[') {
        if let Ok(_) = serde_json::from_str::<serde_json::Value>(line) {
            return LogFormat::Json;
        }
    }

    if is_apache_format(line) {
        return LogFormat::Apache;
    }

    if is_syslog_format(line) {
        return LogFormat::Syslog;
    }

    if is_iso8601_format(line) {
        return LogFormat::Iso8601;
    }

    LogFormat::Plaintext
}

fn is_apache_format(line: &str) -> bool {
    let parts: Vec<&str> = line.splitn(4, ' ').collect();
    if parts.len() < 4 {
        return false;
    }

    let has_ip = parts[0].contains('.') || parts[0].contains(':');
    let has_bracket = parts.get(2).map(|s| s.starts_with('[')).unwrap_or(false);
    let has_quote = line.contains('"');

    has_ip && has_bracket && has_quote
}

fn is_syslog_format(line: &str) -> bool {
    let line = line.trim();

    if line.starts_with('<') && line.len() > 3 {
        if let Ok(_) = line[1..3].parse::<u16>() {
            return true;
        }
    }

    let months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    if let Some(first_word) = line.split_whitespace().next() {
        if months.iter().any(|m| *m == first_word) {
            return true;
        }
    }

    false
}

fn is_iso8601_format(line: &str) -> bool {
    let line = line.trim();

    if line.len() < 10 {
        return false;
    }

    let chars: Vec<char> = line.chars().take(10).collect();

    chars[0].is_ascii_digit()
        && chars[1].is_ascii_digit()
        && chars[2].is_ascii_digit()
        && chars[3].is_ascii_digit()
        && chars[4] == '-'
        && chars[5].is_ascii_digit()
        && chars[6].is_ascii_digit()
        && chars[7] == '-'
        && chars[8].is_ascii_digit()
        && chars[9].is_ascii_digit()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_line() {
        let line = parse_line(0, "[INFO] Server started");
        assert_eq!(line.level, Level::Info);
        assert_eq!(line.line_number, 0);
    }

    #[test]
    fn test_parse_line_with_timestamp() {
        let line = parse_line(0, "2024-01-15T10:30:00 ERROR: failed");
        assert_eq!(line.level, Level::Error);
        assert!(line.timestamp.is_some());
    }

    #[test]
    fn test_detect_json() {
        let line = r#"{"level": "info", "message": "test"}"#;
        assert_eq!(detect_format(line), LogFormat::Json);
    }

    #[test]
    fn test_detect_apache() {
        let line = r#"127.0.0.1 - - [15/Jan/2024:10:30:00 +0000] "GET / HTTP/1.1" 200 1234"#;
        assert_eq!(detect_format(line), LogFormat::Apache);
    }

    #[test]
    fn test_detect_syslog() {
        let line = "<134>Jan 15 10:30:00 hostname app: message";
        assert_eq!(detect_format(line), LogFormat::Syslog);
    }

    #[test]
    fn test_detect_iso8601() {
        let line = "2024-01-15T10:30:00 INFO Starting";
        assert_eq!(detect_format(line), LogFormat::Iso8601);
    }

    #[test]
    fn test_detect_plaintext() {
        let line = "some plain log message";
        assert_eq!(detect_format(line), LogFormat::Plaintext);
    }

    #[test]
    fn test_log_line_empty() {
        let line = LogLine::new(0);
        assert!(line.is_empty());

        let line = line.with_text("test".to_string());
        assert!(!line.is_empty());
    }

    #[test]
    fn test_log_format_name() {
        assert_eq!(LogFormat::Json.name(), "JSON");
        assert_eq!(LogFormat::Plaintext.name(), "Plaintext");
    }
}