use std::fmt;

pub struct Output {
    pub verbose: bool,
}

impl Output {
    pub fn new(verbose: bool) -> Self {
        Self { verbose }
    }

    pub fn info(&self, msg: &str) {
        if self.verbose {
            println!("[INFO] {}", msg);
        }
    }

    pub fn warn(&self, msg: &str) {
        println!("[WARN] {}", msg);
    }

    pub fn error(&self, msg: &str) {
        eprintln!("[ERROR] {}", msg);
    }

    pub fn success(&self, msg: &str) {
        println!("✓ {}", msg);
    }
}

impl Default for Output {
    fn default() -> Self {
        Self::new(false)
    }
}

pub struct ValidationOutput {
    pub errors: Vec<ValidationError>,
    pub warnings: Vec<ValidationWarning>,
}

#[derive(Debug, Clone)]
pub struct ValidationError {
    pub path: String,
    pub message: String,
    pub severity: Severity,
}

#[derive(Debug, Clone)]
pub struct ValidationWarning {
    pub path: String,
    pub message: String,
}

#[derive(Debug, Clone, Copy)]
pub enum Severity {
    Error,
    Warning,
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.path, self.message)
    }
}
