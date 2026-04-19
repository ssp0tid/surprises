let monitors = [];
let refreshInterval;

async function loadStatus() {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('total-monitors').textContent = data.total_monitors;
    document.getElementById('up-monitors').textContent = data.up_monitors;
    document.getElementById('down-monitors').textContent = data.down_monitors;
    document.getElementById('last-refresh').textContent = `Last refresh: ${new Date().toLocaleTimeString()}`;
}

async function loadMonitors() {
    const res = await fetch('/api/monitors');
    monitors = await res.json();
    renderMonitors();
    await loadStatus();
}

function renderMonitors() {
    const container = document.getElementById('monitors-list');
    if (monitors.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding: 60px 20px; color: #94a3b8;">
                <h3>No monitors yet</h3>
                <p>Add your first website above to start monitoring</p>
            </div>
        `;
        return;
    }

    container.innerHTML = monitors.map(m => `
        <div class="monitor-card ${m.is_up ? '' : 'down'}">
            <div class="monitor-header">
                <div>
                    <div class="monitor-name">${escapeHtml(m.name || m.url)}</div>
                    <div class="monitor-url">${escapeHtml(m.url)}</div>
                </div>
                <span class="status-badge ${m.is_up ? 'up' : 'down'}">
                    ${m.is_up ? '✓ UP' : '✗ DOWN'}
                </span>
            </div>
            <div class="monitor-stats">
                <div class="stat">
                    <div class="stat-value">${m.uptime}%</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${m.consecutive_failures}</div>
                    <div class="stat-label">Failures</div>
                </div>
            </div>
            <div class="monitor-actions">
                <button class="btn-check" onclick="checkNow(${m.id})">Check Now</button>
                <button class="btn-history" onclick="showHistory(${m.id})">History</button>
                <button class="btn-delete" onclick="deleteMonitor(${m.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function checkNow(id) {
    await fetch(`/api/monitors/${id}/check`, {method: 'POST'});
    await loadMonitors();
}

async function showHistory(id) {
    const res = await fetch(`/api/monitors/${id}/history`);
    const history = await res.json();
    const monitor = monitors.find(m => m.id === id);

    document.getElementById('modal-title').textContent = `History: ${monitor.name || monitor.url}`;
    document.getElementById('history-content').innerHTML = history.map(h => `
        <div class="history-item">
            <span>${new Date(h.timestamp).toLocaleString()}</span>
            <span class="${h.is_up ? 'up' : 'down'}">
                ${h.is_up ? `${Math.round(h.response_time)}ms` : `Failed (${h.status_code})`}
            </span>
        </div>
    `).join('');

    document.getElementById('history-modal').style.display = 'block';
}

async function deleteMonitor(id) {
    if (confirm('Delete this monitor?')) {
        await fetch(`/api/monitors/${id}`, {method: 'DELETE'});
        await loadMonitors();
    }
}

document.getElementById('add-monitor-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('url-input').value.trim();
    const name = document.getElementById('name-input').value.trim() || url;
    
    await fetch('/api/monitors', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url, name})
    });
    
    document.getElementById('url-input').value = '';
    document.getElementById('name-input').value = '';
    await loadMonitors();
});

document.querySelector('.close-btn').addEventListener('click', () => {
    document.getElementById('history-modal').style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === document.getElementById('history-modal')) {
        document.getElementById('history-modal').style.display = 'none';
    }
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    loadMonitors();
    refreshInterval = setInterval(loadMonitors, 30000);
});
