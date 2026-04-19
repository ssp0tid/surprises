use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GeneratorConfig {
    pub length: usize,
    pub uppercase: bool,
    pub lowercase: bool,
    pub numbers: bool,
    pub symbols: bool,
    pub custom_symbols: Option<String>,
    pub exclude_ambiguous: bool,
    pub no_duplicate: bool,
    pub pronounceable: bool,
    pub syllable_count: Option<usize>,
    pub separator: Option<char>,
}

impl Default for GeneratorConfig {
    fn default() -> Self {
        Self {
            length: 16,
            uppercase: true,
            lowercase: true,
            numbers: true,
            symbols: true,
            custom_symbols: None,
            exclude_ambiguous: false,
            no_duplicate: false,
            pronounceable: false,
            syllable_count: None,
            separator: None,
        }
    }
}

impl GeneratorConfig {
    pub fn charset_size(&self) -> usize {
        self.charset().len()
    }

    pub fn charset(&self) -> Vec<char> {
        let mut chars = Vec::new();
        let custom = self.custom_symbols.as_deref().unwrap_or("!@#$%^&*()-_=+[]{}|;:',.<>/?");
        let ambiguous = ['0', 'O', 'l', '1', 'I'];

        if self.lowercase {
            let mut lower: Vec<char> = "abcdefghijklmnopqrstuvwxyz".chars().collect();
            if self.exclude_ambiguous {
                lower.retain(|c| !ambiguous.contains(c));
            }
            chars.extend(lower);
        }

        if self.uppercase {
            let mut upper: Vec<char> = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".chars().collect();
            if self.exclude_ambiguous {
                upper.retain(|c| !ambiguous.contains(c));
            }
            chars.extend(upper);
        }

        if self.numbers {
            let mut nums: Vec<char> = "0123456789".chars().collect();
            if self.exclude_ambiguous {
                nums.retain(|c| !ambiguous.contains(c));
            }
            chars.extend(nums);
        }

        if self.symbols || self.custom_symbols.is_some() {
            let syms: Vec<char> = custom.chars().collect();
            if self.exclude_ambiguous {
                chars.extend(syms.into_iter().filter(|c| !ambiguous.contains(c)));
            } else {
                chars.extend(syms);
            }
        }

        chars
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub generator: GeneratorConfig,
    pub clipboard: ClipboardConfig,
    pub storage: StorageConfig,
    pub output: OutputConfig,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ClipboardConfig {
    pub auto_copy: bool,
    pub auto_clear: bool,
    pub clear_timeout: u64,
}

impl Default for ClipboardConfig {
    fn default() -> Self {
        Self {
            auto_copy: false,
            auto_clear: true,
            clear_timeout: 30,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StorageConfig {
    pub history_enabled: bool,
    pub max_history: usize,
    pub encryption_enabled: bool,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            history_enabled: true,
            max_history: 100,
            encryption_enabled: true,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OutputConfig {
    pub verbose: bool,
    pub color: bool,
    pub show_entropy: bool,
    pub show_strength: bool,
}

impl Default for OutputConfig {
    fn default() -> Self {
        Self {
            verbose: false,
            color: true,
            show_entropy: true,
            show_strength: true,
        }
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            generator: GeneratorConfig::default(),
            clipboard: ClipboardConfig::default(),
            storage: StorageConfig::default(),
            output: OutputConfig::default(),
        }
    }
}

impl AppConfig {
    pub fn config_dir() -> Option<std::path::PathBuf> {
        dirs::config_dir().map(|p| p.join("passgen"))
    }

    pub fn config_path() -> Option<std::path::PathBuf> {
        Self::config_dir().map(|p| p.join("config.toml"))
    }

    pub fn load() -> std::result::Result<Self, Box<dyn std::error::Error>> {
        if let Some(path) = Self::config_path() {
            if path.exists() {
                let content = std::fs::read_to_string(&path)?;
                let config: AppConfig = toml::from_str(&content)?;
                return Ok(config);
            }
        }
        Ok(AppConfig::default())
    }

    pub fn save(&self) -> std::result::Result<(), Box<dyn std::error::Error>> {
        if let Some(dir) = Self::config_dir() {
            std::fs::create_dir_all(&dir)?;
            let content = toml::to_string_pretty(self)?;
            std::fs::write(Self::config_path().unwrap(), content)?;
        }
        Ok(())
    }
}