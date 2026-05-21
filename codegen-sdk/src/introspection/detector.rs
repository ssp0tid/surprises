use anyhow::Result;

pub struct ApiDetector;

impl ApiDetector {
    pub fn detect(_url: &str) -> Result<ApiInfo> {
        anyhow::bail!("Detection not yet implemented")
    }
}

#[derive(Debug)]
pub struct ApiInfo {
    pub url: String,
    pub has_openapi: bool,
}
