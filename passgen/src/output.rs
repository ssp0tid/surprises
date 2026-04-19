use crate::entropy::{EntropyInfo, Strength};

pub fn display_password(password: &str) {
    println!("{}", password);
}

pub fn display_password_verbose(password: &str, info: &EntropyInfo) {
    println!("Password: {}", password);
    println!("Length: {}", info.length);
    println!("Entropy: {:.1} bits", info.entropy);
    println!("Strength: {}", info.strength.as_str());
    println!("Estimated crack time: {}", info.estimate_crack_time());
}

pub fn display_multiple_passwords(passwords: &[String]) {
    for password in passwords {
        println!("{}", password);
    }
}

pub fn display_multiple_passwords_verbose(passwords: &[(String, EntropyInfo)]) {
    for (password, info) in passwords {
        println!("{}", password);
        println!("  Length: {} | Entropy: {:.1} bits | Strength: {}", 
            info.length, info.entropy, info.strength.as_str());
    }
}

pub fn display_strength_str(strength: &Strength) -> String {
    strength.as_str().to_string()
}

pub fn display_history_entry(index: usize, password: &str, length: usize, entropy: f64, strength: &Strength, timestamp: &str) {
    println!("[{}] {} (len: {}, entropy: {:.1}, strength: {}) - {}",
        index + 1,
        password,
        length,
        entropy,
        strength.as_str(),
        timestamp
    );
}

pub fn display_copied_confirmation() {
    println!("Copied to clipboard!");
}

pub fn display_cleared_confirmation() {
    println!("Clipboard cleared!");
}

pub fn display_history_cleared() {
    println!("Password history cleared.");
}

pub fn display_export_success(format: &str, path: &str) {
    println!("History exported to {}: {}", format, path);
}

pub fn display_error(message: &str) {
    eprintln!("Error: {}", message);
}

pub fn display_info(message: &str) {
    println!("{}", message);
}
