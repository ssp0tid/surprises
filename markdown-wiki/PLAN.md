# Personal Markdown Wiki - Implementation Plan

## Project Overview

**Project Name**: Markdown Wiki  
**Project Type**: Full-stack web application  
**Core Functionality**: A personal knowledge base with bidirectional note-linking, tag organization, full-text search, and an elegant reading/writing interface  
**Target Users**: Personal knowledge management, second brain, study notes, project documentation

---

## 1. Architecture Overview

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Runtime | Node.js | ≥20.x |
| Build Tool | Vite | ^5.x |
| Framework | Preact | ^10.x |
| Routing | wouter | ^3.x |
| Styling | CSS Modules + CSS Variables | - |
| Markdown | unified + remark + rehype | ^15.x |
| Search | FlexSearch | ^0.7.x |
| State | Preact Signals | ^1.x |
| Icons | Lucide Preact | ^0.x |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser                              │
│  ┌─────────────────────────────────────────────┐   │
│  │           Preact Application                │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │   │
│  │  │ Router  │ │  Store  │ │  Search    │  │   │
│  │  │ (wouter)│ │(Signals) │ │ (FlexSearch)│  │   │
│  │  └─────────┘ └─────────┘ └─────────────┘  │   │
│  │         │         │           │            │   │
│  │  ┌──────┴─────────┴───────────┴────────┐  │   │
│  │  │        Markdown Renderer            │  │   │
│  │  │  (remark + rehype + custom plugins) │  │   │
│  │  └────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↑
                    File System
                    (via API)
                         ↓
┌─────────────────────────────────────────────────────┐
│                   Node.js Server                    │
│  ┌─────────────────────────────────────────────┐ │
│  │         API Routes (Express/Fastify)           │ │
│  │  GET/POST /notes    GET /search            │ │
│  │  GET /notes/:id     GET /tags               │ │
│  │  POST /notes/:id     GET /backlinks/:id       │ │
│  │  DELETE /notes/:id PUT /notes/:id          │ │
│  └─────────────────────────────────────────────┘ │
│                        │                          │
│  ┌────────────────────┴────────────────────┐│
│  │           Note Storage Layer                 ││
│  │  ├─ File-based (markdown files in notes/)   ││
│  │  ├─ In-memory index (links, tags, search)  ││
│  │  └─ Watcher for file changes              ││
│  └────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

---

## 2. File Structure

```
markdown-wiki/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── index.html
├── .gitignore
├── README.md
│
├── src/                        # Frontend source
│   ├── main.tsx               # Entry point
│   ├── app.tsx               # Root component
│   ├── index.css             # Global styles + CSS variables
│   │
│   ├── components/           # Reusable UI components
│   │   ├── Layout.tsx       # Main layout wrapper
│   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   ├── SearchBar.tsx     # Search input with results
│   │   ├── TagBadge.tsx     # Tag display chip
│   │   ├── Backlinks.tsx    # Backlinks panel
│   │   ├── Editor.tsx       # Markdown editor
│   │   ├── Markdown.tsx    # Markdown renderer
│   │   ├── Loading.tsx      # Loading spinner
│   │   └── Icons.tsx       # Icon components
│   │
│   ├── pages/               # Route pages
│   │   ├── Home.tsx        # Home/welcome page
│   │   ├── NoteView.tsx    # Single note view
│   │   ├── NoteEdit.tsx    # Note edit view
│   │   ├── Search.tsx      # Search results page
│   │   ├── TagView.tsx     # Notes by tag
│   │   └── GraphView.tsx   # Link graph visualization
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── useNotes.ts      # Notes CRUD operations
│   │   ├── useSearch.ts    # Search functionality
│   │   ├── useDebounce.ts  # Debounce utility
│   │   └── useKeyboard.ts  # Keyboard shortcuts
│   │
│   ├── lib/                 # Utility libraries
│   │   ├── api.ts           # API client
│   │   ├── parser.ts       # Link/tag parser
│   │   ├── links.ts       # Link processing utilities
│   │   └── search.ts     # Search indexing
│   │
│   ├── store/              # Global state (Signals)
│   │   ├── notes.ts       # Notes state
│   │   ├── ui.ts         # UI state (sidebar, theme)
│   │   └── search.ts     # Search state
│   │
│   └── types/              # TypeScript definitions
│       └── index.ts       # All type definitions
│
├── server/                    # Backend source
│   ├── index.ts            # Server entry point
│   ├── routes/
│   │   ├── notes.ts       # Notes API routes
│   │   ├── search.ts     # Search API routes
│   │   └── tags.ts       # Tags API routes
│   │
│   ├── services/
│   │   ├── storage.ts    # File storage service
│   │   ├── indexer.ts    # Note indexer (links, tags)
│   │   └── watcher.ts    # File system watcher
│   │
│   └── utils/
│       ├── logger.ts      # Logging utility
│       └── cors.ts      # CORS configuration
│
├── notes/                    # Notes storage (git-tracked)
│   ├── welcome.md         # Default welcome note
│   └── .gitkeep
│
├── public/                  # Static assets
│   ├── favicon.svg
│   └── fonts/
│
└─��� SPEC.md                 # Feature specification
```

---

## 3. Core Features & API Design

### 3.1 Note Data Model

```typescript
interface Note {
  id: string;                    // File name without extension (slugified)
  title: string;                // First H1 or filename
  content: string;              // Raw markdown content
  filePath: string;             // Absolute path to file
  createdAt: string;            // ISO timestamp
  updatedAt: string;            // ISO timestamp
  tags: string[];              // Extracted tags [[tag]] or #tag
  outgoingLinks: Link[];        // Links to other notes
  backlinks: Link[];            // Notes linking to this one
}

interface Link {
  noteId: string;              // Target note identifier
  displayText: string;       // Link display text [[target|text]]
  position: {                // Position in source
    start: number;
    end: number;
  };
}

interface SearchResult {
  note: Note;
  score: number;
  matches: {
    field: 'title' | 'content';
    indices: [number, number][];
  }[];
}
```

### 3.2 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes` | List all notes (summary only) |
| GET | `/api/notes/:id` | Get single note with metadata |
| POST | `/api/notes` | Create new note |
| PUT | `/api/notes/:id` | Update note content |
| DELETE | `/api/notes/:id` | Delete a note |
| GET | `/api/search?q=` | Full-text search |
| GET | `/api/tags` | List all tags with counts |
| GET | `/api/tags/:tag` | Get notes with specific tag |
| GET | `/api/backlinks/:id` | Get backlinks for note |
| GET | `/api/graph` | Get full link graph |

### 3.3 Link Parsing Logic

#### Wiki Link Pattern: `[[link]]` and `[[link|display text]]`

**Regex Pattern:**
```typescript
// Basic link: [[note-name]]
const WIKI_LINK = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

// Capture groups:
// $1 = link target (note name)
// $2 = display text (optional, defaults to $1)
```

**Parsing Algorithm:**

```typescript
function parseWikiLinks(content: string): ParsedLink[] {
  const links: ParsedLink[] = [];
  const regex = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
  
  let match;
  while ((match = regex.exec(content)) {
    const [, target, displayText] = match;
    links.push({
      target: target.trim(),
      displayText: displayText?.trim() || target.trim(),
      position: {
        start: match.index,
        end: match.index + match[0].length,
      },
    });
  }
  
  return links;
}
```

#### Tag Pattern: `[[tag]]` (double brackets)

**Regex Pattern:**
```typescript
// Tag: [[tag:tagname]] or #tagname
const TAG_PATTERN = /\[\[tag:([^\]]+)\]\]/g;
const HASHTAG_PATTERN = /#([\w-]+)/g;

// Priority: [[tag:]] syntax takes precedence
// Also support legacy #tag syntax for compatibility
```

### 3.4 Backlink Generation

```typescript
function buildBacklinksMap(notes: Note[]): Map<string, Link[]> {
  const backlinkMap = new Map<string, Link[]>();
  
  // Initialize empty arrays for all notes
  for (const note of notes) {
    backlinkMap.set(note.id, []);
  }
  
  // Populate backlinks
  for (const note of notes) {
    for (const link of note.outgoingLinks) {
      const existing = backlinkMap.get(link.noteId) || [];
      existing.push({
        noteId: note.id,
        displayText: note.title,
        position: link.position,
      });
      backlinkMap.set(link.noteId, existing);
    }
  }
  
  return backlinkMap;
}
```

### 3.5 Full-Text Search Implementation

**FlexSearch Configuration:**

```typescript
import FlexSearch from 'flexsearch';

interface SearchIndex {
  title: FlexSearch.Index;
  content: FlexSearch.Index;
}

// Create document index with separate fields
const searchIndex = new FlexSearch.Document({
  document: {
    id: 'id',
    index: ['title', 'content'],
    store: ['title', 'id'],
  },
  tokenize: 'forward',        // Forward matching for prefixes
  resolution: 9,              // Balance between speed/accuracy
  cache: true,                // Cache results
  context: {
    depth: 2,                 // Context autour du match
    bidirectional: true,
  },
});
```

**Search Query Flow:**

```
User types query
     ↓
Debounce (150ms)
     ↓
FlexSearch query (title + content fields)
     ↓
Merge & rank results by score
     ↓
Highlight matches in results
     ↓
Return SearchResult[]
```

---

## 4. Component Design

### 4.1 Layout Structure

```tsx
// Main application layout
function Layout({ children }) {
  const sidebarOpen = useSignal(true);
  const theme = useSignal('light'); // or 'dark'
  
  return (
    <div className={`layout theme-${theme.value}`}>
      <Header>
        <SearchBar />
        <ThemeToggle />
      </Header>
      
      <div className="layout-body">
        <Sidebar open={sidebarOpen.value} />
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
```

### 4.2 Markdown Rendering Pipeline

```
Raw Markdown
     ↓
remark-parse (AST)
     ↓
remark-gfm (GitHub Flavored Markdown)
     ↓
Custom Plugins:
  - remark-wiki-link (transform [[link]] to <a data-link>)
  - remark-tags (extract [[tag:]] to data-tags)
  - remark-footnotes
     ↓
rehype-stringify (to HTML)
     ↓
Post-process:
  - Add backlinks panel
  - Add hover tooltips
  - Highlight current section
```

### 4.3 Key Components

| Component | Purpose | Props |
|-----------|---------|-------|
| `<SearchBar />` | Global search input | `onSelect(noteId)` |
| `<NoteView />` | Display note content | `noteId: string` |
| `<NoteEdit />` | Edit note with live preview | `noteId?: string` |
| `<Backlinks />` | Show incoming links | `noteId: string` |
| `<TagBadge />` | Render clickable tag | `tag: string` |
| `<LinkGraph />` | Visual graph of links | `centerNoteId: string` |

---

## 5. Error Handling

### 5.1 Error Types

```typescript
enum ErrorCode {
  NOTE_NOT_FOUND = 'NOTE_NOT_FOUND',
  INVALID_LINK = 'INVALID_LINK',
  CIRCULAR_LINK = 'CIRCULAR_LINK',
  FILE_SAVE_ERROR = 'FILE_SAVE_ERROR',
  INVALID_CONTENT = 'INVALID_CONTENT',
  SEARCH_ERROR = 'SEARCH_ERROR',
}

interface AppError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}
```

### 5.2 Error Handling Strategy

| Error Type | User Message | Recovery Action |
|-----------|-------------|----------------|
| NOTE_NOT_FOUND | "Note not found" | Offer to create new |
| INVALID_LINK | "Linked note doesn't exist" | Show as plain text, offer to create |
| CIRCULAR_LINK | N/A (silent) | Allow, show in backlinks |
| FILE_SAVE_ERROR | "Failed to save. Check permissions" | Retry button |
| INVALID_CONTENT | "Invalid markdown syntax" | Show raw with error indicator |

### 5.3 Link Resolution with Error Handling

```typescript
function resolveLink(link: string, notes: Map<string, Note>): LinkResolution {
  const noteId = slugify(link);
  const note = notes.get(noteId);
  
  if (!note) {
    return {
      valid: false,
      status: 'broken',
      message: `Note "${link}" does not exist`,
      suggestion: noteId,
    };
  }
  
  // Check for circular links
  if (isCircular(link, currentNote)) {
    return {
      valid: true,
      status: 'circular',
      message: 'This creates a circular reference',
    };
  }
  
  return { valid: true, status: 'valid', noteId };
}
```

---

## 6. Edge Cases

### 6.1 Link Edge Cases

| Case | Input | Expected Output |
|------|-------|------------------|
| Broken link | `[[nonexistent]]` | Red link, dashed, "create" tooltip |
| Self-reference | `[[current-note]]` | Allowed, styled differently |
| Circular | A→B→C→A | Allowed, detected in backlinks |
| Deep nesting | `[[level1[[level2]]]]` | Parse innermost first |
| Link with spaces | `[[my note]]` | Slugify: `my-note` |
| Display text | `[[target|display]]` | Show "display", link to target |
| Anchor links | `[[note#section]]` | Link + scroll to heading |
| External links | `[text](http://...)` | Regular markdown link, no transformation |

### 6.2 Tag Edge Cases

| Case | Input | Expected |
|------|-------|----------|
| Tag with dash | `[[tag:my-tag]]` | Tag: `my-tag` |
| Tag with number | `[[tag:step-2]]` | Tag: `step-2` |
| Duplicate tags | `[[tag:a]] [[tag:a]]` | Unique: `['a']` |
| Nested brackets | `[[tag:[[nested]]]]` | Parse as literal tag |
| Empty tag | `[[tag:]]` | Ignore |
| Tag in code block | `` ``` [[tag:x]] ``` `` | Ignore (not a tag) |

### 6.3 Search Edge Cases

| Case | Input | Expected |
|------|-------|----------|
| Empty query | `""` | Return recent notes |
| No results | `"xyz123"` | "No notes found" message |
| Special chars | `"query[test]"` | Escape, search as literal |
| Very long query | 500+ chars | Truncate, warn user |
| Query with link | `"[[link]]"` | Search for "link" |

### 6.4 File System Edge Cases

| Case | Handling |
|------|---------|
| File deleted externally | Remove from index, show notification |
| File modified externally | Reload on focus/blur |
| Concurrent edits | Last write wins + notification |
| Invalid filename | Sanitize on create |
| Large file (>1MB) | Warn, suggest splitting |
| Binary file | Ignore, don't index |

---

## 7. UI/UX Design Guidelines

### 7.1 Visual Design

**Color Palette:**

```css
:root {
  /* Light theme */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #e9ecef;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --text-muted: #adb5bd;
  --accent: #6366f1;           /* Indigo */
  --accent-hover: #4f46e5;
  --link: #3b82f6;
  --link-broken: #ef4444;
  --border: #dee2e6;
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  
  /* Dark theme */
  --bg-primary: #0f0f0f;
  --bg-secondary: #1a1a1a;
  --bg-tertiary: #262626;
  --text-primary: #f5f5f5;
  --text-secondary: #a3a3a3;
  --text-muted: #525252;
  --accent: #818cf8;
  --link: #60a5fa;
  --border: #404040;
}
```

**Typography:**

```css
:root {
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-body: 1rem;          /* 16px */
  --font-sm: 0.875rem;         /* 14px */
  --font-xs: 0.75rem;          /* 12px */
  --line-height: 1.7;
  --line-height-tight: 1.4;
}
```

### 7.2 Layout Specifications

**Sidebar (280px):**
- Fixed position, collapsible to 0px
- Note tree with expand/collapse
- Tags section with counts
- Quick actions (new note, settings)

**Main Content:**
- Max-width: 720px for readability
- Generous padding: 2rem (32px)
- Smooth scrolling between sections

**Responsive Breakpoints:**
```css
@media (max-width: 768px) {
  .sidebar { position: fixed; z-index: 100; }
  .main-content { margin-left: 0; }
}
```

### 7.3 Animations & Transitions

```css
/* Standard transition timing */
* {
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 400ms ease;
}

/* Page transitions */
.page-enter {
  opacity: 0;
  transform: translateY(8px);
}
.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity var(--transition-normal),
              transform var(--transition-normal);
}

/* Link hover effect */
.wiki-link:hover {
  background: var(--accent);
  color: white;
  border-radius: 2px;
}
```

### 7.4 Component States

| Component | States |
|----------|--------|
| Note card | default, hover, selected |
| Button | default, hover, active, disabled, loading |
| Input | default, focus, error, disabled |
| Link | valid, broken, circular |
| Tag | default, hover, active |

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Project setup with Vite + Preact
- [ ] Basic server with file storage
- [ ] Note CRUD API
- [ ] File system watcher

### Phase 2: Link & Tag System (Week 1-2)
- [ ] Link parsing regex and utilities
- [ ] Backlink generation
- [ ] Tag extraction
- [ ] Link resolution with error states

### Phase 3: Search (Week 2)
- [ ] FlexSearch integration
- [ ] Search UI component
- [ ] Result highlighting

### Phase 4: UI Components (Week 2-3)
- [ ] Layout with sidebar
- [ ] Note viewer with markdown rendering
- [ ] Note editor with live preview
- [ ] Theme toggle (light/dark)

### Phase 5: Polish (Week 3)
- [ ] Responsive design
- [ ] Animations
- [ ] Keyboard shortcuts
- [ ] Performance optimization

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Focus search |
| `Ctrl/Cmd + N` | New note |
| `Ctrl/Cmd + S` | Save note |
| `Ctrl/Cmd + /` | Toggle sidebar |
| `Ctrl/Cmd + \` | Toggle theme |
| `Ctrl/Cmd + [` | Previous note |
| `Ctrl/Cmd + ]` | Next note |
| `Escape` | Close dialog/search |

---

## 10. Future Enhancements (Out of Scope)

- Graph visualization (link graph canvas)
- Daily notes / journal
- Canvas/mind-map mode
- Mobile app
- End-to-end encryption
- Multi-user support
- WebDAV sync
- PDF export
- Slide presentation mode

---

## 11. Dependencies Summary

```json
{
  "dependencies": {
    "preact": "^10.19.x",
    "wouter": "^3.x",
    "@preact/signals": "^1.x",
    "flexsearch": "^0.7.x",
    "unified": "^11.x",
    "remark-parse": "^11.x",
    "remark-gfm": "^4.x",
    "remark-rehype": "^11.x",
    "rehype-stringify": "^9.x",
    "rehype-slug": "^6.x",
    "rehype-autolink-headings": "^7.x",
    "rehype-highlight": "^7.x",
    "lucide-preact": "^0.x",
    "slugify": "^1.x",
    "chokidar": "^3.x",
    "fastify": "^4.x",
    "fastify-cors": "^4.x"
  },
  "devDependencies": {
    "vite": "^5.x",
    "@preact/preset-vite": "^2.x",
    "typescript": "^5.x",
    "@types/node": "^20.x"
  }
}
```

---

## Appendix: Link Parsing Regex Reference

```typescript
// Complete link patterns
const PATTERNS = {
  // Wiki link: [[note]] or [[note|display]]
  wikiLinkFull: /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
  
  // Wiki link (simple): [[note]]
  wikiLinkSimple: /\[\[([^\]]+)\]\]/g,
  
  // Tag: [[tag:name]]
  tagBracket: /\[\[tag:([^\]]+)\]\]/g,
  
  // Tag: #tagname
  tagHash: /#([\w-]+)/g,
  
  // Anchor: [[note#section]]
  anchorLink: /\[\[([^#]+)#([^\]|]+)(?:\|([^\]]+))?\]\]/g,
  
  // External: [text](url)
  externalLink: /\[([^\]]+)\]\(([^)]+)\)/g,
};

// Helper to extract all link targets
function extractLinkTargets(content: string): string[] {
  const targets: string[] = [];
  const regex = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
  let match;
  while ((match = regex.exec(content))) {
    const target = match[1].trim();
    // Handle anchors
    targets.push(target.split('#')[0]);
  }
  return [...new Set(targets)];
}
```

---

*Plan generated for Markdown Wiki project*
*Version: 1.0*
*Last updated: 2026-04-19*