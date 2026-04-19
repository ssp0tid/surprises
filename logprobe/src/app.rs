//! Application state and key handling for logprobe.
//!
//! Manages the application state, routes key events to handlers,
//! and coordinates between UI, search, filters, and bookmarks.

use crate::config::Config;
use crate::errors::Error;
use crate::log::{LogFile, LogLine};
use crate::search::{SearchEngine, SearchOptions, RegexOptions};
use crate::ui::state::{
    AppState, BookmarkState, FilterState, SearchState, UIState, ViewMode,
};
use crate::ui::Theme;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::mpsc;

/// Application mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AppMode {
    /// Normal navigation mode
    #[default]
    Normal,
    /// Search input mode
    Search,
    /// Command input mode
    Command,
    /// Filter selection mode
    Filter,
}

/// Main application struct.
pub struct App {
    /// Log file being viewed
    pub(crate) log_file: LogFile,
    /// Application state
    pub(crate) state: AppState,
    /// Search engine
    pub(crate) search_engine: SearchEngine,
    /// Configuration
    pub(crate) config: Config,
    /// Current mode
    pub(crate) mode: AppMode,
    /// Command input buffer
    pub(crate) command_buffer: String,
    /// Search input buffer
    pub(crate) search_buffer: String,
    /// Theme
    pub(crate) theme: Theme,
    /// Follow mode (tail -f)
    pub(crate) following: bool,
    /// File watcher handle
    #[allow(dead_code)]
    pub(crate) watcher: Option<notify::RecommendedWatcher>,
}

impl App {
    /// Create a new application instance.
    pub async fn new(path: PathBuf, config: Config) -> Result<Self, Error> {
        let log_file = LogFile::open(&path).map_err(|e| Error::Io(std::io::Error::new(
            std::io::ErrorKind::Other,
            e.to_string(),
        )))?;

        let theme = Theme::dark();
        let search_engine = SearchEngine::with_defaults();

        let total_lines = log_file.line_count() as u64;

        let mut state = AppState::default();
        state.ui.total_lines = total_lines;

        Ok(Self {
            log_file,
            state,
            search_engine,
            config,
            mode: AppMode::Normal,
            command_buffer: String::new(),
            search_buffer: String::new(),
            theme,
            following: false,
            watcher: None,
        })
    }

    /// Set the theme.
    pub fn set_theme(&mut self, theme: Theme) {
        self.theme = theme;
    }

    /// Get current theme.
    pub fn theme(&self) -> &Theme {
        &self.theme
    }

    /// Get app state.
    pub fn state(&self) -> &AppState {
        &self.state
    }

    /// Get mutable app state.
    pub fn state_mut(&mut self) -> &mut AppState {
        &mut self.state
    }

    /// Get mode.
    pub fn mode(&self) -> AppMode {
        self.mode
    }

    /// Get following mode.
    pub fn is_following(&self) -> bool {
        self.following
    }

    /// Toggle follow mode.
    pub fn toggle_follow(&mut self) {
        self.following = !self.following;
        if self.following {
            self.state.ui.view_mode = ViewMode::Normal;
        }
    }

    /// Get lines for display.
    pub fn get_visible_lines(&self, start: u64, count: usize) -> Vec<LogLine> {
        self.log_file
            .read_lines(start as usize, count)
            .unwrap_or_default()
    }

    /// Get total lines.
    pub fn total_lines(&self) -> u64 {
        self.state.ui.total_lines
    }

    /// Handle a key event.
    pub fn handle_key_event(&mut self, event: KeyEvent) -> bool {
        match self.mode {
            AppMode::Normal => self.handle_normal_key(event),
            AppMode::Search => self.handle_search_key(event),
            AppMode::Command => self.handle_command_key(event),
            AppMode::Filter => self.handle_filter_key(event),
        }
    }

    /// Handle key in normal mode.
    fn handle_normal_key(&mut self, event: KeyEvent) -> bool {
        let handled = match event.code {
            // Navigation
            KeyCode::Char('j') | KeyCode::Down => {
                self.scroll_down(1);
                true
            }
            KeyCode::Char('k') | KeyCode::Up => {
                self.scroll_up(1);
                true
            }
            KeyCode::Char('g') => {
                self.go_to_top();
                true
            }
            KeyCode::Char('G') => {
                self.go_to_bottom();
                true
            }
            KeyCode::Char('d') => {
                if event.modifiers.contains(KeyModifiers::CONTROL) {
                    self.page_down();
                } else {
                    self.scroll_down(self.state.ui.visible_lines / 2);
                }
                true
            }
            KeyCode::Char('u') => {
                if event.modifiers.contains(KeyModifiers::CONTROL) {
                    self.page_up();
                } else {
                    self.scroll_up(self.state.ui.visible_lines / 2);
                }
                true
            }
            KeyCode::Char('f') | KeyCode::PageDown => {
                self.page_down();
                true
            }
            KeyCode::Char('b') | KeyCode::PageUp => {
                self.page_up();
                true
            }

            // Search
            KeyCode::Char('/') => {
                self.mode = AppMode::Search;
                self.search_buffer.clear();
                self.state.search.clear();
                true
            }
            KeyCode::Char('?') => {
                self.mode = AppMode::Search;
                self.search_buffer.clear();
                self.state.search.clear();
                true
            }
            KeyCode::Char('n') => {
                self.next_match();
                true
            }
            KeyCode::Char('N') => {
                self.previous_match();
                true
            }

            // Filters
            KeyCode::Char('l') => {
                self.mode = AppMode::Filter;
                self.state.ui.view_mode = ViewMode::Filter;
                true
            }
            KeyCode::Char('t') => {
                // Toggle time filter - simplified for now
                true
            }
            KeyCode::Char('v') => {
                self.state.filters.toggle_inverted();
                true
            }
            KeyCode::Ctrl('r') => {
                self.state.filters.clear();
                true
            }

            // Bookmarks
            KeyCode::Char('m') => {
                // Next char is bookmark key - simplified handling
                true
            }

            // View modes
            KeyCode::Char('s') => {
                if self.state.ui.view_mode == ViewMode::Split {
                    self.state.ui.view_mode = ViewMode::Normal;
                } else {
                    self.state.ui.view_mode = ViewMode::Split;
                }
                true
            }

            // Help
            KeyCode::F(1) => {
                if self.state.ui.view_mode == ViewMode::Help {
                    self.state.ui.view_mode = ViewMode::Normal;
                } else {
                    self.state.ui.view_mode = ViewMode::Help;
                }
                true
            }

            // Quit
            KeyCode::Char('q') | KeyCode::Ctrl('c') => {
                return false;
            }
            KeyCode::Ctrl('q') => {
                return false;
            }

            // Escape to cancel
            KeyCode::Esc => {
                if self.state.ui.view_mode != ViewMode::Normal {
                    self.state.ui.view_mode = ViewMode::Normal;
                }
                true
            }

            _ => false,
        };

        handled
    }

    /// Handle key in search mode.
    fn handle_search_key(&mut self, event: KeyEvent) -> bool {
        match event.code {
            KeyCode::Esc => {
                self.mode = AppMode::Normal;
                self.search_buffer.clear();
                self.state.search.clear();
                true
            }
            KeyCode::Enter => {
                self.execute_search();
                self.mode = AppMode::Normal;
                true
            }
            KeyCode::Backspace => {
                self.search_buffer.pop();
                true
            }
            KeyCode::Char(c) => {
                self.search_buffer.push(c);
                true
            }
            KeyCode::Up => {
                if let Some(prev) = self.state.search.history_prev() {
                    self.search_buffer = prev.to_string();
                }
                true
            }
            KeyCode::Down => {
                if let Some(next) = self.state.search.history_next() {
                    self.search_buffer = next.to_string();
                }
                true
            }
            _ => false,
        }
    }

    /// Handle key in command mode.
    fn handle_command_key(&mut self, event: KeyEvent) -> bool {
        match event.code {
            KeyCode::Esc => {
                self.mode = AppMode::Normal;
                self.command_buffer.clear();
                true
            }
            KeyCode::Enter => {
                self.execute_command();
                self.command_buffer.clear();
                self.mode = AppMode::Normal;
                true
            }
            KeyCode::Backspace => {
                self.command_buffer.pop();
                true
            }
            KeyCode::Char(c) => {
                self.command_buffer.push(c);
                true
            }
            _ => false,
        }
    }

    /// Handle key in filter mode.
    fn handle_filter_key(&mut self, event: KeyEvent) -> bool {
        match event.code {
            KeyCode::Esc => {
                self.mode = AppMode::Normal;
                self.state.ui.view_mode = ViewMode::Normal;
                true
            }
            KeyCode::Char('d') => {
                self.state.filters.disable_level(0); // DEBUG
                true
            }
            KeyCode::Char('i') => {
                self.state.filters.toggle_level(1); // INFO
                true
            }
            KeyCode::Char('w') => {
                self.state.filters.toggle_level(2); // WARN
                true
            }
            KeyCode::Char('e') => {
                self.state.filters.toggle_level(3); // ERROR
                true
            }
            KeyCode::Char('f') => {
                self.state.filters.toggle_level(4); // FATAL
                true
            }
            KeyCode::Char('a') => {
                self.state.filters.enable_all_levels();
                true
            }
            KeyCode::Char('r') => {
                self.state.filters.clear();
                true
            }
            _ => false,
        }
    }

    /// Execute search.
    fn execute_search(&mut self) {
        if self.search_buffer.is_empty() {
            return;
        }

        let lines: Vec<String> = self.log_file
            .read_lines(0, self.state.ui.total_lines as usize)
            .unwrap_or_default()
            .iter()
            .map(|l| l.text.clone())
            .collect();

        let options = SearchOptions {
            case_insensitive: self.state.search.options.case_insensitive,
            whole_word: self.state.search.options.whole_word,
            regex: true,
        };

        match self.search_engine.search(&self.search_buffer, &lines, options) {
            Ok(matches) => {
                let line_nums: Vec<u64> = matches.iter().map(|m| m.line as u64).collect();
                self.state.search.set_results(self.search_buffer.clone(), line_nums);

                if let Some(line) = self.state.search.current_line() {
                    self.state.ui.go_to_line(line);
                }
            }
            Err(e) => {
                self.state.search.set_error(e.to_string());
            }
        }
    }

    /// Execute command.
    fn execute_command(&mut self) {
        let cmd = self.command_buffer.trim();
        if cmd.is_empty() {
            return;
        }

        if cmd == "q" || cmd == "quit" {
            // Will be handled externally
        } else if cmd == "wq" || cmd == "x" {
            // Save and quit - nothing to save for now
        } else if let Some(line_str) = cmd.strip_prefix("goto ") {
            if let Ok(line) = line_str.parse::<u64>() {
                self.state.ui.go_to_line(line);
            }
        } else if let Some(theme) = cmd.strip_prefix("set theme=") {
            if theme == "dark" {
                self.theme = Theme::dark();
            } else if theme == "light" {
                self.theme = Theme::light();
            }
        } else if cmd.starts_with('/') {
            self.search_buffer = cmd[1..].to_string();
            self.execute_search();
        }
    }

    /// Scroll down by lines.
    fn scroll_down(&mut self, lines: u64) {
        self.state.ui.scroll_down(lines);
    }

    /// Scroll up by lines.
    fn scroll_up(&mut self, lines: u64) {
        self.state.ui.scroll_up(lines);
    }

    /// Go to top.
    fn go_to_top(&mut self) {
        self.state.ui.go_top();
    }

    /// Go to bottom.
    fn go_to_bottom(&mut self) {
        self.state.ui.go_to_bottom();
        if self.following {
            self.state.ui.go_to_bottom();
        }
    }

    /// Page down.
    fn page_down(&mut self) {
        self.state.ui.page_down();
    }

    /// Page up.
    fn page_up(&mut self) {
        self.state.ui.page_up();
    }

    /// Go to next search match.
    fn next_match(&mut self) {
        if let Some(line) = self.state.search.next() {
            self.state.ui.go_to_line(line);
        }
    }

    /// Go to previous search match.
    fn previous_match(&mut self) {
        if let Some(line) = self.state.search.previous() {
            self.state.ui.go_to_line(line);
        }
    }

    /// Set bookmark.
    pub fn set_bookmark(&mut self, key: char) {
        self.state.bookmarks.set(key, self.state.ui.selection);
    }

    /// Go to bookmark.
    pub fn go_to_bookmark(&mut self, key: char) {
        if let Some(line) = self.state.bookmarks.get(key) {
            self.state.ui.go_to_line(line);
        }
    }

    /// Reload file.
    pub fn reload(&mut self) -> Result<(), Error> {
        self.log_file.refresh().map_err(|e| Error::Io(std::io::Error::new(
            std::io::ErrorKind::Other,
            e.to_string(),
        )))?;
        let total_lines = self.log_file.line_count() as u64;
        self.state.ui.set_total_lines(total_lines);
        Ok(())
    }

    /// Refresh state (e.g., after resize).
    pub fn refresh(&mut self, visible_lines: u64) {
        self.state.ui.set_visible_lines(visible_lines);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_mode_default() {
        assert_eq!(AppMode::Normal, AppMode::default());
    }
}
