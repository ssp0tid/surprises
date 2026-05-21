# Markdown Wiki

A personal knowledge base with bidirectional note linking, built with Vite + Preact and Fastify.

## Features

- **[[wiki-link]] Linking** - Create links between notes using `[[note-name]]` syntax. Supports optional display text: `[[actual-note|Display Text]]`
- **Bidirectional Backlinks** - See which notes link to the current note automatically
- **#tag Organization** - Organize notes with hashtags. Tags are automatically extracted and displayed
- **Full-text Search** - Search across all notes by title and content
- **Beautiful Dark UI** - GitHub-inspired dark theme with smooth animations

## Quick Start

```bash
# Install dependencies
npm install

# Start the backend server (terminal 1)
npm start

# Start the frontend dev server (terminal 2)
npm run dev
```

Then open http://localhost:5173 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes` | List all notes with metadata |
| GET | `/api/notes/:slug` | Get a single note by slug |
| POST | `/api/notes` | Create a new note |
| PUT | `/api/notes/:slug` | Update an existing note |
| DELETE | `/api/notes/:slug` | Delete a note |
| GET | `/api/tags` | List all tags with counts |
| GET | `/api/search?q=query` | Search notes |
| GET | `/health` | Server health check |

## Keyboard Shortcuts

| Shortcut | Action |
|---------|--------|
| `Ctrl+S` | Save current note |
| `Ctrl+N` | Create new note |
| `Escape` | Cancel editing |

## Configuration

Edit these values in `server.js`:

```javascript
const NOTES_DIR = path.join(__dirname, 'notes');  // Notes storage folder
const PORT = 3456;                        // Server port
```

## Writing Notes

### Wiki Links

```markdown
# My Note Title

This is a link to [[another-note]].

This link shows custom text: [[target-note|Custom Display]]
```

### Tags

```markdown
# Note Title

Content here. #tag1 #tag2 #my-tag
```

### Markdown Support

- Headers, bold, italic, lists
- Code blocks with backticks
- Blockquotes
- Links and images

## Tech Stack

- **Frontend**: Vite + Preact + @preact/signals
- **Backend**: Fastify + @fastify/cors
- **Rendering**: marked (for Markdown)

## Project Structure

```
markdown-wiki/
├── src/
│   ├── App.jsx           # Main app component
│   ├── components/       # UI components
│   │   ├── NoteView.jsx
│   │   ├── NoteEditor.jsx
│   │   ├── Sidebar.jsx
│   │   ├── SearchBar.jsx
│   │   └── TagList.jsx
│   ├── store.js          # State management
│   ├── styles.css        # Dark theme styles
│   └── main.jsx         # Entry point
├── server.js             # Fastify backend
├── notes/               # Your notes (.md files)
└── package.json
```

## License

MIT