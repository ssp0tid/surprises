use std::collections::HashMap;
use std::sync::{Arc, RwLock};

use regex::{Regex, RegexBuilder};

use crate::errors::Error;

#[derive(Clone, Debug)]
pub struct RegexOptions {
    pub case_insensitive: bool,
    pub whole_word: bool,
}

impl Default for RegexOptions {
    fn default() -> Self {
        Self {
            case_insensitive: false,
            whole_word: false,
        }
    }
}

#[derive(Clone)]
pub struct RegexCache {
    cache: Arc<RwLock<HashMap<String, Regex>>>,
    options: RegexOptions,
}

impl RegexCache {
    pub fn new(options: RegexOptions) -> Self {
        Self {
            cache: Arc::new(RwLock::new(HashMap::new())),
            options,
        }
    }

    pub fn with_defaults() -> Self {
        Self::new(RegexOptions::default())
    }

    pub fn compile_regex(&self, pattern: &str) -> Result<Regex, Error> {
        let cache_key = self.cache_key(pattern);

        if let Ok(cache) = self.cache.read() {
            if let Some(cached) = cache.get(&cache_key) {
                return Ok(cached.clone());
            }
        }

        let mut regex_pattern = String::new();
        if self.options.whole_word {
            regex_pattern.push_str("\\b");
        }
        regex_pattern.push_str(pattern);
        if self.options.whole_word {
            regex_pattern.push_str("\\b");
        }

        let regex = RegexBuilder::new(&regex_pattern)
            .case_insensitive(self.options.case_insensitive)
            .build()
            .map_err(|e| {
                Error::InvalidRegex(format!("Invalid regex '{}': {}", pattern, e))
            })?;

        if let Ok(mut cache) = self.cache.write() {
            cache.insert(cache_key, regex.clone());
        }

        Ok(regex)
    }

    fn cache_key(&self, pattern: &str) -> String {
        format!(
            "{}|{}|{}",
            pattern,
            self.options.case_insensitive,
            self.options.whole_word
        )
    }

    pub fn set_options(&mut self, options: RegexOptions) {
        self.options = options;
    }

    pub fn options(&self) -> &RegexOptions {
        &self.options
    }

    pub fn clear_cache(&self) -> Result<(), Error> {
        let mut cache = self.cache.write().map_err(|_| {
            Error::InvalidRegex("Failed to acquire write lock on cache".to_string())
        })?;
        cache.clear();
        Ok(())
    }
}

impl Default for RegexCache {
    fn default() -> Self {
        Self::with_defaults()
    }
}