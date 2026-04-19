//! UI module for logprobe TUI.
//!
//! Provides complete UI implementation including layout, views, state management,
//! and theming for the terminal log viewer.

pub mod layout;
pub mod state;
pub mod styles;
pub mod views;

pub use layout::{calculate_layout, LayoutConfig, LayoutRegions, Region};
pub use state::{
    AppState, BookmarkState, FilterState, SearchOptions, SearchState, UIState, ViewMode,
};
pub use styles::{LevelColors, Theme, ThemePreset};
pub use views::{
    FilterPanel, FilterPanelState, HeaderWidget, HelpPopup, Level, LineContent, LogLineData,
    LogView, LogViewState, SearchBar, SearchBarState, StatusBar,
};

use ratatui::Frame;

pub use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::Style,
    widgets::{Block, Borders, Paragraph, Scrollbar, ScrollbarOrientation},
};

/// Render the main UI with all components.
pub fn render_ui(frame: &mut Frame, app_state: &AppState, file_path: &str, theme: &Theme) {
    let area = frame.area();

    let config = LayoutConfig {
        show_sidebar: app_state.ui.view_mode == ViewMode::Split,
        show_search: app_state.ui.view_mode == ViewMode::Search,
        show_filter: app_state.ui.view_mode == ViewMode::Filter,
        ..Default::default()
    };

    let regions = calculate_layout(area, config);

    let header = HeaderWidget::new(std::sync::Arc::new(*theme));
    header.render_state(regions.header, frame.buffer_mut(), app_state, file_path);

    if app_state.ui.view_mode == ViewMode::Search {
        let search = SearchBar::new(std::sync::Arc::new(*theme));
        let mut state = SearchBarState::default();
        state.input = app_state.search.pattern_str().to_string();
        state.selected = true;

        if let Some(ref err) = app_state.search.error {
            state.error = Some(err.clone());
        }

        search.styled_render(regions.search, frame.buffer_mut(), &mut state);
    }

    match app_state.ui.view_mode {
        ViewMode::Filter => {
            let filter = FilterPanel::new(std::sync::Arc::new(*theme));
            let mut state = FilterPanelState::default();
            state.enabled_levels = app_state
                .filters
                .levels
                .iter()
                .map(|b| *b)
                .collect();

            filter.styled_render(regions.main, frame.buffer_mut(), &mut state);
        }
        ViewMode::Split => {
            let log_view = LogView::new(std::sync::Arc::new(*theme));
            let mut state = LogViewState::default();
            state.scroll_offset = app_state.ui.scroll;
            state.selected_line = app_state.ui.selection;
            state.visible_lines = app_state.ui.visible_lines;

            log_view.styled_render(regions.main, frame.buffer_mut(), &mut state);
        }
        _ => {
            let log_view = LogView::new(std::sync::Arc::new(*theme));
            let mut state = LogViewState::default();
            state.scroll_offset = app_state.ui.scroll;
            state.selected_line = app_state.ui.selection;
            state.visible_lines = app_state.ui.visible_lines;

            log_view.styled_render(regions.main, frame.buffer_mut(), &mut state);
        }
    }

    if app_state.ui.view_mode == ViewMode::Help {
        let help = HelpPopup::new(std::sync::Arc::new(*theme));
        help.render(area, frame.buffer_mut());
    }

    let status = StatusBar::new(std::sync::Arc::new(*theme));
    status.render_state(regions.status, frame.buffer_mut(), app_state);
}

/// Extension trait to allow styled rendering.
pub trait StyledRender {
    fn styled_render(&self, area: Rect, buf: &mut ratatui::buffer::Buffer, state: &mut Self::State);
}

impl StyledRender for SearchBar {
    fn styled_render(&self, area: Rect, buf: &mut ratatui::buffer::Buffer, state: &mut Self::State) {
        SearchBar::render(self.clone(), area, buf, state)
    }
}

impl Clone for SearchBar {
    fn clone(&self) -> Self {
        Self {
            placeholder: self.placeholder.clone(),
            theme: self.theme.clone(),
        }
    }
}

impl StyledRender for FilterPanel {
    fn styled_render(&self, area: Rect, buf: &mut ratatui::buffer::Buffer, state: &mut FilterPanelState) {
        FilterPanel::render(self.clone(), area, buf, state)
    }
}

impl Clone for FilterPanel {
    fn clone(&self) -> Self {
        Self {
            theme: self.theme.clone(),
        }
    }
}

impl StyledRender for LogView {
    fn styled_render(&self, area: Rect, buf: &mut ratatui::buffer::Buffer, state: &mut LogViewState) {
        LogView::render(self.clone(), area, buf, state)
    }
}

impl Clone for LogView {
    fn clone(&self) -> Self {
        Self {
            lines: self.lines.clone(),
            theme: self.theme.clone(),
            show_line_numbers: self.show_line_numbers,
        }
    }
}

pub trait StatefulWidgetExt: StatefulWidget + Sized {
    fn styled_render(&self, area: Rect, buf: &mut ratatui::buffer::Buffer, state: &mut Self::State) {
        StatefulWidget::render(self.clone(), area, buf, state)
    }
}

impl<T: StatefulWidget + Clone> StatefulWidgetExt for T {}

#[cfg(test)]
mod tests {
    #[test]
    fn test_ui_module_exports() {
        use super::*;

        let _theme = Theme::dark();
        let _state = UIState::default();
        let _config = LayoutConfig::default();
    }
}