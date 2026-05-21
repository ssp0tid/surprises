# SQL Playground

A self-hosted, browser-based SQL runner that provides an interactive environment for writing and executing SQL queries using in-browser SQLite (sql.js). The application persists user data and query history server-side while executing queries client-side for performance and privacy.

## Features

- **Interactive SQL Editor**: CodeMirror-powered editor with SQL syntax highlighting
- **Client-Side Execution**: Uses sql.js (WebAssembly SQLite) for fast, private query execution
- **Schema Browser**: View tables and columns with click-to-insert functionality
- **Sample Datasets**: Pre-loaded sample databases (Employees, Products, Orders, Chinook)
- **Query History**: Automatically saves executed queries with execution time and row counts
- **Export Results**: Export query results to CSV or JSON
- **Dark Theme**: Modern VS Code-inspired dark theme

## Tech Stack

- **Backend**: Python Flask + SQLite (for persistence)
- **Client-side SQL**: sql.js (WebAssembly SQLite)
- **Query Editor**: CodeMirror 5
- **UI**: Vanilla JavaScript
- **Styling**: Custom CSS with dark theme

## Prerequisites

- Python 3.8+
- pip

## Installation

1. **Clone or download the project**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   
   Navigate to: `http://localhost:5000`

## Usage

### Writing and Executing Queries

1. Type your SQL query in the editor
2. Press **Ctrl+Enter** or click the **Run** button
3. View results in the Results panel

### Schema Browser

- The left sidebar shows all tables in your database
- Click the table name to expand and see columns
- Click a column name to insert it into the editor

### Loading Sample Data

1. Click on a sample dataset in the sidebar (Employees, Products, Orders, Chinook)
2. The sample data will be loaded into the database
3. Refresh the schema browser to see the new tables

### Saving Queries

1. Click the **Save** button in the editor toolbar
2. Enter a name for your query
3. Saved queries appear in the sidebar for quick access

### Exporting Results

After executing a SELECT query:
- Click **CSV** to download results as a CSV file
- Click **JSON** to download results as a JSON file

### Query History

- Click **History** in the navigation to view past queries
- Each entry shows the query, execution time, and row count
- Click **Load** to put a query back in the editor
- Click **Delete** to remove a history entry

## API Endpoints

### Query History

- `GET /api/query/history` - Get query history with pagination
- `POST /api/query/history` - Save a query to history
- `DELETE /api/query/history/<id>` - Delete a history item
- `DELETE /api/query/history` - Clear all history

### Saved Queries

- `GET /api/query/saved` - Get all saved queries
- `POST /api/query/save` - Save a named query
- `DELETE /api/query/saved/<id>` - Delete a saved query

### Database Management

- `GET /api/db/samples` - Get list of available sample datasets
- `POST /api/db/load-sample` - Load a sample dataset

### Export

- `POST /api/export` - Export results to CSV or JSON

## Project Structure

```
sql-playground/
├── app.py                      # Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── database/
│   ├── init_db.py             # Database initialization
│   └── schema.sql             # Database schema
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   └── js/
│       ├── app.js             # Main application logic
│       ├── codemirror-setup.js # CodeMirror configuration
│       ├── results-table.js    # Results table with sorting/filtering
│       ├── schema-browser.js   # Schema browser logic
│       ├── query-history.js    # Query history management
│       └── export.js            # CSV/JSON export utilities
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Main playground page
│   └── history.html           # Query history page
├── sample_data/
│   ├── employees.sql          # Sample employee dataset
│   ├── products.sql           # Sample product dataset
│   ├── orders.sql             # Sample orders dataset
│   └── chinook.sql            # Chinook music store dataset
└── instance/
    └── playground.db          # SQLite database (generated)
```

## Data Persistence

- **Query History**: Stored in server-side SQLite database
- **Database State**: Saved in browser's localStorage (persists across sessions)

## Keyboard Shortcuts

- **Ctrl+Enter** / **Cmd+Enter**: Execute query
- **Tab**: Insert spaces (when no text selected)
- **Escape**: Close modal dialogs

## Supported SQL Operations

- SELECT queries with JOINs, GROUP BY, ORDER BY, etc.
- INSERT, UPDATE, DELETE statements
- CREATE TABLE, ALTER TABLE, DROP TABLE
- All SQLite built-in functions

## License

MIT License

## Credits

- [sql.js](https://github.com/sql-js/sql.js) - SQLite compiled to JavaScript
- [CodeMirror](https://codemirror.net/) - Code editor component
