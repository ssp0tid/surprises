use std::path::PathBuf;
use std::sync::Arc;

use chrono::{DateTime, NaiveDate, Utc};
use clap::{Parser, Subcommand, ValueEnum};
use color_eyre::eyre::Result;
use color_eyre::Report;
use tokio::sync::Mutex;

use shellmem_core::{
    config::Config as ShellmemConfig,
    models::{Command, NewCommand, SearchOptions, SearchResult, Shell, Tag},
    storage::Database,
    search::SearchEngine,
};

fn get_default_db_path() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("shellmem")
        .join("shellmem.db")
}

fn parse_date(s: &str) -> Result<DateTime<Utc>> {
    let date = NaiveDate::parse_from_str(s, "%Y-%m-%d")
        .map_err(|e| Report::msg(format!("Invalid date format: {}", e)))?;
    let datetime = date.and_hms_opt(0, 0, 0).unwrap();
    Ok(DateTime::from_naive_utc_and_offset(datetime, Utc))
}

fn format_command_table(commands: &[Command]) -> String {
    if commands.is_empty() {
        return "No commands found.".to_string();
    }

    let mut output = String::new();
    output.push_str(&format!("{:>4} | {:<20} | {:<10} | {}", 
        "ID", "TIMESTAMP", "SHELL", "COMMAND"));
    output.push('\n');
    output.push_str(&"-".repeat(4));
    output.push('+');
    output.push_str(&"-".repeat(20));
    output.push('+');
    output.push_str(&"-".repeat(10));
    output.push('+');
    output.push_str(&"=".repeat(1));
    output.push('\n');

    for cmd in commands {
        let timestamp = cmd.timestamp.format("%Y-%m-%d %H:%M").to_string();
        let shell_str = match cmd.shell {
            Shell::Bash => "bash",
            Shell::Zsh => "zsh",
            Shell::Fish => "fish",
        };
        let cmd_preview = if cmd.command.len() > 80 {
            format!("{}...", &cmd.command[..77])
        } else {
            cmd.command.clone()
        };
        output.push_str(&format!("{:>4} | {:<20} | {:<10} | {}", 
            cmd.id, timestamp, shell_str, cmd_preview));
        output.push('\n');
    }

    output
}

#[derive(Parser)]
#[command(name = "shellmem")]
#[command(about = "Shell history manager", long_about = None)]
struct Cli {
    #[arg(global = true, long = "database", value_name = "PATH")]
    database: Option<PathBuf>,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Search(SearchArgs),

    List(ListArgs),

    Fav {
        #[arg(value_parser)]
        action: FavAction,

        id: i64,
    },

    Tag(TagArgs),

    Import {
        shell: Shell,
        path: PathBuf,
    },

    Export {
        format: ExportFormat,
        path: PathBuf,
    },

    Dedupe {
        #[arg(long = "dry-run")]
        dry_run: bool,
    },

    Sync {
        #[arg(value_parser)]
        action: SyncAction,
    },

    Config(ConfigArgs),

    Tui,

    Completion {
        #[arg(value_parser)]
        shell: CompletionShell,
    },
}

#[derive(Args, Debug)]
struct SearchArgs {
    query: String,

    #[arg(long = "exact")]
    exact: bool,

    #[arg(long = "shell")]
    shell: Option<Shell>,

    #[arg(long = "from")]
    from_date: Option<String>,

    #[arg(long = "to")]
    to_date: Option<String>,

    #[arg(long = "favorites-only")]
    favorites_only: bool,

    #[arg(long = "limit")]
    limit: Option<usize>,
}

#[derive(Args, Debug)]
struct ListArgs {
    #[arg(long = "limit")]
    limit: Option<usize>,

    #[arg(long = "shell")]
    shell: Option<Shell>,

    #[arg(long = "from")]
    from_date: Option<String>,

    #[arg(long = "to")]
    to_date: Option<String>,
}

#[derive(ValueEnum, Debug, Clone)]
enum FavAction {
    Add,
    Remove,
}

#[derive(Args, Debug)]
struct TagArgs {
    #[command(subcommand)]
    subcommand: TagSubcommand,

    args: Vec<String>,
}

#[derive(Subcommand, Debug, Clone)]
enum TagSubcommand {
    Create,
    Add,
    Remove,
    List,
}

#[derive(ValueEnum, Debug, Clone)]
enum ExportFormat {
    Json,
    Csv,
}

#[derive(ValueEnum, Debug, Clone)]
enum SyncAction {
    Start,
    Stop,
    Status,
}

#[derive(Args, Debug)]
struct ConfigArgs {
    #[command(subcommand)]
    subcommand: ConfigSubcommand,

    args: Vec<String>,
}

#[derive(Subcommand, Debug, Clone)]
enum ConfigSubcommand {
    Get,
    Set,
    Show,
}

#[derive(ValueEnum, Debug, Clone)]
enum CompletionShell {
    Bash,
    Zsh,
    Fish,
}

async fn handle_search(
    db: Arc<Mutex<Database>>,
    args: SearchArgs,
) -> Result<()> {
    let from = if let Some(s) = args.from_date {
        Some(parse_date(&s)?)
    } else {
        None
    };
    let to = if let Some(s) = args.to_date {
        Some(parse_date(&s)?)
    } else {
        None
    };

    let options = SearchOptions {
        query: Some(args.query.clone()),
        shell: args.shell,
        from_date: from,
        to_date: to,
        tags: None,
        favorites_only: args.favorites_only,
        limit: args.limit,
        offset: None,
    };

    let db_guard = db.lock().await;
    let all_commands = db_guard.search(options)?;

    let engine = SearchEngine::new();
    let results = if args.exact {
        all_commands
            .into_iter()
            .filter(|cmd| cmd.command == args.query)
            .map(|cmd| SearchResult { command: cmd, score: 0 })
            .collect()
    } else {
        engine.search(&args.query, &all_commands)
    };

    println!("{}", format_search_results(&results));
    Ok(())
}

fn format_search_results(results: &[SearchResult]) -> String {
    if results.is_empty() {
        return "No results found.".to_string();
    }

    let mut output = String::new();
    output.push_str(&format!("{:>4} | {:>6} | {:<10} | {}", 
        "ID", "SCORE", "SHELL", "COMMAND"));
    output.push('\n');
    output.push_str(&"-".repeat(4));
    output.push('+');
    output.push_str(&"-".repeat(6));
    output.push('+');
    output.push_str(&"-".repeat(10));
    output.push('+');
    output.push_str(&"=".repeat(1));
    output.push('\n');

    for result in results {
        let shell_str = match result.command.shell {
            Shell::Bash => "bash",
            Shell::Zsh => "zsh",
            Shell::Fish => "fish",
        };
        let cmd_preview = if result.command.command.len() > 70 {
            format!("{}...", &result.command.command[..67])
        } else {
            result.command.command.clone()
        };
        output.push_str(&format!("{:>4} | {:>6} | {:<10} | {}", 
            result.command.id, result.score, shell_str, cmd_preview));
        output.push('\n');
    }

    output
}

async fn handle_list(
    db: Arc<Mutex<Database>>,
    args: ListArgs,
) -> Result<()> {
    let from = if let Some(s) = args.from_date {
        Some(parse_date(&s)?)
    } else {
        None
    };
    let to = if let Some(s) = args.to_date {
        Some(parse_date(&s)?)
    } else {
        None
    };

    let options = SearchOptions {
        query: None,
        shell: args.shell,
        from_date: from,
        to_date: to,
        tags: None,
        favorites_only: false,
        limit: args.limit,
        offset: None,
    };

    let db_guard = db.lock().await;
    let commands = db_guard.search(options)?;

    println!("{}", format_command_table(&commands));
    Ok(())
}

async fn handle_fav(
    db: Arc<Mutex<Database>>,
    action: FavAction,
    id: i64,
) -> Result<()> {
    let db_guard = db.lock().await;
    match action {
        FavAction::Add => {
            db_guard.set_favorite(id, true)?;
            println!("Added command {} to favorites.", id);
        }
        FavAction::Remove => {
            db_guard.set_favorite(id, false)?;
            println!("Removed command {} from favorites.", id);
        }
    }
    Ok(())
}

async fn handle_tag(
    db: Arc<Mutex<Database>>,
    args: TagArgs,
) -> Result<()> {
    let db_guard = db.lock().await;
    match args.subcommand {
        TagSubcommand::Create => {
            if args.args.is_empty() {
                return Err(Report::msg("tag create requires <name> [color]"));
            }
            let name = &args.args[0];
            let color = args.args.get(1).map(|s| s.as_str()).unwrap_or("#808080");
            let tag = db_guard.create_tag(name, color)?;
            println!("Created tag: {} (id: {}, color: {})", tag.name, tag.id, tag.color);
        }
        TagSubcommand::Add => {
            if args.args.len() < 2 {
                return Err(Report::msg("tag add requires <command_id> <tag_name>"));
            }
            let cmd_id: i64 = args.args[0].parse()
                .map_err(|_| Report::msg("invalid command id"))?;
            let tag_name = &args.args[1];
            let tag = db_guard.tag_exists(tag_name)?
                .ok_or_else(|| Report::msg(format!("tag '{}' not found", tag_name)))?;
            db_guard.add_tag(cmd_id, tag.id)?;
            println!("Added tag '{}' to command {}", tag_name, cmd_id);
        }
        TagSubcommand::Remove => {
            if args.args.len() < 2 {
                return Err(Report::msg("tag remove requires <command_id> <tag_name>"));
            }
            let cmd_id: i64 = args.args[0].parse()
                .map_err(|_| Report::msg("invalid command id"))?;
            let tag_name = &args.args[1];
            let tag = db_guard.tag_exists(tag_name)?
                .ok_or_else(|| Report::msg(format!("tag '{}' not found", tag_name)))?;
            db_guard.remove_tag(cmd_id, tag.id)?;
            println!("Removed tag '{}' from command {}", tag_name, cmd_id);
        }
        TagSubcommand::List => {
            let tags = db_guard.get_all_tags()?;
            if tags.is_empty() {
                println!("No tags found.");
            } else {
                println!("Tags:");
                for tag in tags {
                    println!("  {} - {} (id: {})", tag.name, tag.color, tag.id);
                }
            }
        }
    }
    Ok(())
}

async fn handle_import(
    db: Arc<Mutex<Database>>,
    shell: Shell,
    path: PathBuf,
) -> Result<()> {
    if !path.exists() {
        return Err(Report::msg(format!("File not found: {}", path.display())));
    }

    let content = std::fs::read_to_string(&path)?;
    let parsed_commands = shellmem_core::parser::parse_shell(shell.clone(), &content)?;

    let mut imported = 0;
    let mut skipped = 0;
    let mut db_guard = db.lock().await;
    for parsed in parsed_commands {
        let new_cmd = NewCommand {
            command: parsed.command,
            shell: shell.clone(),
            timestamp: chrono::DateTime::from_timestamp_opt(parsed.timestamp, 0)
                .unwrap_or_else(chrono::Utc::now),
            duration_ms: parsed.duration_ms,
            working_dir: parsed.working_dir,
            exit_status: parsed.exit_status,
            is_favorite: false,
            tags: Vec::new(),
            hash: parsed.hash,
            source_file: Some(path.to_string_lossy().to_string()),
            source_id: None,
        };
        match db_guard.add_command(new_cmd) {
            Ok(id) if id > 0 => imported += 1,
            _ => skipped += 1,
        }
    }
    drop(db_guard);

    println!("Imported {} commands from {} ({} duplicates skipped).", imported, path.display(), skipped);
    Ok(())
}

async fn handle_export(
    db: Arc<Mutex<Database>>,
    format: ExportFormat,
    path: PathBuf,
) -> Result<()> {
    let options = SearchOptions {
        query: None,
        shell: None,
        from_date: None,
        to_date: None,
        tags: None,
        favorites_only: false,
        limit: None,
        offset: None,
    };

    let db_guard = db.lock().await;
    let commands = db_guard.search(options)?;

    match format {
        ExportFormat::Json => {
            let json = serde_json::to_string_pretty(&commands)
                .map_err(|e| Report::msg(format!("JSON serialization error: {}", e)))?;
            std::fs::write(&path, json)?;
            println!("Exported {} commands to {}", commands.len(), path.display());
        }
        ExportFormat::Csv => {
            let mut csv = String::new();
            csv.push_str("id,command,shell,timestamp,duration_ms,working_dir,exit_status,is_favorite,hash\n");
            for cmd in commands {
                let escaped = cmd.command.replace('"', "\"\"");
                let shell_name = match cmd.shell {
                    Shell::Bash => "bash",
                    Shell::Zsh => "zsh",
                    Shell::Fish => "fish",
                };
                csv.push_str(&format!(
                    "{},\"{}\",{},{},{},{},{},{},{}\n",
                    cmd.id,
                    escaped,
                    shell_name,
                    cmd.timestamp,
                    cmd.duration_ms.map(|d| d.to_string()).unwrap_or_default(),
                    cmd.working_dir.as_deref().unwrap_or_default(),
                    cmd.exit_status.map(|e| e.to_string()).unwrap_or_default(),
                    cmd.is_favorite,
                    cmd.hash
                ));
            }
            std::fs::write(&path, csv)?;
            println!("Exported {} commands to {}", commands.len(), path.display());
        }
    }

    Ok(())
}

async fn handle_dedupe(
    db: Arc<Mutex<Database>>,
    dry_run: bool,
) -> Result<()> {
    let mut db_guard = db.lock().await;
    let report = db_guard.dedupe()?;

    if dry_run {
        println!("Dry run - would remove {} duplicates", report.duplicates_removed);
        println!("Would keep {} unique commands", report.unique_commands);
        println!("Total before: {}", report.total_before);
    } else {
        println!("Removed {} duplicates", report.duplicates_removed);
        println!("Kept {} unique commands", report.unique_commands);
    }
    Ok(())
}

async fn handle_sync(
    _db: Arc<Mutex<Database>>,
    action: SyncAction,
) -> Result<()> {
    match action {
        SyncAction::Start => {
            println!("Sync started (file watching not yet implemented)");
        }
        SyncAction::Stop => {
            println!("Sync stopped");
        }
        SyncAction::Status => {
            println!("Sync status: inactive");
        }
    }
    Ok(())
}

fn handle_config(args: ConfigArgs) -> Result<()> {
    let config = ShellmemConfig::load().unwrap_or_default();

    match args.subcommand {
        ConfigSubcommand::Get => {
            if args.args.is_empty() {
                println!("{}", toml::to_string_pretty(&config.inner).unwrap());
            } else {
                let key = &args.args[0];
                match key.as_str() {
                    "fuzzy" => println!("{}", config.inner.search.fuzzy),
                    "default_limit" => println!("{}", config.inner.search.default_limit),
                    "max_results" => println!("{}", config.inner.search.max_results),
                    "interval" => println!("{}", config.inner.sync.interval),
                    _ => return Err(Report::msg(format!("Unknown config key: {}", key))),
                }
            }
        }
        ConfigSubcommand::Set => {
            if args.args.len() < 2 {
                return Err(Report::msg("config set requires <key> <value>"));
            }
            let key = &args.args[0];
            let value = &args.args[1];
            match key.as_str() {
                "fuzzy" => {
                    config.inner.search.fuzzy = value.parse()
                        .map_err(|_| Report::msg("invalid boolean value"))?;
                }
                "default_limit" => {
                    config.inner.search.default_limit = value.parse()
                        .map_err(|_| Report::msg("invalid number"))?;
                }
                "max_results" => {
                    config.inner.search.max_results = value.parse()
                        .map_err(|_| Report::msg("invalid number"))?;
                }
                "interval" => {
                    config.inner.sync.interval = value.parse()
                        .map_err(|_| Report::msg("invalid number"))?;
                }
                _ => return Err(Report::msg(format!("Unknown config key: {}", key))),
            }
            config.save()?;
            println!("Set {} = {}", key, value);
        }
        ConfigSubcommand::Show => {
            println!("{}", toml::to_string_pretty(&config.inner).unwrap());
        }
    }
    Ok(())
}

fn handle_tui() -> Result<()> {
    std::process::Command::new("shellmem-tui")
        .spawn()
        .map_err(|e| Report::msg(format!("Failed to launch tui: {}", e)))?;
    Ok(())
}

fn handle_completion(shell: CompletionShell) {
    use clap_complete::shells::Shell as ClapShell;
    use clap_complete::generate;

    let mut cmd = Cli::command();
    
    match shell {
        CompletionShell::Bash => {
            generate::<Cli, ClapShell>(&mut cmd, "shellmem", &mut std::io::stdout());
        }
        CompletionShell::Zsh => {
            generate::<Cli, ClapShell>(&mut cmd, "shellmem", &mut std::io::stdout());
        }
        CompletionShell::Fish => {
            generate::<Cli, ClapShell>(&mut cmd, "shellmem", &mut std::io::stdout());
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    color_eyre::install()?;

    let cli = Cli::parse();
    let db_path = cli.database.unwrap_or_else(get_default_db_path);

    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let db = Arc::new(Mutex::new(Database::new(&db_path)?));

    match cli.command {
        Commands::Search(args) => {
            handle_search(db, args).await?;
        }
        Commands::List(args) => {
            handle_list(db, args).await?;
        }
        Commands::Fav { action, id } => {
            handle_fav(db, action, id).await?;
        }
        Commands::Tag(args) => {
            handle_tag(db, args).await?;
        }
        Commands::Import { shell, path } => {
            handle_import(db, shell, path).await?;
        }
        Commands::Export { format, path } => {
            handle_export(db, format, path).await?;
        }
        Commands::Dedupe { dry_run } => {
            handle_dedupe(db, dry_run).await?;
        }
        Commands::Sync { action } => {
            handle_sync(db, action).await?;
        }
        Commands::Config(args) => {
            handle_config(args)?;
        }
        Commands::Tui => {
            handle_tui()?;
        }
        Commands::Completion { shell } => {
            handle_completion(shell);
        }
    }

    Ok(())
}