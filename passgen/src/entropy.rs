use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum Strength {
    Weak,
    Fair,
    Good,
    Strong,
    VeryStrong,
}

impl Strength {
    pub fn from_entropy(entropy: f64) -> Self {
        if entropy < 28.0 {
            Strength::Weak
        } else if entropy < 36.0 {
            Strength::Fair
        } else if entropy < 60.0 {
            Strength::Good
        } else if entropy < 80.0 {
            Strength::Strong
        } else {
            Strength::VeryStrong
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            Strength::Weak => "Weak",
            Strength::Fair => "Fair",
            Strength::Good => "Good",
            Strength::Strong => "Strong",
            Strength::VeryStrong => "Very Strong",
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EntropyInfo {
    pub entropy: f64,
    pub strength: Strength,
    pub charset_size: usize,
    pub length: usize,
}

impl EntropyInfo {
    pub fn calculate(password: &str, charset_size: usize) -> Self {
        let length = password.len();
        let entropy = if charset_size > 0 {
            (charset_size as f64).log2() * (length as f64)
        } else {
            0.0
        };
        let strength = Strength::from_entropy(entropy);

        Self {
            entropy,
            strength,
            charset_size,
            length,
        }
    }

    pub fn estimate_crack_time(&self) -> String {
        let combinations = 2.0_f64.powf(self.entropy);
        let guesses_per_second = 1.0e10_f64;
        let seconds = combinations / guesses_per_second;

        if seconds < 1.0 {
            format!("instantly")
        } else if seconds < 60.0 {
            format!("{:.1} seconds", seconds)
        } else if seconds < 3600.0 {
            format!("{:.1} minutes", seconds / 60.0)
        } else if seconds < 86400.0 {
            format!("{:.1} hours", seconds / 3600.0)
        } else if seconds < 31536000.0 {
            format!("{:.1} days", seconds / 86400.0)
        } else if seconds < 31536000.0 * 1000.0 {
            format!("{:.1e} years", seconds / 31536000.0)
        } else {
            format!("{:.1e} years", seconds / 31536000.0)
        }
    }
}