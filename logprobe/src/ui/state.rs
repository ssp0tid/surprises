//! UI state management for logprobe TUI.
//!
//! Tracks scroll position, selection, view modes, filters, and search state.

use bitvec::prelude::BitVec;
use chrono::{DateTime, Utc};

/// View mode for the log display.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ViewMode {
    /// Normal log viewing mode
    #[default]
    Normal,
    /// Split view (filtered + full side-by-side)
    Split,
    /// Search mode active
    Search,
    /// Filter panel visible
    Filter,
    /// Help popup visible
    Help,
}

/// UI state tracking for the TUI.
///
/// Manages scroll position, selection, and current view mode.
#[derive(Debug, Clone)]
pub struct UIState {
    /// Current scroll offset (top visible line)
    pub scroll: u64,
    /// Currently selected line index
    pub selection: u64,
    /// Current view mode
    pub view_mode: ViewMode,
    /// Total number of lines in the file
    pub total_lines: u64,
    /// Number of visible lines in viewport
    pub visible_lines: u64,
}

impl Default for UIState {
    fn default() -> Self {
        Self {
            scroll: 0,
            selection: 0,
            view_mode: ViewMode::default(),
            total_lines: 0,
            visible_lines: 0,
        }
    }
}

impl UIState {
    /// Check if scroll is at the top.
    pub fn at_top(&self) -> bool {
        self.scroll == 0
    }

    /// Check if scroll is at the bottom.
    pub fn at_bottom(&self) -> bool {
        self.scroll + self.visible_lines >= self.total_lines
    }

    /// Scroll up by specified lines.
    pub fn scroll_up(&mut self, lines: u64) {
        self.scroll = self.scroll.saturating_sub(lines);
        self.selection = self.selection.saturating_sub(lines);
    }

    /// Scroll down by specified lines.
    pub fn scroll_down(&mut self, lines: u64) {
        let max_scroll = self.total_lines.saturating_sub(self.visible_lines);
        self.scroll = (self.scroll + lines).min(max_scroll);
        self.selection = (self.selection + lines).min(self.total_lines.saturating_sub(1));
    }

    /// Go to first line.
    pub fn go_top(&mut self) {
        self.scroll = 0;
        self.selection = 0;
    }

    /// Go to last line.
    pub fn go_bottom(&mut self) {
        self.scroll = self.total_lines.saturating_sub(self.visible_lines);
        self.selection = self.total_lines.saturating_sub(1);
    }

    /// Scroll by a page.
    pub fn page_down(&mut self) {
        self.scroll_down(self.visible_lines.saturating_sub(1));
    }

    /// Scroll by a page up.
    pub fn page_up(&mut self) {
        self.scroll_up(self.visible_lines.saturating_sub(1));
    }

    /// Go to specific line.
    pub fn go_to_line(&mut self, line: u64) {
        let target = line.saturating_sub(1);
        let max_scroll = self.total_lines.saturating_sub(self.visible_lines);
        self.scroll = target.min(max_scroll);
        self.selection = target.min(self.total_lines.saturating_sub(1));
    }

    /// Set total lines and adjust scroll.
    pub fn set_total_lines(&mut self, total: u64) {
        self.total_lines = total;
        if self.scroll > total.saturating_sub(self.visible_lines) {
            self.scroll = total.saturating_sub(self.visible_lines);
        }
    }

    /// Set visible lines.
    pub fn set_visible_lines(&mut self, lines: u64) {
        self.visible_lines = lines;
    }
}

/// Filter state for log level and time filtering.
///
/// Tracks which log levels are visible and the time range filter.
#[derive(Debug, Clone)]
pub struct FilterState {
    /// Enabled log levels (as bitset)
    pub levels: BitVec,
    /// Time range start (inclusive)
    pub time_start: Option<DateTime<Utc>>,
    /// Time range end (inclusive)
    pub time_end: Option<DateTime<Utc>>,
    /// Whether filtering is inverted (show non-matching)
    pub inverted: bool,
    /// Whether level filter is active
    pub level_active: bool,
    /// Whether time filter is active
    pub time_active: bool,
}

impl Default for FilterState {
    fn default() -> Self {
        let mut levels = BitVec::new();
        levels.resize(6, true); // 6 levels: Debug, Info, Warn, Error, Fatal, Unknown
        Self {
            levels,
            time_start: None,
            time_end: None,
            inverted: false,
            level_active: false,
            time_active: false,
        }
    }
}

impl FilterState {
    /// Enable a specific log level.
    pub fn enable_level(&mut self, level: usize) {
        if level < self.levels.len() {
            self.levels.set(level, true);
            self.level_active = true;
        }
    }

    /// Disable a specific log level.
    pub fn disable_level(&mut self, level: usize) {
        if level < self.levels.len() {
            self.levels.set(level, false);
            self.level_active = true;
        }
    }

    /// Toggle a specific log level.
    pub fn toggle_level(&mut self, level: usize) {
        if level < self.levels.len() {
            let current = self.levels.get(level).copied();
            self.levels.set(level, !current);
            self.level_active = true;
        }
    }

    /// Check if a level is enabled.
    pub fn is_level_enabled(&self, level: usize) -> bool {
        self.levels.get(level).copied().unwrap_or(true)
    }

    /// Enable all levels.
    pub fn enable_all_levels(&mut self) {
        self.levels.fill(true);
        self.level_active = false;
    }

    /// Disable all levels (show none).
    pub fn disable_all_levels(&mut self) {
        self.levels.fill(false);
        self.level_active = true;
    }

    /// Set time range filter.
    pub fn set_time_range(&mut self, start: Option<DateTime<Utc>>, end: Option<DateTime<Utc>>) {
        self.time_start = start;
        self.time_end = end;
        self.time_active = start.is_some() || end.is_some();
    }

    /// Clear time range filter.
    pub fn clear_time_range(&mut self) {
        self.time_start = None;
        self.time_end = None;
        self.time_active = false;
    }

    /// Toggle filter inversion.
    pub fn toggle_inverted(&mut self) {
        self.inverted = !self.inverted;
    }

    /// Clear all filters.
    pub fn clear(&mut self) {
        self.enable_all_levels();
        self.clear_time_range();
        self.inverted = false;
    }

    /// Reset state to default (all enabled, no filters).
    pub fn reset(&mut self) {
        *self = Self::default();
    }
}

/// Search mode options.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct SearchOptions {
    /// Case insensitive matching
    pub case_insensitive: bool,
    /// Whole word matching
    pub whole_word: bool,
    /// Regex mode (enabled by default)
    pub regex: bool,
}

/// Search state tracking.
///
/// Manages search pattern, results, and navigation.
#[derive(Debug, Clone)]
pub struct SearchState {
    /// Current search pattern
    pub pattern: Option<String>,
    /// Matched line indices
    pub results: Vec<u64>,
    /// Current result index when navigating
    pub current_index: usize,
    /// Search options
    pub options: SearchOptions,
    /// Whether search is active
    pub active: bool,
    /// Error message if search failed
    pub error: Option<String>,
    /// Search history
    pub history: Vec<String>,
    /// History index for navigation
    pub history_index: Option<usize>,
}

impl Default for SearchState {
    fn default() -> Self {
        Self {
            pattern: None,
            results: Vec::new(),
            current_index: 0,
            options: SearchOptions::default(),
            active: false,
            error: None,
            history: Vec::new(),
            history_index: None,
        }
    }
}

impl SearchState {
    /// Get current pattern as string.
    pub fn pattern_str(&self) -> &str {
        self.pattern.as_deref().unwrap_or("")
    }

    /// Check if there are results.
    pub fn has_results(&self) -> bool {
        !self.results.is_empty()
    }

    /// Get total match count.
    pub fn match_count(&self) -> usize {
        self.results.len()
    }

    /// Get current match position (1-indexed for display).
    pub fn current_position(&self) -> (usize, usize) {
        if self.results.is_empty() {
            (0, 0)
        } else {
            (self.current_index + 1, self.results.len())
        }
    }

    /// Get current result line number.
    pub fn current_line(&self) -> Option<u64> {
        self.results.get(self.current_index).copied()
    }

    /// Set pattern and results.
    pub fn set_results(&mut self, pattern: String, results: Vec<u64>) {
        self.pattern = Some(pattern);
        self.results = results;
        self.current_index = 0;
        self.active = !results.is_empty();
        self.error = None;

        // Add to history if new pattern
        if let Some(ref pat) = self.pattern {
            if !self.history.contains(pat) {
                self.history.push(pat.clone());
            }
        }
    }

    /// Set search error.
    pub fn set_error(&mut self, error: String) {
        self.error = Some(error);
        self.active = false;
    }

    /// Clear search.
    pub fn clear(&mut self) {
        self.pattern = None;
        self.results.clear();
        self.current_index = 0;
        self.active = false;
        self.error = None;
    }

    /// Go to next match.
    pub fn next(&mut self) -> Option<u64> {
        if self.results.is_empty() {
            return None;
        }
        self.current_index = (self.current_index + 1) % self.results.len();
        self.results.get(self.current_index).copied()
    }

    /// Go to previous match.
    pub fn previous(&mut self) -> Option<u64> {
        if self.results.is_empty() {
            return None;
        }
        if self.current_index == 0 {
            self.current_index = self.results.len() - 1;
        } else {
            self.current_index -= 1;
        }
        self.results.get(self.current_index).copied()
    }

    /// Go to specific match index.
    pub fn go_to_index(&mut self, index: usize) -> Option<u64> {
        if index < self.results.len() {
            self.current_index = index;
            return self.results.get(index).copied();
        }
        None
    }

    /// Go to specific line.
    pub fn go_to_line(&mut self, line: u64) -> Option<usize> {
        let idx = self.results.iter().position(|&l| l >= line);
        idx.map(|i| {
            self.current_index = i;
            i
        })
    }

    /// Navigate search history (previous).
    pub fn history_prev(&mut self) -> Option<&str> {
        let idx = match self.history_index {
            None => Some(self.history.len().saturating_sub(1)),
            Some(0) => return None,
            Some(i) => Some(i - 1),
        };
        self.history_index = idx;
        self.history.get(idx).map(|s| s.as_str())
    }

    /// Navigate search history (next).
    pub fn history_next(&mut self) -> Option<&str> {
        let idx = match self.history_index {
            None => return None,
            Some(i) if i >= self.history.len() - 1 => return None,
            Some(i) => Some(i + 1),
        };
        self.history_index = idx;
        self.history.get(idx).map(|s| s.as_str())
    }

    /// Toggle case sensitivity.
    pub fn toggle_case(&mut self) {
        self.options.case_insensitive = !self.options.case_insensitive;
    }

    /// Toggle whole word.
    pub fn toggle_whole_word(&mut self) {
        self.options.whole_word = !self.options.whole_word;
    }
}

/// Bookmarks for quick line navigation.
#[derive(Debug, Clone, Default)]
pub struct BookmarkState {
    /// Bookmarked lines (index a-z)
    pub bookmarks: std::collections::HashMap<char, u64>,
}

impl BookmarkState {
    /// Set bookmark at position.
    pub fn set(&mut self, key: char, line: u64) {
        self.bookmarks.insert(key.to_ascii_lowercase(), line);
    }

    /// Get bookmark position.
    pub fn get(&self, key: char) -> Option<u64> {
        self.bookmarks.get(&key.to_ascii_lowercase()).copied()
    }

    /// Clear bookmark.
    pub fn clear(&mut self, key: char) {
        self.bookmarks.remove(&key.to_ascii_lowercase());
    }

    /// Clear all bookmarks.
    pub fn clear_all(&mut self) {
        self.bookmarks.clear();
    }

    /// Check if bookmark exists.
    pub fn has(&self, key: char) -> bool {
        self.bookmarks.contains_key(&key.to_ascii_lowercase())
    }
}

/// Complete application state.
#[derive(Debug, Clone, Default)]
pub struct AppState {
    /// UI state (scroll, selection, view mode)
    pub ui: UIState,
    /// Filter state (levels, time range)
    pub filters: FilterState,
    /// Search state (pattern, results)
    pub search: SearchState,
    /// Bookmarks
    pub bookmarks: BookmarkState,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ui_state_scroll() {
        let mut state = UIState::default();
        state.total_lines = 1000;
        state.visible_lines = 50;

        state.scroll_down(10);
        assert_eq!(state.scroll, 10);

        state.scroll_up(5);
        assert_eq!(state.scroll, 5);
    }

    #[test]
    fn test_filter_state_levels() {
        let mut state = FilterState::default();

        state.disable_level(2); // WARN
        assert!(!state.is_level_enabled(2));
        assert!(state.is_level_enabled(0));

        state.enable_all_levels();
        assert!(state.is_level_enabled(2));
    }

    #[test]
    fn test_search_state_navigation() {
        let mut state = SearchState::default();
        state.set_results("test".to_string(), vec![10, 20, 30, 40]);

        assert_eq!(state.current_index, 0);
        assert_eq!(state.next(), Some(20));
        assert_eq!(state.current_index, 1);

        assert_eq!(state.previous(), Some(10));
        assert_eq!(state.current_index, 0);
    }

    #[test]
    fn test_bookmarks() {
        let mut bm = BookmarkState::default();
        bm.set('a', 100);
        bm.set('b', 200);

        assert_eq!(bm.get('a'), Some(100));
        assert_eq!(bm.get('b'), Some(200));
        assert_eq!(bm.get('c'), None);

        bm.clear('a');
        assert_eq!(bm.get('a'), None);
    }
}