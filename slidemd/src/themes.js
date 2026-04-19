export const themes = {
  default: {
    name: 'default',
    displayName: 'Default (Light)',
    vars: {
      '--bg-primary': '#ffffff',
      '--bg-secondary': '#f8f9fa',
      '--text-primary': '#2c3e50',
      '--text-secondary': '#7f8c8d',
      '--accent': '#3498db',
      '--accent-secondary': '#2ecc71',
      '--font-heading': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-body': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-mono': 'Consolas, "Liberation Mono", Menlo, monospace',
      '--heading-weight': '700',
      '--body-weight': '400',
      '--base-size': '48px',
      '--heading-scale': '1.5',
      '--line-height': '1.4',
      '--transition-duration': '300ms',
      '--slide-padding': '60px'
    }
  },
  dark: {
    name: 'dark',
    displayName: 'Dark',
    vars: {
      '--bg-primary': '#1a1a2e',
      '--bg-secondary': '#16213e',
      '--text-primary': '#eaeaea',
      '--text-secondary': '#a0a0a0',
      '--accent': '#e94560',
      '--accent-secondary': '#0f3460',
      '--font-heading': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-body': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-mono': 'Consolas, "Liberation Mono", Menlo, monospace',
      '--heading-weight': '700',
      '--body-weight': '400',
      '--base-size': '48px',
      '--heading-scale': '1.5',
      '--line-height': '1.4',
      '--transition-duration': '300ms',
      '--slide-padding': '60px'
    }
  },
  minimal: {
    name: 'minimal',
    displayName: 'Minimal',
    vars: {
      '--bg-primary': '#ffffff',
      '--bg-secondary': '#fafafa',
      '--text-primary': '#111111',
      '--text-secondary': '#666666',
      '--accent': '#000000',
      '--accent-secondary': '#333333',
      '--font-heading': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-body': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-mono': 'system-ui, monospace',
      '--heading-weight': '300',
      '--body-weight': '300',
      '--base-size': '42px',
      '--heading-scale': '1.4',
      '--line-height': '1.6',
      '--transition-duration': '200ms',
      '--slide-padding': '80px'
    }
  },
  gradient: {
    name: 'gradient',
    displayName: 'Gradient',
    vars: {
      '--bg-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      '--bg-secondary': 'linear-gradient(135deg, #764ba2 0%, #6B8DD6 100%)',
      '--text-primary': '#ffffff',
      '--text-secondary': 'rgba(255,255,255,0.8)',
      '--accent': '#ffd700',
      '--accent-secondary': '#ff6b6b',
      '--font-heading': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-body': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--font-mono': 'Consolas, "Liberation Mono", Menlo, monospace',
      '--heading-weight': '700',
      '--body-weight': '400',
      '--base-size': '48px',
      '--heading-scale': '1.5',
      '--line-height': '1.4',
      '--transition-duration': '400ms',
      '--slide-padding': '60px'
    }
  },
  serif: {
    name: 'serif',
    displayName: 'Serif',
    vars: {
      '--bg-primary': '#fdfbf7',
      '--bg-secondary': '#f5f2eb',
      '--text-primary': '#2c2416',
      '--text-secondary': '#6b5d4d',
      '--accent': '#8b4513',
      '--accent-secondary': '#d2691e',
      '--font-heading': 'Georgia, "Times New Roman", serif',
      '--font-body': 'Georgia, "Times New Roman", serif',
      '--font-mono': '"Courier New", Courier, monospace',
      '--heading-weight': '400',
      '--body-weight': '400',
      '--base-size': '44px',
      '--heading-scale': '1.3',
      '--line-height': '1.5',
      '--transition-duration': '350ms',
      '--slide-padding': '60px'
    }
  }
};

export function getTheme(name) {
  if (themes[name]) {
    return themes[name];
  }
  return themes.default;
}

export function getAllThemes() {
  return Object.keys(themes);
}

export function validateTheme(theme) {
  if (!theme || typeof theme !== 'object') {
    return false;
  }
  if (!theme.name || typeof theme.name !== 'string') {
    return false;
  }
  return true;
}

export function mergeTheme(baseName, overrides) {
  const base = getTheme(baseName);
  if (!overrides || typeof overrides !== 'object') {
    return base;
  }
  const merged = JSON.parse(JSON.stringify(base));
  if (overrides.vars) {
    merged.vars = { ...merged.vars, ...overrides.vars };
  }
  if (overrides.name) {
    merged.name = overrides.name;
  }
  return merged;
}