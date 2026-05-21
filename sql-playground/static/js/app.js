/**
 * SQL Playground - Main Application
 * Coordinates all components and handles user interactions
 */

class SQLPlayground {
    constructor() {
        this.db = null;
        this.currentResults = null;
        this.currentQuery = '';
        this.editor = null;
        this.currentPage = 1;
        this.rowsPerPage = 100;
        this.SQL = null;
    }
    
    /**
     * Initialize the application
     */
    async init() {
        try {
            // Initialize sql.js
            await this.initSQL();
            
            // Initialize CodeMirror
            this.initEditor();
            
            // Load schema browser
            await this.loadSchema();
            
            // Load sample datasets
            await this.loadSamples();
            
            // Load saved queries
            await this.loadSavedQueries();
            
            // Bind event handlers
            this.bindEvents();
            
            // Update status
            this.updateStatus('Ready');
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.updateStatus('Error: ' + error.message);
            this.showError('Failed to initialize application: ' + error.message);
        }
    }
    
    /**
     * Initialize sql.js database
     */
    async initSQL() {
        this.updateStatus('Loading SQLite...');
        
        const SQL = await initSqlJs({
            locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/${file}`
        });
        
        this.SQL = SQL;
        
        // Try to load saved database from localStorage
        const savedDb = localStorage.getItem('sql_playground_db');
        if (savedDb) {
            try {
                const uint8Array = new Uint8Array(JSON.parse(savedDb));
                this.db = new SQL.Database(uint8Array);
                this.updateStatus('Database loaded from local storage');
            } catch (e) {
                console.warn('Failed to load saved database, creating new one');
                this.db = new SQL.Database();
                this.createDefaultTables();
            }
        } else {
            this.db = new SQL.Database();
            this.createDefaultTables();
        }
    }
    
    /**
     * Create default tables
     */
    createDefaultTables() {
        this.db.run(`
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        // Insert sample data
        this.db.run(`INSERT OR IGNORE INTO users (name, email) VALUES ('Alice', 'alice@example.com')`);
        this.db.run(`INSERT OR IGNORE INTO users (name, email) VALUES ('Bob', 'bob@example.com')`);
        this.db.run(`INSERT OR IGNORE INTO users (name, email) VALUES ('Charlie', 'charlie@example.com')`);
        
        this.updateStatus('Default tables created');
    }
    
    /**
     * Initialize CodeMirror editor
     */
    initEditor() {
        const container = document.getElementById('query-editor');
        if (!container) return;
        
        this.editor = initCodeMirror(container, {
            value: '-- Write your SQL query here\n-- Press Ctrl+Enter to execute\n\nSELECT * FROM users;',
            mode: 'text/x-sql',
            theme: 'monokai',
            lineNumbers: true,
            autofocus: true,
            indentUnit: 2,
            smartIndent: true,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        // Update cursor position display
        this.editor.on('cursorActivity', () => {
            const pos = getCursorPosition(this.editor);
            const posEl = document.getElementById('cursor-position');
            if (posEl) posEl.textContent = pos;
        });
        
        this.updateStatus('Editor initialized');
    }
    
    /**
     * Load schema browser
     */
    async loadSchema() {
        await loadSchema();
    }
    
    /**
     * Load sample datasets
     */
    async loadSamples() {
        try {
            const response = await fetch('/api/db/samples');
            const data = await response.json();
            
            const container = document.getElementById('sample-datasets');
            if (!container) return;
            
            container.innerHTML = data.samples.map(sample => `
                <div class="sample-item" data-sample="${sample.id}">
                    <span class="sample-icon">📁</span>
                    <div class="sample-info">
                        <div class="sample-name">${sample.name}</div>
                        <div class="sample-desc">${sample.description}</div>
                    </div>
                </div>
            `).join('');
            
            // Bind click events
            container.querySelectorAll('.sample-item').forEach(item => {
                item.addEventListener('click', () => {
                    this.loadSampleDataset(item.dataset.sample);
                });
            });
            
        } catch (error) {
            console.error('Failed to load samples:', error);
        }
    }
    
    /**
     * Load saved queries
     */
    async loadSavedQueries() {
        try {
            const response = await fetch('/api/query/saved');
            const data = await response.json();
            
            const container = document.getElementById('saved-queries');
            if (!container) return;
            
            if (!data.queries || data.queries.length === 0) {
                container.innerHTML = '<div class="empty-state-small">No saved queries</div>';
                return;
            }
            
            container.innerHTML = data.queries.map(query => `
                <div class="saved-query-item" data-id="${query.id}">
                    <span class="saved-query-name">${escapeHtml(query.name)}</span>
                    <button class="btn-delete-query" data-id="${query.id}" title="Delete">×</button>
                </div>
            `).join('');
            
            // Bind click events
            container.querySelectorAll('.saved-query-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('btn-delete-query')) {
                        const queryId = item.dataset.id;
                        const queryData = data.queries.find(q => q.id == queryId);
                        if (queryData) {
                            this.editor.setValue(queryData.query);
                            this.editor.focus();
                        }
                    }
                });
            });
            
            // Bind delete buttons
            container.querySelectorAll('.btn-delete-query').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = btn.dataset.id;
                    if (confirm('Delete this saved query?')) {
                        await this.deleteSavedQuery(id);
                    }
                });
            });
            
        } catch (error) {
            console.error('Failed to load saved queries:', error);
        }
    }
    
    /**
     * Load sample dataset
     * @param {string} sampleId - Sample dataset ID
     */
    async loadSampleDataset(sampleId) {
        this.updateStatus(`Loading ${sampleId} dataset...`);
        
        try {
            const response = await fetch('/api/db/load-sample', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dataset: sampleId })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load dataset');
            }
            
            // Execute SQL statements
            const statements = data.sql.split(';').filter(s => s.trim());
            for (const stmt of statements) {
                if (stmt.trim()) {
                    this.db.run(stmt);
                }
            }
            
            // Refresh schema
            await this.loadSchema();
            
            // Save database state
            this.saveDatabase();
            
            // Show success message
            this.showSuccess(`Loaded ${data.name} dataset`);
            this.updateStatus('Ready');
            
        } catch (error) {
            console.error('Failed to load sample:', error);
            this.showError('Failed to load dataset: ' + error.message);
            this.updateStatus('Error loading dataset');
        }
    }
    
    /**
     * Execute query
     */
    async executeQuery() {
        const query = this.editor.getValue().trim();
        if (!query) {
            this.showError('Please enter a query');
            return;
        }
        
        this.currentQuery = query;
        this.updateStatus('Executing query...');
        
        const startTime = performance.now();
        
        try {
            // Check if it's a SELECT query
            const isSelect = /^SELECT/i.test(query);
            
            if (isSelect) {
                const results = this.db.exec(query);
                const executionTime = performance.now() - startTime;
                
                if (results.length === 0) {
                    this.displaySuccess({
                        message: 'Query executed successfully. No results returned.',
                        executionTime
                    });
                    this.currentResults = null;
                } else {
                    this.currentResults = results[0];
                    this.displayResults(this.currentResults);
                }
                
                // Save to history
                this.saveToHistory(query, this.currentResults ? this.currentResults.values.length : 0, executionTime, null);
                
            } else {
                // Non-SELECT query
                this.db.run(query);
                const changes = this.db.getRowsModified();
                const executionTime = performance.now() - startTime;
                
                this.displaySuccess({
                    message: `Query executed successfully. ${changes} row(s) affected.`,
                    executionTime
                });
                this.currentResults = null;
                
                // Save to history
                this.saveToHistory(query, changes, executionTime, null);
                
                // Refresh schema if tables were modified
                await this.loadSchema();
            }
            
            // Save database state
            this.saveDatabase();
            
            this.updateStatus(`Ready (${(performance.now() - startTime).toFixed(2)}ms)`);
            
        } catch (error) {
            const executionTime = performance.now() - startTime;
            this.displayError(error.message);
            this.saveToHistory(query, 0, executionTime, error.message);
            this.updateStatus('Error');
        }
    }
    
    /**
     * Display results
     * @param {Object} result - Query result
     */
    displayResults(result) {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        renderResultsTable(container, result.columns, result.values);
        
        const infoEl = document.getElementById('results-info');
        if (infoEl) {
            infoEl.textContent = `${result.values.length} row(s)`;
        }
        
        // Enable export buttons
        const csvBtn = document.getElementById('btn-export-csv');
        const jsonBtn = document.getElementById('btn-export-json');
        if (csvBtn) csvBtn.disabled = false;
        if (jsonBtn) jsonBtn.disabled = false;
    }
    
    /**
     * Display success message
     * @param {Object} info - Success info
     */
    displaySuccess(info) {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="success-message">
                <span class="icon">✓</span>
                <p>${info.message}</p>
                <p class="execution-time">Execution time: ${info.executionTime.toFixed(2)}ms</p>
            </div>
        `;
        
        // Disable export buttons
        const csvBtn = document.getElementById('btn-export-csv');
        const jsonBtn = document.getElementById('btn-export-json');
        if (csvBtn) csvBtn.disabled = true;
        if (jsonBtn) jsonBtn.disabled = true;
        
        // Update info
        const infoEl = document.getElementById('results-info');
        if (infoEl) infoEl.textContent = 'Success';
    }
    
    /**
     * Display error message
     * @param {string} error - Error message
     */
    displayError(error) {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="error-message">
                <span class="icon">✗</span>
                <p class="error-title">SQL Error</p>
                <pre class="error-details">${this.escapeHtml(error)}</pre>
            </div>
        `;
        
        // Disable export buttons
        const csvBtn = document.getElementById('btn-export-csv');
        const jsonBtn = document.getElementById('btn-export-json');
        if (csvBtn) csvBtn.disabled = true;
        if (jsonBtn) jsonBtn.disabled = true;
        
        // Update info
        const infoEl = document.getElementById('results-info');
        if (infoEl) infoEl.textContent = 'Error';
    }
    
    /**
     * Show error (alert)
     * @param {string} message - Error message
     */
    showError(message) {
        this.displayError(message);
    }
    
    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="success-message">
                    <span class="icon">✓</span>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    /**
     * Save query to history
     */
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
    
    /**
     * Save database to localStorage
     */
    saveDatabase() {
        try {
            const data = this.db.export();
            const buffer = Array.from(data);
            localStorage.setItem('sql_playground_db', JSON.stringify(buffer));
        } catch (e) {
            console.warn('Failed to save database:', e);
        }
    }
    
    /**
     * Clear editor
     */
    clearEditor() {
        this.editor.setValue('');
        this.editor.focus();
    }
    
    /**
     * Format query
     */
    formatQuery() {
        const query = this.editor.getValue();
        const formatted = formatSQL(query);
        this.editor.setValue(formatted);
    }
    
    /**
     * Show save modal
     */
    showSaveModal() {
        const modal = document.getElementById('save-modal');
        const input = document.getElementById('query-name');
        if (modal) {
            modal.classList.remove('hidden');
            if (input) {
                input.value = '';
                input.focus();
            }
        }
    }
    
    /**
     * Hide save modal
     */
    hideSaveModal() {
        const modal = document.getElementById('save-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    /**
     * Save query
     */
    async saveQuery() {
        const nameInput = document.getElementById('query-name');
        const name = nameInput?.value.trim();
        
        if (!name) {
            alert('Please enter a name for the query');
            return;
        }
        
        const query = this.editor.getValue().trim();
        if (!query) {
            alert('No query to save');
            return;
        }
        
        try {
            const response = await fetch('/api/query/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideSaveModal();
                this.loadSavedQueries();
                this.showSuccess('Query saved successfully');
            } else {
                alert('Failed to save query: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Failed to save query:', error);
            alert('Failed to save query');
        }
    }
    
    /**
     * Delete saved query
     */
    async deleteSavedQuery(id) {
        try {
            await fetch(`/api/query/saved/${id}`, { method: 'DELETE' });
            this.loadSavedQueries();
        } catch (error) {
            console.error('Failed to delete query:', error);
        }
    }
    
    /**
     * Update status bar
     */
    updateStatus(message) {
        const statusEl = document.getElementById('sql-dialect');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }
    
    /**
     * Bind event handlers
     */
    bindEvents() {
        // Run button
        const runBtn = document.getElementById('btn-run');
        if (runBtn) {
            runBtn.addEventListener('click', () => this.executeQuery());
        }
        
        // Clear button
        const clearBtn = document.getElementById('btn-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearEditor());
        }
        
        // Format button
        const formatBtn = document.getElementById('btn-format');
        if (formatBtn) {
            formatBtn.addEventListener('click', () => this.formatQuery());
        }
        
        // Save button
        const saveBtn = document.getElementById('btn-save');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.showSaveModal());
        }
        
        // Export buttons
        const csvBtn = document.getElementById('btn-export-csv');
        if (csvBtn) {
            csvBtn.addEventListener('click', () => exportToCSV(this.currentResults));
        }
        
        const jsonBtn = document.getElementById('btn-export-json');
        if (jsonBtn) {
            jsonBtn.addEventListener('click', () => exportToJSON(this.currentResults));
        }
        
        // Modal events
        const closeBtn = document.getElementById('close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideSaveModal());
        }
        
        const cancelBtn = document.getElementById('cancel-save');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideSaveModal());
        }
        
        const confirmBtn = document.getElementById('confirm-save');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.saveQuery());
        }
        
        // Close modal on outside click
        const modal = document.getElementById('save-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideSaveModal();
                }
            });
        }
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideSaveModal();
            }
        });
    }
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global executeQuery function
window.executeQuery = function() {
    if (window.playground) {
        window.playground.executeQuery();
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    // Only initialize on main page
    if (document.getElementById('query-editor')) {
        window.playground = new SQLPlayground();
        await window.playground.init();
    }
});