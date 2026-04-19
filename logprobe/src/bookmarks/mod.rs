//! Bookmarks module for logprobe.
//! Provides functionality to bookmark and track specific lines in log files.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A bookmark representing a specific line in a file.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Bookmark {
    /// The line number in the file (1-indexed).
    pub line_number: u64,
    /// User-defined label for the bookmark.
    pub label: String,
    /// Timestamp when the bookmark was created.
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl Bookmark {
    /// Create a new bookmark.
    pub fn new(line_number: u64, label: String) -> Self {
        Self {
            line_number,
            label,
            timestamp: chrono::Utc::now(),
        }
    }
}

/// Store for managing bookmarks, keyed by a single character.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BookmarkStore {
    /// HashMap storing bookmarks keyed by a single character.
    bookmarks: HashMap<char, Bookmark>,
}

impl BookmarkStore {
    /// Create a new empty BookmarkStore.
    pub fn new() -> Self {
        Self {
            bookmarks: HashMap::new(),
        }
    }
}

impl Default for Bookmark {
    fn default() -> Self {
        Self::new(0, String::new())
    }
}

impl BookmarkStore {
    /// Set a bookmark at the given line with the provided key character and label.
    ///
    /// # Arguments
    /// * `key` - Single character to use as the bookmark key.
    /// * `line` - Line number to bookmark.
    /// * `label` - User-defined label for the bookmark.
    pub fn set_bookmark(&mut self, key: char, line: u64, label: String) {
        self.bookmarks.insert(key, Bookmark::new(line, label));
    }

    /// Get a bookmark by its key character.
    ///
    /// # Arguments
    /// * `key` - The key character to look up.
    ///
    /// # Returns
    /// Option containing a reference to the bookmark if found.
    pub fn get_bookmark(&self, key: char) -> Option<&Bookmark> {
        self.bookmarks.get(&key)
    }

    /// Remove a bookmark by its key character.
    ///
    /// # Arguments
    /// * `key` - The key character to remove.
    ///
    /// # Returns
    /// Option containing the removed bookmark if it existed.
    pub fn remove_bookmark(&mut self, key: char) -> Option<Bookmark> {
        self.bookmarks.remove(&key)
    }

    /// Clear all bookmarks.
    pub fn clear_all(&mut self) {
        self.bookmarks.clear();
    }

    /// List all bookmarks as a sorted iterator of (key, bookmark) pairs.
    ///
    /// # Returns
    /// An iterator over all bookmarks, sorted by key.
    pub fn list_bookmarks(&self) -> impl Iterator<Item = (&char, &Bookmark)> {
        let mut items: Vec<_> = self.bookmarks.iter().collect();
        items.sort_by(|a, b| a.0.cmp(b.0));
        items.into_iter()
    }

    /// Get the number of bookmarks.
    ///
    /// # Returns
    /// The number of bookmarks in the store.
    pub fn len(&self) -> usize {
        self.bookmarks.len()
    }

    /// Check if the store is empty.
    ///
    /// # Returns
    /// True if there are no bookmarks.
    pub fn is_empty(&self) -> bool {
        self.bookmarks.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_set_and_get_bookmark() {
        let mut store = BookmarkStore::new();
        store.set_bookmark('a', 42, "Important line".to_string());

        let bookmark = store.get_bookmark('a');
        assert!(bookmark.is_some());
        assert_eq!(bookmark.unwrap().line_number, 42);
    }

    #[test]
    fn test_remove_bookmark() {
        let mut store = BookmarkStore::new();
        store.set_bookmark('b', 100, "Test".to_string());

        let removed = store.remove_bookmark('b');
        assert!(removed.is_some());
        assert!(store.get_bookmark('b').is_none());
    }

    #[test]
    fn test_clear_all() {
        let mut store = BookmarkStore::new();
        store.set_bookmark('a', 1, "A".to_string());
        store.set_bookmark('b', 2, "B".to_string());

        store.clear_all();
        assert!(store.is_empty());
    }

    #[test]
    fn test_list_bookmarks() {
        let mut store = BookmarkStore::new();
        store.set_bookmark('z', 26, "Z".to_string());
        store.set_bookmark('a', 1, "A".to_string());
        store.set_bookmark('m', 13, "M".to_string());

        let keys: Vec<char> = store.list_bookmarks().map(|(k, _)| *k).collect();
        assert_eq!(keys, vec!['a', 'm', 'z']);
    }
}