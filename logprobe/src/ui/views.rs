//! Custom views and widgets for logprobe TUI.
//!
//! Implements LogView, SearchBar, FilterPanel, StatusBar, HelpPopup,
//! and LineContent for rendering individual log lines with level colors.

use ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::{LineNumber, Style, Stylize},
    text::Line,
    widgets::{Paragraph, Scrollbar, ScrollbarOrientation, StatefulWidget, Widget},
    Frame,
};
use std::sync::Arc;

use super::state::{AppState, FilterState, SearchState, UIState, ViewMode};
use super::styles::Theme;

/// Log level for coloring.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Level {
    Debug,
    Info,
    Warn,
    Error,
    Fatal,
    Unknown,
}

impl Level {
    pub fn to_color(self, theme: &Theme) -> ratatui::style::Color {
        match self {
            Level::Debug => theme.levels.debug,
            Level::Info => theme.levels.info,
            Level::Warn => theme.levels.warn,
            Level::Error => theme.levels.error,
            Level::Fatal => theme.levels.fatal,
            Level::Unknown => theme.foreground,
        }
    }

    /// Detect level from log text.
    pub fn from_text(text: &str) -> Self {
        let upper = text.to_uppercase();
        if upper.contains("FATAL") || upper.contains("PANIC") {
            Level::Fatal
        } else if upper.contains("ERROR") || upper.contains("ERR") || upper.contains("[E]") {
            Level::Error
        } else if upper.contains("WARN") || upper.contains("WARNING") || upper.contains("[W]") {
            Level::Warn
        } else if upper.contains("INFO") || upper.contains("[I]") {
            Level::Info
        } else if upper.contains("DEBUG") || upper.contains("TRACE") || upper.contains("[D]") {
            Level::Debug
        } else {
            Level::Unknown
        }
    }
}

/// Parsed log line data.
#[derive(Debug, Clone)]
pub struct LogLineData {
    pub line_number: u64,
    pub text: String,
    pub level: Level,
    pub matches: Vec<(usize, usize)>,
}

/// LineContent: Renders a single log line with level-based coloring.
pub struct LineContent<'a> {
    pub data: &'a LogLineData,
    pub selected: bool,
    pub show_line_number: bool,
    pub theme: &'a Theme,
    pub highlight_matches: bool,
}

impl<'a> LineContent<'a> {
    pub fn new(data: &'a LogLineData, theme: &'a Theme) -> Self {
        Self {
            data,
            selected: false,
            show_line_number: true,
            theme,
            highlight_matches: true,
        }
    }

    pub fn with_selection(mut self, selected: bool) -> Self {
        self.selected = selected;
        self
    }

    pub fn with_line_numbers(mut self, show: bool) -> Self {
        self.show_line_number = show;
        self
    }
}

impl Widget for LineContent<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if area.width == 0 {
            return;
        }

        let level = self.data.level;
        let level_color = level.to_color(self.theme);

        let mut line = Line::from("");

        if self.show_line_number {
            let ln = format!("{:>6} ", self.data.line_number);
            line = line.push_span(
                ratatui::text::Span::raw(ln).fg(self.theme.line_number)
            );
        }

        if self.highlight_matches && !self.data.matches.is_empty() {
            let text = &self.data.text;
            let mut last_end = 0;

            for (start, end) in &self.data.matches {
                if *start > last_end {
                    line = line.push_span(
                        ratatui::text::Span::raw(&text[last_end..*start]).fg(level_color)
                    );
                }
                line = line.push_span(
                    ratatui::text::Span::raw(&text[*start..*end])
                        .fg(self.theme.search_match)
                        .bg(self.theme.search_match)
                        .add_modifier(ratatui::style::Modifier::REVERSED)
                );
                last_end = *end;
            }

            if last_end < text.len() {
                line = line.push_span(
                    ratatui::text::Span::raw(&text[last_end..]).fg(level_color)
                );
            }
        } else {
            line = line.push_span(
                ratatui::text::Span::raw(&self.data.text).fg(level_color)
            );
        }

        let style = if self.selected {
            Style::default().bg(self.theme.selection)
        } else {
            Style::default()
        };

        let mut paragraph = Paragraph::new(line);
        paragraph = paragraph.style(style);

        if self.selected {
            paragraph = paragraph.bg(self.theme.selection);
        }

        paragraph.render(area, buf);
    }
}

/// LogView: Main log display widget with scrolling.
pub struct LogView {
    pub lines: Vec<LogLineData>,
    pub theme: Arc<Theme>,
    pub show_line_numbers: bool,
}

impl LogView {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self {
            lines: Vec::new(),
            theme,
            show_line_numbers: true,
        }
    }

    pub fn with_lines(mut self, lines: Vec<LogLineData>) -> Self {
        self.lines = lines;
        self
    }

    pub fn with_line_numbers(mut self, show: bool) -> Self {
        self.show_line_numbers = show;
        self
    }
}

impl StatefulWidget for LogView {
    type State = LogViewState;

    fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
        if area.width == 0 || area.height == 0 {
            return;
        }

        let visible_lines = state.visible_lines as usize;
        let start = state.scroll_offset as usize;
        let end = (start + visible_lines).min(self.lines.len());

        let available_width = if self.show_line_numbers {
            area.width.saturating_sub(8)
        } else {
            area.width
        };

        for (i, line_idx) in (start..end).enumerate() {
            let y = area.y + i as u16;
            if y >= area.y + area.height {
                break;
            }

            if let Some(line_data) = self.lines.get(line_idx) {
                let line_area = Rect::new(area.x, y, area.x + available_width, y + 1);
                let is_selected = line_idx == state.selected_line;

                LineContent::new(line_data, &self.theme)
                    .with_selection(is_selected)
                    .with_line_numbers(self.show_line_numbers)
                    .render(line_area, buf);
            }
        }

        if state.show_scrollbar && self.lines.len() > visible_lines {
            let scrollbar = Scrollbar::new(
                ScrollbarOrientation::VerticalRight,
            )
            .begin_symbol(Some("▲"))
            .end_symbol(Some("▼"))
            .track_symbol(Some("░"))
            .thumb_symbol("█")
            .style(Style::default().fg(self.theme.scrollbar_thumb));

            let sb_area = Rect::new(
                area.x + area.width - 1,
                area.y,
                area.x + area.width,
                area.height,
            );
            scrollbar.render(sb_area, buf);
        }
    }
}

/// State for LogView widget.
#[derive(Debug, Clone)]
pub struct LogViewState {
    pub scroll_offset: u64,
    pub selected_line: u64,
    pub visible_lines: u64,
    pub show_scrollbar: bool,
}

impl Default for LogViewState {
    fn default() -> Self {
        Self {
            scroll_offset: 0,
            selected_line: 0,
            visible_lines: 24,
            show_scrollbar: true,
        }
    }
}

/// SearchBar: Search input widget.
pub struct SearchBar {
    pub placeholder: String,
    pub theme: Arc<Theme>,
}

impl SearchBar {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self {
            placeholder: "/".to_string(),
            theme,
        }
    }

    pub fn with_placeholder(mut self, placeholder: &str) -> Self {
        self.placeholder = placeholder.to_string();
        self
    }
}

impl StatefulWidget for SearchBar {
    type State = SearchBarState;

    fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
        if area.width < 3 {
            return;
        }

        let prefix = if state.backward { "?" } else { "/" };

        let content = if state.input.is_empty() {
            self.placeholder.clone()
        } else {
            state.input.clone()
        };

        let display_text = if state.selected {
            format!("{}{}", prefix, content)
        } else {
            format!("{} {}", prefix, content)
        };

        let style = if state.selected {
            Style::default().fg(self.theme.foreground).bg(self.theme.selection)
        } else {
            Style::default().fg(self.theme.foreground)
        };

        let line = Line::from(display_text).style(style);
        let mut paragraph = Paragraph::new(line);
        paragraph = paragraph.style(style);

        paragraph.render(area, buf);

        if state.error.is_some() {
            let error_text = state.error.as_ref().unwrap();
            let error_area = Rect::new(
                area.x + 1,
                area.y + 1,
                area.x + area.width,
                area.y + 2,
            );
            let error_line = Line::from(error_text.clone())
                .fg(self.theme.levels.fatal);
            let error_p = Paragraph::new(error_line);
            error_p.render(error_area, buf);
        }
    }
}

/// State for SearchBar widget.
#[derive(Debug, Clone)]
pub struct SearchBarState {
    pub input: String,
    pub selected: bool,
    pub backward: bool,
    pub cursor_position: usize,
    pub error: Option<String>,
}

impl Default for SearchBarState {
    fn default() -> Self {
        Self {
            input: String::new(),
            selected: false,
            backward: false,
            cursor_position: 0,
            error: None,
        }
    }
}

/// FilterPanel: Level filter checkbox panel.
pub struct FilterPanel {
    pub theme: Arc<Theme>,
}

impl FilterPanel {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self { theme }
    }
}

impl StatefulWidget for FilterPanel {
    type State = FilterPanelState;

    fn render(self, area: Rect, buf: &mut Buffer, state: &mut Self::State) {
        if area.width < 15 {
            return;
        }

        let levels = [
            (Level::Debug, "DEBUG"),
            (Level::Info, "INFO"),
            (Level::Warn, "WARN"),
            (Level::Error, "ERROR"),
            (Level::Fatal, "FATAL"),
            (Level::Unknown, "UNKNOWN"),
        ];

        for (i, (level, name)) in levels.iter().enumerate() {
            let y = area.y + i as u16;
            if y >= area.y + area.height {
                break;
            }

            let checkbox = if state.enabled_levels[i] { "[x]" } else { "[ ]" };
            let color = level.to_color(&self.theme);

            let text = format!("{} {}", checkbox, name);
            let line = Line::from(text).fg(color);

            let is_selected = i as u16 == state.selected_index;
            let style = if is_selected {
                Style::default().bg(self.theme.selection)
            } else {
                Style::default()
            };

            let checkbox_area = Rect::new(area.x, y, area.x + area.width, y + 1);
            let paragraph = Paragraph::new(line.style(style));
            paragraph.render(checkbox_area, buf);
        }
    }
}

/// State for FilterPanel widget.
#[derive(Debug, Clone)]
pub struct FilterPanelState {
    pub enabled_levels: Vec<bool>,
    pub selected_index: u16,
}

impl Default for FilterPanelState {
    fn default() -> Self {
        Self {
            enabled_levels: vec![true; 6],
            selected_index: 0,
        }
    }
}

/// StatusBar: Bottom status display.
pub struct StatusBar {
    pub theme: Arc<Theme>,
}

impl StatusBar {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self { theme }
    }

    pub fn render_state(&self, area: Rect, buf: &mut Buffer, app_state: &AppState) {
        if area.width < 10 {
            return;
        }

        let mut left_parts = Vec::new();

        left_parts.push(format!("Lines: {}", app_state.ui.total_lines));

        if app_state.filters.level_active || app_state.filters.time_active {
            let active: Vec<&str> = [
                (app_state.filters.level_active, "levels"),
                (app_state.filters.time_active, "time"),
            ]
            .iter()
            .filter(|(active, _)| *active)
            .map(|(_, name)| *name)
            .collect();

            if !active.is_empty() {
                left_parts.push(format!("Filter: {}", active.join(",")));
            }
        }

        if app_state.search.active {
            let (current, total) = app_state.search.current_position();
            if total > 0 {
                left_parts.push(format!("Match: {}/{}", current, total));
            }
        }

        let left_text = left_parts.join(" | ");

        let mut right_parts = Vec::new();

        right_parts.push(format!("{:?}", app_state.ui.view_mode));

        if app_state.ui.view_mode == ViewMode::Search {
            if app_state.search.options.case_insensitive {
                right_parts.push("ic");
            }
            if app_state.search.options.whole_word {
                right_parts.push("ww");
            }
        }

        let right_text = right_parts.join(" ");

        let left_line = Line::from(left_text).fg(self.theme.foreground);
        let right_line = Line::from(right_text).fg(self.theme.line_number);

        let left_para = Paragraph::new(left_line);
        let right_para = Paragraph::new(right_line).right_aligned();

        let split_point = area.width.saturating_sub(right_text.len() as u16 + 2);
        let left_area = Rect::new(area.x, area.y, area.x + split_point, area.y + 1);
        let right_area = Rect::new(area.x + split_point, area.y, area.x + area.width, area.y + 1);

        left_para.render(left_area, buf);
        right_para.render(right_area, buf);
    }
}

/// HelpPopup: Keyboard shortcut help dialog.
pub struct HelpPopup {
    pub theme: Arc<Theme>,
}

impl HelpPopup {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self { theme }
    }

    pub fn render(&self, area: Rect, buf: &mut Buffer) {
        let help_width = 40u16;
        let help_height = 20u16;

        let x = area.x + (area.width.saturating_sub(help_width)) / 2;
        let y = area.y + (area.height.saturating_sub(help_height)) / 2;
        let help_area = Rect::new(x, y, x + help_width, y + help_height);

        let help_block = ratatui::widgets::Block::default()
            .title(" Help ")
            .borders(ratatui::widgets::Borders::ALL)
            .border_style(Style::default().fg(self.theme.border))
            .title_style(Style::default().fg(self.theme.foreground));

        help_block.render(help_area, buf);

        let inner_area = help_block.inner(help_area);
        if inner_area.width < 5 || inner_area.height < 5 {
            return;
        }

        let shortcuts = [
            ("j/k, ↓/↑", "Scroll line down/up"),
            ("gg/G", "Go to first/last line"),
            ("d/u", "Scroll half page"),
            ("f/b", "Scroll full page"),
            ("/", "Search forward"),
            ("?", "Search backward"),
            ("n/N", "Next/prev match"),
            ("l", "Toggle level filter"),
            ("t", "Toggle time filter"),
            ("m[a-z]", "Set bookmark"),
            ("'[a-z]", "Jump to bookmark"),
            (":", "Command mode"),
            ("q, Esc", "Quit/back"),
            ("?", "Show this help"),
        ];

        let mut y_offset = inner_area.y;
        for (key, action) in shortcuts.iter() {
            if y_offset >= inner_area.y + inner_area.height {
                break;
            }

            let line = format!(" {:12} {}", key, action);
            let text_line = Line::from(line.as_str())
                .fg(self.theme.foreground);

            let line_area = Rect::new(inner_area.x, y_offset, inner_area.x + inner_area.width, y_offset + 1);
            Paragraph::new(text_line).render(line_area, buf);

            y_offset += 1;
        }
    }
}

/// HeaderWidget: Top header with file info.
pub struct HeaderWidget {
    pub theme: Arc<Theme>,
}

impl HeaderWidget {
    pub fn new(theme: Arc<Theme>) -> Self {
        Self { theme }
    }

    pub fn render_state(&self, area: Rect, buf: &mut Buffer, app_state: &AppState, file_path: &str) {
        if area.width < 5 {
            return;
        }

        let title = format!(" LogProbe: {} ", file_path);
        let title_line = Line::from(title).fg(self.theme.foreground);

        let meta_parts = vec![
            format!("{} lines", app_state.ui.total_lines),
            format!("{:?}", app_state.ui.view_mode),
        ];
        let meta = meta_parts.join(" | ");

        let title_area = Rect::new(area.x, area.y, area.x + area.width.saturating_sub(meta.len() as u16 + 2), area.y + 1);
        let meta_area = Rect::new(area.x + area.width.saturating_sub(meta.len() as u16 + 2), area.y, area.x + area.width, area.y + 1);

        let title_block = ratatui::widgets::Block::default()
            .borders(ratatui::widgets::Borders::NONE);

        Paragraph::new(title_line)
            .block(title_block)
            .render(title_area, buf);

        let meta_line = Line::from(format!(" {}", meta)).fg(self.theme.line_number).right_aligned();
        Paragraph::new(meta_line).render(meta_area, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_level_detection() {
        assert_eq!(Level::from_text("[INFO] Starting"), Level::Info);
        assert_eq!(Level::from_text("ERROR: failed"), Level::Error);
        assert_eq!(Level::from_text("WARN - low memory"), Level::Warn);
        assert_eq!(Level::from_text("DEBUG: trace info"), Level::Debug);
        assert_eq!(Level::from_text("FATAL PANIC"), Level::Fatal);
        assert_eq!(Level::from_text("some random text"), Level::Unknown);
    }

    #[test]
    fn test_log_line_data() {
        let data = LogLineData {
            line_number: 42,
            text: "ERROR: test message".to_string(),
            level: Level::Error,
            matches: vec![],
        };

        assert_eq!(data.line_number, 42);
        assert_eq!(data.level, Level::Error);
    }
}