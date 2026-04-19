// Webhook Inspector - Frontend JavaScript

const API_BASE = '';

// State
let requests = [];
let selectedRequest = null;
let eventSource = null;

// DOM Elements
const requestList = document.getElementById('requestList');
const requestDetail = document.getElementById('requestDetail');
const emptyState = document.getElementById('emptyState');
const detailEmpty = document.getElementById('detailEmpty');
const webhookUrlInput = document.getElementById('webhookUrl');
const copyUrlBtn = document.getElementById('copyUrlBtn');
const clearBtn = document.getElementById('clearBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const methodFilter = document.getElementById('methodFilter');
const searchInput = document.getElementById('searchInput');

// Initialize
function init() {
  setWebhookUrl();
  connectSSE();
  loadRequests();
  setupEventListeners();
}

function setWebhookUrl() {
  const baseUrl = window.location.origin;
  webhookUrlInput.value = `${baseUrl}/webhook`;
}

function setupEventListeners() {
  copyUrlBtn.addEventListener('click', copyWebhookUrl);
  clearBtn.addEventListener('click', clearAllRequests);
  methodFilter.addEventListener('change', filterRequests);
  searchInput.addEventListener('input', filterRequests);
}

function copyWebhookUrl() {
  navigator.clipboard.writeText(webhookUrlInput.value).then(() => {
    copyUrlBtn.classList.add('copied');
    setTimeout(() => copyUrlBtn.classList.remove('copied'), 1500);
  });
}

async function loadRequests() {
  try {
    const response = await fetch('/api/requests');
    requests = await response.json();
    renderRequestList();
  } catch (error) {
    console.error('Failed to load requests:', error);
  }
}

function connectSSE() {
  eventSource = new EventSource('/events');
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'new-request') {
      requests.unshift(data.data);
      if (requests.length > 100) requests.pop();
      renderRequestList();
      showNotification('New webhook received!');
    } else if (data.type === 'cleared') {
      requests = [];
      selectedRequest = null;
      renderRequestList();
      renderRequestDetail();
    }
  };
  
  eventSource.onerror = () => {
    console.log('SSE connection error, reconnecting...');
  };
}

function filterRequests() {
  renderRequestList();
}

function renderRequestList() {
  const method = methodFilter.value;
  const search = searchInput.value.toLowerCase();
  
  let filtered = requests;
  if (method !== 'all') {
    filtered = filtered.filter(r => r.method === method);
  }
  if (search) {
    filtered = filtered.filter(r => 
      r.path.toLowerCase().includes(search) ||
      r.method.toLowerCase().includes(search) ||
      (r.body && JSON.stringify(r.body).toLowerCase().includes(search))
    );
  }
  
  if (filtered.length === 0) {
    requestList.innerHTML = `
      <div class="empty-list">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M20 13V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7m16 0v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-5m16 0h-2.586a1 1 0 0 0-.707.293l-2.414 2.414a1 1 0 0 1-.707.293h-3.172a1 1 0 0 1-.707-.293l-2.414-2.414A1 1 0 0 0 6.586 13H4"/>
        </svg>
        <p>No requests yet</p>
        <span>Send a webhook to get started</span>
      </div>
    `;
    return;
  }
  
  requestList.innerHTML = filtered.map(req => `
    <div class="request-item ${selectedRequest && selectedRequest.id === req.id ? 'selected' : ''}" data-id="${req.id}">
      <div class="request-item-main">
        <span class="method ${req.method.toLowerCase()}">${req.method}</span>
        <span class="path">${req.path}</span>
      </div>
      <div class="request-item-meta">
        <span class="time">${formatTime(req.timestamp)}</span>
        <span class="content-type">${req.contentType || 'unknown'}</span>
      </div>
    </div>
  `).join('');
  
  document.querySelectorAll('.request-item').forEach(item => {
    item.addEventListener('click', () => selectRequest(item.dataset.id));
  });
}

function selectRequest(id) {
  selectedRequest = requests.find(r => r.id === id);
  renderRequestList();
  renderRequestDetail();
}

function renderRequestDetail() {
  if (!selectedRequest) {
    requestDetail.innerHTML = `
      <div class="detail-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
          <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        </svg>
        <p>Select a request to view details</p>
      </div>
    `;
    return;
  }
  
  const req = selectedRequest;
  requestDetail.innerHTML = `
    <div class="detail-header">
      <div class="detail-title">
        <span class="method ${req.method.toLowerCase()}">${req.method}</span>
        <span class="path">${req.path}</span>
      </div>
      <div class="detail-meta">
        <span class="timestamp">${formatTimestamp(req.timestamp)}</span>
        <span class="id">${req.id}</span>
      </div>
    </div>
    
    <div class="detail-section">
      <div class="section-header">
        <h3>Query Parameters</h3>
        <span class="count">${Object.keys(req.query || {}).length}</span>
      </div>
      <div class="section-content">
        ${renderKeyValue(req.query || {})}
      </div>
    </div>
    
    <div class="detail-section">
      <div class="section-header">
        <h3>Headers</h3>
        <span class="count">${Object.keys(req.headers || {}).length}</span>
      </div>
      <div class="section-content">
        ${renderKeyValue(req.headers || {})}
      </div>
    </div>
    
    <div class="detail-section">
      <div class="section-header">
        <h3>Body</h3>
        <div class="section-actions">
          <button class="copy-btn-small" onclick="copyBody()">Copy</button>
        </div>
      </div>
      <div class="section-content body-content">
        <pre><code id="bodyContent">${formatBody(req.body)}</code></pre>
      </div>
    </div>
  `;
}

function renderKeyValue(obj) {
  if (Object.keys(obj).length === 0) {
    return '<div class="empty">No data</div>';
  }
  
  return Object.entries(obj).map(([key, value]) => `
    <div class="kv-row">
      <span class="kv-key">${key}</span>
      <span class="kv-value">${value}</span>
    </div>
  `).join('');
}

function formatBody(body) {
  if (!body) return 'No body content';
  if (typeof body === 'string') return body;
  try {
    return JSON.stringify(body, null, 2);
  } catch {
    return String(body);
  }
}

function copyBody() {
  const body = selectedRequest.body;
  const text = typeof body === 'string' ? body : JSON.stringify(body, null, 2);
  navigator.clipboard.writeText(text);
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  });
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

async function clearAllRequests() {
  if (!confirm('Clear all requests?')) return;
  
  try {
    await fetch('/api/requests', { method: 'DELETE' });
    requests = [];
    selectedRequest = null;
    renderRequestList();
    renderRequestDetail();
  } catch (error) {
    console.error('Failed to clear requests:', error);
  }
}

function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Start the app
init();