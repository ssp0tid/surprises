use chrono::{DateTime, NaiveDateTime, TimeZone, Utc};

/// Result of timestamp parsing.
#[derive(Debug, Clone, PartialEq)]
pub enum Timestamp {
    /// DateTime with timezone (UTC).
    DateTime(DateTime<Utc>),
    /// Unix timestamp in seconds.
    UnixSeconds(i64),
    /// Unix timestamp in milliseconds.
    UnixMillis(i64),
    /// Extracted string representation (unparsed).
    Raw(String),
}

impl Timestamp {
    pub fn as_datetime(&self) -> Option<DateTime<Utc>> {
        match self {
            Timestamp::DateTime(dt) => Some(*dt),
            _ => None,
        }
    }

    pub fn as_unix_seconds(&self) -> Option<i64> {
        match self {
            Timestamp::UnixSeconds(s) => Some(*s),
            Timestamp::UnixMillis(ms) => Some(*ms / 1000),
            Timestamp::DateTime(dt) => Some(dt.timestamp()),
            _ => None,
        }
    }
}

/// Format hints for timestamp parsing.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TimestampFormat {
    Iso8601,
    Apache,
    Syslog,
    UnixSeconds,
    UnixMillis,
    Plaintext,
}

/// Parse timestamp from a string.
///
/// Tries formats in order:
/// 1. ISO 8601 with timezone
/// 2. ISO 8601 without timezone (assume UTC)
/// 3. Apache/Nginx combined log
/// 4. Syslog (month day timestamp)
/// 5. Unix timestamp (seconds)
/// 6. Unix timestamp (milliseconds)
pub fn parse_timestamp(text: &str) -> Option<Timestamp> {
    let text = text.trim();

    if text.is_empty() {
        return None;
    }

    if let Some(ts) = try_iso8601_with_tz(text) {
        return Some(ts);
    }

    if let Some(ts) = try_iso8601_without_tz(text) {
        return Some(ts);
    }

    if let Some(ts) = try_apache_format(text) {
        return Some(ts);
    }

    if let Some(ts) = try_syslog_format(text) {
        return Some(ts);
    }

    if let Some(ts) = try_unix_timestamp(text) {
        return Some(ts);
    }

    None
}

fn try_iso8601_with_tz(text: &str) -> Option<Timestamp> {
    // Try ISO 8601 with timezone: 2024-01-15T10:30:00.123Z or 2024-01-15T10:30:00+05:30
    let formats = [
        "%Y-%m-%dT%H:%M:%S%.f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%dT%H:%M:%S",
    ];

    for fmt in formats {
        if let Ok(dt) = DateTime::parse_from_str(text, fmt) {
            return Some(Timestamp::DateTime(dt.with_timezone(&Utc)));
        }
    }

    None
}

fn try_iso8601_without_tz(text: &str) -> Option<Timestamp> {
    // Try ISO 8601 without timezone, assume UTC
    let formats = [
        "%Y-%m-%d %H:%M:%S%.f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%dT%H:%M:%S",
    ];

    for fmt in formats {
        if let Ok(naive) = NaiveDateTime::parse_from_str(text, fmt) {
            return Some(Timestamp::DateTime(Utc.from_utc_datetime(&naive)));
        }
    }

    None
}

fn try_apache_format(text: &str) -> Option<Timestamp> {
    // Apache/Nginx: 15/Jan/2024:10:30:00 +0000
    let fmt = "%d/%b/%Y:%H:%M:%S %z";
    if let Ok(dt) = DateTime::parse_from_str(text, fmt) {
        return Some(Timestamp::DateTime(dt.with_timezone(&Utc)));
    }
    None
}

fn try_syslog_format(text: &str) -> Option<Timestamp> {
    // Syslog: Jan 15 10:30:00 (no year, use current year)
    let fmt = "%b %d %H:%M:%S";
    if let Ok(naive) = NaiveDateTime::parse_from_str(text, fmt) {
        let current_year = Utc::now().year();
        let full = format!("{}-{:02}-{:02} {:02}:{:02}:{:02}",
            current_year, naive.month(), naive.day(), naive.hour(), naive.minute(), naive.second());
        if let Ok(full_naive) = NaiveDateTime::parse_from_str(&full, "%Y-%m-%d %H:%M:%S") {
            return Some(Timestamp::DateTime(Utc.from_utc_datetime(&full_naive)));
        }
    }
    None
}

fn try_unix_timestamp(text: &str) -> Option<Timestamp> {
    // Try as plain number
    if let Ok(seconds) = text.parse::<i64>() {
        // Determine if seconds or milliseconds based on magnitude
        // Unix timestamp in seconds is typically < 2^31 (until 2038)
        // Unix timestamp in milliseconds is typically > 1e9
        if seconds < 1_000_000_000 {
            return Some(Timestamp::UnixSeconds(seconds));
        } else if seconds < 10_000_000_000 {
            return Some(Timestamp::UnixMillis(seconds));
        }
    }
    None
}

/// Extract timestamp from a log line.
///
/// Searches for timestamp patterns at the beginning of the line or in known positions.
pub fn extract_timestamp_from_line(line: &str) -> Option<Timestamp> {
    let line = line.trim();

    if line.is_empty() {
        return None;
    }

    // Try the full line first
    if let Some(ts) = parse_timestamp(line) {
        return Some(ts);
    }

    // Try first word
    if let Some(first) = line.split_whitespace().next() {
        if let Some(ts) = parse_timestamp(first) {
            return Some(ts);
        }
    }

    // Try first 32 chars (common timestamp length)
    if line.len() > 32 {
        if let Some(ts) = parse_timestamp(&line[..32]) {
            return Some(ts);
        }
    }

    None
}

/// Detect the format of a timestamp in the given text.
pub fn detect_timestamp_format(text: &str) -> TimestampFormat {
    let text = text.trim();

    if text.is_empty() {
        return TimestampFormat::Plaintext;
    }

    // ISO 8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    if text.len() >= 10 && text.chars().next().map(|c| c.is_ascii_digit()).unwrap_or(false) {
        if text.contains('T') || text.contains('-') {
            return TimestampFormat::Iso8601;
        }
    }

    // Apache: DD/Mon/YYYY or DD/Mon/YYYY:HH:MM:SS
    if text.len() >= 5 && text.contains('/') && text.contains(':') {
        if text.chars().nth(2).map(|c| c == '/').unwrap_or(false) {
            return TimestampFormat::Apache;
        }
    }

    // Syslog: Mon DD HH:MM:SS
    if text.len() >= 6 && !text.chars().next().map(|c| c.is_ascii_digit()).unwrap_or(false) {
        if !text.contains('/') {
            return TimestampFormat::Syslog;
        }
    }

    // Unix: all digits
    if text.chars().all(|c| c.is_ascii_digit()) {
        if text.len() <= 10 {
            return TimestampFormat::UnixSeconds;
        } else {
            return TimestampFormat::UnixMillis;
        }
    }

    TimestampFormat::Plaintext
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_iso8601_with_tz() {
        let ts = parse_timestamp("2024-01-15T10:30:00Z").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));

        let ts = parse_timestamp("2024-01-15T10:30:00+05:30").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));
    }

    #[test]
    fn test_parse_iso8601_without_tz() {
        let ts = parse_timestamp("2024-01-15 10:30:00").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));

        let ts = parse_timestamp("2024-01-15T10:30:00").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));
    }

    #[test]
    fn test_parse_iso8601_millis() {
        let ts = parse_timestamp("2024-01-15T10:30:00.123Z").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));
    }

    #[test]
    fn test_parse_unix_seconds() {
        let ts = parse_timestamp("1705315800").unwrap();
        assert!(matches!(ts, Timestamp::UnixSeconds(s) if s == 1705315800));
    }

    #[test]
    fn test_parse_unix_millis() {
        let ts = parse_timestamp("1705315800000").unwrap();
        assert!(matches!(ts, Timestamp::UnixMillis(ms) if ms == 1705315800000));
    }

    #[test]
    fn test_parse_invalid() {
        assert!(parse_timestamp("").is_none());
        assert!(parse_timestamp("not a timestamp").is_none());
    }

    #[test]
    fn test_extract_timestamp_from_line() {
        let ts = extract_timestamp_from_line("2024-01-15T10:30:00 ERROR: failed").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));

        let ts = extract_timestamp_from_line("2024-01-15 10:30:00 [INFO] Something").unwrap();
        assert!(matches!(ts, Timestamp::DateTime(_)));
    }

    #[test]
    fn test_detect_format() {
        assert_eq!(detect_timestamp_format("2024-01-15T10:30:00"), TimestampFormat::Iso8601);
        assert_eq!(detect_timestamp_format("15/Jan/2024:10:30:00"), TimestampFormat::Apache);
        assert_eq!(detect_timestamp_format("Jan 15 10:30:00"), TimestampFormat::Syslog);
        assert_eq!(detect_timestamp_format("1705315800"), TimestampFormat::UnixSeconds);
    }

    #[test]
    fn test_timestamp_conversions() {
        let ts = parse_timestamp("2024-01-15T10:30:00Z").unwrap();
        assert!(ts.as_datetime().is_some());
        assert!(ts.as_unix_seconds().is_some());
    }
}