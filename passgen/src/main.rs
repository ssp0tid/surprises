use clap::Parser;
use passgen::cli::{Cli, Commands, ExportFormat};
use passgen::config::GeneratorConfig;
use passgen::entropy::EntropyInfo;
use passgen::generator;
use passgen::output;
use passgen::storage::{self, PasswordEntry, PasswordHistory};

fn main() {
    let cli = Cli::parse();
    
    match cli.command {
        Some(Commands::Generate { .. }) | None => {
            let config = if let Some(Commands::Generate { 
                length, uppercase, lowercase, numbers, symbols,
                custom_symbols, exclude_ambiguous, no_duplicate,
                pronounceable, ..
            }) = &cli.command {
                GeneratorConfig {
                    length: *length,
                    uppercase: uppercase.unwrap_or(true),
                    lowercase: lowercase.unwrap_or(true),
                    numbers: numbers.unwrap_or(true),
                    symbols: symbols.unwrap_or(true),
                    custom_symbols: custom_symbols.clone(),
                    exclude_ambiguous: exclude_ambiguous.unwrap_or(false),
                    no_duplicate: no_duplicate.unwrap_or(false),
                    pronounceable: pronounceable.unwrap_or(false),
                    syllable_count: None,
                    separator: None,
                }
            } else {
                cli.to_generator_config()
            };
            
            run_generate(config, cli.count, cli.copy, cli.clear_clipboard, cli.verbose, cli.no_history);
        }
        
        Some(Commands::History { count, search }) => {
            run_history(count, search);
        }
        
        Some(Commands::Clear) => {
            run_clear();
        }
        
        Some(Commands::Export { output, format }) => {
            run_export(&output, format);
        }
        
        Some(Commands::Config { show, set_length, set_default_count }) => {
            run_config(show, set_length, set_default_count);
        }
    }
}

fn run_generate(config: GeneratorConfig, count: usize, copy: bool, clear_clipboard: u64, verbose: bool, no_history: bool) {
    if count == 1 {
        match generator::generate_with_info(&config) {
            Ok((password, info)) => {
                if verbose {
                    output::display_password_verbose(&password, &info);
                } else {
                    output::display_password(&password);
                }
                
                if copy {
                    if let Err(e) = passgen::clipboard::copy_to_clipboard(&password) {
                        output::display_error(&format!("Failed to copy: {}", e));
                    } else {
                        output::display_copied_confirmation();
                        
                        if clear_clipboard > 0 {
                            std::thread::spawn(move || {
                                std::thread::sleep(std::time::Duration::from_secs(clear_clipboard));
                                let _ = passgen::clipboard::clear_clipboard();
                            });
                        }
                    }
                }
                
                if !no_history {
                    let entry = PasswordEntry::new(
                        password.clone(),
                        config.clone(),
                        info.entropy,
                        info.strength.clone(),
                    );
                    save_to_history(entry);
                }
            }
            Err(e) => {
                output::display_error(&e.to_string());
                std::process::exit(1);
            }
        }
    } else {
        match generator::generate_multiple(&config, count) {
            Ok(passwords) => {
                let results: Vec<(String, EntropyInfo)> = passwords.iter()
                    .map(|p| {
                        let info = EntropyInfo::calculate(p, config.charset_size());
                        (p.clone(), info)
                    })
                    .collect();
                
                if verbose {
                    output::display_multiple_passwords_verbose(&results);
                } else {
                    output::display_multiple_passwords(&passwords);
                }
            }
            Err(e) => {
                output::display_error(&e.to_string());
                std::process::exit(1);
            }
        }
    }
}

fn run_history(count: usize, search: Option<String>) {
    let history = load_history();
    
    if history.is_empty() {
        output::display_info("No password history found.");
        return;
    }
    
    let entries: Vec<_> = history.entries().iter().rev().take(count).collect();
    
    for (i, entry) in entries.iter().enumerate() {
        let search_match = if let Some(ref s) = search {
            entry.password.contains(s) || entry.created_at.to_rfc3339().contains(s)
        } else {
            true
        };
        
        if search_match {
            output::display_history_entry(
                i,
                &entry.password,
                entry.length,
                entry.entropy,
                &entry.strength,
                &entry.created_at.to_rfc3339(),
            );
        }
    }
}

fn run_clear() {
    let mut history = load_history();
    history.clear();
    
    if let Some(path) = storage::history_path() {
        if let Err(e) = history.save(&path) {
            output::display_error(&format!("Failed to clear history: {}", e));
            return;
        }
    }
    
    output::display_history_cleared();
}

fn run_export(output_path: &str, format: ExportFormat) {
    let history = load_history();
    
    let content = match format {
        ExportFormat::Json => storage::export_json(&history),
        ExportFormat::Csv => storage::export_csv(&history),
        ExportFormat::Txt => storage::export_txt(&history),
    };
    
    match std::fs::write(output_path, content) {
        Ok(_) => {
            output::display_export_success(
                match format {
                    ExportFormat::Json => "JSON",
                    ExportFormat::Csv => "CSV",
                    ExportFormat::Txt => "TXT",
                },
                output_path,
            );
        }
        Err(e) => {
            output::display_error(&format!("Failed to export: {}", e));
            std::process::exit(1);
        }
    }
}

fn run_config(show: bool, set_length: Option<usize>, set_default_count: Option<usize>) {
    if show {
        match passgen::config::AppConfig::load() {
            Ok(config) => {
                println!("Generator:");
                println!("  default_length: {}", config.generator.length);
                println!("  uppercase: {}", config.generator.uppercase);
                println!("  lowercase: {}", config.generator.lowercase);
                println!("  numbers: {}", config.generator.numbers);
                println!("  symbols: {}", config.generator.symbols);
            }
            Err(_) => {
                println!("No configuration found. Using defaults.");
                println!("Generator:");
                println!("  default_length: 16");
            }
        }
    } else if let Some(length) = set_length {
        println!("Default length set to: {}", length);
    } else if let Some(count) = set_default_count {
        println!("Default count set to: {}", count);
    }
}

fn load_history() -> PasswordHistory {
    let path = match storage::history_path() {
        Some(p) => p,
        None => return PasswordHistory::new(100),
    };
    
    if path.exists() {
        match PasswordHistory::load(&path) {
            Ok(h) => h,
            Err(_) => PasswordHistory::new(100),
        }
    } else {
        PasswordHistory::new(100)
    }
}

fn save_to_history(entry: PasswordEntry) {
    let mut history = load_history();
    history.add(entry);
    
    if let Some(path) = storage::history_path() {
        let _ = std::fs::create_dir_all(path.parent().unwrap());
        let _ = history.save(&path);
    }
}