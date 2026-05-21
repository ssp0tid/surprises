use anyhow::Result;

pub struct OpenApiGenerator;

impl OpenApiGenerator {
    pub fn generate(_url: &str) -> Result<String> {
        anyhow::bail!("Introspection not yet implemented")
    }
}
