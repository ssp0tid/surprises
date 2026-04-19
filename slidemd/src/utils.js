export function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  const htmlEscapes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };
  return str.replace(/[&<>"']/g, char => htmlEscapes[char]);
}

export function escapeHtmlAttr(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/`/g, '&#x60;');
}

export function debounce(fn, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

export function generateId() {
  return Math.random().toString(36).substring(2, 11);
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function parseAspectRatio(ratio) {
  const parts = ratio.split(':');
  if (parts.length !== 2) {
    return { width: 16, height: 9 };
  }
  const width = parseInt(parts[0], 10);
  const height = parseInt(parts[1], 10);
  if (isNaN(width) || isNaN(height) || width <= 0 || height <= 0) {
    return { width: 16, height: 9 };
  }
  return { width, height };
}

export function isValidPath(path) {
  if (!path || typeof path !== 'string') return false;
  return path.trim().length > 0;
}

export function normalizeLineEndings(str) {
  return str.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

export function cleanWhitespace(str) {
  return str.replace(/[\t\s]+/g, ' ').trim();
}

export function isEmpty(str) {
  return !str || str.trim().length === 0;
}