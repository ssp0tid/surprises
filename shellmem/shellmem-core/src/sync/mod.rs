use std::path::Path;
use std::sync::Arc;
use std::time::Duration;

use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher, Event, EventKind};
use tokio::sync::Mutex;

use crate::error::ShellmemError;
use crate::models::{Command, NewCommand, Shell};
use crate::parser::parse_shell;
use crate::storage::Database;

pub trait HistoryWatcher {
    fn start_watching(&self, shell: Shell, path: &Path) -> Result<(), ShellmemError>;
    fn stop_watching(&self) -> Result<(), ShellmemError>;
    fn get_changes(&self) -> Vec<Command>;
}

pub struct FileWatcher {
    store: Arc<Mutex<Database>>,
    watcher: Option<RecommendedWatcher>,
    shell: Option<Shell>,
    watch_path: Option<std::path::PathBuf>,
    changes: Vec<Command>,
}

impl FileWatcher {
    pub fn new(store: Arc<Mutex<Database>>) -> Self {
        Self {
            store,
            watcher: None,
            shell: None,
            watch_path: None,
            changes: Vec::new(),
        }
    }
}

impl HistoryWatcher for FileWatcher {
    fn start_watching(&self, shell: Shell, path: &Path) -> Result<(), ShellmemError> {
        if !path.exists() {
            return Ok(());
        }

        let store = self.store.clone();
        let watch_path = path.to_path_buf();
        let shell_for_watcher = shell;

        let mut watcher = RecommendedWatcher::new(
            move |res: Result<Event, notify::Error>| {
                if let Ok(event) = res {
                    match event.kind {
                        EventKind::Modify(_) | EventKind::Create(_) => {
                            let store = store.clone();
                            let watch_path = watch_path.clone();
                            let runtime = tokio::runtime::Handle::current();
                            
                            runtime.spawn(async move {
                                tokio::time::sleep(Duration::from_millis(100)).await;
                                let content = std::fs::read_to_string(&watch_path);
                                if let Ok(c) = content {
                                    let parsed = parse_shell(shell_for_watcher, &c);
                                    if let Ok(commands) = parsed {
                                        let mut store = store.lock().await;
                                        for cmd in commands {
                                            let new_cmd = NewCommand {
                                                command: cmd.command,
                                                shell: shell_for_watcher,
                                                timestamp: chrono::DateTime::from_timestamp(cmd.timestamp, 0)
                                                    .unwrap_or_else(chrono::Utc::now),
                                                duration_ms: cmd.duration_ms,
                                                working_dir: cmd.working_dir,
                                                exit_status: cmd.exit_status,
                                                is_favorite: false,
                                                tags: Vec::new(),
                                                hash: cmd.hash,
                                                source_file: Some(watch_path.to_string_lossy().to_string()),
                                                source_id: None,
                                            };
                                            let _ = store.add_command(new_cmd);
                                        }
                                    }
                                }
                            });
                        }
                        _ => {}
                    }
                }
            },
            Config::default(),
        ).map_err(|e| ShellmemError::Sync(e.to_string()))?;

        watcher.watch(path, RecursiveMode::NonRecursive)
            .map_err(|e| ShellmemError::Sync(e.to_string()))?;

        Ok(())
    }

    fn stop_watching(&self) -> Result<(), ShellmemError> {
        Ok(())
    }

    fn get_changes(&self) -> Vec<Command> {
        Vec::new()
    }
}
