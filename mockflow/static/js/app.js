(function() {
    'use strict';

    const API_BASE = '/api';

    let currentProjectId = null;
    let endpoints = [];
    let logs = [];

    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    async function apiRequest(path, options = {}) {
        const url = `${API_BASE}${path}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options
        };
        if (options.body) config.body = JSON.stringify(options.body);

        const res = await fetch(url, config);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        return data;
    }

    function showView(viewName) {
        $$('.view').forEach(v => v.classList.add('hidden'));
        $$('.nav-item').forEach(n => n.classList.remove('active'));

        const view = $(`#${viewName}View`);
        if (view) view.classList.remove('hidden');

        const navBtn = $(`.nav-item[data-view="${viewName}"]`);
        if (navBtn) navBtn.classList.add('active');
    }

    async function loadProjects() {
        try {
            const data = await apiRequest('/projects');
            const select = $('#projectSelect');
            select.innerHTML = '<option value="">Select Project</option>';

            data.projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                select.appendChild(opt);
            });
        } catch (e) {
            console.error('Failed to load projects:', e);
        }
    }

    async function loadEndpoints(projectId) {
        if (!projectId) {
            endpoints = [];
            renderEndpoints();
            return;
        }
        try {
            const data = await apiRequest(`/projects/${projectId}/endpoints`);
            endpoints = data.endpoints || [];
            renderEndpoints();
        } catch (e) {
            console.error('Failed to load endpoints:', e);
            endpoints = [];
            renderEndpoints();
        }
    }

    function renderEndpoints() {
        const list = $('#endpointsList');
        if (!list) return;

        if (endpoints.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <h3>No endpoints yet</h3>
                    <p>Create your first endpoint to get started</p>
                </div>
            `;
            return;
        }

        list.innerHTML = endpoints.map(ep => `
            <div class="endpoint-item" data-id="${ep.id}">
                <span class="method-badge ${ep.method.toLowerCase()}">${ep.method}</span>
                <span class="endpoint-path">${ep.path}</span>
                <div class="endpoint-actions">
                    <label class="toggle-switch">
                        <input type="checkbox" ${ep.enabled ? 'checked' : ''} data-action="toggle">
                        <span class="toggle-slider"></span>
                    </label>
                    <button class="btn btn-small btn-secondary" data-action="edit">Edit</button>
                    <button class="btn btn-small btn-danger" data-action="delete">Delete</button>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.endpoint-item').forEach(item => {
            item.addEventListener('click', handleEndpointAction);
        });
    }

    async function handleEndpointAction(e) {
        const action = e.target.dataset.action;
        const item = e.target.closest('.endpoint-item');
        const id = item?.dataset.id;

        if (!id) return;

        if (action === 'toggle') {
            await toggleEndpoint(id, e.target.checked);
        } else if (action === 'edit') {
            openEndpointModal(id);
        } else if (action === 'delete') {
            await deleteEndpoint(id);
        }
    }

    async function toggleEndpoint(id, enabled) {
        try {
            const ep = endpoints.find(e => e.id == id);
            if (!ep) return;

            await apiRequest(`/endpoints/${id}`, {
                method: 'PUT',
                body: { enabled }
            });

            ep.enabled = enabled;
        } catch (e) {
            console.error('Failed to toggle endpoint:', e);
        }
    }

    async function deleteEndpoint(id) {
        if (!confirm('Delete this endpoint?')) return;

        try {
            await apiRequest(`/endpoints/${id}`, { method: 'DELETE' });
            endpoints = endpoints.filter(e => e.id != id);
            renderEndpoints();
        } catch (e) {
            console.error('Failed to delete endpoint:', e);
        }
    }

    function openEndpointModal(id = null) {
        const ep = id ? endpoints.find(e => e.id == id) : null;
        const isEdit = !!ep;

        const modal = $('#modal');
        const title = $('#modalTitle');
        const body = $('#modalBody');

        title.textContent = isEdit ? 'Edit Endpoint' : 'New Endpoint';

        body.innerHTML = `
            <form id="endpointForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>Method</label>
                        <select name="method" required>
                            <option value="GET" ${ep?.method === 'GET' ? 'selected' : ''}>GET</option>
                            <option value="POST" ${ep?.method === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${ep?.method === 'PUT' ? 'selected' : ''}>PUT</option>
                            <option value="PATCH" ${ep?.method === 'PATCH' ? 'selected' : ''}>PATCH</option>
                            <option value="DELETE" ${ep?.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Path</label>
                        <input type="text" name="path" placeholder="/api/users/:id" value="${ep?.path || ''}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <input type="text" name="description" value="${ep?.description || ''}">
                </div>
                <div class="form-group">
                    <label>Response Body (JSON)</label>
                    <textarea name="body">${ep?.responses?.[0]?.body || '{}'}</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Status Code</label>
                        <input type="number" name="status_code" value="${ep?.responses?.[0]?.status_code || 200}">
                    </div>
                    <div class="form-group">
                        <label>Delay (ms)</label>
                        <input type="number" name="delay_ms" value="${ep?.responses?.[0]?.delay_ms || 0}">
                    </div>
                </div>
            </form>
        `;

        $('#modalSave').onclick = () => saveEndpoint(id);
        modal.classList.remove('hidden');
    }

    async function saveEndpoint(id) {
        const form = $('#endpointForm');
        const formData = new FormData(form);

        const payload = {
            method: formData.get('method'),
            path: formData.get('path'),
            description: formData.get('description'),
            body: formData.get('body'),
            status_code: parseInt(formData.get('status_code')),
            delay_ms: parseInt(formData.get('delay_ms'))
        };

        try {
            let result;
            if (id) {
                result = await apiRequest(`/endpoints/${id}`, {
                    method: 'PUT',
                    body: payload
                });
            } else {
                result = await apiRequest(`/projects/${currentProjectId}/endpoints`, {
                    method: 'POST',
                    body: payload
                });
            }

            closeModal();
            if (currentProjectId) loadEndpoints(currentProjectId);
        } catch (e) {
            alert(e.message);
        }
    }

    function closeModal() {
        $('#modal').classList.add('hidden');
    }

    async function loadLogs(projectId) {
        if (!projectId) {
            logs = [];
            renderLogs();
            return;
        }
        try {
            const data = await apiRequest(`/projects/${projectId}/logs`);
            logs = data.logs || [];
            renderLogs();
        } catch (e) {
            console.error('Failed to load logs:', e);
            logs = [];
            renderLogs();
        }
    }

    function renderLogs() {
        const tbody = $('#logsTableBody');
        if (!tbody) return;

        if (logs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">No logs yet</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = logs.slice(0, 100).map(log => `
            <tr>
                <td>${new Date(log.created_at).toLocaleString()}</td>
                <td><span class="method-badge ${log.method.toLowerCase()}">${log.method}</span></td>
                <td>${log.path}</td>
                <td><span class="status-badge ${log.response_status < 400 ? 'success' : 'error'}">${log.response_status}</span></td>
                <td>${log.response_time_ms}ms</td>
            </tr>
        `).join('');
    }

    async function loadDashboard(projectId) {
        if (!projectId) {
            $('#endpointCount').textContent = '0';
            $('#requestCount').textContent = '0';
            $('#matchRate').textContent = '0%';
            return;
        }

        try {
            const [epData, logData, stats] = await Promise.all([
                apiRequest(`/projects/${projectId}/endpoints`),
                apiRequest(`/projects/${projectId}/logs?per_page=1000`),
                apiRequest(`/projects/${projectId}/server/stats`)
            ]);

            const endpointCount = epData.total || 0;
            const requestCount = logData.total || 0;
            const matchedCount = logData.logs?.filter(l => l.matched).length || 0;
            const matchRate = requestCount > 0 ? Math.round((matchedCount / requestCount) * 100) : 0;

            $('#endpointCount').textContent = endpointCount;
            $('#requestCount').textContent = requestCount;
            $('#matchRate').textContent = `${matchRate}%`;
        } catch (e) {
            console.error('Failed to load dashboard:', e);
        }
    }

    async function loadServerStatus(projectId) {
        if (!projectId) {
            updateServerStatus(false);
            return;
        }
        try {
            const status = await apiRequest(`/projects/${projectId}/server`);
            updateServerStatus(status.enabled);
        } catch (e) {
            console.error('Failed to load server status:', e);
            updateServerStatus(false);
        }
    }

    function updateServerStatus(running) {
        const statusEl = $('#serverStatus');
        const btn = $('#serverToggleBtn');

        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');

        if (running) {
            dot.classList.remove('offline');
            dot.classList.add('online');
            text.textContent = 'Server Running';
            btn.textContent = 'Stop Server';
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-danger');
        } else {
            dot.classList.remove('online');
            dot.classList.add('offline');
            text.textContent = 'Server Offline';
            btn.textContent = 'Start Server';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-secondary');
        }
    }

    async function toggleServer() {
        if (!currentProjectId) return;

        const statusEl = $('#serverStatus');
        const isRunning = statusEl.querySelector('.status-dot').classList.contains('online');

        try {
            if (isRunning) {
                await apiRequest(`/projects/${currentProjectId}/server/stop`, { method: 'POST' });
            } else {
                await apiRequest(`/projects/${currentProjectId}/server/start`, { method: 'POST' });
            }
            loadServerStatus(currentProjectId);
        } catch (e) {
            console.error('Failed to toggle server:', e);
            alert(e.message);
        }
    }

    async function createProject() {
        const name = prompt('Project name:');
        if (!name) return;

        try {
            const project = await apiRequest('/projects', {
                method: 'POST',
                body: { name }
            });

            await loadProjects();
            $('#projectSelect').value = project.id;
            handleProjectChange();
        } catch (e) {
            console.error('Failed to create project:', e);
            alert(e.message);
        }
    }

    function handleProjectChange() {
        currentProjectId = $('#projectSelect')?.value;
        loadDashboard(currentProjectId);
        loadEndpoints(currentProjectId);
        loadLogs(currentProjectId);
        loadServerStatus(currentProjectId);
    }

    function init() {
        showView('dashboard');
        loadProjects();

        $('#projectSelect').addEventListener('change', handleProjectChange);
        $('#newProjectBtn').addEventListener('click', createProject);
        $('#serverToggleBtn').addEventListener('click', toggleServer);
        $('#newEndpointBtn').addEventListener('click', () => openEndpointModal());

        $$('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => showView(btn.dataset.view));
        });

        $('#modalClose').addEventListener('click', closeModal);
        $('#modalCancel').addEventListener('click', closeModal);

        $('#modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') closeModal();
        });

        $('#methodFilter, #searchInput').addEventListener('input', filterEndpoints);

        let pollInterval;
        const startPolling = () => {
            pollInterval = setInterval(() => {
                if (currentProjectId) {
                    loadLogs(currentProjectId);
                    loadDashboard(currentProjectId);
                }
            }, 3000);
        };

        startPolling();
    }

    function filterEndpoints() {
        const method = $('#methodFilter')?.value;
        const search = $('#searchInput')?.value.toLowerCase();

        let filtered = endpoints;

        if (method) {
            filtered = filtered.filter(e => e.method === method);
        }
        if (search) {
            filtered = filtered.filter(e => e.path.toLowerCase().includes(search));
        }

        const list = $('#endpointsList');
        if (!list) return;

        if (filtered.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <h3>No endpoints found</h3>
                    <p>Try adjusting your filters</p>
                </div>
            `;
            return;
        }

        renderFilteredEndpoints(filtered);
    }

    function renderFilteredEndpoints(filtered) {
        const list = $('#endpointsList');
        list.innerHTML = filtered.map(ep => `
            <div class="endpoint-item" data-id="${ep.id}">
                <span class="method-badge ${ep.method.toLowerCase()}">${ep.method}</span>
                <span class="endpoint-path">${ep.path}</span>
                <div class="endpoint-actions">
                    <label class="toggle-switch">
                        <input type="checkbox" ${ep.enabled ? 'checked' : ''} data-action="toggle">
                        <span class="toggle-slider"></span>
                    </label>
                    <button class="btn btn-small btn-secondary" data-action="edit">Edit</button>
                    <button class="btn btn-small btn-danger" data-action="delete">Delete</button>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.endpoint-item').forEach(item => {
            item.addEventListener('click', handleEndpointAction);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();