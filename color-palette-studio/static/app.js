document.addEventListener('DOMContentLoaded', init);

let currentColors = [];

function init() {
    document.getElementById('generate-btn').addEventListener('click', generatePalette);
    document.getElementById('random-btn').addEventListener('click', randomBase);
    document.getElementById('check-contrast-btn').addEventListener('click', checkContrast);
    document.getElementById('save-btn').addEventListener('click', savePalette);
    document.getElementById('base-color').addEventListener('input', syncColorToHex);
    document.getElementById('base-color-hex').addEventListener('change', syncHexToColor);

    document.querySelectorAll('.export-buttons button').forEach(btn => {
        btn.addEventListener('click', () => exportPalette(btn.dataset.format));
    });

    generatePalette();
}

function syncColorToHex() {
    document.getElementById('base-color-hex').value = document.getElementById('base-color').value;
}

function syncHexToColor() {
    const hex = document.getElementById('base-color-hex').value.trim();
    if (/^#[0-9a-fA-F]{6}$/.test(hex)) {
        document.getElementById('base-color').value = hex;
    }
}

async function generatePalette() {
    const base = document.getElementById('base-color').value.replace('#', '');
    const rule = document.getElementById('harmony-rule').value;

    try {
        const res = await fetch(`/api/harmony?base=${base}&rule=${rule}`);
        const json = await res.json();
        if (!json.success) {
            showError(json.error);
            return;
        }
        currentColors = json.data.colors;
        renderSwatches(currentColors);
        updateContrastSelects(currentColors);
        clearExport();
    } catch (err) {
        showError('Failed to generate palette.');
    }
}

async function randomBase() {
    try {
        const res = await fetch('/api/random');
        const json = await res.json();
        if (json.success) {
            const hex = json.data.hex;
            document.getElementById('base-color').value = hex;
            document.getElementById('base-color-hex').value = hex;
            generatePalette();
        }
    } catch (err) {
        showError('Failed to get random color.');
    }
}

function renderSwatches(colors) {
    const container = document.getElementById('swatches');
    container.innerHTML = '';

    colors.forEach(color => {
        const swatch = document.createElement('div');
        swatch.className = 'swatch';
        swatch.style.backgroundColor = color;
        swatch.setAttribute('role', 'button');
        swatch.setAttribute('aria-label', `Color ${color}. Click to copy.`);
        swatch.tabIndex = 0;

        const label = document.createElement('span');
        label.className = 'swatch-label';
        label.textContent = color;
        swatch.appendChild(label);

        const tooltip = document.createElement('span');
        tooltip.className = 'swatch-tooltip';
        const rgb = hexToRgb(color);
        const hsl = hexToHsl(color);
        tooltip.textContent = `RGB(${rgb.r}, ${rgb.g}, ${rgb.b}) HSL(${hsl.h}°, ${hsl.s}%, ${hsl.l}%)`;
        swatch.appendChild(tooltip);

        swatch.addEventListener('click', () => copyToClipboard(color, swatch));
        swatch.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                copyToClipboard(color, swatch);
            }
        });

        container.appendChild(swatch);
    });
}

function copyToClipboard(text, element) {
    navigator.clipboard.writeText(text).then(() => {
        const feedback = document.createElement('span');
        feedback.className = 'copy-feedback';
        feedback.textContent = 'Copied!';
        element.appendChild(feedback);
        setTimeout(() => feedback.remove(), 1000);
    });
}

function updateContrastSelects(colors) {
    const select1 = document.getElementById('contrast-color1');
    const select2 = document.getElementById('contrast-color2');

    [select1, select2].forEach(select => {
        select.innerHTML = '';
        colors.forEach(color => {
            const option = document.createElement('option');
            option.value = color;
            option.textContent = color;
            select.appendChild(option);
        });
    });

    if (colors.length >= 2) {
        select2.selectedIndex = 1;
    }
}

async function checkContrast() {
    const color1 = document.getElementById('contrast-color1').value.replace('#', '');
    const color2 = document.getElementById('contrast-color2').value.replace('#', '');

    if (!color1 || !color2) return;

    try {
        const res = await fetch(`/api/contrast?color1=${color1}&color2=${color2}`);
        const json = await res.json();
        if (!json.success) {
            document.getElementById('contrast-result').textContent = json.error;
            return;
        }

        const { ratio, rating, color1: c1, color2: c2 } = json.data;
        const ratingClass = getRatingClass(rating);

        document.getElementById('contrast-result').innerHTML = `
            <span class="ratio">${ratio}:1</span>
            <span class="rating ${ratingClass}">${rating}</span>
            <div class="contrast-preview">
                <span class="contrast-preview-box" style="background:${c1};color:${c2}">Text on Color 1</span>
                <span class="contrast-preview-box" style="background:${c2};color:${c1}">Text on Color 2</span>
            </div>
        `;
    } catch (err) {
        document.getElementById('contrast-result').textContent = 'Failed to check contrast.';
    }
}

function getRatingClass(rating) {
    switch (rating) {
        case 'AAA': return 'rating-aaa';
        case 'AA': return 'rating-aa';
        case 'AA Large': return 'rating-aa-large';
        default: return 'rating-fail';
    }
}

async function exportPalette(format) {
    if (currentColors.length === 0) return;

    const colorsParam = currentColors.map(c => c.replace('#', '')).join(',');

    try {
        const res = await fetch(`/api/export?colors=${colorsParam}&format=${format}`);
        const json = await res.json();
        if (json.success) {
            document.getElementById('export-output').textContent = json.data.output;
        }
    } catch (err) {
        document.getElementById('export-output').textContent = 'Export failed.';
    }
}

function clearExport() {
    document.getElementById('export-output').textContent = '';
}

async function savePalette() {
    const name = document.getElementById('palette-name').value.trim();
    const msgEl = document.getElementById('save-message');

    if (!name) {
        msgEl.textContent = 'Please enter a palette name.';
        msgEl.style.color = '#ff8080';
        return;
    }

    if (currentColors.length === 0) {
        msgEl.textContent = 'Generate a palette first.';
        msgEl.style.color = '#ff8080';
        return;
    }

    try {
        const res = await fetch('/api/palette/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, colors: currentColors }),
        });
        const json = await res.json();
        if (json.success) {
            msgEl.textContent = `Saved "${name}" successfully.`;
            msgEl.style.color = '#4aff8b';
            document.getElementById('palette-name').value = '';
        } else {
            msgEl.textContent = json.error;
            msgEl.style.color = '#ff8080';
        }
    } catch (err) {
        msgEl.textContent = 'Failed to save palette.';
        msgEl.style.color = '#ff8080';
    }
}

function showError(msg) {
    const container = document.getElementById('swatches');
    container.innerHTML = `<p style="color:#ff8080">${msg}</p>`;
}

function hexToRgb(hex) {
    hex = hex.replace('#', '');
    return {
        r: parseInt(hex.substring(0, 2), 16),
        g: parseInt(hex.substring(2, 4), 16),
        b: parseInt(hex.substring(4, 6), 16),
    };
}

function hexToHsl(hex) {
    const { r, g, b } = hexToRgb(hex);
    const rn = r / 255, gn = g / 255, bn = b / 255;
    const max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn);
    const l = (max + min) / 2;
    let h = 0, s = 0;

    if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case rn: h = ((gn - bn) / d + (gn < bn ? 6 : 0)) / 6; break;
            case gn: h = ((bn - rn) / d + 2) / 6; break;
            case bn: h = ((rn - gn) / d + 4) / 6; break;
        }
    }

    return {
        h: Math.round(h * 360),
        s: Math.round(s * 100),
        l: Math.round(l * 100),
    };
}
