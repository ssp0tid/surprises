use crate::parser::openapi::validator::OpenApiValidator;
use crate::parser::types::ApiSpec;
use anyhow::{Context, Result};
use std::path::PathBuf;
use tracing::info;

use super::super::args::{OutputFormat, ValidateArgs};

pub fn execute(args: &ValidateArgs) -> Result<()> {
    let input = args.input.clone().context("INPUT required")?;

    info!("Validating spec: {:?}", input);

    let spec = load_spec(&input)?;
    let errors = OpenApiValidator::validate(&spec);

    match args.format.as_ref().unwrap_or(&OutputFormat::Text) {
        OutputFormat::Text => {
            if errors.is_empty() {
                println!("✓ Spec is valid");
                println!("  Title: {}", spec.info.title);
                println!("  Version: {}", spec.info.version);
                Ok(())
            } else {
                println!("✗ Validation errors found: {}", errors.len());
                for err in &errors {
                    println!("  - {}", err);
                }
                std::process::exit(1);
            }
        }
        OutputFormat::Json => {
            let json = serde_json::json!({
                "valid": errors.is_empty(),
                "errors": errors,
                "spec": {
                    "title": spec.info.title,
                    "version": spec.info.version,
                }
            });
            println!("{}", serde_json::to_string_pretty(&json)?);
            if !errors.is_empty() {
                std::process::exit(1);
            }
            Ok(())
        }
        OutputFormat::Sarif => {
            println!("SARIF output not yet implemented");
            Ok(())
        }
    }
}

fn load_spec(input: &PathBuf) -> Result<ApiSpec> {
    let content = std::fs::read_to_string(input)
        .with_context(|| format!("Failed to read file: {:?}", input))?;

    let spec = crate::parser::openapi::parser::OpenApiParser::parse(&content)?;

    Ok(spec)
}
