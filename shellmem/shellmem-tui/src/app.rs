use shellmem_core::models::{Command, SearchOptions, Shell, Tag};
use shellmem_core::storage::Database;
use shellmem_core::ShellmemError;
use shellmem_core::HistoryStore;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AppMode {
    Browse,
    Search,
    TagSelect,
    CommandDetail,
}

impl Default for AppMode {
    fn default() -> Self {
        AppMode::Browse
    }
}

#[derive(Debug, Clone, Default)]
pub struct Filters {
    pub from_time: Option<chrono::DateTime<chrono::Utc>>,
    pub to_time: Option<chrono::DateTime<chrono::Utc>>,
    pub shells: Vec<Shell>,
    pub tags: Vec<i64>,
    pub favorites_only: bool,
}

#[derive(Debug)]
pub struct App {
    pub commands: Vec<Command>,
    pub filtered: Vec<Command>,
    pub search_query: String,
    pub selected: usize,
    pub mode: AppMode,
    pub filters: Filters,
    pub tags: Vec<Tag>,
    pub should_quit: bool,
    pub active_panel: Panel,
    pub tag_input: String,
    pub show_tag_menu: bool,
    database: Database,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Panel {
    List,
    Detail,
}

impl Default for Panel {
    fn default() -> Self {
        Panel::List
    }
}

impl App {
    pub fn new(database: Database) -> Self {
        let commands = Self::load_commands(&database);
        let tags = database.get_all_tags().unwrap_or_default();

        App {
            commands: commands.clone(),
            filtered: commands,
            search_query: String::new(),
            selected: 0,
            mode: AppMode::Browse,
            filters: Filters::default(),
            tags,
            should_quit: false,
            active_panel: Panel::List,
            tag_input: String::new(),
            show_tag_menu: false,
            database,
        }
    }

    fn load_commands(database: &Database) -> Vec<Command> {
        let options = SearchOptions {
            query: None,
            shell: None,
            from_date: None,
            to_date: None,
            tags: None,
            favorites_only: false,
            limit: Some(1000),
            offset: None,
        };

        database.search(options).unwrap_or_default()
    }

    pub fn update(&mut self) {
        let options = self.build_search_options();
        self.filtered = self.database.search(options).unwrap_or_else(|_| {
            self.commands.clone()
        });

        if self.selected >= self.filtered.len() {
            self.selected = self.filtered.len().saturating_sub(1);
        }
    }

    fn build_search_options(&self) -> SearchOptions {
        SearchOptions {
            query: if self.search_query.is_empty() {
                None
            } else {
                Some(self.search_query.clone())
            },
            shell: self.filters.shells.first().cloned(),
            from_date: self.filters.from_time,
            to_date: self.filters.to_time,
            tags: if self.filters.tags.is_empty() {
                None
            } else {
                Some(self.filters.tags.iter().map(|id| id.to_string()).collect())
            },
            favorites_only: self.filters.favorites_only,
            limit: Some(1000),
            offset: None,
        }
    }

    pub fn handle_input(&mut self, key: crossterm::event::KeyEvent) {
        use crossterm::event::KeyCode;
        use crossterm::event::KeyModifiers;

        match self.mode {
            AppMode::Browse => {
                match key.code {
                    KeyCode::Char('q') => {
                        self.should_quit = true;
                    }
                    KeyCode::Char('/') => {
                        self.mode = AppMode::Search;
                    }
                    KeyCode::Char('c') => {
                        self.copy_to_clipboard();
                    }
                    KeyCode::Char('f') => {
                        self.toggle_favorite();
                    }
                    KeyCode::Char('t') => {
                        self.show_tag_menu = !self.show_tag_menu;
                        if self.show_tag_menu {
                            self.mode = AppMode::TagSelect;
                        }
                    }
                    KeyCode::Char('\t') => {
                        self.active_panel = if self.active_panel == Panel::List {
                            Panel::Detail
                        } else {
                            Panel::List
                        };
                    }
                    KeyCode::Down | KeyCode::Char('j') => {
                        if self.selected < self.filtered.len().saturating_sub(1) {
                            self.selected += 1;
                        }
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        if self.selected > 0 {
                            self.selected -= 1;
                        }
                    }
                    KeyCode::Enter => {
                        self.execute_selected();
                    }
                    KeyCode::Esc => {
                        if self.show_tag_menu {
                            self.show_tag_menu = false;
                            self.mode = AppMode::Browse;
                        }
                    }
                    KeyCode::Delete => {
                        self.delete_selected();
                    }
                    _ => {}
                }

                if key.modifiers.contains(KeyModifiers::CONTROL) {
                    match key.code {
                        KeyCode::Char('r') => {
                            self.refresh();
                        }
                        KeyCode::Char('d') => {
                            self.delete_selected();
                        }
                        KeyCode::Char('f') => {
                            self.filters.favorites_only = !self.filters.favorites_only;
                            self.update();
                        }
                        KeyCode::Char('t') => {
                            self.show_tag_menu = !self.show_tag_menu;
                            if self.show_tag_menu {
                                self.mode = AppMode::TagSelect;
                            }
                        }
                        _ => {}
                    }
                }
            }
            AppMode::Search => {
                match key.code {
                    KeyCode::Enter => {
                        self.mode = AppMode::Browse;
                        self.update();
                    }
                    KeyCode::Esc => {
                        self.search_query.clear();
                        self.mode = AppMode::Browse;
                        self.update();
                    }
                    KeyCode::Char(c) => {
                        self.search_query.push(c);
                    }
                    KeyCode::Backspace => {
                        self.search_query.pop();
                    }
                    _ => {}
                }
            }
            AppMode::TagSelect => {
                match key.code {
                    KeyCode::Enter => {
                        self.add_tag_to_selected();
                        self.show_tag_menu = false;
                        self.mode = AppMode::Browse;
                    }
                    KeyCode::Esc => {
                        self.show_tag_menu = false;
                        self.mode = AppMode::Browse;
                    }
                    KeyCode::Char(c) => {
                        self.tag_input.push(c);
                    }
                    KeyCode::Backspace => {
                        self.tag_input.pop();
                    }
                    _ => {}
                }
            }
            AppMode::CommandDetail => {
                match key.code {
                    KeyCode::Esc => {
                        self.mode = AppMode::Browse;
                    }
                    _ => {}
                }
            }
        }
    }

    fn copy_to_clipboard(&self) {
        if let Some(cmd) = self.filtered.get(self.selected) {
            #[cfg(target_os = "windows")]
            {
                let _ = std::process::Command::new("cmd")
                    .args(["/C", "echo", &cmd.command, "|", "clip"])
                    .output();
            }
            #[cfg(target_os = "linux")]
            {
                let _ = std::process::Command::new("xclip")
                    .arg("-selection")
                    .arg("clipboard")
                    .arg("-f")
                    .stdin(std::process::Stdio::pipe())
                    .spawn()
                    .and_then(|mut child| {
                        use std::io::Write;
                        let mut stdin = child.stdin.take().unwrap();
                        stdin.write_all(cmd.command.as_bytes())?;
                        drop(stdin);
                        child.wait()
                    });
            }
            #[cfg(target_os = "macos")]
            {
                let _ = std::process::Command::new("pbcopy")
                    .stdin(std::process::Stdio::piped())
                    .spawn()
                    .and_then(|mut child| {
                        use std::io::Write;
                        let mut stdin = child.stdin.take().unwrap();
                        stdin.write_all(cmd.command.as_bytes())?;
                        drop(stdin);
                        child.wait()
                    });
            }
        }
    }

    fn toggle_favorite(&mut self) {
        if let Some(cmd) = self.filtered.get(self.selected) {
            let new_favorite = !cmd.is_favorite;
            if self.database.set_favorite(cmd.id, new_favorite).is_ok() {
                if let Some(filtered_cmd) = self.filtered.get_mut(self.selected) {
                    filtered_cmd.is_favorite = new_favorite;
                }
                if let Some(cmd) = self.commands.iter_mut().find(|c| c.id == cmd.id) {
                    cmd.is_favorite = new_favorite;
                }
            }
        }
    }

    fn add_tag_to_selected(&mut self) {
        if let Some(cmd) = self.filtered.get(self.selected) {
            let tag_name = self.tag_input.trim();
            if !tag_name.is_empty() {
                if let Ok(Some(tag)) = self.database.tag_exists(tag_name) {
                    let _ = self.database.add_tag(cmd.id, tag.id);
                } else if let Ok(tag) = self.database.create_tag(tag_name, "#808080") {
                    let _ = self.database.add_tag(cmd.id, tag.id);
                }
                self.tag_input.clear();
                self.update();
                self.tags = self.database.get_all_tags().unwrap_or_default();
            }
        }
    }

    fn execute_selected(&self) {
        if let Some(cmd) = self.filtered.get(self.selected) {
            println!("{}", cmd.command);
        }
    }

    fn delete_selected(&mut self) {
        if let Some(cmd) = self.filtered.get(self.selected) {
            if self.database.set_deleted(cmd.id, true).is_ok() {
                self.update();
            }
        }
    }

    fn refresh(&mut self) {
        self.commands = Self::load_commands(&self.database);
        self.tags = self.database.get_all_tags().unwrap_or_default();
        self.update();
    }

    pub fn get_selected_command(&self) -> Option<&Command> {
        self.filtered.get(self.selected)
    }
}