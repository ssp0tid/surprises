use crate::config::model::Config;
use anyhow::{Context, Result};
use std::path::Path;

pub struct ConfigLoader;

impl ConfigLoader {
    const CONFIG_FILE_NAMES: &'static [&'static str] = &[
        ".codegen.yaml",
        ".codegen.yml",
        "codegen.yaml",
        "codegen.yml",
        ".codegen.config.yaml",
    ];

    pub fn load(path: Option<&Path>) -> Result<Option<Config>> {
        if let Some(p) = path {
            return Ok(Some(Self::load_file(p)?));
        }

        for name in Self::CONFIG_FILE_NAMES {
            if let Ok(config) = Self::load_file(Path::new(name)) {
                return Ok(Some(config));
            }
        }

        Ok(None)
    }

    fn load_file(path: &Path) -> Result<Config> {
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("Failed to read config: {:?}", path))?;

        if path.extension().and_then(|s| s.to_str()) == Some("yaml")
            || path.extension().and_then(|s| s.to_str()) == Some("yml")
        {
            serde_yaml::from_str(&content)
                .with_context(|| format!("Failed to parse YAML config: {:?}", path))
        } else {
            toml::from_str(&content)
                .with_context(|| format!("Failed to parse TOML config: {:?}", path))
        }
    }

    pub fn save(config: &Config, path: &Path) -> Result<()> {
        let content = serde_yaml::to_string(config)?;
        std::fs::write(path, content)?;
        Ok(())
    }
}
