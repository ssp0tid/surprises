# ClipStash

A Flask-based clipboard history manager that stores, organizes, and searches your clipboard entries with tagging and favorites support.

## Features

- **Clipboard Storage** - Save and persist clipboard content with timestamps
- **Tagging System** - Organize entries with custom tags (comma-separated)
- **Favorites** - Mark important entries as favorites for quick access
- **Search** - Full-text search across all clipboard entries
- **Filtering** - Filter by favorites or specific tags
- **REST API** - JSON-based programmatic access to your clipboard history
- **Web Interface** - Clean, functional UI for managing entries

## Installation

```bash
# Clone the repository or navigate to the project directory
cd clipstash

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

The application will start on `http://0.0.0.0:5000`. Open your browser to access the web interface.

## Usage Instructions

### Web Interface

1. **Add Entry** - Use the form at the top to add new clipboard content and optional tags
2. **View Entries** - All entries appear in a list sorted by timestamp (newest first)
3. **Search** - Use the search box to filter entries by content
4. **Filter** - Toggle "Favorites only" or select a specific tag to filter
5. **Favorite** - Click the star icon to mark/unmark entries as favorites
6. **Add Tags** - Use the tag input to add additional tags to existing entries
7. **Remove Tags** - Click the X next to a tag to remove it
8. **Delete** - Click the delete button to remove an entry

### API Usage

#### Get All Entries

```bash
curl http://localhost:5000/api/entries
```

#### Search Entries

```bash
curl "http://localhost:5000/api/entries?q=search_term"
```

#### Get Favorites Only

```bash
curl "http://localhost:5000/api/entries?favorites=true"
```

#### Example Response

```json
[
  {
    "id": 1,
    "content": "Sample clipboard text",
    "timestamp": "2024-01-15T10:30:00",
    "is_favorite": true,
    "tags": ["work", "important"]
  }
]
```

## API Endpoint Documentation

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/` | Main web interface | `q` (search), `favorites` (filter), `tag` (filter) |
| POST | `/add` | Add new entry | `content` (required), `tags` (optional) |
| GET | `/delete/<id>` | Delete entry by ID | - |
| GET | `/favorite/<id>` | Toggle favorite status | - |
| POST | `/add_tags/<id>` | Add tags to entry | `tags` (comma-separated) |
| GET | `/remove_tag/<id>/<tag>` | Remove tag from entry | - |
| GET | `/api/entries` | Get all entries (JSON) | `q` (search), `favorites` (boolean) |

## Database

The application uses SQLite and automatically creates `clipstash.db` in the project directory on first run.

## Requirements

- Python 3.8+
- Flask >= 2.3.0
- SQLAlchemy >= 2.0.0