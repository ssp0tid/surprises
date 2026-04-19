const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Common user agent to avoid being blocked by servers
const DEFAULT_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (compatible; MarkdownLinkChecker/1.0)'
};

/**
 * Validate a link (internal or external)
 * @param {string} link - The link URL
 * @param {string} basePath - Base directory for relative links
 * @param {number} timeout - Request timeout in ms
 * @returns {Promise<{status: string, code?: number, error?: string}>}
 */
async function validateLink(link, basePath, timeout = 5000) {
  // Check if external link
  if (link.startsWith('http://') || link.startsWith('https://')) {
    return validateExternal(link, timeout);
  }

  // Handle internal links
  return validateInternal(link, basePath);
}

/**
 * Validate an external URL
 * @param {string} url - The URL
 * @param {number} timeout - Request timeout
 * @returns {Promise<{status: string, code?: number, error?: string}>}
 */
async function validateExternal(url, timeout = 5000) {
  try {
    const response = await axios.head(url, {
      timeout,
      maxRedirects: 3,
      validateStatus: (status) => status < 400,
      headers: { ...DEFAULT_HEADERS }
    });
    if (response.status >= 200 && response.status < 300) {
      return { status: 'valid', code: response.status };
    }
    const getResponse = await axios.get(url, {
      timeout,
      maxRedirects: 3,
      validateStatus: (status) => status < 400,
      headers: { ...DEFAULT_HEADERS }
    });
    return { status: getResponse.status >= 200 && getResponse.status < 300 ? 'valid' : 'broken', code: getResponse.status };
  } catch (err) {
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
      return { status: 'timeout', error: 'Request timed out' };
    }
    if (err.code === 'ENOTFOUND' || err.code === 'EAI_AGAIN') {
      return { status: 'error', error: 'DNS resolution failed' };
    }
    if (err.code === 'CERT_HAS_EXPIRED' || err.code === 'UNABLE_TO_VERIFY_LEAF_SIGNATURE') {
      return { status: 'error', error: 'SSL certificate error' };
    }
    if (err.code === 'ECONNREFUSED') {
      return { status: 'error', error: 'Connection refused' };
    }
    if (err.response) {
      return { status: 'broken', code: err.response.status };
    }
    return { status: 'error', error: err.message };
  }
}

/**
 * Validate an internal link (file or anchor)
 * @param {string} link - The link path
 * @param {string} basePath - Base directory
 * @returns {Promise<{status: string, error?: string}>}
 */
async function validateInternal(link, basePath) {
  // Parse anchor from link: ./file.md#section
  let filePath = link;
  let anchor = '';

  const anchorIndex = link.lastIndexOf('#');
  if (anchorIndex !== -1) {
    filePath = link.slice(0, anchorIndex);
    anchor = link.slice(anchorIndex + 1);
  }

  // Handle relative paths
  let fullPath;
  if (filePath.startsWith('/')) {
    fullPath = filePath;
  } else if (filePath.startsWith('./')) {
    fullPath = path.join(basePath, filePath.slice(2));
  } else if (filePath === '' || filePath === '.') {
    fullPath = basePath;
  } else {
    fullPath = path.join(basePath, filePath);
  }

  // Normalize and resolve
  fullPath = path.normalize(fullPath);

  // Check if file exists
  if (!fs.existsSync(fullPath)) {
    return { status: 'broken', error: 'File not found' };
  }

  // If anchor present, check for heading in file
  if (anchor) {
    try {
      const content = fs.readFileSync(fullPath, 'utf8');
      // Simple heading check - # heading or ## heading
      const headingRegex = new RegExp(`^#{1,6}\\s+${escapeRegex(anchor)}`, 'im');
      if (!headingRegex.test(content)) {
        // Also check for HTML id anchors
        const htmlIdRegex = new RegExp(`id=["']${escapeRegex(anchor)}["']`, 'i');
        if (!htmlIdRegex.test(content)) {
          return { status: 'broken', error: 'Anchor not found' };
        }
      }
    } catch {
      return { status: 'broken', error: 'Cannot read file' };
    }
  }

  return { status: 'valid' };
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Validate multiple links concurrently
 * @param {Array} links - Array of links to validate
 * @param {string} basePath - Base directory
 * @param {number} concurrency - Max concurrent requests
 * @param {number} timeout - Request timeout
 * @returns {Promise<Array>} Array of validated links
 */
async function validateLinks(links, basePath, concurrency = 10, timeout = 5000) {
  const results = [];
  const queue = [...links];
  let active = 0;

  async function processLink() {
    while (true) {
      const idx = queue.length - 1;
      if (idx < 0) break;
      const link = queue.splice(idx, 1)[0];
      if (!link) break;
      active++;
      const result = await validateLink(link.url, basePath, timeout);
      results.push({ ...link, ...result });
      active--;
    }
  }

  const workers = [];
  const numWorkers = Math.min(concurrency, links.length);
  for (let i = 0; i < numWorkers; i++) {
    workers.push(processLink());
  }

  await Promise.all(workers);
  return results;
}

module.exports = { validateLink, validateLinks };