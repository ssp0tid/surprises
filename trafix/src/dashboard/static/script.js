// Trafix Dashboard JavaScript

const API_BASE = '';
const POLL_INTERVAL = 5000;

let requests = [];
let metrics = null;

// Format timestamp
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

// Format duration in ms
function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

// Get status class
function getStatusClass(status) {
    if (status >= 200 && status < 300) return 'status-2xx';
    if (status >= 300 && status < 400) return 'status-3xx';
    if (status >= 400 && status < 500) return 'status-4xx';
    return 'status-5xx';
}

// Render metrics
function renderMetrics() {
    if (!metrics) return;

    document.getElementById('totalRequests').textContent =
        metrics.total_requests?.toLocaleString() || '0';

    document.getElementById('requestsPerSec').textContent =
        metrics.requests_per_second?.toFixed(2) || '0.00';

    document.getElementById('avgResponse').textContent =
        metrics.avg_response_time || '0ms';

    const errorRate = metrics.total_requests > 0
        ? ((metrics.error_count / metrics.total_requests) * 100).toFixed(1)
        : '0.0';
    document.getElementById('errorRate').textContent = `${errorRate}%`;
}

// Render requests table
function renderRequests() {
    const tbody = document.getElementById('requestsList');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    let filtered = requests;

    // Filter by search term
    if (searchTerm) {
        filtered = filtered.filter(r => r.path.toLowerCase().includes(searchTerm));
    }

    // Filter by status
    if (statusFilter) {
        filtered = filtered.filter(r => {
            const prefix = statusFilter.replace('xx', '');
            return r.status_code.toString().startsWith(prefix);
        });
    }

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No requests found</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(r => `
        <tr>
            <td>${formatTime(r.timestamp)}</td>
            <td>${r.method}</td>
            <td>${r.path}</td>
            <td>${r.target_url || '-'}</td>
            <td class="${getStatusClass(r.status_code)}">${r.status_code}</td>
            <td>${formatDuration(r.duration_ms)}</td>
        </tr>
    `).join('');
}

// Fetch data from API
async function fetchData() {
    try {
        const [metricsRes, requestsRes] = await Promise.all([
            fetch(`${API_BASE}/metrics`),
            fetch(`${API_BASE}/api/requests?limit=100`)
        ]);

        if (metricsRes.ok) {
            metrics = await metricsRes.json();
            renderMetrics();
        }

        if (requestsRes.ok) {
            const data = await requestsRes.json();
            requests = data.data || [];
            renderRequests();
        }
    } catch (error) {
        console.error('Failed to fetch data:', error);
        document.getElementById('requestsList').innerHTML =
            '<tr><td colspan="6" class="error-message">Failed to load data</td></tr>';
    }
}

// Event listeners
document.getElementById('refreshBtn').addEventListener('click', fetchData);
document.getElementById('searchInput').addEventListener('input', renderRequests);
document.getElementById('statusFilter').addEventListener('change', renderRequests);

// Initial load
fetchData();

// Auto-refresh
setInterval(fetchData, POLL_INTERVAL);