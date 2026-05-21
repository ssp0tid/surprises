use crate::parser::types::*;
use anyhow::Result;

pub struct PostmanParser;

impl PostmanParser {
    pub fn parse(input: &str) -> Result<ApiSpec> {
        let _collection: serde_json::Value = serde_json::from_str(input)?;
        anyhow::bail!("Postman parsing not yet implemented")
    }

    pub fn parse_file(path: &std::path::Path) -> Result<ApiSpec> {
        let content = std::fs::read_to_string(path)?;
        Self::parse(&content)
    }
}
