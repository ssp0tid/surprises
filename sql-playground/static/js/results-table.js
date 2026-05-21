/**
 * Results Table Module
 * Handles rendering, sorting, filtering, and pagination of query results
 */

/**
 * Render results as an interactive table
 * @param {HTMLElement} container - Container element
 * @param {string[]} columns - Column names
 * @param {Array[]} rows - Row data
 * @param {Object} options - Rendering options
 * @returns {Object} Table API
 */
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
                   value="">
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
                td.title = cell === null ? 'NULL' : String(cell);
                if (cell === null) td.className = 'null-value';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        updatePagination();
    }
    
    function applyFilter() {
        if (!filterValue) {
            filteredRows = [...rows];
        } else {
            filteredRows = rows.filter(row => 
                row.some(cell => 
                    cell !== null && String(cell).toLowerCase().includes(filterValue)
                )
            );
        }
        currentPage = 1;
        sortColumn = null;
        sortDirection = 'asc';
        renderPage();
        updateRowCount();
        updateSortIndicators();
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
        updateSortIndicators();
    }
    
    function updateSortIndicators() {
        const headers = table.querySelectorAll('th');
        headers.forEach((th, index) => {
            th.classList.remove('sorted-asc', 'sorted-desc');
            if (index === sortColumn) {
                th.classList.add(`sorted-${sortDirection}`);
                th.textContent = columns[index] + (sortDirection === 'asc' ? ' ↑' : ' ↓');
            } else {
                th.textContent = columns[index];
            }
        });
    }
    
    function updateRowCount() {
        const countEl = wrapper.querySelector('.row-count');
        if (countEl) {
            countEl.textContent = `${filteredRows.length} rows`;
        }
    }
    
    function updatePagination() {
        const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
        const paginationEl = document.getElementById('results-pagination');
        const pageInfoEl = document.getElementById('page-info');
        
        if (paginationEl) {
            if (totalPages > 1) {
                paginationEl.classList.remove('hidden');
                if (pageInfoEl) {
                    pageInfoEl.textContent = `Page ${currentPage} of ${totalPages}`;
                }
            } else {
                paginationEl.classList.add('hidden');
            }
        }
    }
    
    table.appendChild(tbody);
    wrapper.appendChild(table);
    
    // Clear and replace container content
    container.innerHTML = '';
    container.appendChild(wrapper);
    
    // Initial render
    renderPage();
    updateRowCount();
    
    // Bind pagination buttons
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    if (prevBtn) {
        prevBtn.onclick = () => {
            if (currentPage > 1) {
                currentPage--;
                renderPage();
            }
        };
    }
    
    if (nextBtn) {
        nextBtn.onclick = () => {
            const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
            if (currentPage < totalPages) {
                currentPage++;
                renderPage();
            }
        };
    }
    
    return {
        getFilteredRows: () => filteredRows,
        getColumns: () => columns,
        getRawRows: () => rows,
        refresh: () => renderPage(),
        getCurrentPage: () => currentPage,
        setPage: (page) => {
            currentPage = page;
            renderPage();
        }
    };
}

/**
 * Debounce function for search input
 */
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

// Export functions
window.renderResultsTable = renderResultsTable;
window.debounce = debounce;
