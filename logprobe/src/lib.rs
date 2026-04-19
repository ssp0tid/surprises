//! LogProbe - Interactive Terminal Log Explorer & Analyzer
//!
//! A high-performance TUI log file viewer with vim-like navigation,
//! regex search, filtering, and live tailing capabilities.
//!
//! # Features
//!
//! - **High Performance**: Handles files from KB to 10GB+
//! - **Vim-like Navigation**: Familiar keyboard shortcuts
//! - **Live Tailing**: Real-time file monitoring
//! - **Powerful Search**: Regex search with highlighting
//! - **Log Filtering**: Filter by level and timestamp
//!
//! # Usage
//!
//! ```rust,no_run
//! use logprobe::{LogViewer, Config};
//!
//! let viewer = LogViewer::new("app.log")?;
//! viewer.run()?;
//! # Ok::<(), logprobe::Error>(())
//! ```

pub mod app;
pub mod bookmarks;
pub mod config;
pub mod errors;
pub mod log;
pub mod search;
pub mod ui;

// Re-export commonly used types
pub use app::{App, AppMode};
pub use bookmarks::{Bookmark, BookmarkStore};
pub use config::Config;
pub use errors::Error;
pub use log::{Level, LogLine, LogFile, LogFileError};
pub use search::{Match, SearchEngine};
pub use search::index::LineIndex as SearchIndex;

// Re-export UI types
pub use ui::{Theme, ThemePreset};
pub use ui::state::{AppState, FilterState, SearchState, UIState, ViewMode};

/// LogViewer is the main entry point for programmatic usage.
pub struct LogViewer {
    app: App,
}

impl LogViewer {
    /// Create a new viewer for a log file.
    pub async fn new<P: AsRef<std::path::Path>>(path: P) -> Result<Self, Error> {
        let config = Config::default();
        let app = App::new(path.as_ref().to_path_buf(), config).await?;
        Ok(Self { app })
    }

    /// Create a new viewer with custom configuration.
    pub async fn with_config<P: AsRef<std::path::Path>>(
        path: P,
        config: Config,
    ) -> Result<Self, Error> {
        let app = App::new(path.as_ref().to_path_buf(), config).await?;
        Ok(Self { app })
    }

    /// Run the viewer (blocking).
    pub fn run(&mut self) -> Result<(), Error> {
        // This would typically start the TUI event loop
        // For now, just return ok as the binary handles the loop
        Ok(())
    }

    /// Get the underlying log file.
    pub fn file(&self) -> &LogFile {
        &self.app.log_file
    }

    /// Get the search engine.
    pub fn search_engine(&self) -> &SearchEngine {
        &self.app.search_engine
    }
}
