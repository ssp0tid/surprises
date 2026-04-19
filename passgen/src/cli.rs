use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "passgen")]
#[command(version = "1.0.0")]
#[command(about = "Secure Password Generator CLI Tool", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Commands>,
    
    #[arg(short, long, default_value = "16")]
    pub length: usize,
    
#[arg(short = 'u', long)]
    pub uppercase: Option<bool>,
    
    #[arg(long)]
    pub lowercase: Option<bool>,
    
    #[arg(short = 'n', long)]
    pub numbers: Option<bool>,
    
    #[arg(short = 's', long)]
    pub symbols: Option<bool>,
    
    #[arg(long)]
    pub custom_symbols: Option<String>,
    
    #[arg(long)]
    pub exclude_ambiguous: Option<bool>,
    
    #[arg(long)]
    pub no_duplicate: Option<bool>,
    
    #[arg(long, default_value = "1")]
    pub count: usize,
    
    #[arg(short = 'p', long)]
    pub pronounceable: Option<bool>,
    
    #[arg(long)]
    pub copy: bool,
    
    #[arg(long, default_value = "30")]
    pub clear_clipboard: u64,
    
    #[arg(short, long)]
    pub output: Option<String>,
    
    #[arg(short, long, value_enum)]
    pub format: Option<ExportFormat>,
    
    #[arg(long)]
    pub no_history: bool,
    
    #[arg(short, long)]
    pub verbose: bool,
}

#[derive(Subcommand)]
pub enum Commands {
Generate {
        #[arg(short, long, default_value = "16")]
        length: usize,
        
        #[arg(short = 'u', long)]
        uppercase: Option<bool>,
        
        #[arg(long)]
        lowercase: Option<bool>,
        
        #[arg(short = 'n', long)]
        numbers: Option<bool>,
        
        #[arg(short = 's', long)]
        symbols: Option<bool>,
        
        #[arg(long)]
        custom_symbols: Option<String>,
        
        #[arg(long)]
        exclude_ambiguous: Option<bool>,
        
        #[arg(long)]
        no_duplicate: Option<bool>,
        
        #[arg(long, default_value = "1")]
        count: usize,
        
        #[arg(short = 'p', long)]
        pronounceable: Option<bool>,
        
        #[arg(long)]
        copy: bool,
        
        #[arg(long, default_value = "30")]
        clear_clipboard: u64,
        
        #[arg(long)]
        no_history: bool,
        
        #[arg(short, long)]
        verbose: bool,
    },
    
    History {
        #[arg(short = 'n', long, default_value = "10")]
        count: usize,
        
        #[arg(short, long)]
        search: Option<String>,
    },
    
    Clear,
    
    Export {
        #[arg(short, long)]
        output: String,
        
        #[arg(short, long, value_enum, default_value = "json")]
        format: ExportFormat,
    },
    
    Config {
        #[arg(short, long)]
        show: bool,
        
        #[arg(long)]
        set_length: Option<usize>,
        
        #[arg(long)]
        set_default_count: Option<usize>,
    },
}

#[derive(clap::ValueEnum, Clone)]
pub enum ExportFormat {
    Json,
    Csv,
    Txt,
}

impl Cli {
    pub fn to_generator_config(&self) -> crate::config::GeneratorConfig {
        crate::config::GeneratorConfig {
            length: self.length,
            uppercase: self.uppercase.unwrap_or(true),
            lowercase: self.lowercase.unwrap_or(true),
            numbers: self.numbers.unwrap_or(true),
            symbols: self.symbols.unwrap_or(true),
            custom_symbols: self.custom_symbols.clone(),
            exclude_ambiguous: self.exclude_ambiguous.unwrap_or(false),
            no_duplicate: self.no_duplicate.unwrap_or(false),
            pronounceable: self.pronounceable.unwrap_or(false),
            syllable_count: None,
            separator: None,
        }
    }
}

impl Commands {
    pub fn to_generator_config(&self) -> crate::config::GeneratorConfig {
        match self {
            Commands::Generate { length, uppercase, lowercase, numbers, symbols, 
                                custom_symbols, exclude_ambiguous, no_duplicate,
                                pronounceable, .. } => {
                crate::config::GeneratorConfig {
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
            },
            _ => crate::config::GeneratorConfig::default(),
        }
    }
}