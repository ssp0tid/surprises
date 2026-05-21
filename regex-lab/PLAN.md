# Regex Lab - Web Regex Debugger Plan

## Project Overview

**Project Name:** Regex Lab
**Type:** Single-page web application (HTML/CSS/JS)
**Core Functionality:** Interactive regex debugger with real-time matching and syntax highlighting
**Target Users:** Developers learning or debugging regex patterns

---

## UI/UX Specification

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  HEADER (Logo + Title)                                 │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────┐ │
│  │  REGEX INPUT       │  │  FLAGS (g i m s u y)      │ │
│  │  [pattern editor] │  │  [toggle buttons]        │ │
│  └─────────────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────┐ │
│  │  TEST STRING       │  │  MATCHES OUTPUT         │ │
│  │  [textarea]       │  │  [highlighted results] │ │
│  │                   │  │  + match groups         │ │
│  └─────────────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  FOOTER (keyboard shortcuts hint)                      │
└─────────────────────────────────────────────────────────┘
```

- **Desktop:** Two-column layout (input | output side by side)
- **Tablet (< 900px):** Stack vertically
- **Mobile (< 600px):** Single column, full width inputs

### Visual Design

**Color Palette:**
- Background: `#0d1117` (deep navy-black)
- Surface: `#161b22` (card background)
- Border: `#30363d` (subtle borders)
- Text Primary: `#e6edf3` (off-white)
- Text Muted: `#8b949e` (gray)
- Accent Primary: `#58a6ff` (bright blue)
- Accent Success: `#3fb950` (green for matches)
- Accent Error: `#f85149` (red for errors)
- Accent Warning: `#d29922` (yellow)

**Syntax Highlighting (Regex):**
- Metacharacters (^ $ . |): `#ff7b72` (coral)
- Quantifiers (* + ? {}): `#79c0ff` (light blue)
- Character classes ([] [^]): `#a5d6ff` (sky blue)
- Groups (() (?:) (?=): `#d2a8ff` (purple)
- Escape sequences (\d \w \s): `#7ee787` (green)
- Anchors (\b \B): `#ffa657` (orange)

**Typography:**
- Font Family: `"JetBrains Mono", "Fira Code", monospace`
- Headings: 600 weight
- Body: 400 weight
- Font Sizes:
  - Logo: 24px
  - Section headers: 14px uppercase
  - Input text: 16px
  - Match output: 16px
  - Hints: 12px

**Spacing:**
- Container max-width: 1200px, centered
- Section padding: 24px
- Input padding: 16px
- Gap between elements: 16px
- Border radius: 8px (cards), 4px (inputs)

**Visual Effects:**
- Input focus: 2px outline `#58a6ff`
- Error state: 2px outline `#f85149`
- Hover on flags: background `#21262d`
- Active flag: background `#388bfd`, text white
- Smooth transitions: 150ms ease

### Components

**1. Regex Input**
- Monospace textarea/editor
- Line numbers (optional)
- Syntax highlighting inline
- Error message below if invalid

**2. Flags Panel**
- Toggle buttons for: `g` (global), `i` (ignore case), `m` (multiline), `s` (dotAll), `u` (unicode), `y` (sticky)
- Active state: filled background
- Tooltip on hover showing meaning

**3. Test String Input**
- Large textarea
- Placeholder text guiding usage
- Line numbers

**4. Match Results**
- Highlighted matches in test string
- Match index and captured groups
- Empty state: "No matches" or "Enter a pattern"
- Error state: Invalid regex message

**5. Match Groups Panel** (optional expand)
- List of captured groups per match
- Named groups support

---

## Functionality Specification

### Core Features

1. **Real-time Matching**
   - Match as user types (debounced 150ms)
   - Support all JavaScript RegExp flags
   - Handle invalid regex gracefully

2. **Syntax Highlighting**
   - Parse regex pattern and apply colored spans
   - Highlight: metacharacters, quantifiers, groups, character classes, escapes

3. **Match Visualization**
   - Highlight matched substrings in test string
   - Show match index, start/end positions
   - Display captured groups (numbered + named)

4. **Error Handling**
   - Show clear error for invalid regex
   - Highlight error position if possible

### User Interactions

- Type in regex input → real-time match update
- Type in test string → real-time match update
- Click flag button → toggle flag, re-match
- Click on match → scroll to/highlight that match
- Keyboard: `Ctrl+Enter` to force re-match

### Edge Cases

- Empty pattern: show "Enter a pattern"
- Empty test string: show "No matches" or "Enter test string"
- Invalid regex: show error message, disable matching
- Very long test string: truncate display, show "N more" indicator
- Many matches (>100): paginate or show summary

---

## Acceptance Criteria

1. ✅ Page loads without errors
2. ✅ Typing regex updates matches in real-time
3. ✅ Invalid regex shows error message
4. ✅ All 6 flags can be toggled and affect matching
5. ✅ Matches are visually highlighted in test string
6. ✅ Match count is displayed
7. ✅ Captured groups are shown
8. ✅ Responsive on mobile
9. ✅ Syntax highlighting works on regex pattern
10. ✅ Keyboard shortcuts work

---

## Technical Implementation

### File Structure
```
regex-lab/
├── index.html      # Single HTML file with embedded CSS/JS
└── PLAN.md       # This file
```

### Dependencies (CDN)
- JetBrains Mono font (Google Fonts)

### Implementation Approach
- Vanilla JavaScript (no framework)
- RegExp for matching
- Custom tokenizer for syntax highlighting
- CSS custom properties for theming