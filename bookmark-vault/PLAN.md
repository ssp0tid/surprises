# Bookmark Vault - Implementation Plan

## Project Overview

**Bookmark Vault** is a self-hosted, local-first bookmark manager with tag-based organization, full-text search, import/export capabilities, and a clean modern web UI. The application runs locally, stores data in a SQLite database, and provides a responsive web interface for managing bookmarks.

**Core Philosophy**: Local-first - data stays on the user's machine, no cloud dependencies, privacy-focused.

---

## Technology Stack

### Backend
- **Language**: Go 1.21+
- **Web Framework**: Chi (lightweight, idiomatic)
- **Database**: SQLite with modernc.org/sqlite (pure Go, no C dependencies)
- **ORM**: GORM or Bun-like approach (or raw SQL for simplicity)
- **HTML Parsing**: goquery (for metadata extraction)
- **Full-Text Search**: SQLite FTS5 (built-in)

### Frontend
- **Framework**: Vanilla JS or Preact (lightweight)
- **CSS**: TailwindCSS (via CDN for simplicity) or custom CSS
- **Build**: None required - served as static files

### Project Structure
```
bookmark-vault/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── database/
│   │   ├── db.go
│   │   └── migrations.go
│   ├── handlers/
│   │   ├── bookmarks.go
│   │   ├── tags.go
│   │   └── export.go
│   ├── models/
│   │   └── bookmark.go
│   ├── services/
│   │   ├── bookmark_service.go
│   │   ├── search_service.go
│   │   └── metadata_service.go
│   └── static/
│       ├── index.html
│       ├── css/
│       │   └── styles.css
│       └── js/
│           └── app.js
├── go.mod
└── go.sum
```

---

## Data Model

### Bookmark
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| url | TEXT (UNIQUE) | The bookmark URL |
| title | TEXT | Page title (user-editable) |
| description | TEXT | Optional notes/description |
| favicon | TEXT | Base64 or URL to favicon |
| created_at | DATETIME | When bookmark was added |
| updated_at | DATETIME | Last modification time |
| is_archived | BOOLEAN | Soft-delete flag |

### Tag
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| name | TEXT (UNIQUE) | Tag name (lowercase, slugified) |
| color | TEXT | Hex color code |
| created_at | DATETIME | Creation timestamp |

### BookmarkTag (Join Table)
| Field | Type | Description |
|-------|------|-------------|
| bookmark_id | INTEGER (FK) | Reference to bookmark |
| tag_id | INTEGER (FK) | Reference to tag |

### BookmarkFT (FTS5 Virtual Table)
- Indexed content: title, description, url
- Used for full-text search queries

---

## Core Features

### 1. Bookmark Management
- **Add Bookmark**: Enter URL, auto-fetch title/favicon
- **Edit Bookmark**: Modify title, description, tags
- **Delete Bookmark**: Soft delete (archive) with undo option
- **View Bookmark**: Display details with external link

### 2. Tag System
- **Create Tags**: Name + optional color
- **Assign Tags**: Multiple tags per bookmark
- **Filter by Tag**: Click tag to filter bookmarks
- **Tag Suggestions**: Autocomplete from existing tags
- **Tag Management**: Edit/delete tags (bulk operations)

### 3. Full-Text Search
- **Search Fields**: Title, description, URL, tags
- **FTS5 Implementation**: SQLite FTS5 for fast searching
- **Relevance Scoring**: Rank results by relevance
- **Instant Search**: Debounced live search as you type

### 4. Import/Export
- **Import Formats**:
  - Netscape HTML (browser bookmark export)
  - JSON (Bookmark Vault format)
  - CSV (URL,Title,Description,Tags)
- **Export Formats**:
  - JSON (full backup with tags)
  - Netscape HTML (browser-compatible)
  - CSV

### 5. User Interface
- **Dashboard**: Grid/list view of bookmarks
- **Sidebar**: Tag cloud/list with counts
- **Search Bar**: Prominent, always visible
- **Quick Add**: Modal or slide-out panel
- **Responsive**: Works on desktop and mobile
- **Dark Mode**: System preference detection

---

## API Design

### REST Endpoints

#### Bookmarks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/bookmarks | List bookmarks (paginated) |
| GET | /api/bookmarks/:id | Get single bookmark |
| POST | /api/bookmarks | Create bookmark |
| PUT | /api/bookmarks/:id | Update bookmark |
| DELETE | /api/bookmarks/:id | Delete (archive) bookmark |
| GET | /api/bookmarks/search?q= | Full-text search |

#### Tags
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/tags | List all tags |
| POST | /api/tags | Create tag |
| PUT | /api/tags/:id | Update tag |
| DELETE | /api/tags/:id | Delete tag |

#### Import/Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/import | Import bookmarks |
| GET | /api/export | Export bookmarks |

### Request/Response Examples

#### Create Bookmark
```json
POST /api/bookmarks
{
  "url": "https://example.com",
  "title": "Example Site",
  "description": "A great website",
  "tags": ["tech", "reference"]
}
```

#### Search Response
```json
GET /api/bookmarks/search?q=python
{
  "results": [
    {
      "id": 1,
      "url": "https://python.org",
      "title": "Python",
      "description": "Official Python site",
      "tags": ["tech", "programming"],
      "score": 1.5
    }
  ],
  "total": 1
}
```

---

## UI/UX Specification

### Layout
```
┌─────────────────────────────────────────────────────┐
│  [Logo]  Search...                    [+ Add]     │ ← Header
├────────────┬────────────────────────────────────────┤
│            │                                        │
│  Tags      │   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│  ─────     │   │ 📄  │ │ 📄  │ │ 📄  │ │ 📄  │     │
│  tech (5)  │   │title│ │title│ │title│ │title│     │
│  work (3)  │   │tags │ │tags │ │tags │ │tags │     │
│  read (8)  │   └─────┘ └─────┘ └─────┘ └─────┘     │
│            │                                        │
│            │   ┌─────┐ ┌─────┐ ┌─────┐              │
│            │   │ ... │ │ ... │ │ ... │              │
│            │                                        │
├────────────┴────────────────────────────────────────┤
│  Showing 24 of 156 bookmarks          ← Pagination │
└─────────────────────────────────────────────────────┘
```

### Color Palette
- **Primary**: #3B82F6 (Blue-500)
- **Secondary**: #64748B (Slate-500)
- **Accent**: #10B981 (Emerald-500)
- **Background**: #F8FAFC (Slate-50)
- **Surface**: #FFFFFF
- **Text Primary**: #1E293B (Slate-800)
- **Text Secondary**: #64748B (Slate-500)
- **Border**: #E2E8F0 (Slate-200)

### Component States
- **Hover**: Slight background color shift
- **Active/Selected**: Primary color highlight
- **Disabled**: 50% opacity
- **Loading**: Skeleton placeholders

---

## Implementation Phases

### Phase 1: Foundation (Day 1)
- [ ] Set up Go project with go.mod
- [ ] Configure Chi router
- [ ] Set up SQLite database with migrations
- [ ] Implement basic Bookmark CRUD
- [ ] Serve static files

### Phase 2: Core Features (Day 2)
- [ ] Implement Tag system
- [ ] Add full-text search (FTS5)
- [ ] Create bookmark-tag associations
- [ ] Build metadata fetching service

### Phase 3: Import/Export (Day 3)
- [ ] Implement JSON import/export
- [ ] Add Netscape HTML parser
- [ ] Add CSV support
- [ ] Validation and error handling

### Phase 4: Frontend (Day 4-5)
- [ ] Build HTML templates
- [ ] Implement CSS styling
- [ ] Add JavaScript interactivity
- [ ] Connect to API
- [ ] Implement search UI

### Phase 5: Polish (Day 6)
- [ ] Add dark mode support
- [ ] Responsive design testing
- [ ] Performance optimization
- [ ] Error handling and logging
- [ ] Documentation

---

## Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8080 | Server port |
| DB_PATH | ./data/bookmarks.db | SQLite database path |
| DATA_DIR | ./data | Data directory |
| BASE_URL | http://localhost:8080 | Public URL for exports |

### Config File (config.yaml)
```yaml
server:
  port: 8080
  host: "0.0.0.0"

database:
  path: "./data/bookmarks.db"

app:
  title: "Bookmark Vault"
  base_url: "http://localhost:8080"
```

---

## Acceptance Criteria

1. **Add Bookmark**: User can add URL, system auto-fetches title and favicon
2. **Tag Organization**: User can create tags and assign multiple to bookmarks
3. **Search Works**: Full-text search returns relevant results within 100ms
4. **Import Browser Bookmarks**: Successfully import Firefox/Chrome export
5. **Export Data**: Export all bookmarks to JSON for backup
6. **Responsive UI**: Works on mobile and desktop browsers
7. **Local Storage**: All data persists in local SQLite database
8. **No External Dependencies**: App runs offline after initial setup

---

## Future Enhancements (Post-MVP)

- [ ] Browser extension for quick bookmarking
- [ ] URL shortening functionality
- [ ] Bookmark archiving system
- [ ] Reading list / "read later" feature
- [ ] Password protection for sensitive bookmarks
- [ ] Automatic link checking (verify URLs still work)
- [ ] Markdown notes support
- [ ] Keyboard shortcuts
- [ ] Docker support
- [ ] PWA support for offline access

---

## Testing Strategy

- **Unit Tests**: Core services (search, import/export)
- **Integration Tests**: API endpoints with test database
- **Manual Testing**: Browser-based UI testing
- **Test Data**: Sample bookmarks for development

---

## Notes

- SQLite FTS5 provides excellent full-text search without external dependencies
- Use transactions for multi-table operations (bookmark + tags)
- Store favicons as URLs initially, cache as base64 for offline use
- Implement rate limiting for metadata fetching to avoid IP bans
- Consider using go:embed for bundling static files
