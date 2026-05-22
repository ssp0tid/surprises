# Markov Poet

A CLI text generator that builds Markov chain models from input text files and generates poetry, prose, or song lyrics. Supports configurable chain order (1-5), multiple output modes, corpus management, and syllable-aware line breaking for poetry.

## Tech Stack

- Python 3 (stdlib only — no external dependencies)
- SQLite for corpus storage and model persistence
- `argparse` for CLI
- `json` for model serialization
- `re` for tokenization
- `random` for generation
- `textwrap` for formatting

## File Structure

```
markov-poet/
├── PLAN.md
├── README.md
├── markov_poet.py        # Entry point — CLI interface
├── chain.py              # Markov chain builder and generator
├── corpus.py             # Corpus management (add/list/remove texts)
├── formatter.py          # Output formatting (poetry, prose, haiku)
├── tokenizer.py          # Text tokenization and normalization
├── db.py                 # SQLite persistence layer
└── sample_corpus/
    └── shakespeare.txt   # Small sample text (~50 lines of sonnets)
```

## Features

### 1. Corpus Management (`corpus.py`)
- `add_text(db_path: str, name: str, filepath: str) -> int` — reads file, tokenizes, stores in SQLite
- `list_texts(db_path: str) -> list[dict]` — returns [{id, name, word_count, added_at}]
- `remove_text(db_path: str, name: str) -> bool` — removes text and associated chains
- SQLite schema:
  ```sql
  CREATE TABLE texts (id INTEGER PRIMARY KEY, name TEXT UNIQUE, content TEXT, word_count INTEGER, added_at TEXT);
  CREATE TABLE chains (id INTEGER PRIMARY KEY, text_id INTEGER, order_n INTEGER, state TEXT, next_word TEXT, count INTEGER);
  CREATE INDEX idx_chains_state ON chains(order_n, state);
  ```

### 2. Tokenizer (`tokenizer.py`)
- `tokenize(text: str) -> list[str]` — splits on whitespace, preserves punctuation attached to words, lowercases
- `sentence_split(text: str) -> list[list[str]]` — splits into sentences on `.!?` then tokenizes each
- Handles contractions, hyphenated words, em-dashes

### 3. Chain Builder (`chain.py`)
- `build_chain(tokens: list[str], order: int) -> dict` — builds {state_tuple: {next_word: count}}
- `generate(chain: dict, order: int, length: int, seed: str|None) -> list[str]` — weighted random walk
- `generate_sentence(chain: dict, order: int, max_words: int) -> str` — generates until sentence-ending punctuation
- Supports orders 1-5 (default 2)

### 4. Formatter (`formatter.py`)
- `format_prose(words: list[str], width: int) -> str` — wraps to width, capitalizes sentence starts
- `format_poetry(words: list[str], lines_per_stanza: int, words_per_line: tuple[int,int]) -> str` — random line lengths within range, stanza breaks
- `format_haiku(chain: dict, order: int) -> str` — attempts 5-7-5 syllable structure using simple syllable counter
- `count_syllables(word: str) -> int` — vowel-group heuristic

### 5. Persistence (`db.py`)
- `init_db(path: str) -> sqlite3.Connection` — creates tables if not exist
- `save_chain(conn, text_id: int, order: int, chain: dict)` — bulk inserts chain data
- `load_chain(conn, text_id: int|None, order: int) -> dict` — loads chain (all texts if text_id is None)
- DB path: `~/.markov-poet/markov.db` (default, configurable via --db)

### 6. CLI Interface (`markov_poet.py`)
Subcommands:
- `markov_poet.py add <name> <file>` — add text to corpus
- `markov_poet.py list` — list corpus texts
- `markov_poet.py remove <name>` — remove text from corpus
- `markov_poet.py generate [options]` — generate text
  - `--order N` (default 2)
  - `--length N` (word count, default 100)
  - `--mode prose|poetry|haiku` (default prose)
  - `--source <name>` (specific text, or all if omitted)
  - `--seed <word>` (starting word)
  - `--lines N` (for poetry mode, default 14)
  - `--stanza N` (lines per stanza, default 4)
- `markov_poet.py demo` — generates sample output from built-in shakespeare corpus

## Constraints

- Python 3 stdlib only — zero pip dependencies
- Single DB file for all state
- Graceful error messages (missing corpus, empty chain, etc.)
- Works offline — no API calls
- Sample corpus included so `demo` command works immediately
