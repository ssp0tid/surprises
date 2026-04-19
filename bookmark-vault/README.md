# Bookmark Vault

A self-hosted, local-first bookmark manager built with Python Flask and SQLite.

## Features

- **Tag-based organization** - Create and manage tags with custom colors
- **Full-text search** - Fast search across titles, descriptions, and URLs using SQLite FTS5
- **Import/Export** - Support for JSON, Netscape HTML, and CSV formats
- **Clean modern UI** - Responsive design with dark mode support

## Quick Start

```bash
# Install Flask (if not already installed)
pip install flask

# Run the application
python app.py
```

The app will be available at http://localhost:8080

## Import/Export Formats

### JSON
Export all bookmarks with tags to a JSON file for backup:
```
GET /api/export?format=json
```

Import from JSON:
```
POST /api/import?format=json
```

### Netscape HTML
Import browser bookmarks (Chrome/Firefox export):
```
POST /api/import?format=netscape
```

Export for browser import:
```
GET /api/export?format=netscape
```

### CSV
Import/export comma-separated values:
```
POST /api/import?format=csv
GET /api/export?format=csv
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/bookmarks | List all bookmarks |
| GET | /api/bookmarks/{id} | Get single bookmark |
| POST | /api/bookmarks | Create bookmark |
| PUT | /api/bookmarks/{id} | Update bookmark |
| DELETE | /api/bookmarks/{id} | Delete bookmark |
| GET | /api/bookmarks/search?q= | Search bookmarks |
| GET | /api/tags | List all tags |
| POST | /api/tags | Create tag |
| PUT | /api/tags/{id} | Update tag |
| DELETE | /api/tags/{id} | Delete tag |

## Data Storage

All data is stored in a local SQLite database (`bookmarks.db`) in the same directory as the app.

## Dark Mode

The UI automatically detects your system preference for dark/light mode. You can also toggle manually by clicking the theme button in the header.