use crate::models::Shell;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    inner: ConfigInner,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigInner {
    pub home: PathBuf,
    pub shells: HashMap<Shell, ShellConfig>,
    pub sync: SyncConfig,
    pub search: SearchConfig,
    pub tags: Vec<TagConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShellConfig {
    pub history_file: PathBuf,
    pub parser: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncConfig {
    pub enabled: bool,
    pub interval: u64,
    pub watch: Vec<PathBuf>,
}

impl Default for SyncConfig {
    fn default() -> Self {
        SyncConfig {
            enabled: false,
            interval: 60,
            watch: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchConfig {
    pub fuzzy: bool,
    pub default_limit: usize,
    pub max_results: usize,
}

impl Default for SearchConfig {
    fn default() -> Self {
        SearchConfig {
            fuzzy: true,
            default_limit: 50,
            max_results: 1000,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TagConfig {
    pub name: String,
    pub color: String,
}

impl Default for TagConfig {
    fn default() -> Self {
        TagConfig {
            name: String::new(),
            color: String::from("#808080"),
        }
    }
}

impl Default for ConfigInner {
    fn default() -> Self {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        ConfigInner {
            home: home.clone(),
            shells: default_shells(&home),
            sync: SyncConfig::default(),
            search: SearchConfig::default(),
            tags: Vec::new(),
        }
    }
}

fn default_shells(home: &PathBuf) -> HashMap<Shell, ShellConfig> {
    let mut shells = HashMap::new();
    shells.insert(
        Shell::Bash,
        ShellConfig {
            history_file: home.join(".bash_history"),
            parser: "bash".to_string(),
        },
    );
    shells.insert(
        Shell::Zsh,
        ShellConfig {
            history_file: home.join(".zsh_history"),
            parser: "zsh".to_string(),
        },
    );
    shells.insert(
        Shell::Fish,
        ShellConfig {
            history_file: home.join(".local/share/fish/fish_history"),
            parser: "fish".to_string(),
        },
    );
    shells
}

impl Default for Config {
    fn default() -> Self {
        Config {
            inner: ConfigInner::default(),
        }
    }
}

impl Config {
    pub fn load() -> Result<Self, crate::ShellmemError> {
        let config_path = Self::config_path()?;
        if config_path.exists() {
            let content = fs::read_to_string(&config_path)?;
            let inner: ConfigInner = toml::from_str(&content).map_err(|e| {
                crate::ShellmemError::Config(format!("Failed to parse config: {}", e))
            })?;
            Ok(Config { inner })
        } else {
            Ok(Config::default())
        }
    }

    fn config_path() -> Result<PathBuf, crate::ShellmemError> {
        let base = dirs::config_dir().ok_or_else(|| {
            crate::ShellmemError::Config("Could not determine config directory".to_string())
        })?;
        Ok(base.join("shellmem").join("config.toml"))
    }

    pub fn save(&self) -> Result<(), crate::ShellmemError> {
        let config_path = Self::config_path()?;
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let content = toml::to_string_pretty(&self.inner).map_err(|e| {
            crate::ShellmemError::Config(format!("Failed to serialize config: {}", e))
        })?;
        fs::write(config_path, content)?;
        Ok(())
    }
}