const RECENT_REPOS_KEY = 'gitDashboardRecentRepos';
const MAX_RECENT_REPOS = 5;

function saveRecentRepo(path) {
    let recent = getRecentRepos();
    recent = recent.filter(p => p !== path);
    recent.unshift(path);
    if (recent.length > MAX_RECENT_REPOS) {
        recent = recent.slice(0, MAX_RECENT_REPOS);
    }
    localStorage.setItem(RECENT_REPOS_KEY, JSON.stringify(recent));
}

function getRecentRepos() {
    try {
        const stored = localStorage.getItem(RECENT_REPOS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function loadRecentRepos() {
    const recent = getRecentRepos();
    const container = document.getElementById('recentRepos');
    if (!container) return;

    if (recent.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent repositories</p>';
        return;
    }

    container.innerHTML = recent.map(path => {
        const name = path.split('/').pop();
        return `<a href="/dashboard/${encodeURIComponent(path)}" class="list-group-item list-group-item-action">${name}</a>`;
    }).join('');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatNumber(num) {
    if (!num) return '0';
    return num.toLocaleString();
}

function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = '';
}

function hideLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'none';
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = '';
    }
}

function showContent(contentId, loadingId) {
    hideLoading(loadingId);
    const el = document.getElementById(contentId);
    if (el) el.style.display = '';
}

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'Request failed');
    }
    return response.json();
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