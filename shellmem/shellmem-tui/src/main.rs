mod app;
mod input;
mod ui;
mod widgets;

use std::io;
use std::panic;
use std::path::PathBuf;

use color_eyre::Install;
use crossterm::{
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};

use app::{App, AppMode};
use input::InputHandler;

fn get_db_path() -> PathBuf {
    let home = dirs::data_local_dir().unwrap_or_else(|| PathBuf::from("."));
    let shellmem_dir = home.join("shellmem");
    std::fs::create_dir_all(&shellmem_dir).ok();
    shellmem_dir.join("shellmem.db")
}

fn main() -> Result<()> {
    color_eyre::install()?;

    let db_path = get_db_path();
    let database = storage::Database::new(&db_path).map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

    execute!(io::stdout(), EnterAlternateScreen)?;
    enable_raw_mode()?;

    let panic_hook = panic::take_hook();
    panic::set_hook(Box::new(move |info| {
        let _ = disable_raw_mode();
        let _ = execute!(io::stdout(), LeaveAlternateScreen);
        panic_hook(info);
    }));

    let backend = CrosstermBackend::new(io::stdout());
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new(database);

    terminal.draw(|frame| {
        ui::render(frame, &app);
    })?;

    let mut input_handler = InputHandler::new();

    loop {
        if app.should_quit {
            break;
        }

        if let Some(key_event) = input_handler.read_key()? {
            let new_mode = input_handler.handle_key_event(key_event, &mut app);

            match new_mode {
                AppMode::Browse | AppMode::Search | AppMode::TagSelect | AppMode::CommandDetail => {
                    app.mode = new_mode;
                }
            }

            app.update();

            terminal.draw(|frame| {
                ui::render(frame, &app);
            })?;
        }
    }

    execute!(io::stdout(), LeaveAlternateScreen)?;
    disable_raw_mode()?;

    Ok(())
}

mod storage {
    pub use shellmem_core::storage::{Database, HistoryStore};
}

use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("IO error: {0}")]
    Io(#[from] io::Error),
    #[error("Database error: {0}")]
    Database(#[from] shellmem_core::error::ShellmemError),
}