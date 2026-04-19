//! Layout definitions using ratatui.
//!
//! Uses ratatui Layout with Constraints to define UI regions.

use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    Frame,
};

/// Layout region identifiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Region {
    Header,
    Main,
    Sidebar,
    StatusBar,
    SearchBar,
}

/// Layout configuration for main views.
#[derive(Debug, Clone, Copy)]
pub struct LayoutConfig {
    /// Show sidebar in split view
    pub show_sidebar: bool,
    /// Show search bar
    pub show_search: bool,
    /// Show filter panel
    pub show_filter: bool,
    /// Header height
    pub header_height: u16,
    /// Status bar height
    pub status_height: u16,
    /// Search bar height
    pub search_height: u16,
    /// Sidebar width (as percentage if fraction, or exact)
    pub sidebar_width: u16,
    /// Minimum content width
    pub min_content_width: u16,
}

impl Default for LayoutConfig {
    fn default() -> Self {
        Self {
            show_sidebar: false,
            show_search: false,
            show_filter: false,
            header_height: 1,
            status_height: 1,
            search_height: 1,
            sidebar_width: 30,
            min_content_width: 80,
        }
    }
}

impl LayoutConfig {
    /// Configure split view mode.
    pub fn with_split_view(mut self, enabled: bool) -> Self {
        self.show_sidebar = enabled;
        self
    }

    /// Configure search bar visibility.
    pub fn with_search_bar(mut self, visible: bool) -> Self {
        self.show_search = visible;
        self
    }

    /// Configure filter panel visibility.
    pub fn with_filter_panel(mut self, visible: bool) -> Self {
        self.show_filter = visible;
        self
    }
}

/// Layout regions computed from constraints.
#[derive(Debug, Clone)]
pub struct LayoutRegions {
    /// Header region
    pub header: Rect,
    /// Search bar region (may be zero-width if hidden)
    pub search: Rect,
    /// Main content region
    pub main: Rect,
    /// Sidebar region (may be zero-width if hidden)
    pub sidebar: Rect,
    /// Status bar region
    pub status: Rect,
}

impl LayoutRegions {
    /// Get region by identifier.
    pub fn get(&self, region: Region) -> Rect {
        match region {
            Region::Header => self.header,
            Region::SearchBar => self.search,
            Region::Main => self.main,
            Region::Sidebar => self.sidebar,
            Region::StatusBar => self.status,
        }
    }
}

/// Calculate layout regions from terminal area.
///
/// Returns layout with header, optional search bar, main content,
/// optional sidebar, and status bar.
pub fn calculate_layout(area: Rect, config: LayoutConfig) -> LayoutRegions {
    let min_height = config.header_height + config.status_height + config.search_height + 2;
    if area.height < min_height {
        return LayoutRegions {
            header: Rect::new(area.x, area.y, area.x, area.y),
            search: Rect::new(area.x, area.y, area.x, area.y),
            main: Rect::new(area.x, area.y, area.x, area.y),
            sidebar: Rect::new(area.x, area.y, area.x, area.y),
            status: Rect::new(area.x, area.y, area.x, area.y),
        };
    }

    let remaining_width = area.width;
    let remaining_height = area.height.saturating_sub(
        config.header_height + config.status_height + config.search_height,
    );

    // Build constraint list based on visibility
    let mut constraints = Vec::new();

    // Vertical direction: [header][search][content/status]
    // For content: need to split into main + sidebar if enabled

    if config.show_sidebar && remaining_width >= config.min_content_width + config.sidebar_width {
        // Horizontal split for sidebar
        let main_width = remaining_width.saturating_sub(config.sidebar_width);
        let sidebar_x = area.x + main_width;

        LayoutRegions {
            header: Rect::new(area.x, area.y, area.x + area.width, area.y + config.header_height),
            search: Rect::new(
                area.x,
                area.y + config.header_height,
                area.x + remaining_width,
                area.y + config.header_height + config.search_height,
            ),
            main: Rect::new(
                area.x,
                area.y + config.header_height + config.search_height,
                area.x + main_width,
                area.y + config.header_height + config.search_height + remaining_height,
            ),
            sidebar: Rect::new(
                sidebar_x,
                area.y + config.header_height + config.search_height,
                sidebar_x + config.sidebar_width,
                area.y + config.header_height + config.search_height + remaining_height,
            ),
            status: Rect::new(
                area.x,
                area.y + config.header_height + config.search_height + remaining_height,
                area.x + remaining_width,
                area.y + config.header_height + config.search_height + remaining_height + config.status_height,
            ),
        }
    } else {
        // No sidebar
        LayoutRegions {
            header: Rect::new(area.x, area.y, area.x + area.width, area.y + config.header_height),
            search: Rect::new(
                area.x,
                area.y + config.header_height,
                area.x + remaining_width,
                area.y + config.header_height + config.search_height,
            ),
            main: Rect::new(
                area.x,
                area.y + config.header_height + config.search_height,
                area.x + remaining_width,
                area.y + config.header_height + config.search_height + remaining_height,
            ),
            sidebar: Rect::new(area.x, area.y, area.x, area.y),
            status: Rect::new(
                area.x,
                area.y + config.header_height + config.search_height + remaining_height,
                area.x + remaining_width,
                area.y + config.header_height + config.search_height + remaining_height + config.status_height,
            ),
        }
    }
}

/// Get default layout with visible search bar.
pub fn default_layout(config: LayoutConfig) -> LayoutConfig {
    config
}

/// Ratatui Layout helper functions.
///
/// Create commonly used layout patterns.
pub mod ratatui_helpers {
    use super::*;

    /// Create vertical stack of regions.
    pub fn vertical_stack(area: Rect, heights: &[u16]) -> Vec<Rect> {
        Layout::vertical(
            heights
                .iter()
                .map(|&h| Constraint::Length(h))
                .collect::<Vec<_>>(),
        )
        .split(area)
    }

    /// Create horizontal stack of regions.
    pub fn horizontal_stack(area: Rect, widths: &[u16]) -> Vec<Rect> {
        Layout::horizontal(
            widths
                .iter()
                .map(|&w| Constraint::Length(w))
                .collect::<Vec<_>>(),
        )
        .split(area)
    }

    /// Create main layout: header + content + status.
    pub fn main_layout(area: Rect, header: u16, status: u16) -> Vec<Rect> {
        Layout::vertical([
            Constraint::Length(header),
            Constraint::Min(3),
            Constraint::Length(status),
        ])
        .split(area)
    }

    /// Create split layout: main + sidebar.
    pub fn split_layout(area: Rect, main_width: u16) -> (Rect, Rect) {
        let chunks = Layout::horizontal([
            Constraint::Length(main_width),
            Constraint::Min(3),
        ])
        .split(area);
        (chunks[0], chunks[1])
    }

    /// Create search bar layout: input + results count.
    pub fn search_bar_layout(area: Rect) -> (Rect, Rect) {
        let chunks = Layout::horizontal([
            Constraint::Min(10),
            Constraint::Length(20),
        ])
        .split(area);
        (chunks[0], chunks[1])
    }

    /// Create centered popup layout for dialogs.
    pub fn centered_popup(area: Rect, width: u16, height: u16) -> Rect {
        let x = area.x + (area.width.saturating_sub(width)) / 2;
        let y = area.y + (area.height.saturating_sub(height)) / 2;
        Rect::new(x, y, x + width, y + height)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_layout_regions() {
        let area = Rect::new(0, 0, 100, 50);
        let config = LayoutConfig::default();
        let regions = calculate_layout(area, config);

        assert_eq!(regions.header.width, 100);
        assert_eq!(regions.status.width, 100);
    }

    #[test]
    fn test_split_view_layout() {
        let area = Rect::new(0, 0, 120, 50);
        let config = LayoutConfig::default().with_split_view(true);
        let regions = calculate_layout(area, config);

        assert!(regions.sidebar.width > 0);
    }
}