use std::io::{self, Read};

use crossterm::event::{Event, EventStream, KeyEvent, KeyEventKind, KeyModifiers, Read => Read};

use crate::app::{App, AppMode};

pub struct InputHandler {
    stdin: io::Stdin,
    reader: EventStream,
}

impl InputHandler {
    pub fn new() -> Self {
        InputHandler {
            stdin: io::stdin(),
            reader: EventStream::new(),
        }
    }

    pub fn read_key(&mut self) -> Result<Option<KeyEvent>, io::Error> {
        use futures::StreamExt;

        loop {
            if let Some(result) = self.reader.next().now_or_never() {
                match result {
                    Ok(Event::Key(key)) => {
                        if key.kind == KeyEventKind::Press {
                            return Ok(Some(key));
                        }
                    }
                    Ok(Event::Resize(_, _)) => {
                        continue;
                    }
                    _ => {}
                }
            }

            let mut buf = [0u8; 1];
            match self.stdin.read(&mut buf) {
                Ok(1) => {
                    let c = buf[0] as char;
                    return Ok(Some(KeyEvent {
                        code: crossterm::event::KeyCode::Char(c),
                        modifiers: KeyModifiers::empty(),
                        kind: KeyEventKind::Press,
                        state: crossterm::event::KeyEventState::NONE,
                    }));
                }
                Ok(0) => return Ok(None),
                Err(e) if e.kind() == io::ErrorKind::WouldBlock => return Ok(None),
                Err(e) => return Err(e),
            }
        }
    }

    pub fn handle_key_event(&mut self, key: KeyEvent, app: &mut App) -> AppMode {
        use crossterm::event::KeyCode;
        use crossterm::event::KeyModifiers;

        let current_mode = app.mode;

        if app.show_tag_menu && current_mode == AppMode::TagSelect {
            app.handle_input(key);
            return current_mode;
        }

        match key.code {
            KeyCode::Char('/') if key.modifiers.is_empty() => {
                app.mode = AppMode::Search;
                return AppMode::Search;
            }
            KeyCode::Char('q') if key.modifiers.is_empty() => {
                app.should_quit = true;
                return current_mode;
            }
            KeyCode::Enter if key.modifiers.is_empty() => {
                if current_mode == AppMode::Search {
                    app.mode = AppMode::Browse;
                    app.update();
                    return AppMode::Browse;
                } else if current_mode == AppMode::TagSelect {
                    app.add_tag_to_selected();
                    app.show_tag_menu = false;
                    app.mode = AppMode::Browse;
                    return AppMode::Browse;
                } else {
                    app.execute_selected();
                    return current_mode;
                }
            }
            KeyCode::Esc if key.modifiers.is_empty() => {
                if current_mode == AppMode::Search {
                    app.search_query.clear();
                    app.mode = AppMode::Browse;
                    app.update();
                } else if current_mode == AppMode::TagSelect {
                    app.show_tag_menu = false;
                    app.mode = AppMode::Browse;
                } else if current_mode == AppMode::CommandDetail {
                    app.mode = AppMode::Browse;
                }
                return app.mode;
            }
            KeyCode::Tab if key.modifiers.is_empty() => {
                app.active_panel = if app.active_panel == crate::app::Panel::List {
                    crate::app::Panel::Detail
                } else {
                    crate::app::Panel::List
                };
                return current_mode;
            }
            _ => {}
        }

        if key.modifiers.contains(KeyModifiers::CONTROL) {
            match key.code {
                KeyCode::Char('r') => {
                    app.refresh();
                    return current_mode;
                }
                KeyCode::Char('d') => {
                    app.delete_selected();
                    return current_mode;
                }
                KeyCode::Char('f') => {
                    app.filters.favorites_only = !app.filters.favorites_only;
                    app.update();
                    return current_mode;
                }
                KeyCode::Char('t') => {
                    app.show_tag_menu = !app.show_tag_menu;
                    if app.show_tag_menu {
                        return AppMode::TagSelect;
                    }
                    return current_mode;
                }
                _ => {}
            }
        }

        match current_mode {
            AppMode::Search => {
                match key.code {
                    KeyCode::Char(c) => {
                        app.search_query.push(c);
                    }
                    KeyCode::Backspace => {
                        app.search_query.pop();
                    }
                    _ => {}
                }
            }
            AppMode::TagSelect => {
                match key.code {
                    KeyCode::Char(c) => {
                        app.tag_input.push(c);
                    }
                    KeyCode::Backspace => {
                        app.tag_input.pop();
                    }
                    _ => {}
                }
            }
            _ => {
                app.handle_input(key);
            }
        }

        app.mode
    }
}

impl Default for InputHandler {
    fn default() -> Self {
        Self::new()
    }
}