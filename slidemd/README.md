# SlideMD

Single-file markdown presentation generator. Transform markdown files into beautiful, self-contained HTML presentations with zero external dependencies.

## Features

- **Zero dependencies**: Output is a single HTML file with no external scripts, styles, or fonts
- **Beautiful themes**: 5 built-in themes (default, dark, minimal, gradient, serif)
- **Keyboard navigation**: Arrow keys, Space, h/l, Home/End, f for fullscreen
- **Presenter mode**: Press `p` to see current slide, next slide, and speaker notes
- **Overview mode**: Press `o` to see thumbnail overview of all slides
- **Speaker notes**: Add notes with `<!-- notes -->` syntax
- **Aspect ratio support**: 16:9, 16:10, 4:3, 1:1

## Installation

```bash
npm install
```

## Usage

### Command Line

```bash
# Basic usage
node bin/slidemd --input presentation.md

# Specify output file
node bin/slidemd --input presentation.md --output my-talk.html

# Use a theme
node bin/slidemd --input presentation.md --theme dark

# Custom title and author
node bin/slidemd --input presentation.md --title "My Talk" --author "John Doe"

# Change transition style
node bin/slidemd --input presentation.md --transition fade

# Change aspect ratio
node bin/slidemd --input presentation.md --aspect 4:3

# List available themes
node bin/slidemd --list-themes

# Help
node bin/slidemd --help
```

### Programmatic API

```javascript
import { generate, generateFile } from './src/cli.js';
import { getAllThemes } from './src/renderer.js';

// Generate HTML from markdown file
const html = await generate('presentation.md', {
  theme: 'dark',
  title: 'My Presentation',
  transition: 'slide',
  aspectRatio: '16:9'
});

// Generate and save to file
await generateFile('presentation.md', 'output.html', {
  theme: 'minimal'
});

// Get available themes
const themes = getAllThemes();
console.log(themes); // ['default', 'dark', 'minimal', 'gradient', 'serif']
```

## Markdown Format

### Slide Separator

Use `---` to separate slides:

```markdown
# Slide 1

Content for slide 1

---

# Slide 2

Content for slide 2
```

### Frontmatter

Optional YAML frontmatter for metadata:

```markdown
---
title: My Presentation
author: John Doe
theme: dark
transition: slide
---

# Slide content...
```

### Speaker Notes

Add speaker notes with `<!-- notes -->`:

```markdown
# Slide Title

Slide content here.

<!-- notes
Remember to mention:
- Key point 1
- Key point 2
-->
```

### Code Blocks

```markdown
```javascript
console.log('Hello, world!');
```
```

### Images

```markdown
![Alt text](image.png)
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| → / Space / l | Next slide |
| ← / h | Previous slide |
| Home / g | First slide |
| End / G | Last slide |
| f | Toggle fullscreen |
| p | Toggle presenter mode |
| o | Toggle overview mode |
| b | Blackout screen |
| t | Show current time |
| Esc | Exit current mode |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --input` | Input markdown file | Required |
| `-o, --output` | Output HTML file | `{input-name}.html` |
| `-t, --theme` | Theme name | `default` |
| `--title` | Presentation title | From frontmatter or filename |
| `--author` | Author name | From frontmatter |
| `--transition` | Slide transition | `slide` |
| `--aspect` | Aspect ratio | `16:9` |

## Themes

- **default**: Clean, professional with blue accents
- **dark**: Dark background, light text
- **minimal**: Maximum whitespace, subtle typography
- **gradient**: Vibrant gradient backgrounds
- **serif**: Classic typography with serif fonts

## Example

```markdown
---
title: Welcome to SlideMD
author: Your Name
theme: dark
---

# SlideMD

Transform markdown into beautiful presentations.

---

# Features

- Zero external dependencies
- Beautiful themes
- Keyboard navigation
- Presenter mode
- Speaker notes

<!-- notes
Demo each feature briefly.
-->

---

# Code Example

```javascript
const greeting = 'Hello, World!';
console.log(greeting);
```
```

Generate with:

```bash
node bin/slidemd --input example.md --theme dark
```

## Browser Compatibility

Tested on modern browsers:
- Chrome 58+
- Firefox 54+
- Safari 11+
- Edge 79+

## License

MIT