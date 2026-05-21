# Regex Lab

Interactive regex debugger with real-time matching and syntax highlighting.

## Features

- **Real-time matching** - Matches update as you type (150ms debounce)
- **Syntax highlighting** - Regex pattern tokens are color-coded:
  - Metacharacters (`^ $ . |`) in coral
  - Quantifiers (`* + ? {}`) in light blue
  - Character classes (`[] [^]`) in sky blue
  - Groups (`()` `(?:` `(?=`) in purple
  - Escape sequences (`\d \w \s`) in green
  - Anchors (`\b \B`) in orange
- **Flag toggles** - `g` `i` `m` `s` `u` `y` flags
- **Match visualization** - Highlighted matches in test string
- **Capture groups** - Display numbered and named groups
- **Error handling** - Clear error messages for invalid regex

## Usage

1. Open `index.html` in a browser
2. Enter a regex pattern in the Pattern input
3. Enter test text in the Test String input
4. Toggle flags as needed
5. View matches in the Matches panel

## Keyboard Shortcuts

- `Ctrl+Enter` - Force re-match

## Files

```
regex-lab/
├── index.html   # Single-file application
├── PLAN.md     # Implementation plan
└── README.md   # This file
```