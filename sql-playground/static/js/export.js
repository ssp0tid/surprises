/**
 * Export Module
 * CSV and JSON export utilities
 */

/**
 * Export results to CSV
 * @param {Object} result - Query result object with columns and values
 */
function exportToCSV(result) {
    if (!result || !result.columns || !result.values) {
        console.error('No results to export');
        showExportError('No results to export');
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

/**
 * Export results to JSON
 * @param {Object} result - Query result object with columns and values
 */
function exportToJSON(result) {
    if (!result || !result.columns || !result.values) {
        console.error('No results to export');
        showExportError('No results to export');
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

/**
 * Export via server API
 * @param {Object} result - Query result object
 * @param {string} format - Export format ('csv' or 'json')
 */
async function exportViaAPI(result, format) {
    if (!result || !result.columns || !result.values) {
        console.error('No results to export');
        return;
    }
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                columns: result.columns,
                rows: result.values,
                format: format
            })
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        // Handle file download
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `query_results.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Export failed:', error);
        showExportError(error.message);
    }
}

/**
 * Escape CSV value
 * @param {*} value - Value to escape
 * @returns {string} Escaped value
 */
function escapeCSV(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'number') return value;
    
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
        return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
}

/**
 * Download file
 * @param {string} content - File content
 * @param {string} filename - Download filename
 * @param {string} mimeType - MIME type
 */
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
    
    showExportSuccess(filename);
}

/**
 * Show export success message
 * @param {string} filename - Downloaded filename
 */
function showExportSuccess(filename) {
    // Could show a toast notification
    console.log(`Exported ${filename}`);
}

/**
 * Show export error
 * @param {string} message - Error message
 */
function showExportError(message) {
    console.error('Export error:', message);
    alert('Export failed: ' + message);
}

/**
 * Convert results to CSV string
 * @param {Object} result - Query result
 * @returns {string} CSV string
 */
function resultsToCSV(result) {
    if (!result || !result.columns || !result.values) {
        return '';
    }
    
    const { columns, values } = result;
    let csv = columns.map(escapeCSV).join(',') + '\n';
    
    values.forEach(row => {
        csv += row.map(cell => escapeCSV(cell)).join(',') + '\n';
    });
    
    return csv;
}

/**
 * Convert results to JSON string
 * @param {Object} result - Query result
 * @returns {string} JSON string
 */
function resultsToJSON(result) {
    if (!result || !result.columns || !result.values) {
        return '[]';
    }
    
    const { columns, values } = result;
    
    const data = values.map(row => {
        const obj = {};
        columns.forEach((col, i) => {
            obj[col] = row[i];
        });
        return obj;
    });
    
    return JSON.stringify(data, null, 2);
}

// Export functions
window.exportToCSV = exportToCSV;
window.exportToJSON = exportToJSON;
window.exportViaAPI = exportViaAPI;
window.escapeCSV = escapeCSV;
window.downloadFile = downloadFile;
window.resultsToCSV = resultsToCSV;
window.resultsToJSON = resultsToJSON;