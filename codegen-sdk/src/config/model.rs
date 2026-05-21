use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub version: String,
    #[serde(default)]
    pub language: Option<String>,
    #[serde(default)]
    pub output: Option<String>,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub template: Option<String>,
    #[serde(default)]
    pub options: ConfigOptions,
    #[serde(default)]
    pub auth: Option<AuthConfig>,
    #[serde(default)]
    pub base_url: Option<String>,
    #[serde(default)]
    pub headers: HashMap<String, String>,
    #[serde(default)]
    pub include: Vec<String>,
    #[serde(default)]
    pub exclude: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigOptions {
    #[serde(rename = "skip-validation", default)]
    pub skip_validation: bool,
    #[serde(rename = "types-only", default)]
    pub types_only: bool,
    #[serde(default)]
    pub force: bool,
    #[serde(default)]
    pub strict: bool,
}

impl Default for ConfigOptions {
    fn default() -> Self {
        Self {
            skip_validation: false,
            types_only: false,
            force: false,
            strict: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    #[serde(rename = "type")]
    pub auth_type: String,
    #[serde(default)]
    pub token: Option<String>,
    #[serde(default)]
    pub key: Option<String>,
    #[serde(default)]
    pub location: Option<String>,
}
