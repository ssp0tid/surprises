# Markov Poet

A CLI text generator that builds Markov chain models from input text files and generates poetry, prose, or song lyrics.

## Features

- Configurable chain order (1-5)
- Three output modes: prose, poetry, haiku
- Corpus management (add/list/remove texts)
- Syllable-aware line breaking for poetry
- SQLite persistence
- Zero external dependencies — Python 3 stdlib only

## Quick Start

```bash
# Run the demo (uses built-in Shakespeare sonnets)
python markov_poet.py demo

# Add your own text
python markov_poet.py add mytexts path/to/file.txt

# Generate prose
python markov_poet.py generate --mode prose --length 100

# Generate poetry
python markov_poet.py generate --mode poetry --source mytexts --order 3

# Generate a haiku
python markov_poet.py generate --mode haiku
```

## Commands

### add

```bash
python markov_poet.py add <name> <file>
```

Add a text file to the corpus. The text is tokenized and Markov chains (orders 1-5) are built and stored automatically.

### list

```bash
python markov_poet.py list
```

Show all texts in the corpus with word counts and dates.

### remove

```bash
python markov_poet.py remove <name>
```

Remove a text and its associated chain data.

### generate

```bash
python markov_poet.py generate [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--order N` | 2 | Chain order (1-5). Higher = more coherent, less random |
| `--length N` | 100 | Number of words to generate |
| `--mode` | prose | Output mode: `prose`, `poetry`, or `haiku` |
| `--source` | all | Use a specific text (by name) |
| `--seed` | random | Starting word |
| `--stanza N` | 4 | Lines per stanza (poetry mode) |

### demo

```bash
python markov_poet.py demo
```

Generate sample output from the built-in Shakespeare corpus. No setup required.

## Configuration

By default, the database is stored at `~/.markov-poet/markov.db`. Override with:

```bash
python markov_poet.py --db /path/to/custom.db generate
```

## How It Works

1. Text is tokenized (lowercased, whitespace-split, punctuation preserved)
2. A Markov chain maps N-word states to weighted next-word probabilities
3. Generation performs a weighted random walk through the chain
4. Output is formatted according to the selected mode

## Requirements

- Python 3.10+
- No external dependencies
