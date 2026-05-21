const API_BASE = '/api/v1';

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

async function loadMetrics() {
    try {
        const metrics = await fetchJSON(`${API_BASE}/metrics`);

        document.getElementById('pipeline-count').textContent = metrics.total_pipelines;
        document.getElementById('run-count').textContent = metrics.total_runs;
        document.getElementById('running-count').textContent = metrics.running_runs;
        document.getElementById('success-rate').textContent = `${metrics.success_rate}%`;
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

async function triggerPipeline(pipelineId) {
    try {
        const response = await fetch(`${API_BASE}/pipelines/${pipelineId}/trigger`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            const run = await response.json();
            alert(`Pipeline triggered! Run ID: ${run.id}`);
            window.location.href = `/runs/${run.id}`;
        } else {
            const error = await response.json();
            alert(`Failed to trigger pipeline: ${error.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

if (document.getElementById('pipeline-count')) {
    loadMetrics();
}

window.triggerPipeline = triggerPipeline;