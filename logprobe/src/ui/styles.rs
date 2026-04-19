//! UI styling and theming for logprobe TUI.
//!
//! Provides Theme struct with color definitions for dark and light themes
//! matching the plan section 12 specifications.

use ratatui::style::{Color, Style};

/// Log level color scheme.
///
/// Each variant maps to a specific color for visual distinction
/// of log severity levels.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LevelColors {
    /// DEBUG level color (gray/muted)
    pub debug: Color,
    /// INFO level color (blue)
    pub info: Color,
    /// WARN level color (yellow)
    pub warn: Color,
    /// ERROR level color (red/pink)
    pub error: Color,
    /// FATAL level color (bright red)
    pub fatal: Color,
}

impl Default for LevelColors {
    fn default() -> Self {
        Self {
            debug: Color::RGB(108, 112, 134),    // #6c7086
            info: Color::RGB(137, 180, 250),    // #89b4fa
            warn: Color::RGB(249, 226, 175),    // #f9e2af
            error: Color::RGB(243, 139, 168),   // #f38ba8
            fatal: Color::RGB(210, 15, 57),     // #d20f39
        }
    }
}

/// Theme configuration for the TUI.
///
/// Defines all color schemes used throughout the UI including
/// background, foreground, selections, and level-specific colors.
///
/// # Colors
///
/// - `background`: Main background color
/// - `foreground`: Primary text color
/// - `selection`: Selected line/region background
/// - `search_match`: Highlight color for search matches
/// - `line_number`: Color for line number display
/// - `levels`: Color scheme per log level
/// - `border`: Border and separator color
/// - `scrollbar`: Scrollbar track and thumb colors
/// - `status_bar`: Status bar background color
/// - `header`: Header background color
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Theme {
    /// Main background color
    pub background: Color,
    /// Primary text and foreground color
    pub foreground: Color,
    /// Selection/highlight background
    pub selection: Color,
    /// Search match highlight color
    pub search_match: Color,
    /// Line number display color
    pub line_number: Color,
    /// Color scheme per log level
    pub levels: LevelColors,
    /// Border and separator color
    pub border: Color,
    /// Scrollbar track color
    pub scrollbar_thumb: Color,
    /// Status bar background color
    pub status_bar: Color,
    /// Header background color
    pub header: Color,
    /// Search bar background
    pub search_bar: Color,
    /// Help popup background
    pub help_background: Color,
}

impl Default for Theme {
    fn default() -> Self {
        Self::dark()
    }
}

impl Theme {
    /// Create the default dark theme.
    ///
    /// Based on the Catppuccin Mocha palette as specified in PLAN.md.
    ///
    /// # Colors
    ///
    /// - Background: #1e1e2e (dark surface)
    /// - Foreground: #cdd6f4 (light text)
    /// - Selection: #45475a (muted selection)
    /// - Search match: #f38ba8 (pink highlight)
    /// - Line numbers: #6c7086 (muted gray)
    /// - Border: #45475a (subtle border)
    pub fn dark() -> Self {
        Self {
            background: Color::RGB(30, 30, 46),      // #1e1e2e
            foreground: Color::RGB(205, 214, 244), // #cdd6f4
            selection: Color::RGB(69, 71, 90),      // #45475a
            search_match: Color::RGB(243, 139, 168), // #f38ba8
            line_number: Color::RGB(108, 112, 134), // #6c7086
            levels: LevelColors::default(),
            border: Color::RGB(69, 71, 90),        // #45475a
            scrollbar_thumb: Color::RGB(108, 112, 134), // #6c7086
            status_bar: Color::RGB(30, 30, 46),     // #1e1e2e
            header: Color::RGB(30, 30, 46),        // #1e1e2e
            search_bar: Color::RGB(24, 24, 37),      // #181825
            help_background: Color::RGB(24, 24, 37), // #181825
        }
    }

    /// Create the light theme.
    ///
    /// Based on the Catppuccin Latte palette.
    ///
    /// # Colors
    ///
    /// - Background: #eff1f5 (light surface)
    /// - Foreground: #4c4f69 (dark text)
    /// - Selection: #ccd0da (light selection)
    /// - Search match: #d20f39 (red highlight)
    /// - Line numbers: #9ca0b0 (muted gray)
    pub fn light() -> Self {
        Self {
            background: Color::RGB(239, 241, 245),  // #eff1f5
            foreground: Color::RGB(76, 79, 105),  // #4c4f69
            selection: Color::RGB(204, 208, 218), // #ccd0da
            search_match: Color::RGB(210, 15, 57), // #d20f39
            line_number: Color::RGB(156, 160, 176), // #9ca0b0
            levels: LevelColors {
                debug: Color::RGB(156, 160, 176),  // #9ca0b0
                info: Color::RGB(32, 98, 200),   // #2062c8
                warn: Color::RGB(190, 137, 11),  // #be891b
                error: Color::RGB(210, 15, 57), // #d20f39
                fatal: Color::RGB(196, 28, 54),  // #c41c36
            },
            border: Color::RGB(204, 208, 218), // #ccd0da
            scrollbar_thumb: Color::RGB(156, 160, 176), // #9ca0b0
            status_bar: Color::RGB(230, 232, 240), // #e6e8f0
            header: Color::RGB(230, 232, 240), // #e6e8f0
            search_bar: Color::RGB(220, 224, 232), // #dce0e8
            help_background: Color::RGB(230, 232, 240), // #e6e8f0
        }
    }

    /// Get style for text content.
    pub fn text_style(self) -> Style {
        Style::default().fg(self.foreground)
    }

    /// Get style for line numbers.
    pub fn line_number_style(self) -> Style {
        Style::default().fg(self.line_number)
    }

    /// Get style for search matches.
    pub fn search_match_style(self) -> Style {
        Style::default().fg(self.search_match).bg(self.search_match).add_modifier(
            ratatui::style::Modifier::REVERSED,
        )
    }

    /// Get style for selection.
    pub fn selection_style(self) -> Style {
        Style::default().bg(self.selection)
    }
}

/// Available theme presets.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ThemePreset {
    #[default]
    Dark,
    Light,
}

impl ThemePreset {
    /// Get the corresponding theme.
    pub fn theme(self) -> Theme {
        match self {
            Self::Dark => Theme::dark(),
            Self::Light => Theme::light(),
        }
    }
}

impl std::fmt::Display for ThemePreset {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Dark => write!(f, "dark"),
            Self::Light => write!(f, "light"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dark_theme_colors() {
        let theme = Theme::dark();
        assert_eq!(theme.background, Color::RGB(30, 30, 46));
        assert_eq!(theme.foreground, Color::RGB(205, 214, 244));
        assert_eq!(theme.search_match, Color::RGB(243, 139, 168));
    }

    #[test]
    fn test_light_theme_colors() {
        let theme = Theme::light();
        assert_eq!(theme.background, Color::RGB(239, 241, 245));
        assert_eq!(theme.foreground, Color::RGB(76, 79, 105));
    }

    #[test]
    fn test_theme_preset() {
        assert_eq!(ThemePreset::Dark.theme(), Theme::dark());
        assert_eq!(ThemePreset::Light.theme(), Theme::light());
    }
}