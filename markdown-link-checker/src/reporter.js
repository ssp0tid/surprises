const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  dim: '\x1b[2m'
};

const symbols = {
  valid: '✓',
  broken: '✗',
  skipped: '○',
  info: 'ℹ'
};

/**
 * Format output without colors
 */
function noColor(str) {
  return str;
}

/**
 * Reporter class for formatting link check results
 */
class Reporter {
  constructor(options = {}) {
    this.useColor = options.color !== false;
    this.verbose = options.verbose || false;
    this.color = this.useColor ? (s) => s : noColor;
  }

  formatStatus(status) {
    switch (status) {
      case 'valid':
        return `${colors.green}${symbols.valid}${colors.reset}`;
      case 'broken':
        return `${colors.red}${symbols.broken}${colors.reset}`;
      case 'timeout':
      case 'error':
        return `${colors.yellow}${symbols.skipped}${colors.reset}`;
      default:
        return `${colors.dim}${symbols.skipped}${colors.reset}`;
    }
  }

  formatUrl(url, status) {
    if (!this.useColor) {
      return url;
    }
    switch (status) {
      case 'valid':
        return `${colors.green}${url}${colors.reset}`;
      case 'broken':
        return `${colors.red}${url}${colors.reset}`;
      default:
        return `${colors.yellow}${url}${colors.reset}`;
    }
  }

  /**
   * Report results for a single file
   */
  reportFile(filePath, links) {
    const lines = [];
    const fileName = path.basename(filePath);
    const brokenLinks = links.filter(l => l.status === 'broken');
    const validLinks = links.filter(l => l.status === 'valid');

    if (brokenLinks.length > 0) {
      lines.push(`${this.formatStatus('broken')} ${fileName} (${brokenLinks.length} broken link${brokenLinks.length > 1 ? 's' : ''})`);
      for (const link of brokenLinks) {
        const reason = link.error || `HTTP ${link.code}`;
        lines.push(`  ${this.formatStatus('broken')} ${this.formatUrl(link.url, 'broken')} (line ${link.line}) - ${reason}`);
      }
    } else if (this.verbose) {
      lines.push(`${this.formatStatus('valid')} ${fileName} (${validLinks.length} link${validLinks.length !== 1 ? 's' : ''} checked)`);
      for (const link of validLinks) {
        lines.push(`  ${this.formatStatus('valid')} ${this.formatUrl(link.url, 'valid')}`);
      }
    } else {
      lines.push(`${this.formatStatus('valid')} ${fileName} (${validLinks.length} link${validLinks.length !== 1 ? 's' : ''} checked)`);
    }

    return lines.join('\n');
  }

  /**
   * Report summary
   */
  reportSummary(results) {
    const totalFiles = results.length;
    const totalLinks = results.reduce((sum, r) => sum + r.links.length, 0);
    const validLinks = results.reduce((sum, r) => sum + r.links.filter(l => l.status === 'valid').length, 0);
    const brokenLinks = results.reduce((sum, r) => sum + r.links.filter(l => l.status === 'broken').length, 0);

    const lines = [];
    lines.push('');
    if (brokenLinks > 0) {
      lines.push(`${this.formatStatus('broken')} Found ${brokenLinks} broken link${brokenLinks > 1 ? 's' : ''} in ${totalFiles} file${totalFiles > 1 ? 's' : ''}`);
    } else {
      lines.push(`${this.formatStatus('valid')} All links valid (${totalLinks} checked in ${totalFiles} file${totalFiles > 1 ? 's' : ''})`);
    }

    return lines.join('\n');
  }

  /**
   * Generate JSON output
   */
  toJSON(results) {
    const output = {
      scannedAt: new Date().toISOString(),
      files: results.map(r => ({
        file: r.file,
        links: r.links.map(l => ({
          url: l.url,
          type: l.type,
          status: l.status,
          line: l.line,
          code: l.code,
          error: l.error
        }))
      })),
      summary: {
        totalFiles: results.length,
        totalLinks: results.reduce((sum, r) => sum + r.links.length, 0),
        valid: results.reduce((sum, r) => sum + r.links.filter(l => l.status === 'valid').length, 0),
        broken: results.reduce((sum, r) => sum + r.links.filter(l => l.status === 'broken').length, 0)
      }
    };

    return JSON.stringify(output, null, 2);
  }
}

module.exports = { Reporter };