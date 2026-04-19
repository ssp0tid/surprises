use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use chrono::{DateTime, Utc};
use rand::RngCore;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::path::PathBuf;

use crate::config::GeneratorConfig;
use crate::entropy::Strength;
use crate::errors::{PassgenError, Result};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PasswordEntry {
    pub id: String,
    pub password: String,
    pub created_at: DateTime<Utc>,
    pub length: usize,
    pub entropy: f64,
    pub strength: Strength,
    pub config: GeneratorConfig,
}

impl PasswordEntry {
    pub fn new(password: String, config: GeneratorConfig, entropy: f64, strength: Strength) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            password,
            created_at: Utc::now(),
            length: config.length,
            entropy,
            strength,
            config,
        }
    }
}

#[derive(Clone, Serialize, Deserialize)]
pub struct PasswordHistory {
    entries: VecDeque<PasswordEntry>,
    max_entries: usize,
    encryption_key: Option<Vec<u8>>,
}

impl PasswordHistory {
    pub fn new(max_entries: usize) -> Self {
        Self {
            entries: VecDeque::with_capacity(max_entries),
            max_entries,
            encryption_key: None,
        }
    }

    pub fn with_encryption(max_entries: usize, key: Vec<u8>) -> Self {
        Self {
            entries: VecDeque::with_capacity(max_entries),
            max_entries,
            encryption_key: Some(key),
        }
    }

    pub fn add(&mut self, entry: PasswordEntry) {
        if self.entries.len() >= self.max_entries {
            self.entries.pop_front();
        }
        self.entries.push_back(entry);
    }

    pub fn entries(&self) -> &VecDeque<PasswordEntry> {
        &self.entries
    }

    pub fn entries_mut(&mut self) -> &mut VecDeque<PasswordEntry> {
        &mut self.entries
    }

    pub fn clear(&mut self) {
        self.entries.clear();
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    fn encrypt_password(&self, password: &str) -> Result<String> {
        let key = self.encryption_key.as_ref()
            .ok_or_else(|| PassgenError::EncryptionError("No encryption key set".into()))?;
        
        let cipher = Aes256Gcm::new_from_slice(key)
            .map_err(|e| PassgenError::EncryptionError(e.to_string()))?;
        
        let mut rng = rand::rngs::OsRng;
        let mut nonce_bytes = [0u8; 12];
        rng.fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);
        
        let ciphertext = cipher.encrypt(nonce, password.as_bytes())
            .map_err(|e| PassgenError::EncryptionError(e.to_string()))?;
        
        let mut result = nonce_bytes.to_vec();
        result.extend(ciphertext);
        Ok(BASE64.encode(&result))
    }

    pub fn save(&self, path: &PathBuf) -> Result<()> {
        let mut data = self.clone();
        
        if data.encryption_key.is_some() {
            let history = &mut data;
            for entry in history.entries_mut() {
                entry.password = self.encrypt_password(&entry.password)?;
            }
        }
        
        let json = serde_json::to_string_pretty(&data)?;
        std::fs::write(path, json)?;
        Ok(())
    }

    pub fn load(path: &PathBuf) -> Result<Self> {
        let json = std::fs::read_to_string(path)?;
        let mut history: PasswordHistory = serde_json::from_str(&json)?;
        history.encryption_key = None;
        Ok(history)
    }
}

pub fn history_path() -> Option<PathBuf> {
    dirs::data_dir().map(|p| p.join("passgen").join("history.json"))
}

pub fn export_json(history: &PasswordHistory) -> String {
    let entries: Vec<_> = history.entries()
        .iter()
        .map(|e| serde_json::json!({
            "password": "*******",
            "created_at": e.created_at.to_rfc3339(),
            "length": e.length,
            "entropy": e.entropy,
            "strength": e.strength.as_str(),
        }))
        .collect();
    
    serde_json::json!({ "passwords": entries }).to_string()
}

pub fn export_csv(history: &PasswordHistory) -> String {
    let mut output = String::from("password,created_at,length,entropy,strength\n");
    
    for entry in history.entries() {
        output.push_str(&format!(
            "******,{},{},{:.1},{}\n",
            entry.created_at.to_rfc3339(),
            entry.length,
            entry.entropy,
            entry.strength.as_str()
        ));
    }
    
    output
}

pub fn export_txt(history: &PasswordHistory) -> String {
    history.entries()
        .iter()
        .map(|e| e.password.clone())
        .collect::<Vec<_>>()
        .join("\n")
}