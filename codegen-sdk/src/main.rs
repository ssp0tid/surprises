use clap::Parser;
use codegen_sdk::cli::args::Cli;
use tracing_subscriber::EnvFilter;

fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into()))
        .init();

    let cli = Cli::parse();

    match cli.command {
        codegen_sdk::cli::args::Commands::Generate(args) => {
            codegen_sdk::cli::commands::generate::execute(&args)?;
        }
        codegen_sdk::cli::args::Commands::Validate(args) => {
            codegen_sdk::cli::commands::validate::execute(&args)?;
        }
        codegen_sdk::cli::args::Commands::Init(_args) => {
            println!("Init command not yet implemented");
        }
        codegen_sdk::cli::args::Commands::Introspect(_args) => {
            println!("Introspect command not yet implemented");
        }
    }

    Ok(())
}
