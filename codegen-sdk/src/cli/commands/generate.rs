use crate::parser::types::ApiSpec;
use anyhow::{Context, Result};
use std::path::PathBuf;
use tracing::info;

use super::super::args::GenerateArgs;

pub fn execute(args: &GenerateArgs) -> Result<()> {
    let input = args.input.clone().context("INPUT required")?;
    let output = args
        .output
        .clone()
        .unwrap_or_else(|| PathBuf::from("./generated"));

    info!("Generating SDK from: {:?}", input);
    info!("Output directory: {:?}", output);

    let spec = load_spec(&input)?;

    info!("Parsed spec: {} - v{}", spec.info.title, spec.info.version);
    info!("Found {} endpoints", spec.endpoints.len());
    info!("Found {} schemas", spec.schemas.len());

    println!("Successfully parsed OpenAPI spec:");
    println!("  Title: {}", spec.info.title);
    println!("  Version: {}", spec.info.version);
    println!("  Endpoints: {}", spec.endpoints.len());
    println!("  Schemas: {}", spec.schemas.len());

    if let Some(ref desc) = spec.info.description {
        println!("  Description: {}", desc);
    }

    Ok(())
}

fn load_spec(input: &PathBuf) -> Result<ApiSpec> {
    if !input.exists() {
        anyhow::bail!("Input file not found: {:?}", input);
    }

    let content = std::fs::read_to_string(input)?;
    let spec = crate::parser::openapi::parser::OpenApiParser::parse(&content)?;

    Ok(spec)
}
