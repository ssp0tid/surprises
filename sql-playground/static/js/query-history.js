/**
 * Query History Module
 * Manages query history display and interactions
 */

let historyCurrentPage = 1;
let historyPerPage = 50;
let historyTotal = 0;

/**
 * Load query history from API
 * @param {number} page - Page number
 * @param {number} perPage - Items per page
 */
async function loadHistory(page = 1, perPage = 50) {
    try {
        const response = await fetch(`/api/query/history?page=${page}&per_page=${perPage}`);
        const data = await response.json();
        
        historyCurrentPage = page;
        historyPerPage = perPage;
        historyTotal = data.total;
        
        // Check if this is the history page or main page sidebar
        if (window.HISTORY_PAGE) {
            renderHistoryPage(data.history, page, data.total, perPage);
        }
        
        return data;
    } catch (error) {
        console.error('Failed to load history:', error);
        showHistoryError(error.message);
    }
}

/**
 * Render history on history page
 * @param {Array} history - History items
 * @param {number} currentPage - Current page
 * @param {number} total - Total items
 * @param {number} perPage - Items per page
 */
function renderHistoryPage(history, currentPage, total, perPage) {
    const container = document.getElementById('history-list');
    if (!container) return;
    
    if (!history || history.length === 0) {
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

/**
 * Render history pagination
 * @param {number} currentPage - Current page
 * @param {number} total - Total items
 * @param {number} perPage - Items per page
 */
function renderHistoryPagination(currentPage, total, perPage) {
    const paginationEl = document.getElementById('history-pagination');
    const pageInfo = paginationEl?.querySelector('#page-info');
    const prevBtn = paginationEl?.querySelector('#prev-page');
    const nextBtn = paginationEl?.querySelector('#next-page');
    
    if (!paginationEl) return;
    
    const totalPages = Math.ceil(total / perPage) || 1;
    
    if (totalPages <= 1) {
        paginationEl.classList.add('hidden');
        return;
    }
    
    paginationEl.classList.remove('hidden');
    
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
    
    if (prevBtn) {
        prevBtn.disabled = currentPage <= 1;
        prevBtn.onclick = () => {
            if (currentPage > 1) {
                loadHistory(currentPage - 1, perPage);
            }
        };
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentPage >= totalPages;
        nextBtn.onclick = () => {
            if (currentPage < totalPages) {
                loadHistory(currentPage + 1, perPage);
            }
        };
    }
}

/**
 * Load query into editor
 * @param {string} query - Query text
 */
function loadQueryIntoEditor(query) {
    if (window.playground && window.playground.editor) {
        window.playground.editor.setValue(query);
        window.playground.editor.focus();
        
        // If not on history page, navigate to playground
        if (window.location.pathname === '/history') {
            window.location.href = '/';
        }
    }
}

/**
 * Delete history item
 * @param {number} id - History item ID
 */
async function deleteHistoryItem(id) {
    if (!confirm('Delete this history item?')) return;
    
    try {
        await fetch(`/api/query/history/${id}`, { method: 'DELETE' });
        loadHistory(historyCurrentPage, historyPerPage);
    } catch (error) {
        console.error('Failed to delete history item:', error);
    }
}

/**
 * Clear all history
 */
async function clearAllHistory() {
    if (!confirm('Delete all history? This cannot be undone.')) return;
    
    try {
        await fetch('/api/query/history', { method: 'DELETE' });
        loadHistory(1, historyPerPage);
    } catch (error) {
        console.error('Failed to clear history:', error);
    }
}

/**
 * Format timestamp
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
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

/**
 * Show history error
 * @param {string} message - Error message
 */
function showHistoryError(message) {
    const container = document.getElementById('history-list');
    if (container) {
        container.innerHTML = `
            <div class="error-message">
                <p>Error loading history</p>
                <pre class="error-details">${escapeHtml(message)}</pre>
            </div>
        `;
    }
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

/**
 * Initialize history page
 */
function initHistoryPage() {
    if (!window.HISTORY_PAGE) return;
    
    loadHistory(1, 50);
    
    // Clear all button
    const clearBtn = document.getElementById('btn-clear-all');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearAllHistory);
    }
}

// Export functions
window.loadHistory = loadHistory;
window.deleteHistoryItem = deleteHistoryItem;
window.clearAllHistory = clearAllHistory;
window.formatTimestamp = formatTimestamp;
window.loadQueryIntoEditor = loadQueryIntoEditor;
window.initHistoryPage = initHistoryPage;

// Auto-init on load if on history page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHistoryPage);
} else {
    initHistoryPage();
}