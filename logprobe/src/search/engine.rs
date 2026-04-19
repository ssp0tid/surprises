use std::ops::Range;

use regex::Regex;

use super::regex::{RegexCache, RegexOptions};
use crate::errors::Error;

#[derive(Clone, Debug)]
pub struct Match {
    pub line_number: u64,
    pub start: usize,
    pub end: usize,
    pub text: String,
}

pub struct SearchEngine {
    pattern: Option<Regex>,
    cache: RegexCache,
    matches: Vec<Match>,
    current_match: Option<usize>,
    history: Vec<String>,
    history_index: Option<usize>,
}

impl SearchEngine {
    pub fn new(options: RegexOptions) -> Self {
        Self {
            pattern: None,
            cache: RegexCache::new(options),
            matches: Vec::new(),
            current_match: None,
            history: Vec::new(),
            history_index: None,
        }
    }

    pub fn with_defaults() -> Self {
        Self::new(RegexOptions::default())
    }

    pub fn search(&mut self, pattern: &str, lines: &[String]) -> Result<(), Error> {
        let regex = self.cache.compile_regex(pattern)?;
        self.pattern = Some(regex);

        self.matches.clear();
        self.current_match = None;

        for (line_idx, line) in lines.iter().enumerate() {
            let line_num = line_idx as u64;
            for mat in self.pattern.as_ref().unwrap().find_iter(line) {
                self.matches.push(Match {
                    line_number: line_num,
                    start: mat.start(),
                    end: mat.end(),
                    text: mat.as_str().to_string(),
                });
            }
        }

        if !self.history.is_empty() && self.history.last() != Some(&pattern.to_string()) {
            self.history.push(pattern.to_string());
        } else if self.history.is_empty() {
            self.history.push(pattern.to_string());
        }
        self.history_index = Some(self.history.len());

        if !self.matches.is_empty() {
            self.current_match = Some(0);
        }

        Ok(())
    }

    pub fn next_match(&mut self) -> Option<&Match> {
        if self.matches.is_empty() {
            return None;
        }

        let current = self.current_match.unwrap_or(0);
        let next = (current + 1) % self.matches.len();
        self.current_match = Some(next);

        self.matches.get(next)
    }

    pub fn prev_match(&mut self) -> Option<&Match> {
        if self.matches.is_empty() {
            return None;
        }

        let current = self.current_match.unwrap_or(0);
        let prev = if current == 0 {
            self.matches.len() - 1
        } else {
            current - 1
        };
        self.current_match = Some(prev);

        self.matches.get(prev)
    }

    pub fn get_highlights(&self, line_range: Range<u64>) -> Vec<Match> {
        self.matches
            .iter()
            .filter(|m| line_range.start <= m.line_number && m.line_number < line_range.end)
            .cloned()
            .collect()
    }

    pub fn match_count(&self) -> usize {
        self.matches.len()
    }

    pub fn current_match_index(&self) -> Option<usize> {
        self.current_match
    }

    pub fn history(&self) -> &[String] {
        &self.history
    }

    pub fn history_next(&mut self) -> Option<&String> {
        if self.history.is_empty() {
            return None;
        }

        let idx = self.history_index?;
        if idx < self.history.len() {
            self.history_index = Some(idx + 1);
            self.history.get(idx)
        } else {
            None
        }
    }

    pub fn history_prev(&mut self) -> Option<&String> {
        if self.history.is_empty() {
            return None;
        }

        let idx = match self.history_index {
            Some(i) if i > 0 => i - 1,
            _ => 0,
        };
        self.history_index = Some(idx);
        self.history.get(idx)
    }

    pub fn set_options(&mut self, options: RegexOptions) {
        self.cache.set_options(options);
        self.matches.clear();
        self.current_match = None;
        self.pattern = None;
    }

    pub fn clear_matches(&mut self) {
        self.matches.clear();
        self.current_match = None;
        self.pattern = None;
    }

    pub fn current_pattern(&self) -> Option<&Regex> {
        self.pattern.as_ref()
    }

    pub fn options(&self) -> &RegexOptions {
        self.cache.options()
    }
}

impl Default for SearchEngine {
    fn default() -> Self {
        Self::with_defaults()
    }
}