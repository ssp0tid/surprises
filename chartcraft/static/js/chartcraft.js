const PALETTES = {
    vibrant:    ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
    pastel:     ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#E8BAFF', '#FFD9BA'],
    earth:      ['#8B4513', '#D2691E', '#DAA520', '#556B2F', '#2E8B57', '#4682B4'],
    ocean:      ['#001f3f', '#0074D9', '#7FDBFF', '#39CCCC', '#3D9970', '#2ECC40'],
    monochrome: ['#111111', '#333333', '#555555', '#777777', '#999999', '#BBBBBB']
};

let parsedData = null;
let chartInstance = null;
let inputMode = 'csv';
let renderTimeout = null;

function setInputMode(mode) {
    inputMode = mode;
    const btnCsv = document.getElementById('btn-csv');
    const btnJson = document.getElementById('btn-json');
    const input = document.getElementById('data-input');

    if (mode === 'csv') {
        btnCsv.className = 'px-3 py-1 bg-indigo-600 text-white rounded text-sm';
        btnJson.className = 'px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm';
        input.placeholder = 'Paste your CSV data here...';
    } else {
        btnJson.className = 'px-3 py-1 bg-indigo-600 text-white rounded text-sm';
        btnCsv.className = 'px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm';
        input.placeholder = 'Paste your JSON array here...\n[\n  {"name": "A", "value": 10},\n  {"name": "B", "value": 20}\n]';
    }
}

function detectDelimiter(text) {
    const firstLine = text.split('\n')[0];
    const delimiters = [',', '\t', ';'];
    let best = ',';
    let maxCount = 0;
    for (const d of delimiters) {
        const count = (firstLine.match(new RegExp(d === '\t' ? '\\t' : (d === ',' ? ',' : ';'), 'g')) || []).length;
        if (count > maxCount) {
            maxCount = count;
            best = d;
        }
    }
    return best;
}

function parseCSV(text) {
    const lines = text.trim().split('\n').filter(l => l.trim());
    if (lines.length < 2) throw new Error('CSV needs at least a header row and one data row');

    const delimiter = detectDelimiter(text);
    const headers = lines[0].split(delimiter).map(h => h.trim().replace(/^["']|["']$/g, ''));

    if (headers.some(h => h === '')) throw new Error('CSV headers cannot be empty');
    if (new Set(headers).size !== headers.length) throw new Error('CSV headers must be unique');

    const rows = [];

    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(delimiter).map(v => {
            v = v.trim().replace(/^["']|["']$/g, '');
            const num = Number(v);
            return isNaN(num) ? v : num;
        });
        if (values.length !== headers.length) {
            throw new Error(`Row ${i} has ${values.length} columns, expected ${headers.length}`);
        }
        rows.push(values);
    }

    return { headers, rows };
}

function parseJSON(text) {
    const arr = JSON.parse(text);
    if (!Array.isArray(arr) || arr.length === 0) throw new Error('JSON must be a non-empty array of objects');

    const headers = Object.keys(arr[0]);
    const rows = arr.map(obj => headers.map(h => {
        const v = obj[h];
        const num = Number(v);
        return (v !== null && v !== '' && !isNaN(num)) ? num : v;
    }));

    return { headers, rows };
}

function parseData() {
    const input = document.getElementById('data-input').value;
    const errorEl = document.getElementById('parse-error');
    const previewEl = document.getElementById('data-preview');

    errorEl.classList.add('hidden');
    previewEl.classList.add('hidden');

    if (!input.trim()) {
        showError('Please paste some data first');
        return;
    }

    try {
        parsedData = inputMode === 'csv' ? parseCSV(input) : parseJSON(input);
    } catch (e) {
        showError(e.message);
        return;
    }

    renderPreviewTable();
    populateAxisSelectors();
    scheduleRender();
}

function showError(msg) {
    const errorEl = document.getElementById('parse-error');
    errorEl.textContent = msg;
    errorEl.classList.remove('hidden');
}

function renderPreviewTable() {
    const table = document.getElementById('preview-table');
    const previewEl = document.getElementById('data-preview');
    const displayRows = parsedData.rows.slice(0, 10);

    let html = '<thead class="bg-gray-100"><tr>';
    html += parsedData.headers.map(h => `<th class="px-2 py-1 border text-left">${h}</th>`).join('');
    html += '</tr></thead><tbody>';
    for (const row of displayRows) {
        html += '<tr>' + row.map(v => `<td class="px-2 py-1 border">${v}</td>`).join('') + '</tr>';
    }
    html += '</tbody>';

    table.innerHTML = html;
    previewEl.classList.remove('hidden');
}

function populateAxisSelectors() {
    const xSelect = document.getElementById('x-axis');
    const ySelect = document.getElementById('y-axis');

    xSelect.innerHTML = parsedData.headers.map((h, i) =>
        `<option value="${i}">${h}</option>`
    ).join('');

    ySelect.innerHTML = parsedData.headers.map((h, i) =>
        `<option value="${i}" ${i > 0 ? 'selected' : ''}>${h}</option>`
    ).join('');
}

function scheduleRender() {
    if (renderTimeout) clearTimeout(renderTimeout);
    renderTimeout = setTimeout(renderChart, 300);
}

function buildChartConfig(data, options) {
    const { headers, rows } = data;
    const { type, xIndex, yIndices, title, palette, showLegend, showGrid, showLabels } = options;
    const colors = PALETTES[palette] || PALETTES.vibrant;

    const labels = rows.map(r => r[xIndex]);
    const datasets = yIndices.map((yi, i) => ({
        label: headers[yi],
        data: rows.map(r => r[yi]),
        backgroundColor: type === 'line' || type === 'scatter' || type === 'radar'
            ? colors[i % colors.length] + '33'
            : colors.slice(0, rows.length).length > 0
                ? (yIndices.length === 1 ? colors.slice(0, rows.length) : colors[i % colors.length])
                : colors[i % colors.length],
        borderColor: colors[i % colors.length],
        borderWidth: 2,
        fill: type === 'radar'
    }));

    const config = {
        type,
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: { display: !!title, text: title || '' },
                legend: { display: showLegend }
            }
        }
    };

    if (['bar', 'line', 'scatter'].includes(type)) {
        config.options.scales = {
            x: { grid: { display: showGrid } },
            y: { grid: { display: showGrid } }
        };
    }

    if (type === 'scatter') {
        config.data.labels = undefined;
        config.data.datasets = [{
            label: `${headers[xIndex]} vs ${headers[yIndices[0]]}`,
            data: rows.map(r => ({ x: r[xIndex], y: r[yIndices[0]] })),
            backgroundColor: colors[0] + '88',
            borderColor: colors[0],
            borderWidth: 1
        }];
    }

    return config;
}

function renderChart() {
    if (!parsedData) return;

    const canvas = document.getElementById('chart-canvas');
    const noDataMsg = document.getElementById('no-data-msg');
    noDataMsg.classList.add('hidden');

    const type = document.getElementById('chart-type').value;
    const palette = document.getElementById('palette').value;
    const xIndex = parseInt(document.getElementById('x-axis').value);
    const ySelect = document.getElementById('y-axis');
    const yIndices = Array.from(ySelect.selectedOptions).map(o => parseInt(o.value));
    const title = document.getElementById('chart-title').value;
    const showLegend = document.getElementById('show-legend').checked;
    const showGrid = document.getElementById('show-grid').checked;
    const showLabels = document.getElementById('show-labels').checked;

    if (yIndices.length === 0) return;

    const colCount = parsedData.headers.length;
    if (isNaN(xIndex) || xIndex < 0 || xIndex >= colCount) return;
    const validYIndices = yIndices.filter(i => !isNaN(i) && i >= 0 && i < colCount);
    if (validYIndices.length === 0) return;

    const config = buildChartConfig(parsedData, {
        type, xIndex, yIndices: validYIndices, title, palette, showLegend, showGrid, showLabels
    });

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(canvas.getContext('2d'), config);
}

function exportPNG() {
    if (!chartInstance) {
        alert('No chart to export. Parse data and configure a chart first.');
        return;
    }
    const link = document.createElement('a');
    link.download = (document.getElementById('chart-title').value || 'chart') + '.png';
    link.href = chartInstance.toBase64Image();
    link.click();
}

async function saveToServer() {
    if (!chartInstance || !parsedData) {
        alert('No chart to save. Parse data and configure a chart first.');
        return;
    }

    const title = document.getElementById('chart-title').value || 'Untitled Chart';
    const rawData = document.getElementById('data-input').value;
    const thumbnail = chartInstance.toBase64Image();

    const type = document.getElementById('chart-type').value;
    const palette = document.getElementById('palette').value;
    const xIndex = parseInt(document.getElementById('x-axis').value);
    const ySelect = document.getElementById('y-axis');
    const yIndices = Array.from(ySelect.selectedOptions).map(o => parseInt(o.value));
    const showLegend = document.getElementById('show-legend').checked;
    const showGrid = document.getElementById('show-grid').checked;
    const showLabels = document.getElementById('show-labels').checked;

    const config = buildChartConfig(parsedData, {
        type, xIndex, yIndices, title, palette,
        showLegend, showGrid, showLabels
    });

    const resultEl = document.getElementById('share-result');

    try {
        const res = await fetch('/api/charts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                data: rawData,
                config,
                thumbnail_base64: thumbnail
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Failed to save');
        }

        const result = await res.json();
        resultEl.innerHTML = `Saved! <a href="${result.url}" class="text-indigo-600 hover:underline">View shared chart</a>`;
        resultEl.classList.remove('hidden');
    } catch (err) {
        resultEl.textContent = 'Error: ' + err.message;
        resultEl.className = 'mt-2 text-sm text-red-600';
        resultEl.classList.remove('hidden');
    }
}
