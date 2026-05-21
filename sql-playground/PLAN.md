# SQL Playground - Implementation Plan

## Overview
A self-hosted, browser-based SQL runner that provides an interactive environment for writing and executing SQL queries using in-browser SQLite (sql.js). The application persists user data and query history server-side while executing queries client-side for performance and privacy.

## Tech Stack
- **Backend**: Python Flask + SQLite (for persistence)
- **Client-side SQL**: sql.js (WebAssembly SQLite)
- **Query Editor**: CodeMirror 6
- **UI**: Vanilla JavaScript
- **Styling**: Custom CSS with dark theme

---

## Project Structure

```
sql-playground/
├── app.py                      # Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── database/
│   ├── init_db.py              # Database initialization
│   └── schema.sql              # Database schema
├── static/
│   ├── css/
│   │   └── style.css            # Main stylesheet (dark theme)
│   ├── js/
│   │   ├── app.js               # Main application logic
│   │   ├── codemirror-setup.js  # CodeMirror 6 configuration
│   │   ├── results-table.js     # Results table with sorting/filtering
│   │   ├── schema-browser.js    # Schema browser logic
│   │   ├── query-history.js     # Query history management
│   │   └── export.js            # CSV/JSON export utilities
│   └── lib/
│       └── sql-wasm.wasm        # sql.js WebAssembly file
├── templates/
│   ├── base.html                # Base template
│   ├── index.html               # Main playground page
│   └── history.html              # Query history page
├── sample_data/
│   ├── employees.sql            # Sample employee dataset
│   ├── products.sql             # Sample product dataset
│   ├── orders.sql               # Sample orders dataset
│   └── chinook.sql              # Chinook sample database
└── instance/
    └── playground.db            # SQLite database (generated)
```

---

## Database Schema

### Tables

#### 1. `saved_queries`
Stores user-saved queries for later use.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| name | TEXT NOT NULL | Query name/label |
| query | TEXT NOT NULL | SQL query text |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last modified timestamp |

#### 2. `query_history`
Stores executed query history.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| query | TEXT NOT NULL | SQL query text |
| rows_affected | INTEGER | Number of rows affected |
| execution_time | REAL | Query execution time (ms) |
| error | TEXT | Error message if failed |
| executed_at | TIMESTAMP | Execution timestamp |

#### 3. `saved_dbs`
Stores custom database configurations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| name | TEXT NOT NULL | Database name |
| schema_json | TEXT | JSON schema of tables/columns |
| data_json | TEXT | Serialized table data |
| created_at | TIMESTAMP | Creation timestamp |

---

## API Endpoints

### Query Management

#### `POST /api/query/execute`
Execute a SQL query client-side (sql.js).

**Request Body:**
```json
{
  "query": "SELECT * FROM users WHERE active = 1",
  "db_id": "current"
}
```

**Response (Success):**
```json
{
  "success": true,
  "columns": ["id", "name", "email", "created_at"],
  "rows": [
    [1, "Alice", "alice@example.com", "2024-01-15"],
    [2, "Bob", "bob@example.com", "2024-01-16"]
  ],
  "rowCount": 2,
  "executionTime": 12.5
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Syntax error near 'FORM'",
  "executionTime": 2.1
}
```

#### `POST /api/query/save`
Save a query for later use.

**Request Body:**
```json
{
  "name": "Active Users Query",
  "query": "SELECT * FROM users WHERE active = 1"
}
```

**Response:**
```json
{
  "success": true,
  "id": 42
}
```

#### `GET /api/query/history`
Get query history with pagination.

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 50)

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "query": "SELECT * FROM users",
      "executed_at": "2024-01-20T14:30:00Z",
      "execution_time": 15.2,
      "row_count": 100
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 50
}
```

#### `DELETE /api/query/history/<id>`
Delete a history entry.

**Response:**
```json
{
  "success": true
}
```

### Database Management

#### `GET /api/schema`
Get current database schema (tables and columns).

**Response:**
```json
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "INTEGER", "primary_key": true},
        {"name": "name", "type": "TEXT", "nullable": false},
        {"name": "email", "type": "TEXT", "nullable": false}
      ]
    }
  ]
}
```

#### `POST /api/db/load-sample`
Load a sample dataset.

**Request Body:**
```json
{
  "dataset": "employees"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Loaded employees dataset",
  "tables": ["employees", "departments", "salaries"]
}
```

#### `GET /api/db/samples`
Get list of available sample datasets.

**Response:**
```json
{
  "samples": [
    {"id": "employees", "name": "Employees", "description": "Employee data with departments"},
    {"id": "products", "name": "Products", "description": "Product catalog"},
    {"id": "orders", "name": "Orders", "description": "E-commerce orders"},
    {"id": "chinook", "name": "Chinook", "description": "Music store database"}
  ]
}
```

### Export

#### `POST /api/export`
Export query results (processed server-side).

**Request Body:**
```json
{
  "columns": ["id", "name", "email"],
  "rows": [[1, "Alice", "alice@example.com"]],
  "format": "csv"
}
```

**Response:** File download

---

## HTML Templates

### `templates/base.html`
Base template with head, navigation, and structure.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SQL Playground{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">
            <span class="logo">▶</span> SQL Playground
        </div>
        <div class="nav-links">
            <a href="/" class="nav-link active">Playground</a>
            <a href="/history" class="nav-link">History</a>
        </div>
    </nav>
    
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="footer">
        <span>SQL Playground v1.0</span>
    </footer>
</body>
</html>
```

### `templates/index.html`
Main playground page with all interactive elements.

```html
{% extends "base.html" %}

{% block title %}SQL Playground - Interactive SQL Runner{% endblock %}

{% block extra_head %}
<!-- CodeMirror 6 -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/monokai.min.css">
{% endblock %}

{% block content %}
<div class="playground-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
        <!-- Schema Browser -->
        <section class="sidebar-section">
            <h3 class="section-title">
                <span class="icon">📋</span> Schema Browser
            </h3>
            <div id="schema-browser" class="schema-browser">
                <!-- Tables loaded dynamically -->
                <div class="loading">Loading schema...</div>
            </div>
        </section>
        
        <!-- Sample Datasets -->
        <section class="sidebar-section">
            <h3 class="section-title">
                <span class="icon">📁</span> Sample Datasets
            </h3>
            <div id="sample-datasets" class="sample-list">
                <!-- Samples loaded dynamically -->
            </div>
        </section>
    </aside>
    
    <!-- Main Area -->
    <div class="main-panel">
        <!-- Query Editor -->
        <section class="editor-section">
            <div class="editor-toolbar">
                <span class="toolbar-title">Query Editor</span>
                <div class="toolbar-actions">
                    <button id="btn-run" class="btn btn-primary">
                        <span class="btn-icon">▶</span> Run (Ctrl+Enter)
                    </button>
                    <button id="btn-clear" class="btn btn-secondary">
                        <span class="btn-icon">🗑</span> Clear
                    </button>
                    <button id="btn-format" class="btn btn-secondary">
                        <span class="btn-icon">✨</span> Format
                    </button>
                </div>
            </div>
            <div id="query-editor" class="code-editor"></div>
            <div class="editor-status">
                <span id="cursor-position">Ln 1, Col 1</span>
                <span id="sql-dialect">SQLite</span>
            </div>
        </section>
        
        <!-- Results Panel -->
        <section class="results-section">
            <div class="results-toolbar">
                <span class="toolbar-title">Results</span>
                <div class="toolbar-actions">
                    <span id="results-info" class="results-info"></span>
                    <button id="btn-export-csv" class="btn btn-small" disabled>CSV</button>
                    <button id="btn-export-json" class="btn btn-small" disabled>JSON</button>
                    <button id="btn-toggle-chart" class="btn btn-small">📊 Chart</button>
                </div>
            </div>
            <div id="results-container" class="results-container">
                <div class="empty-state">
                    <p>Run a query to see results</p>
                    <p class="hint">Press Ctrl+Enter to execute</p>
                </div>
            </div>
            <div id="results-pagination" class="pagination hidden">
                <button id="prev-page" class="btn btn-small">← Previous</button>
                <span id="page-info">Page 1 of 1</span>
                <button id="next-page" class="btn btn-small">Next →</button>
            </div>
        </section>
    </div>
</div>
{% endblock %}

{% block scripts %}
<!-- sql.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.min.js"></script>
<!-- CodeMirror 6 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/sql/sql.min.js"></script>
<!-- Application Scripts -->
<script src="{{ url_for('static', filename='js/codemirror-setup.js') }}"></script>
<script src="{{ url_for('static', filename='js/results-table.js') }}"></script>
<script src="{{ url_for('static', filename='js/schema-browser.js') }}"></script>
<script src="{{ url_for('static', filename='js/query-history.js') }}"></script>
<script src="{{ url_for('static', filename='js/export.js') }}"></script>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
{% endblock %}
```

### `templates/history.html`
Query history page.

```html
{% extends "base.html" %}

{% block title %}Query History - SQL Playground{% endblock %}

{% block content %}
<div class="history-page">
    <div class="page-header">
        <h1>Query History</h1>
        <div class="header-actions">
            <button id="btn-clear-all" class="btn btn-danger">Clear All History</button>
        </div>
    </div>
    
    <div id="history-list" class="history-list">
        <!-- History items loaded dynamically -->
    </div>
    
    <div id="history-pagination" class="pagination">
        <!-- Pagination controls -->
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/query-history.js') }}"></script>
{% endblock %}
```

---

## JavaScript Files

### `static/js/codemirror-setup.js`
CodeMirror 6 configuration with SQL syntax highlighting.

```javascript
// SQL Keywords for highlighting
const SQL_KEYWORDS = {
    keywords: 'SELECT,FROM,WHERE,AND,OR,NOT,IN,LIKE,BETWEEN,IS,NULL,AS,ON,JOIN,LEFT,RIGHT,INNER,OUTER,FULL,CROSS,UNION,ALL,DISTINCT,GROUP,BY,HAVING,ORDER,ASC,DESC,LIMIT,OFFSET,INSERT,INTO,VALUES,UPDATE,SET,DELETE,CREATE,TABLE,INDEX,DROP,ALTER,ADD,COLUMN,PRIMARY,KEY,FOREIGN,REFERENCES,CONSTRAINT,DEFAULT,AUTO_INCREMENT,INTEGER,TEXT,REAL,BLOB,BOOLEAN,DATE,DATETIME,TIMESTAMP,VIEWS,TRIGGER',
    builtin: 'COUNT,SUM,AVG,MIN,MAX,TOTAL,COALESCE,IFNULL,NULLIF,CAST,SUBSTR,LENGTH,UPPER,LOWER,TRIM,REPLACE,ABS,ROUND,RANDOM,DATE,TIME,DATETIME,STRFTIME,JULIANDAY',
    operators: '=,<,>,<=,>=,!=,<>,||'
};

const SQL_HINT = {
    tables: {} // Populated from schema
};

function initCodeMirror(container, options = {}) {
    const defaultOptions = {
        value: options.value || '',
        mode: 'text/x-sql',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: false,
        autofocus: true,
        indentWithTabs: false,
        tabSize: 2,
        indentUnit: 2,
        autoCloseBrackets: true,
        matchBrackets: true,
        syntaxHighlighting: true,
        keyMap: 'default'
    };
    
    // Custom keyboard shortcuts
    const editor = CodeMirror.fromTextArea(
        document.createElement('textarea'),
        { ...defaultOptions, ...options }
    );
    
    // Ctrl+Enter to execute
    editor.addKeyMap({
        'Ctrl-Enter': function(cm) {
            window.executeQuery();
        },
        'Cmd-Enter': function(cm) {
            window.executeQuery();
        }
    });
    
    return editor;
}

// Export for use in app.js
window.initCodeMirror = initCodeMirror;
```

### `static/js/app.js`
Main application logic connecting all components.

```javascript
class SQLPlayground {
    constructor() {
        this.db = null;
        this.currentResults = null;
        this.currentQuery = '';
        this.editor = null;
        this.currentPage = 1;
        this.rowsPerPage = 100;
    }
    
    async init() {
        // Initialize sql.js
        await this.initSQL();
        
        // Initialize CodeMirror
        this.initEditor();
        
        // Load schema browser
        await this.loadSchema();
        
        // Load sample datasets
        await this.loadSamples();
        
        // Bind event handlers
        this.bindEvents();
    }
    
    async initSQL() {
        const SQL = await initSqlJs({
            locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/${file}`
        });
        
        // Try to load saved database from localStorage
        const savedDb = localStorage.getItem('sql_playground_db');
        if (savedDb) {
            const uint8Array = new Uint8Array(JSON.parse(savedDb));
            this.db = new SQL.Database(uint8Array);
        } else {
            this.db = new SQL.Database();
        }
        
        // Create default tables
        this.db.run(`
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
    }
    
    initEditor() {
        const container = document.getElementById('query-editor');
        const textarea = document.createElement('textarea');
        container.appendChild(textarea);
        
        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: 'text/x-sql',
            theme: 'monokai',
            lineNumbers: true,
            autofocus: true,
            indentUnit: 2,
            smartIndent: true,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        // Set default query
        this.editor.setValue('-- Write your SQL query here\nSELECT * FROM users;');
    }
    
    async executeQuery() {
        const query = this.editor.getValue().trim();
        if (!query) return;
        
        this.currentQuery = query;
        const startTime = performance.now();
        
        try {
            const results = this.db.exec(query);
            const executionTime = performance.now() - startTime;
            
            if (results.length === 0) {
                // Query executed but no results (INSERT, UPDATE, etc.)
                const changes = this.db.getRowsModified();
                this.displaySuccess({
                    message: `Query executed successfully. ${changes} row(s) affected.`,
                    executionTime
                });
                this.saveToHistory(query, changes, executionTime, null);
            } else {
                this.currentResults = results[0];
                this.displayResults(this.currentResults);
                this.saveToHistory(query, this.currentResults.values.length, executionTime, null);
            }
            
            // Refresh schema if tables were modified
            await this.loadSchema();
            
            // Save database state
            this.saveDatabase();
            
        } catch (error) {
            const executionTime = performance.now() - startTime;
            this.displayError(error.message);
            this.saveToHistory(query, 0, executionTime, error.message);
        }
    }
    
    displayResults(result) {
        const container = document.getElementById('results-container');
        renderResultsTable(container, result.columns, result.values);
        
        document.getElementById('results-info').textContent = 
            `${result.values.length} row(s)`;
        
        document.getElementById('btn-export-csv').disabled = false;
        document.getElementById('btn-export-json').disabled = false;
    }
    
    displaySuccess(info) {
        const container = document.getElementById('results-container');
        container.innerHTML = `
            <div class="success-message">
                <span class="icon">✓</span>
                <p>${info.message}</p>
                <p class="execution-time">Execution time: ${info.executionTime.toFixed(2)}ms</p>
            </div>
        `;
    }
    
    displayError(error) {
        const container = document.getElementById('results-container');
        container.innerHTML = `
            <div class="error-message">
                <span class="icon">✗</span>
                <p class="error-title">SQL Error</p>
                <pre class="error-details">${this.escapeHtml(error)}</pre>
            </div>
        `;
    }
    
    async saveToHistory(query, rowCount, executionTime, error) {
        try {
            await fetch('/api/query/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    row_count: rowCount,
                    execution_time: executionTime,
                    error
                })
            });
        } catch (e) {
            console.error('Failed to save history:', e);
        }
    }
    
    saveDatabase() {
        const data = this.db.export();
        const buffer = Array.from(data);
        localStorage.setItem('sql_playground_db', JSON.stringify(buffer));
    }
    
    bindEvents() {
        document.getElementById('btn-run').addEventListener('click', () => this.executeQuery());
        document.getElementById('btn-clear').addEventListener('click', () => this.editor.setValue(''));
        document.getElementById('btn-format').addEventListener('click', () => this.formatQuery());
        document.getElementById('btn-export-csv').addEventListener('click', () => exportToCSV(this.currentResults));
        document.getElementById('btn-export-json').addEventListener('click', () => exportToJSON(this.currentResults));
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.playground = new SQLPlayground();
    window.playground.init();
});
```

### `static/js/results-table.js`
Results table with sorting and filtering capabilities.

```javascript
function renderResultsTable(container, columns, rows, options = {}) {
    const {
        pageSize = 100,
        sortable = true,
        filterable = true,
        searchable = true
    } = options;
    
    let currentPage = 1;
    let sortColumn = null;
    let sortDirection = 'asc';
    let filterValue = '';
    let filteredRows = [...rows];
    
    // Create table structure
    const wrapper = document.createElement('div');
    wrapper.className = 'results-table-wrapper';
    
    // Search/Filter bar
    if (searchable || filterable) {
        const filterBar = document.createElement('div');
        filterBar.className = 'filter-bar';
        filterBar.innerHTML = `
            <input type="text" 
                   id="table-search" 
                   class="search-input" 
                   placeholder="Search all columns..."
                   value="${filterValue}">
            <span class="row-count">${filteredRows.length} rows</span>
        `;
        wrapper.appendChild(filterBar);
        
        const searchInput = filterBar.querySelector('#table-search');
        searchInput.addEventListener('input', debounce((e) => {
            filterValue = e.target.value.toLowerCase();
            applyFilter();
        }, 300));
    }
    
    // Create table
    const table = document.createElement('table');
    table.className = 'results-table';
    
    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    columns.forEach((col, index) => {
        const th = document.createElement('th');
        th.textContent = col;
        th.dataset.column = index;
        
        if (sortable) {
            th.classList.add('sortable');
            th.addEventListener('click', () => sortByColumn(index));
            
            if (sortColumn === index) {
                th.classList.add(`sorted-${sortDirection}`);
                th.innerHTML += sortDirection === 'asc' ? ' ↑' : ' ↓';
            }
        }
        
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body
    const tbody = document.createElement('tbody');
    
    function renderPage() {
        tbody.innerHTML = '';
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        const pageRows = filteredRows.slice(start, end);
        
        pageRows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell === null ? 'NULL' : cell;
                if (cell === null) td.className = 'null-value';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }
    
    function applyFilter() {
        if (!filterValue) {
            filteredRows = [...rows];
        } else {
            filteredRows = rows.filter(row => 
                row.some(cell => 
                    String(cell).toLowerCase().includes(filterValue)
                )
            );
        }
        currentPage = 1;
        renderPage();
        updateRowCount();
    }
    
    function sortByColumn(columnIndex) {
        if (sortColumn === columnIndex) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = columnIndex;
            sortDirection = 'asc';
        }
        
        filteredRows.sort((a, b) => {
            const valA = a[columnIndex];
            const valB = b[columnIndex];
            
            if (valA === null) return 1;
            if (valB === null) return -1;
            
            if (typeof valA === 'number' && typeof valB === 'number') {
                return sortDirection === 'asc' ? valA - valB : valB - valA;
            }
            
            const strA = String(valA);
            const strB = String(valB);
            return sortDirection === 'asc' 
                ? strA.localeCompare(strB) 
                : strB.localeCompare(strA);
        });
        
        renderPage();
    }
    
    function updateRowCount() {
        const countEl = wrapper.querySelector('.row-count');
        if (countEl) {
            countEl.textContent = `${filteredRows.length} rows`;
        }
    }
    
    table.appendChild(tbody);
    wrapper.appendChild(table);
    
    // Clear and replace container content
    container.innerHTML = '';
    container.appendChild(wrapper);
    
    // Initial render
    renderPage();
    
    return {
        getFilteredRows: () => filteredRows,
        getColumns: () => columns,
        refresh: () => renderPage()
    };
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

window.renderResultsTable = renderResultsTable;
```

### `static/js/schema-browser.js`
Schema browser showing tables and columns.

```javascript
async function loadSchema() {
    try {
        const schema = await fetchSchema();
        renderSchemaBrowser(schema);
    } catch (error) {
        console.error('Failed to load schema:', error);
    }
}

async function fetchSchema() {
    // Get schema from sql.js database
    const tables = [];
    const result = window.playground.db.exec(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    );
    
    if (result.length === 0) return { tables };
    
    const tableNames = result[0].values.flat();
    
    for (const tableName of tableNames) {
        const columns = [];
        const colResult = window.playground.db.exec(`PRAGMA table_info(${tableName})`);
        
        if (colResult.length > 0) {
            colResult[0].values.forEach(col => {
                columns.push({
                    name: col[1],
                    type: col[2],
                    nullable: !col[3],
                    primaryKey: col[5] === 1
                });
            });
        }
        
        tables.push({ name: tableName, columns });
    }
    
    return { tables };
}

function renderSchemaBrowser(schema) {
    const container = document.getElementById('schema-browser');
    if (!container) return;
    
    if (schema.tables.length === 0) {
        container.innerHTML = '<div class="empty-state">No tables found</div>';
        return;
    }
    
    container.innerHTML = schema.tables.map(table => `
        <div class="schema-table" data-table="${table.name}">
            <div class="table-header">
                <span class="table-icon">📊</span>
                <span class="table-name">${table.name}</span>
                <span class="table-expand">▼</span>
            </div>
            <div class="table-columns">
                ${table.columns.map(col => `
                    <div class="column-item">
                        <span class="column-type">${col.type}</span>
                        <span class="column-name" 
                              title="Click to insert into query"
                              data-column="${col.name}"
                              data-table="${table.name}">
                            ${col.name}
                            ${col.primaryKey ? ' 🔑' : ''}
                        </span>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    // Bind click events for columns
    container.querySelectorAll('.column-name').forEach(el => {
        el.addEventListener('click', () => {
            const table = el.dataset.table;
            const column = el.dataset.column;
            insertColumnReference(table, column);
        });
    });
    
    // Toggle table expansion
    container.querySelectorAll('.table-header').forEach(el => {
        el.addEventListener('click', () => {
            el.classList.toggle('expanded');
            el.closest('.schema-table').classList.toggle('expanded');
        });
    });
}

function insertColumnReference(table, column) {
    const text = `${table}.${column}`;
    const editor = window.playground.editor;
    
    if (editor.hasSelection()) {
        editor.replaceSelection(text);
    } else {
        editor.replaceRange(text, editor.getCursor());
    }
    
    editor.focus();
}

window.loadSchema = loadSchema;
```

### `static/js/query-history.js`
Query history management with timestamps.

```javascript
async function loadHistory(page = 1, perPage = 50) {
    try {
        const response = await fetch(`/api/query/history?page=${page}&per_page=${perPage}`);
        const data = await response.json();
        renderHistory(data.history, page, data.total, perPage);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(history, currentPage, total, perPage) {
    const container = document.getElementById('history-list');
    if (!container) return;
    
    if (history.length === 0) {
        container.innerHTML = '<div class="empty-state">No query history</div>';
        return;
    }
    
    container.innerHTML = history.map(item => `
        <div class="history-item" data-id="${item.id}">
            <div class="history-query">
                <pre>${escapeHtml(item.query)}</pre>
            </div>
            <div class="history-meta">
                <span class="timestamp">${formatTimestamp(item.executed_at)}</span>
                ${item.row_count !== null 
                    ? `<span class="row-count">${item.row_count} rows</span>` 
                    : ''}
                <span class="execution-time">${item.execution_time.toFixed(2)}ms</span>
                ${item.error 
                    ? `<span class="error-badge">Error</span>` 
                    : ''}
            </div>
            <div class="history-actions">
                <button class="btn btn-small btn-load" title="Load into editor">
                    Load
                </button>
                <button class="btn btn-small btn-delete" title="Delete">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
    
    // Bind events
    container.querySelectorAll('.btn-load').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.closest('.history-item');
            const query = item.querySelector('pre').textContent;
            loadQueryIntoEditor(query);
        });
    });
    
    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.closest('.history-item').dataset.id;
            deleteHistoryItem(id);
        });
    });
    
    // Render pagination
    renderHistoryPagination(currentPage, total, perPage);
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function loadQueryIntoEditor(query) {
    if (window.playground && window.playground.editor) {
        window.playground.editor.setValue(query);
        window.playground.editor.focus();
    }
}

async function deleteHistoryItem(id) {
    if (!confirm('Delete this history item?')) return;
    
    try {
        await fetch(`/api/query/history/${id}`, { method: 'DELETE' });
        loadHistory();
    } catch (error) {
        console.error('Failed to delete history item:', error);
    }
}

async function clearAllHistory() {
    if (!confirm('Delete all history? This cannot be undone.')) return;
    
    try {
        await fetch('/api/query/history', { method: 'DELETE' });
        loadHistory();
    } catch (error) {
        console.error('Failed to clear history:', error);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.loadHistory = loadHistory;
window.clearAllHistory = clearAllHistory;
```

### `static/js/export.js`
CSV and JSON export utilities.

```javascript
function exportToCSV(result) {
    if (!result || !result.columns || !result.values) {
        console.error('No results to export');
        return;
    }
    
    const { columns, values } = result;
    
    // Build CSV content
    let csv = columns.map(escapeCSV).join(',') + '\n';
    
    values.forEach(row => {
        csv += row.map(cell => escapeCSV(cell)).join(',') + '\n';
    });
    
    downloadFile(csv, 'query_results.csv', 'text/csv');
}

function exportToJSON(result) {
    if (!result || !result.columns || !result.values) {
        console.error('No results to export');
        return;
    }
    
    const { columns, values } = result;
    
    const data = values.map(row => {
        const obj = {};
        columns.forEach((col, i) => {
            obj[col] = row[i];
        });
        return obj;
    });
    
    const json = JSON.stringify(data, null, 2);
    downloadFile(json, 'query_results.json', 'application/json');
}

function escapeCSV(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'number') return value;
    
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

window.exportToCSV = exportToCSV;
window.exportToJSON = exportToJSON;
```

---

## CSS Styles (`static/css/style.css`)

### Dark Theme Variables and Base Styles

```css
:root {
    /* Colors */
    --bg-primary: #1e1e1e;
    --bg-secondary: #252526;
    --bg-tertiary: #2d2d30;
    --bg-editor: #1e1e1e;
    --bg-hover: #3c3c3c;
    --bg-selected: #094771;
    
    --text-primary: #d4d4d4;
    --text-secondary: #808080;
    --text-muted: #6a6a6a;
    
    --accent-blue: #007acc;
    --accent-green: #4ec9b0;
    --accent-yellow: #dcdcaa;
    --accent-orange: #ce9178;
    --accent-red: #f14c4c;
    --accent-purple: #c586c0;
    
    --border-color: #3c3c3c;
    --border-focus: #007acc;
    
    /* Spacing */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    
    /* Borders */
    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;
    
    /* Typography */
    --font-mono: 'Consolas', 'Monaco', 'Courier New', monospace;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-size-sm: 12px;
    --font-size-md: 14px;
    --font-size-lg: 16px;
    
    /* Layout */
    --sidebar-width: 280px;
    --toolbar-height: 40px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--font-sans);
    font-size: var(--font-size-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.5;
    overflow: hidden;
}

/* Navigation */
.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    padding: 0 var(--spacing-lg);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-size-lg);
    font-weight: 600;
}

.nav-brand .logo {
    color: var(--accent-green);
}

.nav-links {
    display: flex;
    gap: var(--spacing-md);
}

.nav-link {
    color: var(--text-secondary);
    text-decoration: none;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-sm);
    transition: all 0.2s;
}

.nav-link:hover, .nav-link.active {
    color: var(--text-primary);
    background: var(--bg-hover);
}

/* Layout */
.playground-layout {
    display: flex;
    height: calc(100vh - 48px - 32px);
}

.sidebar {
    width: var(--sidebar-width);
    min-width: var(--sidebar-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
    padding: var(--spacing-md);
}

.main-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Sidebar Sections */
.sidebar-section {
    margin-bottom: var(--spacing-lg);
}

.section-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-size-sm);
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
}

/* Schema Browser */
.schema-browser {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.schema-table {
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    overflow: hidden;
}

.table-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    cursor: pointer;
    user-select: none;
}

.table-header:hover {
    background: var(--bg-hover);
}

.table-icon {
    font-size: var(--font-size-sm);
}

.table-name {
    flex: 1;
    font-weight: 500;
    font-family: var(--font-mono);
}

.table-expand {
    font-size: 10px;
    color: var(--text-secondary);
    transition: transform 0.2s;
}

.schema-table.expanded .table-expand {
    transform: rotate(180deg);
}

.table-columns {
    display: none;
    padding: 0 var(--spacing-md) var(--spacing-sm);
}

.schema-table.expanded .table-columns {
    display: block;
}

.column-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) 0;
    font-size: var(--font-size-sm);
}

.column-type {
    color: var(--accent-purple);
    font-size: 10px;
    background: rgba(197, 134, 192, 0.15);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    font-family: var(--font-mono);
}

.column-name {
    font-family: var(--font-mono);
    cursor: pointer;
    padding: 2px 4px;
    border-radius: var(--radius-sm);
}

.column-name:hover {
    background: var(--bg-selected);
    color: white;
}

/* Sample Datasets */
.sample-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
}

.sample-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background 0.2s;
}

.sample-item:hover {
    background: var(--bg-hover);
}

.sample-icon {
    font-size: var(--font-size-lg);
}

.sample-info {
    flex: 1;
}

.sample-name {
    font-weight: 500;
}

.sample-desc {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
}

/* Editor Section */
.editor-section {
    flex: 0 0 auto;
    display: flex;
    flex-direction: column;
    min-height: 200px;
    max-height: 40%;
}

.editor-toolbar, .results-toolbar {
    display: flex;
    align-items: center;
    height: var(--toolbar-height);
    padding: 0 var(--spacing-md);
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
}

.toolbar-title {
    flex: 1;
    font-weight: 500;
}

.toolbar-actions {
    display: flex;
    gap: var(--spacing-sm);
}

.code-editor {
    flex: 1;
    overflow: auto;
}

.code-editor .CodeMirror {
    height: 100%;
    font-family: var(--font-mono);
    font-size: var(--font-size-md);
}

.editor-status {
    display: flex;
    justify-content: space-between;
    padding: var(--spacing-xs) var(--spacing-md);
    background: var(--bg-tertiary);
    border-top: 1px solid var(--border-color);
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
}

/* Results Section */
.results-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.results-info {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
}

.results-container {
    flex: 1;
    overflow: auto;
    padding: var(--spacing-md);
}

/* Results Table */
.results-table-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.filter-bar {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) 0;
    margin-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--border-color);
}

.search-input {
    flex: 1;
    max-width: 300px;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
}

.search-input:focus {
    outline: none;
    border-color: var(--border-focus);
}

.row-count {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
}

.results-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
}

.results-table th,
.results-table td {
    padding: var(--spacing-sm) var(--spacing-md);
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    white-space: nowrap;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.results-table th {
    background: var(--bg-tertiary);
    font-weight: 600;
    position: sticky;
    top: 0;
    cursor: pointer;
}

.results-table th:hover {
    background: var(--bg-hover);
}

.results-table th.sorted-asc::after { content: ' ↑'; }
.results-table th.sorted-desc::after { content: ' ↓'; }

.results-table tr:hover td {
    background: var(--bg-hover);
}

.null-value {
    color: var(--text-muted);
    font-style: italic;
}

/* Empty State */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
}

.empty-state .hint {
    font-size: var(--font-size-sm);
    margin-top: var(--spacing-sm);
}

/* Messages */
.success-message,
.error-message {
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin: var(--spacing-md);
}

.success-message {
    background: rgba(78, 201, 176, 0.1);
    border: 1px solid var(--accent-green);
    color: var(--accent-green);
}

.error-message {
    background: rgba(241, 76, 76, 0.1);
    border: 1px solid var(--accent-red);
}

.error-title {
    color: var(--accent-red);
    font-weight: 600;
    margin-bottom: var(--spacing-sm);
}

.error-details {
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
    white-space: pre-wrap;
    color: var(--text-primary);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: var(--accent-blue);
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #005a9e;
}

.btn-secondary {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
    background: var(--bg-tertiary);
}

.btn-danger {
    background: var(--accent-red);
    color: white;
}

.btn-danger:hover:not(:disabled) {
    background: #d43c3c;
}

.btn-small {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: 11px;
}

.btn-icon {
    font-size: 12px;
}

/* Pagination */
.pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-color);
}

.pagination.hidden {
    display: none;
}

/* History Page */
.history-page {
    max-width: 900px;
    margin: 0 auto;
    padding: var(--spacing-lg);
}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--spacing-lg);
}

.page-header h1 {
    font-size: var(--font-size-lg);
}

.history-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.history-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
}

.history-query {
    background: var(--bg-primary);
    padding: var(--spacing-md);
    border-radius: var(--radius-sm);
    margin-bottom: var(--spacing-sm);
    overflow-x: auto;
}

.history-query pre {
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
    white-space: pre-wrap;
    word-break: break-word;
}

.history-meta {
    display: flex;
    gap: var(--spacing-md);
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
}

.history-actions {
    display: flex;
    gap: var(--spacing-sm);
}

.error-badge {
    background: var(--accent-red);
    color: white;
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    font-size: 10px;
}

/* Footer */
.footer {
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    font-size: var(--font-size-sm);
    color: var(--text-muted);
}

/* CodeMirror Overrides */
.CodeMirror {
    background: var(--bg-editor) !important;
}

.cm-s-monokai.CodeMirror {
    background: var(--bg-editor) !important;
}

.cm-s-monokai .CodeMirror-gutters {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

.cm-s-monokai .CodeMirror-linenumber {
    color: var(--text-secondary) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--bg-hover);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}
```

---

## Flask Application (`app.py`)

```python
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# ==================== Routes ====================

@app.route('/')
def index():
    """Main playground page."""
    return render_template('index.html')

@app.route('/history')
def history():
    """Query history page."""
    return render_template('history.html')

# ==================== API Routes ====================

@app.route('/api/query/history', methods=['GET'])
def get_query_history():
    """Get query history with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM query_history')
    total = cursor.fetchone()[0]
    
    # Get paginated history
    cursor.execute('''
        SELECT id, query, rows_affected, execution_time, error, executed_at
        FROM query_history
        ORDER BY executed_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'id': row['id'],
            'query': row['query'],
            'row_count': row['rows_affected'],
            'execution_time': row['execution_time'],
            'error': row['error'],
            'executed_at': row['executed_at']
        })
    
    conn.close()
    
    return jsonify({
        'history': history,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/query/history', methods=['POST'])
def save_query_history():
    """Save a query to history."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO query_history (query, rows_affected, execution_time, error, executed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('query'),
        data.get('row_count', 0),
        data.get('execution_time', 0),
        data.get('error'),
        datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    history_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': history_id})

@app.route('/api/query/history/<int:id>', methods=['DELETE'])
def delete_history_item(id):
    """Delete a history item."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM query_history WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/query/history', methods=['DELETE'])
def clear_history():
    """Clear all history."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM query_history')
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/query/save', methods=['POST'])
def save_query():
    """Save a named query."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO saved_queries (name, query, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (
        data.get('name'),
        data.get('query'),
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    query_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': query_id})

@app.route('/api/db/samples', methods=['GET'])
def get_sample_datasets():
    """Get list of available sample datasets."""
    samples = [
        {
            'id': 'employees',
            'name': 'Employees',
            'description': 'Employee data with departments and salaries',
            'tables': ['employees', 'departments', 'salaries']
        },
        {
            'id': 'products',
            'name': 'Products',
            'description': 'E-commerce product catalog',
            'tables': ['products', 'categories']
        },
        {
            'id': 'orders',
            'name': 'Orders',
            'description': 'Customer orders and order items',
            'tables': ['orders', 'order_items', 'customers']
        },
        {
            'id': 'chinook',
            'name': 'Chinook',
            'description': 'Music store database with artists, albums, tracks',
            'tables': ['artists', 'albums', 'tracks', 'invoices', 'customers']
        }
    ]
    
    return jsonify({'samples': samples})

@app.route('/api/db/load-sample', methods=['POST'])
def load_sample():
    """Load a sample dataset - returns SQL to execute client-side."""
    data = request.get_json()
    sample_id = data.get('dataset')
    
    # SQL statements for sample datasets
    samples = {
        'employees': {
            'name': 'Employees',
            'sql': '''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    department_id INTEGER,
                    salary INTEGER,
                    hire_date TEXT
                );
                INSERT INTO employees VALUES (1, 'John', 'Doe', 'john@example.com', 1, 50000, '2020-01-15');
                INSERT INTO employees VALUES (2, 'Jane', 'Smith', 'jane@example.com', 2, 55000, '2019-03-22');
                INSERT INTO employees VALUES (3, 'Bob', 'Johnson', 'bob@example.com', 1, 48000, '2021-06-10');
                
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    budget INTEGER
                );
                INSERT INTO departments VALUES (1, 'Engineering', 500000);
                INSERT INTO departments VALUES (2, 'Marketing', 200000);
                INSERT INTO departments VALUES (3, 'Sales', 300000);
            '''
        },
        'products': {
            'name': 'Products',
            'sql': '''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    price REAL,
                    category_id INTEGER,
                    stock INTEGER
                );
                INSERT INTO products VALUES (1, 'Laptop', 999.99, 1, 50);
                INSERT INTO products VALUES (2, 'Mouse', 29.99, 2, 200);
                INSERT INTO products VALUES (3, 'Keyboard', 79.99, 2, 150);
                
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                );
                INSERT INTO categories VALUES (1, 'Electronics');
                INSERT INTO categories VALUES (2, 'Accessories');
            '''
        }
    }
    
    sample = samples.get(sample_id)
    if not sample:
        return jsonify({'success': False, 'error': 'Sample not found'}), 404
    
    return jsonify({
        'success': True,
        'name': sample['name'],
        'sql': sample['sql']
    })

@app.route('/api/export', methods=['POST'])
def export_data():
    """Export data to CSV or JSON format."""
    data = request.get_json()
    format_type = data.get('format', 'csv')
    columns = data.get('columns', [])
    rows = data.get('rows', [])
    
    if format_type == 'csv':
        content = ','.join(columns) + '\n'
        for row in rows:
            content += ','.join(str(cell) for cell in row) + '\n'
        
        return send_file(
            content,
            mimetype='text/csv',
            as_attachment=True,
            download_name='export.csv'
        )
    
    elif format_type == 'json':
        json_data = []
        for row in rows:
            obj = {}
            for i, col in enumerate(columns):
                obj[col] = row[i]
            json_data.append(obj)
        
        content = json.dumps(json_data, indent=2)
        
        return send_file(
            content,
            mimetype='application/json',
            as_attachment=True,
            download_name='export.json'
        )
    
    return jsonify({'success': False, 'error': 'Invalid format'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## Database Initialization (`database/init_db.py`)

```python
import sqlite3
import os
from config import Config

def init_db():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            rows_affected INTEGER DEFAULT 0,
            execution_time REAL DEFAULT 0,
            error TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_dbs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            schema_json TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_history_executed_at 
        ON query_history(executed_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_saved_queries_name 
        ON saved_queries(name)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {Config.DATABASE}")

if __name__ == '__main__':
    init_db()
```

---

## Configuration (`config.py`)

```python
import os

class Config:
    """Application configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, 'instance', 'playground.db')
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    # Query settings
    MAX_QUERY_HISTORY = 1000
    QUERY_TIMEOUT_SECONDS = 30
```

---

## Sample Data Files

### `sample_data/employees.sql`

```sql
-- Employees and Departments Sample Database

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    department_id INTEGER,
    salary INTEGER,
    hire_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    budget INTEGER,
    manager_id INTEGER
);

INSERT INTO departments VALUES (1, 'Engineering', 500000, NULL);
INSERT INTO departments VALUES (2, 'Marketing', 200000, NULL);
INSERT INTO departments VALUES (3, 'Sales', 300000, NULL);
INSERT INTO departments VALUES (4, 'Human Resources', 150000, NULL);

INSERT INTO employees VALUES (1, 'John', 'Doe', 'john.doe@example.com', 1, 75000, '2019-01-15');
INSERT INTO employees VALUES (2, 'Jane', 'Smith', 'jane.smith@example.com', 1, 82000, '2018-03-22');
INSERT INTO employees VALUES (3, 'Bob', 'Johnson', 'bob.johnson@example.com', 2, 65000, '2020-06-10');
INSERT INTO employees VALUES (4, 'Alice', 'Williams', 'alice.williams@example.com', 3, 70000, '2017-11-05');
INSERT INTO employees VALUES (5, 'Charlie', 'Brown', 'charlie.brown@example.com', 1, 78000, '2019-08-20');
INSERT INTO employees VALUES (6, 'Diana', 'Miller', 'diana.miller@example.com', 4, 62000, '2021-02-14');
INSERT INTO employees VALUES (7, 'Edward', 'Davis', 'edward.davis@example.com', 3, 68000, '2018-09-30');
INSERT INTO employees VALUES (8, 'Fiona', 'Garcia', 'fiona.garcia@example.com', 2, 71000, '2020-04-18');
INSERT INTO employees VALUES (9, 'George', 'Martinez', 'george.martinez@example.com', 1, 85000, '2016-12-01');
INSERT INTO employees VALUES (10, 'Hannah', 'Anderson', 'hannah.anderson@example.com', 4, 60000, '2022-01-10');
```

### `sample_data/products.sql`

```sql
-- E-commerce Products Sample Database

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category_id INTEGER,
    stock INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

INSERT INTO categories VALUES (1, 'Electronics', 'Electronic devices and gadgets');
INSERT INTO categories VALUES (2, 'Computers', 'Desktops, laptops, and tablets');
INSERT INTO categories VALUES (3, 'Accessories', 'Peripherals and add-ons');
INSERT INTO categories VALUES (4, 'Software', 'Applications and programs');

INSERT INTO products VALUES (1, 'MacBook Pro 14"', 'M3 Pro chip, 18GB RAM, 512GB SSD', 1999.00, 2, 25);
INSERT INTO products VALUES (2, 'iPhone 15 Pro', '256GB, Titanium design', 999.00, 1, 100);
INSERT INTO products VALUES (3, 'Wireless Mouse', 'Ergonomic wireless mouse', 49.99, 3, 500);
INSERT INTO products VALUES (4, 'Mechanical Keyboard', 'RGB backlit, Cherry MX switches', 129.99, 3, 150);
INSERT INTO products VALUES (5, '27" 4K Monitor', 'IPS panel, USB-C connectivity', 449.00, 1, 40);
INSERT INTO products VALUES (6, 'External SSD 1TB', 'USB 3.2, portable storage', 89.99, 3, 200);
INSERT INTO products VALUES (7, 'Webcam HD', '1080p, built-in microphone', 79.99, 3, 180);
INSERT INTO products VALUES (8, 'Office Suite', 'Word, Excel, PowerPoint, annual license', 149.99, 4, 1000);
INSERT INTO products VALUES (9, 'USB-C Hub', '7-in-1 adapter with HDMI', 59.99, 3, 300);
INSERT INTO products VALUES (10, 'Noise Canceling Headphones', 'Wireless, 30hr battery', 249.00, 1, 75);
```

---

## Requirements (`requirements.txt`)

```
Flask>=3.0.0
Flask-CORS>=4.0.0
```

---

## Implementation Checklist

### Phase 1: Project Setup
- [ ] Create project directory structure
- [ ] Create requirements.txt
- [ ] Create config.py
- [ ] Create database initialization script
- [ ] Create database schema

### Phase 2: Backend (Flask)
- [ ] Implement Flask application (app.py)
- [ ] Implement API endpoints for query history
- [ ] Implement API endpoints for saved queries
- [ ] Implement API endpoints for sample datasets
- [ ] Implement export functionality

### Phase 3: Frontend Templates
- [ ] Create base.html template
- [ ] Create index.html (main playground)
- [ ] Create history.html (query history page)

### Phase 4: JavaScript Modules
- [ ] Implement codemirror-setup.js
- [ ] Implement app.js (main application)
- [ ] Implement results-table.js (sorting/filtering)
- [ ] Implement schema-browser.js
- [ ] Implement query-history.js
- [ ] Implement export.js

### Phase 5: Styling
- [ ] Create dark theme CSS (style.css)
- [ ] Ensure responsive design
- [ ] Add CodeMirror theme overrides

### Phase 6: Sample Data
- [ ] Create employees.sql sample data
- [ ] Create products.sql sample data
- [ ] Create orders.sql sample data
- [ ] Create chinook.sql sample data

### Phase 7: Testing
- [ ] Test all API endpoints
- [ ] Test query execution
- [ ] Test export functionality
- [ ] Test history management
- [ ] Test sample data loading

---

## Future Enhancements (Not in Initial Scope)

1. **Multi-tab support** - Multiple query tabs
2. **Query auto-complete** - Intelligent SQL suggestions
3. **Visual query builder** - Drag-and-drop query construction
4. **Charts/Visualizations** - Bar charts, pie charts from results
5. **Keyboard shortcuts** - Vim/Emacs keybindings
6. **Collaboration** - Share queries with other users
7. **Database upload** - Upload custom SQLite files
8. **Bookmarking** - Save favorite queries
9. **Themes** - Light theme option
10. **Mobile support** - Responsive design improvements
