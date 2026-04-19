# Markdown Link Checker - Plan

## Project Overview

- **Name**: Markdown Link Checker (mdlink)
- **Type**: CLI Tool (Node.js)
- **Core Functionality**: Scans markdown files and reports broken links (internal and external)
- **Target Users**: Developers, technical writers, content maintainers

## Features

| Feature | Description |
|---------|-------------|
| Recursive scanning | Walk directories and find all `.md` files |
| Internal link validation | Verify links to local files, headers, and anchors |
| External link validation | HTTP HEAD/GET requests to validate URLs |
| Color output | Terminal-friendly colored status indicators |
| JSON export | Export results to JSON for CI/CD integration |

## CLI Interface

```
mdlink [options] [path]

Options:
  -r, --recursive      Scan directories recursively (default: true)
  -e, --extensions    File extensions to scan (default: .md,.markdown)
  -t, --timeout       Request timeout in ms (default: 5000)
  -c, --concurrency   Max concurrent requests (default: 10)
  -j, --json          Output JSON format
  -q, --quiet         Suppress summary output
  -v, --verbose       Show all link checks (including valid)
  --no-color          Disable color output
  -h, --help          Show help
```

## Link Types Support

### Internal Links
- Relative file paths: `[text](./docs/page.md)`
- Local anchors: `[text](#section-id)`
- File+anchor: `[text](./file.md#section)`
- Wiki-style: `[[page-name]]` (Optional)

### External Links
- HTTP/HTTPS URLs: `[text](https://example.com)`
- Query parameters preserved
- Follow redirects (max 3)

## Output Formats

### Human (Terminal)
```
✓ index.md (2 links checked)
  ✓ https://example.com/docs
  ✓ ./api.md
✗ README.md (1 broken link)
  ✗ https://expired-link.com (404)
```

### JSON
```json
{
  "scannedAt": "2024-01-15T10:30:00Z",
  "files": [
    {
      "file": "README.md",
      "links": [
        {
          "url": "https://example.com",
          "type": "external",
          "status": "valid",
          "line": 10
        }
      ]
    }
  ],
  "summary": {
    "totalFiles": 5,
    "totalLinks": 23,
    "valid": 20,
    "broken": 3
  }
}
```

## Color Scheme

| Status | Color | Symbol |
|--------|-------|--------|
| Valid | Green | ✓ |
| Broken | Red | ✗ |
| Skipped/Unknown | Yellow | ○ |
| Info | Blue | ℹ |

## Architecture

### File Structure
```
src/
  index.js        # Entry point, CLI parser
  scanner.js      # File discovery
  parser.js       # Markdown link extraction
  validator.js   # Link validation logic
  reporter.js    # Output formatting
  utils/
    colors.js    # Terminal colors
    cache.js     # HTTP cache for revalidation
```

### Core Flow
1. **Scanner** finds all `.md` files in path
2. **Parser** extracts links with line numbers
3. **Validator** checks each link:
   - Internal → filesystem check
   - External → HTTP request
4. **Reporter** formats and outputs results
5. **Export** writes JSON if requested

## Acceptance Criteria

- [ ] Accepts directory or file path as argument
- [ ] Recursively finds all markdown files
- [ ] Extracts markdown links: `[text](url)` and `[text][ref]`
- [ ] Validates internal links (file existence, anchor existence)
- [ ] Validates external links (HTTP status codes 200-299 = valid)
- [ ] Reports line number for each broken link
- [ ] Colored terminal output
- [ ] `-j/--json` flag produces valid JSON
- [ ] Non-zero exit code when broken links found
- [ ] Handles rate limiting gracefully

## Dependencies

- **commander**: CLI argument parsing
- **marked**: Markdown parsing (for anchor extraction)
- **axios** or **fetch**: HTTP requests for external links