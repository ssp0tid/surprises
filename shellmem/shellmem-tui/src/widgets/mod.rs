use ratatui::{
    Frame,
    layout::Rect,
    style::{Color, Style, Modifier},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
};

use crate::app::{Command, Panel};

pub struct CommandList<'a> {
    commands: &'a [Command],
    selected: usize,
    highlight_style: Style,
}

impl<'a> CommandList<'a> {
    pub fn new(commands: &'a [Command]) -> Self {
        CommandList {
            commands,
            selected: 0,
            highlight_style: Style::default()
                .bg(Color::DarkGray)
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        }
    }

    pub fn selected(mut self, selected: usize) -> Self {
        self.selected = selected;
        self
    }

    pub fn highlight_style(mut self, style: Style) -> Self {
        self.highlight_style = style;
        self
    }
}

impl<'a> ratatui::widgets::Widget for CommandList<'a> {
    fn render(self, area: Rect, buf: &mut ratatui::buffer::Buffer) {
        if self.commands.is_empty() {
            let block = Block::default()
                .title("Commands")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::White));
            block.render(area, buf);
            let text = vec![Line::from(Span::styled(
                "No commands found",
                Style::default().fg(Color::Gray),
            ))];
            let paragraph = Paragraph::new(text)
                .block(block)
                .alignment(ratatui::layout::Alignment::Center);
            paragraph.render(area, buf);
            return;
        }

        let items: Vec<ListItem> = self
            .commands
            .iter()
            .enumerate()
            .map(|(idx, cmd)| {
                let display = format_command_line(cmd, idx == self.selected);
                let style = if idx == self.selected as usize {
                    self.highlight_style
                } else {
                    let fg = if cmd.is_favorite {
                        Color::Yellow
                    } else {
                        Color::Green
                    };
                    Style::default().fg(fg)
                };
                ListItem::new(display).style(style)
            })
            .collect();

        let list = List::new(items)
            .block(
                Block::default()
                    .title("Commands")
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(Color::White)),
            )
            .highlight_style(self.highlight_style);

        list.render(area, buf);
    }
}

fn format_command_line(cmd: &Command, selected: bool) -> Line<'static> {
    let shell_indicator = match cmd.shell {
        shellmem_core::models::Shell::Bash => "[Bash]",
        shellmem_core::models::Shell::Zsh => "[Zsh]",
        shellmem_core::models::Shell::Fish => "[Fish]",
    };

    let fav_indicator = if cmd.is_favorite {
        " ★"
    } else {
        ""
    };

    let truncated = if cmd.command.len() > 60 {
        format!("{}...", &cmd.command[..57])
    } else {
        cmd.command.clone()
    };

    let tag_str = if cmd.tags.is_empty() {
        String::new()
    } else {
        let tags: Vec<String> = cmd.tags.iter().map(|t| t.name.clone()).collect();
        format!(" [{}]", tags.join(", "))
    };

    Line::from(vec![
        Span::raw(shell_indicator),
        Span::raw(" "),
        Span::raw(truncated),
        Span::raw(fav_indicator),
        Span::raw(tag_str),
    ])
}

pub struct DetailPanel<'a> {
    command: Option<&'a Command>,
}

impl<'a> DetailPanel<'a> {
    pub fn new(command: &'a Command) -> Self {
        DetailPanel {
            command: Some(command),
        }
    }

    pub fn new_empty() -> Self {
        DetailPanel { command: None }
    }
}

impl<'a> ratatui::widgets::Widget for DetailPanel<'a> {
    fn render(self, area: Rect, buf: &mut ratatui::buffer::Buffer) {
        let block = Block::default()
            .title("Detail")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::White));

        if area.height < 3 {
            block.render(area, buf);
            return;
        }

        block.render(area, buf);

        let inner = block.inner(area);
        if self.command.is_none() {
            return;
        }

        let cmd = self.command.unwrap();
        let mut y = inner.y;

        let cmd_line = Line::from(Span::styled(
            "Command:",
            Style::default().add_modifier(Modifier::BOLD),
        ));
        let cmd_text = Span::raw(&cmd.command);
        cmd_line.render(inner.x, y, buf);
        y += 1;

        let cmd_para = Paragraph::new(Line::from(cmd_text))
            .wrap(true);
        cmd_para.render(Rect::new(inner.x, y, inner.width, 1), buf);
        y += 2;

        let shell_line = Line::from(vec![
            Span::raw("Shell: "),
            Span::raw(match cmd.shell {
                shellmem_core::models::Shell::Bash => "Bash",
                shellmem_core::models::Shell::Zsh => "Zsh",
                shellmem_core::models::Shell::Fish => "Fish",
            }),
        ]);
        shell_line.render(inner.x, y, buf);
        y += 1;

        let time_str = cmd.timestamp.format("%Y-%m-%d %H:%M:%S").to_string();
        let time_line = Line::from(vec![
            Span::raw("Time: "),
            Span::raw(time_str),
        ]);
        time_line.render(inner.x, y, buf);
        y += 1;

        if let Some(dir) = &cmd.working_dir {
            let dir_line = Line::from(vec![
                Span::raw("Dir: "),
                Span::raw(dir),
            ]);
            dir_line.render(inner.x, y, buf);
            y += 1;
        }

        if let Some(status) = cmd.exit_status {
            let status_line = Line::from(vec![
                Span::raw("Exit: "),
                Span::raw(status.to_string()),
            ]);
            status_line.render(inner.x, y, buf);
            y += 1;
        }

        if !cmd.tags.is_empty() {
            let tags: Vec<&str> = cmd.tags.iter().map(|t| t.name.as_str()).collect();
            let tags_line = Line::from(vec![
                Span::raw("Tags: "),
                Span::raw(tags.join(", ")),
            ]);
            tags_line.render(inner.x, y, buf);
        }
    }
}

pub struct SearchInput<'a> {
    query: &'a str,
}

impl<'a> SearchInput<'a> {
    pub fn new(query: &'a str) -> Self {
        SearchInput { query }
    }
}

impl<'a> ratatui::widgets::Widget for SearchInput<'a> {
    fn render(self, area: Rect, buf: &mut ratatui::buffer::Buffer) {
        let block = Block::default()
            .title("Search")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan))
            .bg(Color::Black);

        block.render(area, buf);

        let inner = block.inner(area);
        if inner.width > 0 {
            let input_text = format!("/{}", self.query);
            let spans = vec![Span::raw(input_text)];
            let line = Line::from(spans);
            line.render(inner.x, inner.y, buf);
        }
    }
}