# SlideMD - Single-File Markdown Presentation Generator

## Executive Summary

A standalone tool that transforms markdown files into beautiful, self-contained HTML presentations. The output is a single HTML file with zero external dependencies, capable of running directly in any browser without a server.

---

## 1. Concept & Vision

### Core Value Proposition
- **Zero friction**: Drop in a markdown file, get a presentation
- **Truly portable**: Single HTML file works anywhere - email it, USB it, open offline
- **Beautiful by default**: Polished themes without configuration
- **Developer-friendly**: Write slides in the format you already know

### Design Philosophy
- KISS principle: Simple markdown in, gorgeous slides out
- Progressive enhancement: Works everywhere, polished on modern browsers
- Content-first: The markdown is the source of truth

---

## 2. Architecture Overview

### Tool Structure

```
slidemd/
├── src/
│   ├── cli.js              # Command-line interface
│   ├── parser.js           # Markdown parsing + slide extraction
│   ├── renderer.js         # HTML generation
│   ├── themes.js           # Built-in theme definitions
│   ├── keyboard.js         # Keyboard navigation handler
│   ├── presenter.js        # Presenter mode logic
│   ├── notes.js            # Speaker notes extraction
│   └── utils.js            # Helpers (escape, debounce, etc.)
├── themes/                 # CSS theme files (inlined)
│   ├── default.css
│   ├── dark.css
│   ├── minimal.css
│   ├── gradient.css
│   └── serif.css
├── bin/
│   └── slidemd             # Executable entry point
├── package.json
└── README.md
```

### Data Flow

```
Markdown File
     │
     ▼
┌─────────────┐
│  CLI (cli.js) │
└──────┬──────┘
       │ parsed AST
       ▼
┌─────────────┐
│ Parser       │  ──► Extract slides (split on ---)
│ (parser.js)  │  ──► Parse frontmatter (YAML)
│              │  ──► Extract speaker notes (<!-- notes -->)
└──────┬──────┘
       │ structured data
       ▼
┌─────────────┐
│ Renderer     │  ──► Generate slide HTML
│ (renderer.js)│  ──► Inline CSS (selected theme)
│              │  ──► Inline JS (keyboard, presenter)
└──────┬──────┘
       │ complete HTML string
       ▼
   Output HTML File
```

---

## 3. File Structure & Module Design

### 3.1 CLI (`cli.js`)

**Responsibilities**:
- Parse command-line arguments
- Read input markdown file
- Load and validate theme
- Orchestrate parsing → rendering pipeline
- Write output file

**API**:
```javascript
// Command-line usage
// slidemd input.md -o output.html --theme dark

// Programmatic usage
const { generate } = require('slidemd');

async function main() {
  const presentation = await generate('input.md', {
    theme: 'dark',
    title: 'My Presentation',
    author: 'John Doe',
    transition: 'slide' // 'slide' | 'fade' | 'none'
  });

  fs.writeFileSync('output.html', presentation);
  console.log('Generated: output.html');
}
```

**Command-line options**:
| Flag | Description | Default |
|------|-------------|---------|
| `-i, --input <file>` | Input markdown file | Required |
| `-o, --output <file>` | Output HTML file | `{input-name}.html` |
| `-t, --theme <name>` | Theme name | `default` |
| `--title <text>` | Presentation title | From frontmatter or filename |
| `--author <name>` | Author name | From frontmatter |
| `--transition <type>` | Slide transition | `slide` |
| `--aspect <ratio>` | Aspect ratio | `16:9` |
| `--list-themes` | Show available themes | - |
| `-v, --version` | Show version | - |
| `-h, --help` | Show help | - |

### 3.2 Parser (`parser.js`)

**Responsibilities**:
- Split markdown into slides by `---` separator
- Parse YAML frontmatter for metadata
- Extract speaker notes from slide content
- Process markdown to intermediate representation

**Slide Format**:
```markdown
---
title: Introduction
theme: dark
---

# Welcome to SlideMD

This is a beautiful presentation.

<!-- notes
Remember to mention the key features here.
- Zero dependencies
- Single file output
-->

---

# Second Slide

- Item 1
- Item 2

<!-- notes
Keep this slide brief.
-->

---

# Code Example

```javascript
console.log('Hello, world!');
```

<!-- notes
Explain what this code does.
-->
```

**Output Structure**:
```javascript
{
  metadata: {
    title: 'Introduction',
    theme: 'dark',
    author: null,
    transition: 'slide'
  },
  slides: [
    {
      index: 0,
      content: '# Welcome to SlideMD\n\nThis is a beautiful presentation.',
      notes: 'Remember to mention the key features here.\n- Zero dependencies\n- Single file output',
      html: '<h1>Welcome to SlideMD</h1><p>This is a beautiful presentation.</p>'
    },
    // ... more slides
  ]
}
```

**Edge Cases Handled**:
- `---` inside code blocks (use counting: increment on ```{, decrement on }})
- `---` inside HTML comments
- Empty slides (skip or preserve based on config)
- Slide with only notes (valid, renders blank slide)
- Escaped `\- - -` sequence

### 3.3 Renderer (`renderer.js`)

**Responsibilities**:
- Generate complete, self-contained HTML
- Inline theme CSS
- Inline JavaScript for interactivity
- Handle responsive layout
- Generate print styles

**Output HTML Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    /* Inlined theme CSS */
    /* All styles - no external dependencies */
  </style>
</head>
<body>
  <div class="presentation">
    <div class="slides">
      <section class="slide active" data-slide="0">
        <!-- Slide content -->
      </section>
      <!-- More slides -->
    </div>

    <!-- Presenter mode overlay (hidden by default) -->
    <div class="presenter-view">
      <!-- Current slide, next slide, notes, timer -->
    </div>

    <!-- Navigation controls (optional, can be hidden) -->
    <nav class="controls">
      <button class="prev">←</button>
      <span class="slide-counter">1 / 10</span>
      <button class="next">→</button>
    </nav>
  </div>

  <script>
    // All JavaScript inlined
    // No external dependencies
  </script>
</body>
</html>
```

### 3.4 Themes (`themes.js` + CSS files)

**Built-in Themes**:

| Theme | Description |
|-------|-------------|
| `default` | Clean, professional, blue accents |
| `dark` | Dark background, light text |
| `minimal` | Maximum whitespace, subtle typography |
| `gradient` | Vibrant gradient backgrounds |
| `serif` | Classic typography feel |

**Theme Structure**:
```javascript
{
  name: 'default',
  displayName: 'Default (Light)',
  vars: {
    '--bg-primary': '#ffffff',
    '--bg-secondary': '#f8f9fa',
    '--text-primary': '#2c3e50',
    '--text-secondary': '#7f8c8d',
    '--accent': '#3498db',
    '--accent-secondary': '#2ecc71',
    '--font-heading': 'system-ui, sans-serif',
    '--font-body': 'system-ui, sans-serif',
    '--font-mono': 'Consolas, monospace',
    '--heading-weight': '700',
    '--body-weight': '400',
    '--base-size': '48px',       // Base slide text size
    '--heading-scale': '1.5',    // h1 = base * 1.5
    '--line-height': '1.4',
    '--transition-duration': '300ms'
  }
}
```

**CSS Custom Properties**: All themes use CSS variables for consistency and easy customization.

### 3.5 Keyboard Handler (`keyboard.js`)

**Keyboard Shortcuts**:

| Key | Action |
|-----|--------|
| `→` / `Space` / `l` | Next slide |
| `←` / `h` | Previous slide |
| `Home` / `g` | First slide |
| `End` / `G` | Last slide |
| `f` | Toggle fullscreen |
| `p` | Toggle presenter mode |
| `o` | Toggle overview (thumbnail) mode |
| `Esc` | Exit current mode |
| `b` | Blackout screen (blank slide) |
| `t` | Show current time |

**Implementation Notes**:
- Debounce rapid key presses (100ms)
- Prevent default browser behavior for handled keys
- Support keyboard-based presenter notes navigation

### 3.6 Presenter Mode (`presenter.js`)

**Features**:
- Current slide preview (large)
- Next slide preview (smaller)
- Speaker notes display
- Slide timer (elapsed + optional countdown)
- Slide navigation arrows
- Connection status indicator (for sync features)

**Presenter Window** (when opened):
```html
<div class="presenter-view">
  <div class="presenter-header">
    <span class="timer">00:15:30</span>
    <span class="slide-info">Slide 5 of 12</span>
    <button class="exit">Exit Presenter View</button>
  </div>

  <div class="presenter-main">
    <div class="current-slide">
      <!-- Full preview of current slide -->
    </div>
    <div class="side-panel">
      <div class="next-slide">
        <!-- Smaller preview of next slide -->
      </div>
      <div class="notes">
        <h3>Speaker Notes</h3>
        <p>Remember to mention...</p>
      </div>
    </div>
  </div>
</div>
```

**Window Sync** (optional enhancement):
- Open presenter view in second window
- Sync via BroadcastChannel API (same origin)
- Fallback: LocalStorage events for cross-tab sync

### 3.7 Speaker Notes (`notes.js`)

**Syntax**:
```markdown
# Slide Title

Content here.

<!-- notes
Your speaker notes here.
Multiple lines supported.
- Bullet points work
- In notes too
-->

---

# Next Slide
```

**Rendering**:
- Notes extracted and stored in slide data
- Hidden in normal presentation view
- Visible in presenter mode
- Optional: Print notes on separate page (print mode)

---

## 4. Dependencies

### Runtime Dependencies (zero - truly zero!)

The generated HTML has **no external dependencies**. Everything is inlined:
- No external CSS files
- No external JavaScript
- No external fonts (uses system fonts)
- No external images
- No CDN links

### Build Dependencies (dev dependencies only)

```json
{
  "devDependencies": {
    "marked": "^11.0.0",           // Markdown parsing
    "js-yaml": "^4.1.0",           // YAML frontmatter parsing
    "commander": "^11.1.0",        // CLI argument parsing
    "chalk": "^5.3.0",             // Terminal styling
    "ora": "^7.0.1"                // Loading spinners
  }
}
```

### Why Zero Runtime Dependencies?

1. **Portability**: The output file works offline, on any device
2. **Longevity**: No CDN links to break, no library versions to maintain
3. **Security**: No third-party scripts to trust
4. **Performance**: No network requests, instant loading

---

## 5. API Design

### Programmatic API

```javascript
const slidemd = require('slidemd');

// Basic usage
const html = await slidemd.generate('presentation.md');

// With options
const html = await slidemd.generate('presentation.md', {
  theme: 'dark',
  title: 'My Talk',
  transition: 'fade',
  aspectRatio: '16:9'
});

// Custom theme
const html = await slidemd.generate('presentation.md', {
  theme: {
    name: 'custom',
    vars: {
      '--bg-primary': '#1a1a2e',
      '--text-primary': '#eaeaea',
      '--accent': '#e94560'
    }
  }
});

// Parse only (get structured data)
const parsed = await slidemd.parse('presentation.md');
console.log(parsed.slides.length); // 15
console.log(parsed.slides[0].notes); // Speaker notes for slide 1

// Render custom data
const html = await slidemd.render(parsed, { theme: 'minimal' });

// Available themes
const themes = slidemd.getThemes();
console.log(themes); // ['default', 'dark', 'minimal', 'gradient', 'serif']
```

### Internal Module API

```javascript
// parser.js
export function parseMarkdown(content: string): ParsedPresentation
export function splitSlides(content: string): string[]
export function extractFrontmatter(content: string): { metadata: object, body: string }
export function extractNotes(slideContent: string): { content: string, notes: string }

// renderer.js
export function render(presentation: ParsedPresentation, options: RenderOptions): string
export function renderSlide(slide: Slide, theme: Theme): string
export function generateCSS(theme: Theme): string
export function generateJS(slideCount: number, options: RenderOptions): string

// themes.js
export function getTheme(name: string): Theme
export function getAllThemes(): Theme[]
export function validateTheme(theme: Theme): boolean
export function mergeTheme(base: Theme, overrides: Partial<Theme>): Theme

// keyboard.js
export function setupKeyboard(handlers: KeyboardHandlers): void
export function parseKey(event: KeyboardEvent): string

// presenter.js
export function openPresenterWindow(slideData: SlideData[]): void
export function syncPresenter(currentSlide: number): void
export function closePresenterWindow(): void

// notes.js
export function parseNotesBlock(content: string): string
export function formatNotesForDisplay(notes: string): string
```

---

## 6. Markdown Syntax Support

### Standard Markdown

| Syntax | Rendered As |
|--------|-------------|
| `# Heading 1` | Large heading |
| `## Heading 2` | Medium heading |
| `### Heading 3` | Small heading |
| `**bold**` | **Bold text** |
| `*italic*` | *Italic text* |
| `` `code` `` | `inline code` |
| `[link](url)` | [link](url) |
| `> quote` | Block quote |
| `- item` | Bullet list |
| `1. item` | Numbered list |
| `---` | Horizontal rule (also slide separator) |
| ```` ```code`````` | Code block with syntax highlighting |
| `![alt](image.png)` | Image (base64 encoded for self-contained output) |

### Extended Syntax

| Syntax | Description |
|--------|-------------|
| `<!-- notes -->...<!-- -->` | Speaker notes block |
| `---` at line start | Slide separator |
| `{: .class }` | CSS class on element |
| `{:#id }` | ID on element |
| `<!-- transition: fade -->` | Per-slide transition override |

### Slide Separator Logic

The `---` separator is interpreted as slide break when:
1. `---` appears on its own line
2. Not inside a code block
3. Not inside an HTML comment
4. Not inside a ``` code fence ```
5. Preceded by newline (for edge cases like `Text---`)

---

## 7. Error Handling

### Input Validation

```javascript
// errors.js
export class SlideMDErrors {
  static FileNotFound(path: string): Error
  static InvalidMarkdown(reason: string, line: number): Error
  static InvalidFrontmatter(reason: string): Error
  static ThemeNotFound(name: string): Error
  static InvalidTheme(theme: object): Error
  static EmptyPresentation(): Error
}
```

### Error Scenarios & Recovery

| Error | User Message | Recovery |
|-------|--------------|----------|
| File not found | `Error: Input file 'x.md' not found` | Show usage, exit |
| Invalid markdown | `Warning: Could not parse slide 5, treating as regular markdown` | Continue with raw text |
| Empty file | `Warning: No slides found in file` | Exit with code 0, empty output |
| Unknown theme | `Error: Theme 'unknown' not found. Available: default, dark, minimal` | Exit |
| Image not found | `Warning: Image 'logo.png' not found, skipping` | Use placeholder or skip |

### Validation Rules

```javascript
// Input validation
{
  maxFileSize: 10 * 1024 * 1024,  // 10MB
  maxSlides: 500,
  maxSlideSize: 100 * 1024,       // 100KB per slide
  allowedImageExtensions: ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
  maxImageSize: 2 * 1024 * 1024,  // 2MB per image
  supportedAspectRatios: ['16:9', '16:10', '4:3', '1:1']
}
```

---

## 8. Edge Cases

### Slide Separator Edge Cases

| Input | Behavior |
|-------|----------|
| `---` inside \`\`\` code block | Ignored as separator |
| `---` inside HTML comment | Ignored |
| `Text---` (no newline) | Ignored |
| `---` at file start | Skip (empty first slide) |
| Multiple `---` in sequence | Skip empty slides |
| `---` at file end | Skip (no trailing empty slide) |

### Content Edge Cases

| Case | Handling |
|------|----------|
| Empty slide content | Render as blank slide |
| Only notes, no content | Render blank slide with notes |
| Very long slide | Enable scroll within slide, show indicator |
| Very wide content | Horizontal scroll, no text wrap break |
| No frontmatter | Use defaults |
| Invalid YAML in frontmatter | Ignore frontmatter, warn user |
| Missing closing `<!-- notes -->` | Treat rest of slide as notes |
| Nested `<!-- notes -->` | Only outermost counts |

### Browser Compatibility

| Feature | Minimum Browser |
|---------|------------------|
| CSS Custom Properties | Chrome 49, Firefox 31, Safari 9.1 |
| ES6+ JavaScript | Chrome 58, Firefox 54, Safari 11 |
| Fullscreen API | Chrome 71, Firefox 64, Safari 12.1 |
| BroadcastChannel | Chrome 54, Firefox 78, Safari 15.4 |

**Fallback Strategy**:
- For older browsers: Feature detection with graceful degradation
- Presenter sync: Fallback from BroadcastChannel to localStorage events
- Fullscreen: Fallback to browser-native F11

### Image Handling

| Scenario | Handling |
|----------|----------|
| Local image (relative path) | Convert to base64, inline |
| Local image (absolute path) | Convert to base64, inline |
| Remote image (http/https) | Convert to base64 if under 2MB, else warn |
| SVG image | Inline as-is |
| Animated GIF | Preserve animation |
| Missing image | Show placeholder with broken-image icon |

---

## 9. Output HTML Specifications

### Required Attributes

```html
<!-- Viewport for responsive design -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<!-- Prevent phone number detection -->
<meta name="format-detection" content="telephone=no">

<!-- Theme color for browser chrome -->
<meta name="theme-color" content="#2c3e50">
```

### CSS Requirements

```css
/* Print styles for handouts */
@media print {
  .slide {
    page-break-after: always;
    height: auto;
  }
  .controls, .presenter-view {
    display: none;
  }
}

/* Responsive breakpoints */
@media (max-width: 1024px) { /* Tablet */ }
@media (max-width: 768px) { /* Mobile landscape */ }
@media (max-width: 480px) { /* Mobile portrait */ }
```

### JavaScript Requirements

```javascript
// No external dependencies
// Must work in:
// - Chrome 58+
// - Firefox 54+
// - Safari 11+
// - Edge 79+

// No module system (IIFE pattern)
(function() {
  'use strict';
  // All code here
})();
```

---

## 10. Performance Targets

| Metric | Target |
|--------|--------|
| CLI startup | < 100ms |
| Parse + render (50 slides) | < 500ms |
| Output HTML size (50 slides, no images) | < 100KB |
| Browser load time | < 50ms |
| Slide transition | < 300ms |
| Keyboard response | < 16ms (60fps) |

### Bundle Size Breakdown (target 100KB output)

```
┌────────────────────────────┐
│ CSS (theme)          15KB │
├────────────────────────────┤
│ Base CSS              5KB │
├────────────────────────────┤
│ JavaScript           20KB │
├────────────────────────────┤
│ HTML boilerplate      8KB │
├────────────────────────────┤
│ Content (50 slides)  50KB │
├────────────────────────────┤
│ Misc                  2KB │
└────────────────────────────┘
Total: ~100KB
```

---

## 11. Testing Strategy

### Unit Tests
- Parser: Slide splitting, frontmatter extraction, notes parsing
- Renderer: HTML generation, CSS inlining, theme application
- Keyboard: Key mapping, event handling
- Utils: String escaping, URL conversion

### Integration Tests
- Full pipeline: markdown → HTML
- Theme application across all themes
- Edge cases (code blocks, comments, etc.)

### Visual Tests
- Render sample presentations in all themes
- Verify responsive behavior
- Check print output

### Test Fixtures
```
tests/
├── fixtures/
│   ├── basic.md
│   ├── with-notes.md
│   ├── with-images.md
│   ├── with-frontmatter.md
│   ├── code-blocks.md
│   ├── edge-cases.md
│   └── empty.md
├── snapshots/           # Expected HTML outputs
└── themes/              # Theme-specific snapshots
```

---

## 12. Implementation Phases

### Phase 1: Core (MVP)
- [ ] CLI with basic arguments
- [ ] Markdown parsing (slide splitting)
- [ ] Basic HTML generation
- [ ] Default theme
- [ ] Keyboard navigation (next/prev)
- [ ] Single CSS file output

### Phase 2: Polish
- [ ] Speaker notes
- [ ] Multiple themes
- [ ] Presenter mode
- [ ] Fullscreen support
- [ ] Slide transitions
- [ ] Responsive design

### Phase 3: Enhancements
- [ ] Image inlining (base64)
- [ ] Code syntax highlighting
- [ ] Print mode
- [ ] Custom CSS injection
- [ ] Aspect ratio options
- [ ] Timer in presenter mode

### Phase 4: Quality
- [ ] Comprehensive tests
- [ ] Error handling polish
- [ ] Documentation
- [ ] CLI help text
- [ ] Theme validation
- [ ] Performance optimization

---

## 13. Future Considerations

### Potential Features (v2.0)
- Live reload during editing
- PDF export
- Interactive elements (reveals, animations)
- Touch/swipe navigation
- Presentation remote (phone as clicker)
- Collaborative editing hints
- Analytics integration

### Extensibility Points
- Plugin system for custom markdown extensions
- Custom theme loading from files
- Template system for HTML structure
- Export adapters (PDF, images, etc.)

---

## 14. File Naming Conventions

| Pattern | Example | Purpose |
|---------|---------|---------|
| Input | `talk.md` | User's markdown source |
| Output | `talk.html` | Generated presentation |
| Theme CSS | `themes/dark.css` | Theme definitions |
| Module | `parser.js` | ES module, src files |
| Test | `parser.test.js` | Jest test file |
| Fixture | `basic.md` | Test input sample |

---

## Summary

SlideMD transforms markdown into self-contained, beautiful presentations with:
- Zero external dependencies
- Beautiful built-in themes
- Keyboard navigation & presenter mode
- Speaker notes support
- Single-file output that works anywhere

The implementation follows modular design with clear separation of concerns, comprehensive error handling, and extensibility points for future enhancements.
