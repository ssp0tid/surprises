# Markdown Broken Link Checker

✅ **Complete working self-hosted micro SaaS utility**

Checks all links in markdown documents. Runs 100% client side (browser) or as CLI.

## 🖥️ CLI Usage

```bash
# Install globally
npm install -g mdlink

# Check links in current directory
mdlink

# Check specific file
mdlink README.md

# Check directory recursively
mdlink docs/

# JSON output
mdlink --json

# Verbose (show all links, not just broken)
mdlink --verbose

# Custom concurrency and timeout
mdlink --concurrency 5 --timeout 10000
```

### CLI Options
- `-r, --recursive` - Scan directories recursively (default: true)
- `-e, --extensions` - File extensions (default: .md,.markdown)
- `-t, --timeout` - Request timeout in ms (default: 5000)
- `-c, --concurrency` - Max concurrent requests (default: 10)
- `-j, --json` - Output JSON format
- `-q, --quiet` - Suppress summary output
- `-v, --verbose` - Show all link checks
- `--no-color` - Disable color output

## 🌐 Web Usage

Just open `index.html` in any modern browser. That's it, no build steps, no server required.

### Features
- Upload markdown files (drag & drop supported)
- Or paste markdown text directly
- Automatically extracts all URLs
- Checks each link for working/broken status
- Shows status codes, progress bar, live results
- Counts working / broken / warning links
- Download plain text report
- Clean modern responsive UI
- All processing happens **locally in your browser** - your data never leaves your device

## 📁 Files
- `src/index.js` - CLI entry point
- `index.html` - Web application
