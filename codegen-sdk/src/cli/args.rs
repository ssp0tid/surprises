use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "codegen-sdk")]
#[command(about = "Generate typed client SDKs from OpenAPI specs", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    Generate(GenerateArgs),
    Validate(ValidateArgs),
    Init(InitArgs),
    Introspect(IntrospectArgs),
}

#[derive(Parser)]
#[command(about = "Generate client SDK from spec")]
pub struct GenerateArgs {
    #[arg(value_name = "INPUT")]
    pub input: Option<PathBuf>,

    #[arg(short, long, value_name = "DIR")]
    pub output: Option<PathBuf>,

    #[arg(short, long, value_name = "LANG")]
    pub language: Option<String>,

    #[arg(long, value_name = "LANG", hide = true)]
    pub lang: Option<String>,

    #[arg(short, long, value_name = "NAME")]
    pub name: Option<String>,

    #[arg(long, value_name = "NS")]
    pub namespace: Option<String>,

    #[arg(short, long, value_name = "PATH")]
    pub template: Option<PathBuf>,

    #[arg(long)]
    pub skip_validation: bool,

    #[arg(long)]
    pub strict: bool,

    #[arg(long, value_name = "TYPE")]
    pub auth: Option<String>,

    #[arg(long, value_name = "URL")]
    pub base_url: Option<String>,

    #[arg(long = "header", value_name = "KEY=VALUE")]
    pub headers: Vec<String>,

    #[arg(long)]
    pub no_client: bool,

    #[arg(long)]
    pub force: bool,
}

#[derive(Parser)]
#[command(about = "Validate spec file")]
pub struct ValidateArgs {
    #[arg(value_name = "INPUT")]
    pub input: Option<PathBuf>,

    #[arg(short, long, value_name = "FMT")]
    pub format: Option<OutputFormat>,

    #[arg(long)]
    pub strict: bool,
}

#[derive(Parser)]
#[command(about = "Initialize config file")]
pub struct InitArgs {
    #[arg(short, long, value_name = "LANG")]
    pub language: Option<String>,

    #[arg(short, long, value_name = "DIR")]
    pub output: Option<PathBuf>,

    #[arg(long)]
    pub force: bool,
}

#[derive(Parser)]
#[command(about = "Introspect running API")]
pub struct IntrospectArgs {
    #[arg(value_name = "URL")]
    pub url: Option<String>,

    #[arg(short, long, value_name = "FILE")]
    pub output: Option<PathBuf>,

    #[arg(long, value_name = "TYPE")]
    pub scraper: Option<String>,

    #[arg(long = "header", value_name = "KEY=VALUE")]
    pub headers: Vec<String>,
}

#[derive(Clone, ValueEnum)]
pub enum OutputFormat {
    Text,
    Json,
    Sarif,
}

impl Default for OutputFormat {
    fn default() -> Self {
        OutputFormat::Text
    }
}
