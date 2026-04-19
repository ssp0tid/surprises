use fuzzy_matcher::skim::SkimMatcherV2;
use fuzzy_matcher::FuzzyMatcher;

use crate::error::ShellmemError;
use crate::models::{Command, SearchOptions, SearchResult, Shell};
use crate::storage::Database;

pub struct SearchEngine {
    matcher: SkimMatcherV2,
}

impl SearchEngine {
    pub fn new() -> Self {
        SearchEngine {
            matcher: SkimMatcherV2::default(),
        }
    }

    pub fn search(&self, query: &str, commands: &[Command]) -> Vec<SearchResult> {
        if query.is_empty() {
            return commands
                .iter()
                .map(|cmd| SearchResult {
                    command: cmd.clone(),
                    score: 0,
                })
                .collect();
        }

        let mut results: Vec<SearchResult> = commands
            .iter()
            .filter_map(|cmd| {
                self.matcher
                    .fuzzy_match(&cmd.command, query)
                    .map(|score| SearchResult {
                        command: cmd.clone(),
                        score,
                    })
            })
            .collect();

        results.sort_by(|a, b| b.score.cmp(&a.score));
        results
    }

    pub fn filter_commands(
        commands: &[Command],
        options: &SearchOptions,
        store: &Database,
    ) -> Result<Vec<Command>, ShellmemError> {
        let filtered: Vec<Command> = commands
            .iter()
            .filter(|cmd| {
                if cmd.is_deleted {
                    return false;
                }

                if let Some(ref shell) = options.shell {
                    if &cmd.shell != shell {
                        return false;
                    }
                }

                if let Some(ref from_date) = options.from_date {
                    if cmd.timestamp < *from_date {
                        return false;
                    }
                }

                if let Some(ref to_date) = options.to_date {
                    if cmd.timestamp > *to_date {
                        return false;
                    }
                }

                if options.favorites_only && !cmd.is_favorite {
                    return false;
                }

                if let Some(ref tag_names) = options.tags {
                    if tag_names.is_empty() {
                        return true;
                    }
                    let has_matching_tag = cmd.tags.iter().any(|tag| tag_names.contains(&tag.name));
                    if !has_matching_tag {
                        return false;
                    }
                }

                true
            })
            .cloned()
            .collect();

        let limit = options.limit.unwrap_or(usize::MAX);
        let offset = options.offset.unwrap_or(0);

        let limited: Vec<Command> = filtered
            .into_iter()
            .skip(offset)
            .take(limit)
            .collect();

        Ok(limited)
    }
}

impl Default for SearchEngine {
    fn default() -> Self {
        Self::new()
    }
}