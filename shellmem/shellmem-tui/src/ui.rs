use ratatui::{
    Frame,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Style, Modifier},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Tabs},
};

use crate::app::{App, AppMode, Panel};
use crate::widgets::{CommandList, DetailPanel, SearchInput};

pub fn render(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(0),
            Constraint::Length(1),
        ])
        .split(frame.area());

    render_tabs(frame, app, chunks[0]);
    render_main_content(frame, app, chunks[1]);
    render_status_bar(frame, app, chunks[2]);
}

fn render_tabs(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let titles = app
        .filtered
        .iter()
        .take(5)
        .map(|cmd| {
            let truncated = if cmd.command.len() > 40 {
                format!("{}...", &cmd.command[..37])
            } else {
                cmd.command.clone()
            };
            Line::from(truncated)
        })
        .collect::<Vec<_>>();

    if titles.is_empty() {
        return;
    }

    let selected = app.selected.min(titles.len() - 1);
    let tabs = Tabs::new(titles)
        .select(selected)
        .style(Style::default().fg(Color::Cyan))
        .divider(Span::raw(" | "));

    frame.render_widget(tabs, area);
}

fn render_main_content(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(60),
            Constraint::Percentage(40),
        ])
        .split(area);

    render_command_list(frame, app, chunks[0]);

    if chunks.len() > 1 {
        render_detail_panel(frame, app, chunks[1]);
    }

    if app.mode == AppMode::Search {
        render_search_overlay(frame, app, area);
    }

    if app.show_tag_menu && app.mode == AppMode::TagSelect {
        render_tag_menu(frame, app, area);
    }
}

fn render_command_list(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let command_list = CommandList::new(&app.filtered)
        .selected(app.selected)
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        );

    frame.render_widget(command_list, area);
}

fn render_detail_panel(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let detail = if let Some(cmd) = app.filtered.get(app.selected) {
        DetailPanel::new(cmd)
    } else {
        DetailPanel::new_empty()
    };

    frame.render_widget(detail, area);
}

fn render_search_overlay(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let overlay_area = Rect::new(
        area.x + area.width / 4,
        area.y + area.height / 3,
        area.width / 4 * 3,
        area.height / 3,
    );

    let search_input = SearchInput::new(&app.search_query);

    frame.render_widget(search_input, overlay_area);
}

fn render_tag_menu(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let menu_area = Rect::new(
        area.x + area.width / 4,
        area.y + area.height / 3,
        area.width / 4 * 3,
        area.height / 3,
    );

    let tag_items: Vec<ListItem> = app
        .tags
        .iter()
        .map(|tag| {
            ListItem::new(Span::raw(&tag.name)).style(Style::default().fg(Color::LightYellow))
        })
        .collect();

    let tag_list = List::new(tag_items)
        .block(
            Block::default()
                .title("Select Tag")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        )
        .highlight_style(Style::default().bg(Color::DarkGray).fg(Color::White));

    frame.render_widget(tag_list, menu_area);
}

fn render_status_bar(frame: Frame<&mut ratatui::backend::CrosstermBackend<std::io::Stdout>>, app: &App, area: Rect) {
    let mode_str = match app.mode {
        AppMode::Browse => "Browse",
        AppMode::Search => "Search",
        AppMode::TagSelect => "Tag Select",
        AppMode::CommandDetail => "Detail",
    };

    let filter_info = if app.filters.favorites_only {
        " [favorites]"
    } else {
        ""
    };

    let status = format!(
        "{} | {}/{} |{}{} | {} panel",
        mode_str,
        app.selected + 1,
        app.filtered.len(),
        filter_info,
        if app.active_panel == Panel::List {
            " List"
        } else {
            " Detail"
        }
    );

    let status_line = Line::from(Span::raw(status));
    let paragraph = Paragraph::new(status_line)
        .style(Style::default().bg(Color::DarkGray).fg(Color::White))
        .block(Block::default().borders(Borders::NONE));

    frame.render_widget(paragraph, area);
}