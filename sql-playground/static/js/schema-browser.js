/**
 * Schema Browser Module
 * Displays database schema with tables and columns
 */

/**
 * Load and display schema
 */
async function loadSchema() {
    try {
        const schema = await fetchSchema();
        renderSchemaBrowser(schema);
        return schema;
    } catch (error) {
        console.error('Failed to load schema:', error);
        showSchemaError(error.message);
    }
}

/**
 * Fetch schema from sql.js database
 * @returns {Promise<Object>} Schema object
 */
async function fetchSchema() {
    if (!window.playground || !window.playground.db) {
        return { tables: [] };
    }
    
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
                    primaryKey: col[5] === 1,
                    defaultValue: col[4]
                });
            });
        }
        
        tables.push({ name: tableName, columns });
    }
    
    return { tables };
}

/**
 * Render schema browser in container
 * @param {Object} schema - Schema object
 */
function renderSchemaBrowser(schema) {
    const container = document.getElementById('schema-browser');
    if (!container) return;
    
    if (!schema.tables || schema.tables.length === 0) {
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
                        ${!col.nullable ? '<span class="not-null">NOT NULL</span>' : ''}
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

/**
 * Show schema error
 * @param {string} message - Error message
 */
function showSchemaError(message) {
    const container = document.getElementById('schema-browser');
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-message">
            <p>Error loading schema</p>
            <pre class="error-details">${escapeHtml(message)}</pre>
        </div>
    `;
}

/**
 * Insert column reference into editor
 * @param {string} table - Table name
 * @param {string} column - Column name
 */
function insertColumnReference(table, column) {
    if (!window.playground || !window.playground.editor) return;
    
    const editor = window.playground.editor;
    
    // Check if we need a table prefix
    const text = `${table}.${column}`;
    const cursor = editor.getCursor();
    const line = editor.getLine(cursor.line);
    
    // Only add table prefix if not already in query
    if (line.length === 0 || line.includes(table + '.')) {
        text = column;
    }
    
    if (editor.hasSelection()) {
        editor.replaceSelection(text);
    } else {
        editor.replaceRange(text, cursor);
    }
    
    editor.focus();
}

/**
 * Escape HTML
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions
window.loadSchema = loadSchema;
window.fetchSchema = fetchSchema;
window.renderSchemaBrowser = renderSchemaBrowser;
window.insertColumnReference = insertColumnReference;