(function () {
  'use strict';

  let activeEnvironment = null;
  let environments = [];

  document.addEventListener('DOMContentLoaded', function () {
    initTabs();
    addParamRow();
    addHeaderRow();
    loadHistory();
    loadCollections();
    loadEnvironments();
  });

  // --- Tab Management ---

  function initTabs() {
    document.querySelectorAll('.sidebar-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.sidebar-tab').forEach(function (b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        var tab = btn.dataset.sidebarTab;
        document.querySelectorAll('.sidebar-panel').forEach(function (p) {
          p.classList.add('hidden');
        });
        document.getElementById('panel-' + tab).classList.remove('hidden');
      });
    });

    document.querySelectorAll('.req-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.req-tab').forEach(function (b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        var tab = btn.dataset.reqTab;
        document.querySelectorAll('.req-tab-panel').forEach(function (p) {
          p.classList.add('hidden');
        });
        document.getElementById('tab-' + tab).classList.remove('hidden');
      });
    });
  }

  // --- Key-Value Row Helpers ---

  function createKvRow(containerId, keyPlaceholder, valuePlaceholder) {
    var container = document.getElementById(containerId);
    var row = document.createElement('div');
    row.className = 'flex gap-1 items-center';
    row.innerHTML =
      '<input type="text" placeholder="' + keyPlaceholder + '" class="kv-key flex-1 bg-gray-700 rounded px-2 py-1 text-sm border border-gray-600 focus:outline-none focus:border-indigo-500">' +
      '<input type="text" placeholder="' + valuePlaceholder + '" class="kv-value flex-1 bg-gray-700 rounded px-2 py-1 text-sm border border-gray-600 focus:outline-none focus:border-indigo-500">' +
      '<button class="text-red-400 hover:text-red-300 text-sm px-1" onclick="this.parentElement.remove()">×</button>';
    container.appendChild(row);
  }

  window.addParamRow = function () {
    createKvRow('params-list', 'Key', 'Value');
  };

  window.addHeaderRow = function () {
    createKvRow('headers-list', 'Header name', 'Header value');
  };

  // --- Environment Variable Interpolation ---

  function interpolateVariables(text) {
    if (!text || !activeEnvironment) return text;
    var variables = activeEnvironment.variables || {};
    return text.replace(/\{\{(\w+)\}\}/g, function (match, varName) {
      return variables[varName] !== undefined ? variables[varName] : match;
    });
  }

  // --- Collect Form Data ---

  function collectKvPairs(containerId) {
    var pairs = [];
    var container = document.getElementById(containerId);
    container.querySelectorAll('.flex.gap-1').forEach(function (row) {
      var key = row.querySelector('.kv-key').value.trim();
      var value = row.querySelector('.kv-value').value;
      if (key) {
        pairs.push({ key: key, value: value });
      }
    });
    return pairs;
  }

  function getBodyType() {
    var checked = document.querySelector('input[name="body-type"]:checked');
    return checked ? checked.value : 'json';
  }

  function collectRequestData() {
    var method = document.getElementById('req-method').value;
    var url = interpolateVariables(document.getElementById('req-url').value.trim());
    var headers = collectKvPairs('headers-list').map(function (h) {
      return { key: h.key, value: interpolateVariables(h.value) };
    });
    var params = collectKvPairs('params-list').map(function (p) {
      return { key: p.key, value: interpolateVariables(p.value) };
    });
    var body = interpolateVariables(document.getElementById('req-body').value);
    var bodyType = getBodyType();

    return {
      method: method,
      url: url,
      headers: headers,
      params: params,
      body: body,
      body_type: bodyType
    };
  }

  // --- Send Request ---

  window.sendRequest = async function () {
    var data = collectRequestData();
    if (!data.url) {
      showError('Please enter a URL');
      return;
    }

    var btn = document.getElementById('btn-send');
    btn.disabled = true;
    btn.textContent = 'Sending...';

    try {
      var resp = await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      var result = await resp.json();

      if (result.error) {
        showError(result.error);
      } else {
        showResponse(result);
      }
      loadHistory();
    } catch (e) {
      showError('Failed to send request: ' + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Send';
    }
  };

  // --- Response Display ---

  function showResponse(result) {
    document.getElementById('response-placeholder').classList.add('hidden');
    document.getElementById('response-error').classList.add('hidden');
    document.getElementById('response-panel').classList.remove('hidden');

    var statusEl = document.getElementById('resp-status');
    statusEl.textContent = result.status_code;
    statusEl.className = 'font-mono font-bold text-lg ' + getStatusColor(result.status_code);

    document.getElementById('resp-time').textContent = result.duration_ms + ' ms';
    document.getElementById('resp-size').textContent = formatBytes(result.size_bytes);

    var headersHtml = '';
    Object.keys(result.headers || {}).forEach(function (key) {
      headersHtml += '<div><span class="text-indigo-300">' + escapeHtml(key) + '</span>: ' + escapeHtml(result.headers[key]) + '</div>';
    });
    document.getElementById('resp-headers').innerHTML = headersHtml;

    var body = result.body || '';
    try {
      var parsed = JSON.parse(body);
      body = JSON.stringify(parsed, null, 2);
    } catch (e) { /* not JSON, show raw */ }
    document.getElementById('resp-body').textContent = body;
  }

  function showError(message) {
    document.getElementById('response-placeholder').classList.add('hidden');
    document.getElementById('response-panel').classList.add('hidden');
    document.getElementById('response-error').classList.remove('hidden');
    document.getElementById('response-error').querySelector('div').textContent = message;
  }

  function getStatusColor(code) {
    if (code >= 200 && code < 300) return 'text-green-400';
    if (code >= 300 && code < 400) return 'text-blue-400';
    if (code >= 400 && code < 500) return 'text-yellow-400';
    return 'text-red-400';
  }

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // --- History ---

  async function loadHistory() {
    try {
      var resp = await fetch('/api/history');
      var history = await resp.json();
      var container = document.getElementById('history-list');
      container.innerHTML = '';

      history.forEach(function (item) {
        var div = document.createElement('div');
        div.className = 'p-2 rounded bg-gray-800 hover:bg-gray-750 cursor-pointer text-xs space-y-1 border border-gray-700';
        div.innerHTML =
          '<div class="flex items-center gap-2">' +
            '<span class="font-mono font-bold ' + getMethodColor(item.method) + '">' + item.method + '</span>' +
            '<span class="' + getStatusColor(item.status_code) + ' font-mono">' + (item.status_code || '—') + '</span>' +
          '</div>' +
          '<div class="text-gray-400 truncate">' + escapeHtml(item.url) + '</div>' +
          '<div class="text-gray-500">' + formatTimestamp(item.created_at) + ' · ' + (item.duration_ms || 0) + 'ms</div>';
        div.addEventListener('click', function () { loadRequestIntoBuilder(item); });
        container.appendChild(div);
      });
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  }

  window.clearHistory = async function () {
    if (!confirm('Clear all history?')) return;
    try {
      await fetch('/api/history', { method: 'DELETE' });
    } catch (e) {
      console.error('Failed to clear history:', e);
    }
    loadHistory();
  };

  // --- Collections ---

  async function loadCollections() {
    try {
      var resp = await fetch('/api/collections');
      var items = await resp.json();
      var container = document.getElementById('collections-list');
      container.innerHTML = '';

      var grouped = {};
      items.forEach(function (item) {
        if (!grouped[item.collection_name]) grouped[item.collection_name] = [];
        grouped[item.collection_name].push(item);
      });

      Object.keys(grouped).forEach(function (name) {
        var section = document.createElement('div');
        section.className = 'mb-3';
        section.innerHTML = '<div class="text-xs font-bold text-gray-400 uppercase mb-1 px-1">' + escapeHtml(name) + '</div>';

        grouped[name].forEach(function (item) {
          var row = document.createElement('div');
          row.className = 'flex items-center justify-between p-1.5 rounded hover:bg-gray-800 cursor-pointer group';
          row.innerHTML =
            '<div class="flex items-center gap-2 min-w-0">' +
              '<span class="font-mono text-xs font-bold ' + getMethodColor(item.method) + '">' + item.method + '</span>' +
              '<span class="text-xs text-gray-300 truncate">' + escapeHtml(item.request_name) + '</span>' +
            '</div>' +
            '<button class="text-red-400 hover:text-red-300 text-xs opacity-0 group-hover:opacity-100 shrink-0" data-id="' + item.id + '">×</button>';
          row.querySelector('button').addEventListener('click', function (e) {
            e.stopPropagation();
            deleteCollectionItem(item.id);
          });
          row.addEventListener('click', function () { loadRequestIntoBuilder(item); });
          section.appendChild(row);
        });

        container.appendChild(section);
      });
    } catch (e) {
      console.error('Failed to load collections:', e);
    }
  }

  window.saveToCollection = async function () {
    var collectionName = document.getElementById('save-collection-name').value.trim();
    var requestName = document.getElementById('save-request-name').value.trim();
    if (!collectionName || !requestName) {
      alert('Please enter both collection name and request name');
      return;
    }

    var data = collectRequestData();
    data.collection_name = collectionName;
    data.request_name = requestName;

    try {
      var resp = await fetch('/api/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!resp.ok) {
        var err = await resp.json();
        alert(err.error || 'Failed to save');
        return;
      }
      loadCollections();
    } catch (e) {
      alert('Failed to save to collection: ' + e.message);
    }
  };

  async function deleteCollectionItem(id) {
    try {
      await fetch('/api/collections/' + id, { method: 'DELETE' });
    } catch (e) {
      console.error('Failed to delete collection item:', e);
    }
    loadCollections();
  }

  // --- Environments ---

  async function loadEnvironments() {
    try {
      var resp = await fetch('/api/environments');
      environments = await resp.json();
      renderEnvironmentsList();
      updateEnvSelector();
    } catch (e) {
      console.error('Failed to load environments:', e);
    }
  }

  function renderEnvironmentsList() {
    var container = document.getElementById('environments-list');
    container.innerHTML = '';

    environments.forEach(function (env) {
      var div = document.createElement('div');
      div.className = 'flex items-center justify-between p-2 rounded bg-gray-800 border border-gray-700 text-xs';
      var varsCount = Object.keys(env.variables || {}).length;
      div.innerHTML =
        '<div>' +
          '<span class="font-medium text-gray-200">' + escapeHtml(env.name) + '</span>' +
          '<span class="text-gray-500 ml-2">(' + varsCount + ' vars)</span>' +
        '</div>' +
        '<button class="text-red-400 hover:text-red-300" data-id="' + env.id + '">×</button>';
      div.querySelector('button').addEventListener('click', function () {
        deleteEnvironment(env.id);
      });
      container.appendChild(div);
    });
  }

  function updateEnvSelector() {
    var select = document.getElementById('active-env');
    var currentValue = select.value;
    select.innerHTML = '<option value="">None</option>';
    environments.forEach(function (env) {
      var opt = document.createElement('option');
      opt.value = env.id;
      opt.textContent = env.name;
      select.appendChild(opt);
    });
    select.value = currentValue;
    if (!select.dataset.listenerAttached) {
      select.dataset.listenerAttached = 'true';
      select.addEventListener('change', function () {
        var id = parseInt(select.value);
        activeEnvironment = environments.find(function (e) { return e.id === id; }) || null;
      });
    }
  }

  window.addEnvVar = function () {
    var container = document.getElementById('env-vars');
    var row = document.createElement('div');
    row.className = 'flex gap-1 items-center';
    row.innerHTML =
      '<input type="text" placeholder="Variable name" class="env-key flex-1 bg-gray-700 rounded px-2 py-1 text-sm border border-gray-600 focus:outline-none focus:border-indigo-500">' +
      '<input type="text" placeholder="Value" class="env-value flex-1 bg-gray-700 rounded px-2 py-1 text-sm border border-gray-600 focus:outline-none focus:border-indigo-500">' +
      '<button class="text-red-400 hover:text-red-300 text-sm px-1" onclick="this.parentElement.remove()">×</button>';
    container.appendChild(row);
  };

  window.saveEnvironment = async function () {
    var name = document.getElementById('env-name').value.trim();
    if (!name) {
      alert('Please enter an environment name');
      return;
    }

    var variables = {};
    document.querySelectorAll('#env-vars .flex.gap-1').forEach(function (row) {
      var key = row.querySelector('.env-key').value.trim();
      var value = row.querySelector('.env-value').value;
      if (key) variables[key] = value;
    });

    await fetch('/api/environments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, variables: variables })
    });

    document.getElementById('env-name').value = '';
    document.getElementById('env-vars').innerHTML = '';
    loadEnvironments();
  };

  async function deleteEnvironment(id) {
    try {
      await fetch('/api/environments/' + id, { method: 'DELETE' });
    } catch (e) {
      console.error('Failed to delete environment:', e);
    }
    loadEnvironments();
  }

  // --- Load Request Into Builder ---

  function loadRequestIntoBuilder(item) {
    document.getElementById('req-method').value = item.method || 'GET';
    document.getElementById('req-url').value = item.url || '';
    document.getElementById('req-body').value = item.body || '';

    var bodyType = item.body_type || 'json';
    var radio = document.querySelector('input[name="body-type"][value="' + bodyType + '"]');
    if (radio) radio.checked = true;

    var headersList = document.getElementById('headers-list');
    headersList.innerHTML = '';
    var headers = item.headers || [];
    if (typeof headers === 'string') {
      try { headers = JSON.parse(headers); } catch (e) { headers = []; }
    }
    if (headers.length === 0) {
      addHeaderRow();
    } else {
      headers.forEach(function (h) {
        addHeaderRow();
        var rows = headersList.querySelectorAll('.flex.gap-1');
        var lastRow = rows[rows.length - 1];
        lastRow.querySelector('.kv-key').value = h.key || '';
        lastRow.querySelector('.kv-value').value = h.value || '';
      });
    }

    var paramsList = document.getElementById('params-list');
    paramsList.innerHTML = '';
    var params = item.params || [];
    if (typeof params === 'string') {
      try { params = JSON.parse(params); } catch (e) { params = []; }
    }
    if (params.length === 0) {
      addParamRow();
    } else {
      params.forEach(function (p) {
        addParamRow();
        var rows = paramsList.querySelectorAll('.flex.gap-1');
        var lastRow = rows[rows.length - 1];
        lastRow.querySelector('.kv-key').value = p.key || '';
        lastRow.querySelector('.kv-value').value = p.value || '';
      });
    }
  }

  // --- Utilities ---

  function getMethodColor(method) {
    var colors = {
      GET: 'text-green-400',
      POST: 'text-blue-400',
      PUT: 'text-yellow-400',
      PATCH: 'text-orange-400',
      DELETE: 'text-red-400',
      HEAD: 'text-purple-400',
      OPTIONS: 'text-gray-400'
    };
    return colors[method] || 'text-gray-400';
  }

  function formatTimestamp(ts) {
    if (!ts) return '';
    var d = new Date(ts + 'Z');
    return d.toLocaleTimeString();
  }

})();
