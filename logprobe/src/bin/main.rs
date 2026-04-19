//! LogProbe - Interactive Terminal Log Explorer
//!
//! A high-performance TUI application for viewing, searching, and analyzing log files.

use clap::Parser;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEvent},
    execute,
    terminal::{
        disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
    },
};
use logprobe::{App, Config, Error, Theme};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::io;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

/// CLI arguments for logprobe.
#[derive(Parser, Debug)]
#[command(
    name = "logprobe",
    about = "Interactive Terminal Log Explorer & Analyzer",
    version = env!("CARGO_PKG_VERSION"),
    author = env!("CARGO_PKG_AUTHORS")
)]
struct Args {
    /// Log file to open
    #[arg(value_name = "FILE")]
    file: Option<PathBuf>,

    /// Follow file changes (tail -f mode)
    #[arg(short = 'f', long)]
    follow: bool,

    /// Start at last N lines
    #[arg(short = 'n', long, value_name = "N", default_value = "0")]
    lines: u64,

    /// Custom config file
    #[arg(short = 'c', long, value_name = "FILE")]
    config: Option<PathBuf>,

    /// Color theme (dark|light)
    #[arg(long, value_name = "THEME", default_value = "dark")]
    theme: String,

    /// Hide line numbers
    #[arg(long)]
    no_line_numbers: bool,

    /// Filter by log levels (e.g., ERROR,WARN)
    #[arg(short = 'l', long, value_name = "LEVELS")]
    level: Option<String>,

    /// Start time filter (ISO 8601)
    #[arg(short = 't', long, value_name = "TIME")]
    time_from: Option<String>,

    /// End time filter (ISO 8601)
    #[arg(short = 'T', long, value_name = "TIME")]
    time_to: Option<String>,

    /// Initial search pattern
    #[arg(short = 'g', long, value_name = "PATTERN")]
    grep: Option<String>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parse CLI arguments
    let args = Args::parse();

    // Validate file argument
    let file_path = match &args.file {
        Some(path) => {
            if !path.exists() {
                eprintln!("Error: File not found: {}", path.display());
                std::process::exit(1);
            }
            if !path.is_file() {
                eprintln!("Error: Not a file: {}", path.display());
                std::process::exit(1);
            }
            path.clone()
        }
        None => {
            eprintln!("Error: No file specified");
            eprintln!("Usage: logprobe [OPTIONS] [FILE]");
            std::process::exit(1);
        }
    };

    // Load configuration
    let mut config = if let Some(config_path) = &args.config {
        Config::load_from_file(config_path).unwrap_or_default()
    } else {
        Config::default()
    };

    // Apply CLI overrides
    if args.no_line_numbers {
        config.display.line_numbers = false;
    }
    if args.follow {
        config.behavior.follow_on_open = true;
    }

    // Set theme
    let theme = if args.theme.to_lowercase() == "light" {
        Theme::light()
    } else {
        Theme::dark()
    };

    // Setup panic hook for clean exit
    let original_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |panic_info| {
        // Restore terminal on panic
        let _ = restore_terminal();
        original_hook(panic_info);
    }));

    // Enable terminal modes
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;

    // Create terminal backend
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create and run application
    let result = run_app(&mut terminal, file_path, config, theme, args.grep);

    // Restore terminal state
    restore_terminal()?;

    match result {
        Ok(_) => Ok(()),
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    }
}

/// Run the main application loop.
fn run_app(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    file_path: PathBuf,
    config: Config,
    theme: Theme,
    initial_search: Option<String>,
) -> Result<(), Error> {
    // Create application
    let runtime = tokio::runtime::Runtime::new()
        .map_err(|e| Error::Io(std::io::Error::new(std::io::ErrorKind::Other, e.to_string())))?;

    let mut app = runtime.block_on(App::new(file_path, config))?;
    app.set_theme(theme);

    // Apply initial search if provided
    if let Some(pattern) = initial_search {
        app.state_mut().search.pattern = Some(pattern);
    }

    // Track quit flag
    let quit = Arc::new(AtomicBool::new(false));
    let quit_clone = quit.clone();

    // Main event loop
    loop {
        if quit_clone.load(Ordering::Relaxed) {
            break;
        }

        // Render
        let _ = terminal.draw(|f| {
            let area = f.area();
            let visible_lines = area.height.saturating_sub(3) as u64; // Account for header/status
            app.refresh(visible_lines);

            // Simple render for now
            use ratatui::widgets::{Block, Borders, Paragraph};
            use ratatui::layout::Constraint;
            use ratatui::style::Style;

            let block = Block::bordered()
                .title(format!(" LogProbe - {:?}", app.state().ui.total_lines()))
                .border_style(Style::default().fg(theme.foreground));

            let paragraph = Paragraph::new(format!(
                "Lines: {}-{} / {}\nMode: {:?}\nSearch: {:?}",
                app.state().ui.scroll,
                app.state().ui.scroll.saturating_add(visible_lines),
                app.state().ui.total_lines(),
                app.mode(),
                app.state().search.pattern_str(),
            ))
            .block(block);

            f.render_widget(paragraph, area);
        });

        // Handle events
        if let Ok(event) = event::read() {
            match event {
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') && key_event.modifiers.is_empty() {
                        break;
                    }
                    if !app.handle_key_event(key_event) {
                        break;
                    }
                }
                Event::Resize(_, _) => {
                    // Terminal resize handled in draw
                }
                Event::Mouse(_) => {
                    // Mouse events - simplified for now
                }
                Event::Paste(_) => {
                    // Paste events - simplified for now
                }
                Event::FocusGained => {}
                Event::FocusLost => {}
            }
        }
    }

    Ok(())
}

/// Restore terminal to original state.
fn restore_terminal() -> Result<(), Box<dyn std::error::Error>> {
    disable_raw_mode()?;
    execute!(io::stdout(), LeaveAlternateScreen, DisableMouseCapture)?;
    Ok(())
}
