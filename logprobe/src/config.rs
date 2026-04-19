//! Configuration types for logprobe.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Display configuration settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplaySettings {
    pub line_numbers: bool,
    pub wrap: bool,
    pub tab_width: u32,
    pub max_line_length: u32,
}

impl Default for DisplaySettings {
    fn default() -> Self {
        Self {
            line_numbers: true,
            wrap: false,
            tab_width: 8,
            max_line_length: 10000,
        }
    }
}

/// Performance configuration settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceSettings {
    pub index_cache_size: u64,
    pub read_ahead_lines: u32,
    pub search_workers: u32,
    pub tail_debounce_ms: u64,
}

impl Default for PerformanceSettings {
    fn default() -> Self {
        Self {
            index_cache_size: 100 * 1024 * 1024,
            read_ahead_lines: 1000,
            search_workers: 4,
            tail_debounce_ms: 100,
        }
    }
}

/// Behavior configuration settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BehaviorSettings {
    pub follow_on_open: bool,
    pub auto_reload: bool,
    pub confirm_quit: bool,
    pub search_wrap: bool,
}

impl Default for BehaviorSettings {
    fn default() -> Self {
        Self {
            follow_on_open: false,
            auto_reload: true,
            confirm_quit: false,
            search_wrap: true,
        }
    }
}

/// Files configuration settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FilesSettings {
    pub follow_symlinks: bool,
    pub auto_detect_format: bool,
    pub supported_extensions: Vec<String>,
}

impl Default for FilesSettings {
    fn default() -> Self {
        Self {
            follow_symlinks: true,
            auto_detect_format: true,
            supported_extensions: vec![
                ".log".to_string(),
                ".txt".to_string(),
                ".json".to_string(),
                ".out".to_string(),
            ],
        }
    }
}

/// Key action types for keybindings.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum KeyAction {
    ScrollDown,
    ScrollUp,
    ScrollHalfDown,
    ScrollHalfUp,
    ScrollFullDown,
    ScrollFullUp,
    GoTop,
    GoBottom,
    SearchForward,
    SearchBackward,
    NextMatch,
    PrevMatch,
    ToggleLevelFilter,
    ToggleTimestampFilter,
    SetBookmark,
    JumpBookmark,
    CommandMode,
    Quit,
}

/// Keybinding configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Keybindings {
    pub navigation: Vec<(String, KeyAction)>,
    pub search: Vec<(String, KeyAction)>,
    pub filter: Vec<(String, KeyAction)>,
    pub bookmarks: Vec<(String, KeyAction)>,
    pub general: Vec<(String, KeyAction)>,
}

impl Default for Keybindings {
    fn default() -> Self {
        Self {
            navigation: vec![
                ("j".to_string(), KeyAction::ScrollDown),
                ("k".to_string(), KeyAction::ScrollUp),
                ("g".to_string(), KeyAction::GoTop),
                ("G".to_string(), KeyAction::GoBottom),
                ("d".to_string(), KeyAction::ScrollHalfDown),
                ("u".to_string(), KeyAction::ScrollHalfUp),
            ],
            search: vec![
                ("/".to_string(), KeyAction::SearchForward),
                ("?".to_string(), KeyAction::SearchBackward),
                ("n".to_string(), KeyAction::NextMatch),
                ("N".to_string(), KeyAction::PrevMatch),
            ],
            filter: vec![
                ("l".to_string(), KeyAction::ToggleLevelFilter),
                ("t".to_string(), KeyAction::ToggleTimestampFilter),
            ],
            bookmarks: vec![
                ("m".to_string(), KeyAction::SetBookmark),
                ("'".to_string(), KeyAction::JumpBookmark),
            ],
            general: vec![
                (":".to_string(), KeyAction::CommandMode),
                ("q".to_string(), KeyAction::Quit),
            ],
        }
    }
}

/// Theme colors for different log levels (serialization format).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LevelColorsConfig {
    pub debug: String,
    pub info: String,
    pub warn: String,
    pub error: String,
    pub fatal: String,
}

impl Default for LevelColorsConfig {
    fn default() -> Self {
        Self {
            debug: "#6c7086".to_string(),
            info: "#89b4fa".to_string(),
            warn: "#f9e2af".to_string(),
            error: "#f38ba8".to_string(),
            fatal: "#d20f39".to_string(),
        }
    }
}

/// Theme configuration (serialization format for config files).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThemeConfig {
    pub name: String,
    pub background: String,
    pub foreground: String,
    pub selection: String,
    pub search_match: String,
    pub line_number: String,
    pub levels: LevelColorsConfig,
}

impl Default for ThemeConfig {
    fn default() -> Self {
        Self {
            name: "dark".to_string(),
            background: "#1e1e2e".to_string(),
            foreground: "#cdd6f4".to_string(),
            selection: "#45475a".to_string(),
            search_match: "#f38ba8".to_string(),
            line_number: "#6c7086".to_string(),
            levels: LevelColorsConfig::default(),
        }
    }
}

impl ThemeConfig {
    /// Convert to UI Theme.
    pub fn to_ui_theme(&self) -> crate::ui::Theme {
        use crate::ui::styles::{LevelColors, Theme as UiTheme};

        fn parse_hex(hex: &str) -> ratatui::style::Color {
            let hex = hex.trim_start_matches('#');
            if hex.len() == 6 {
                let r = u8::from_str_radix(&hex[0..2], 16).unwrap_or(30);
                let g = u8::from_str_radix(&hex[2..4], 16).unwrap_or(30);
                let b = u8::from_str_radix(&hex[4..6], 16).unwrap_or(46);
                ratatui::style::Color::RGB(r, g, b)
            } else {
                ratatui::style::Color::RGB(30, 30, 46)
            }
        }

        UiTheme {
            background: parse_hex(&self.background),
            foreground: parse_hex(&self.foreground),
            selection: parse_hex(&self.selection),
            search_match: parse_hex(&self.search_match),
            line_number: parse_hex(&self.line_number),
            levels: LevelColors {
                debug: parse_hex(&self.levels.debug),
                info: parse_hex(&self.levels.info),
                warn: parse_hex(&self.levels.warn),
                error: parse_hex(&self.levels.error),
                fatal: parse_hex(&self.levels.fatal),
            },
            border: parse_hex(&self.selection),
            scrollbar_thumb: parse_hex(&self.levels.debug),
            status_bar: parse_hex(&self.background),
            header: parse_hex(&self.background),
            search_bar: parse_hex(&self.background),
            help_background: parse_hex(&self.selection),
        }
    }
}

/// Light theme configuration variant.
pub fn light_theme_config() -> ThemeConfig {
    ThemeConfig {
        name: "light".to_string(),
        background: "#ffffff".to_string(),
        foreground: "#333333".to_string(),
        selection: "#d4d4d4".to_string(),
        search_match: "#ff5252".to_string(),
        line_number: "#888888".to_string(),
        levels: LevelColorsConfig {
            debug: "#888888".to_string(),
            info: "#2196f3".to_string(),
            warn: "#ffc107".to_string(),
            error: "#f44336".to_string(),
            fatal: "#b71c1c".to_string(),
        },
    }
}

/// Main configuration struct.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub display: DisplaySettings,
    pub performance: PerformanceSettings,
    pub behavior: BehaviorSettings,
    pub files: FilesSettings,
    pub keybindings: Keybindings,
    pub theme: ThemeConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            display: DisplaySettings::default(),
            performance: PerformanceSettings::default(),
            behavior: BehaviorSettings::default(),
            files: FilesSettings::default(),
            keybindings: Keybindings::default(),
            theme: ThemeConfig::default(),
        }
    }
}

impl Config {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_theme(mut self, name: &str) -> Self {
        self.theme = match name {
            "light" => light_theme_config(),
            _ => ThemeConfig::default(),
        };
        self
    }

    pub fn with_keybindings(mut self, keybindings: Keybindings) -> Self {
        self.keybindings = keybindings;
        self
    }

    pub fn load_from_file(path: &PathBuf) -> Result<Self, crate::errors::Error> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)
            .map_err(|e| crate::errors::Error::InvalidRegex(e.to_string()))?;
        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert!(config.display.line_numbers);
        assert!(!config.display.wrap);
        assert_eq!(config.performance.search_workers, 4);
    }

    #[test]
    fn test_with_theme() {
        let config = Config::default().with_theme("light");
        assert_eq!(config.theme.name, "light");
    }

    #[test]
    fn test_with_keybindings() {
        let config = Config::default().with_keybindings(Keybindings::default());
        assert!(!config.keybindings.navigation.is_empty());
    }
}