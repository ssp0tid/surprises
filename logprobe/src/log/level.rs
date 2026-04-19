//! Log level detection module.
//!
//! Provides the `Level` enum and `detect_level()` function for identifying
//! log severity levels from text.

use std::fmt;

/// Log severity levels.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Level {
    /// Debug level - detailed information for debugging.
    Debug,
    /// Info level - general informational messages.
    Info,
    /// Warn level - warning messages indicating potential issues.
    Warn,
    /// Error level - error messages indicating failures.
    Error,
    /// Fatal level - fatal/critical errors causing termination.
    Fatal,
    /// Unknown level - unable to determine level.
    Unknown,
}

impl Level {
    /// Get the display name for this level.
    #[inline]
    pub fn name(&self) -> &'static str {
        match self {
            Level::Debug => "DEBUG",
            Level::Info => "INFO",
            Level::Warn => "WARN",
            Level::Error => "ERROR",
            Level::Fatal => "FATAL",
            Level::Unknown => "UNKNOWN",
        }
    }

    /// Get the short code for this level (used in some log formats).
    #[inline]
    pub fn code(&self) -> &'static str {
        match self {
            Level::Debug => "D",
            Level::Info => "I",
            Level::Warn => "W",
            Level::Error => "E",
            Level::Fatal => "F",
            Level::Unknown => "?",
        }
    }

    /// Check if this level should be shown based on minimum filter level.
    #[inline]
    pub fn passes_filter(&self, min_level: Level) -> bool {
        self.rank() >= min_level.rank()
    }

    /// Get numeric rank for comparison (lower = less severe).
    #[inline]
    fn rank(&self) -> u8 {
        match self {
            Level::Debug => 0,
            Level::Info => 1,
            Level::Warn => 2,
            Level::Error => 3,
            Level::Fatal => 4,
            Level::Unknown => 5,
        }
    }
}

impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name())
    }
}

impl Default for Level {
    #[inline]
    fn default() -> Self {
        Level::Unknown
    }
}

/// Detect log level from text content.
///
/// This function matches the implementation notes in section 11 of the plan:
/// - FATAL/PANIC → Fatal
/// - ERROR/ERR/[E] → Error
/// - WARN/WARNING/[W] → Warn
/// - INFO/[I] → Info
/// - DEBUG/TRACE/[D] → Debug
/// - otherwise → Unknown
///
/// # Examples
///
/// ```
/// use logprobe::log::level::{detect_level, Level};
///
/// assert_eq!(detect_level("[INFO] Starting server..."), Level::Info);
/// assert_eq!(detect_level("2024-01-01 ERROR: connection failed"), Level::Error);
/// assert_eq!(detect_level("WARN - low memory"), Level::Warn);
/// assert_eq!(detect_level("[DEBUG] variable x = 42"), Level::Debug);
/// assert_eq!(detect_level("some plain text"), Level::Unknown);
/// ```
#[inline]
pub fn detect_level(text: &str) -> Level {
    let upper = text.to_uppercase();

    if upper.contains("FATAL") || upper.contains("PANIC") {
        return Level::Fatal;
    }
    if upper.contains("ERROR") || upper.contains("ERR") || text.contains("[E]") || text.contains("[ERR]") {
        return Level::Error;
    }
    if upper.contains("WARN") || upper.contains("WARNING") || text.contains("[W]") {
        return Level::Warn;
    }
    if upper.contains("INFO") || text.contains("[I]") || text.contains("[INF]") {
        return Level::Info;
    }
    if upper.contains("DEBUG") || upper.contains("TRACE") || text.contains("[D]") || text.contains("[TRC]") {
        return Level::Debug;
    }

    Level::Unknown
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_level_fatal() {
        assert_eq!(detect_level("FATAL: panic occurred"), Level::Fatal);
        assert_eq!(detect_level("PANIC at line 42"), Level::Fatal);
        assert_eq!(detect_level("FATAL ERROR: cannot continue"), Level::Fatal);
    }

    #[test]
    fn test_detect_level_error() {
        assert_eq!(detect_level("[ERROR] connection failed"), Level::Error);
        assert_eq!(detect_level("2024-01-01 ERROR: timeout"), Level::Error);
        assert_eq!(detect_level("ERR: invalid argument"), Level::Error);
        assert_eq!(detect_level("[E] Something went wrong"), Level::Error);
    }

    #[test]
    fn test_detect_level_warn() {
        assert_eq!(detect_level("[WARN] low memory"), Level::Warn);
        assert_eq!(detect_level("WARNING: deprecated API"), Level::Warn);
        assert_eq!(detect_level("WARN - disk space low"), Level::Warn);
        assert_eq!(detect_level("[W] Deprecation notice"), Level::Warn);
    }

    #[test]
    fn test_detect_level_info() {
        assert_eq!(detect_level("[INFO] Server started"), Level::Info);
        assert_eq!(detect_level("INFO: processing request"), Level::Info);
        assert_eq!(detect_level("[I] State changed"), Level::Info);
        assert_eq!(detect_level("INFO Starting..."), Level::Info);
    }

    #[test]
    fn test_detect_level_debug() {
        assert_eq!(detect_level("[DEBUG] variable value"), Level::Debug);
        assert_eq!(detect_level("DEBUG: x = 42"), Level::Debug);
        assert_eq!(detect_level("TRACE: entering function"), Level::Debug);
        assert_eq!(detect_level("[D] Loop iteration"), Level::Debug);
    }

    #[test]
    fn test_detect_level_unknown() {
        assert_eq!(detect_level("some plain text"), Level::Unknown);
        assert_eq!(detect_level("2024-01-01 10:30:00 starting"), Level::Unknown);
        assert_eq!(detect_level(""), Level::Unknown);
    }

    #[test]
    fn test_level_display() {
        assert_eq!(format!("{}", Level::Error), "ERROR");
        assert_eq!(format!("{}", Level::Info), "INFO");
    }

    #[test]
    fn test_level_rank() {
        assert!(Level::Fatal.rank() > Level::Error.rank());
        assert!(Level::Error.rank() > Level::Warn.rank());
        assert!(Level::Warn.rank() > Level::Info.rank());
        assert!(Level::Info.rank() > Level::Debug.rank());
    }

    #[test]
    fn test_level_filter() {
        assert!(Level::Error.passes_filter(Level::Debug));
        assert!(Level::Error.passes_filter(Level::Error));
        assert!(!Level::Debug.passes_filter(Level::Error));
    }
}