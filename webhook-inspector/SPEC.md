# Webhook Inspector - Specification Document

## 1. Project Overview

**Project Name:** Webhook Inspector  
**Project Type:** Full-stack web application  
**Core Functionality:** A tool that provides a public endpoint to receive webhooks and displays incoming requests in real-time with full inspection of headers, body, and query parameters.  
**Target Users:** Developers debugging webhooks, API integrations, or testing webhook-based workflows.

---

## 2. Architecture

### Tech Stack
- **Backend:** Node.js + Express.js
- **Real-time:** Server-Sent Events (SSE)
- **Frontend:** Vanilla HTML/CSS/JS (no framework)
- **Storage:** In-memory (array of request objects)

### File Structure
```
webhook-inspector/
├── server.js           # Express server + SSE endpoint
├── package.json        # Node.js dependencies
├── public/
│   ├── index.html      # Main UI
│   ├── style.css       # Styles
│   └── app.js          # Frontend JavaScript
└── SPEC.md             # This specification
```

---

## 3. UI/UX Specification

### Layout Structure
- **Header:** Fixed top bar with app title and webhook URL display
- **Main Area:** Two-column layout
  - Left sidebar (30%): List of incoming requests
  - Right panel (70%): Request detail view

### Visual Design

**Color Palette:**
- Background: `#0d1117` (dark charcoal)
- Surface: `#161b22` (elevated dark)
- Border: `#30363d` (subtle gray)
- Primary accent: `#58a6ff` (bright blue)
- Secondary accent: `#f78166` (coral orange)
- Success: `#3fb950` (green)
- Text primary: `#e6edf3` (off-white)
- Text secondary: `#8b949e` (muted gray)
- Code background: `#0d1117`

**Typography:**
- Font family: `"JetBrains Mono", "Fira Code", monospace` for code
- Font family: `"Segoe UI", -apple-system, sans-serif` for UI
- Headings: 18px bold
- Body: 14px regular
- Code: 13px monospace

**Spacing:**
- Base unit: 8px
- Padding: 16px (cards), 24px (containers)
- Gap: 12px (list items), 24px (sections)

**Visual Effects:**
- Box shadows: `0 8px 24px rgba(0,0,0,0.4)` for elevated elements
- Border radius: 8px (cards), 4px (buttons/inputs)
- Transitions: 150ms ease for hover states

### Components

**Header:**
- App title "Webhook Inspector" on left
- Webhook URL display (copyable) on right with copy button
- "Clear All" button

**Request List (Left Sidebar):**
- Each item shows: HTTP method badge, path, timestamp
- Method badges: GET (green), POST (blue), PUT (orange), DELETE (red)
- Selected item highlighted with accent border
- Hover: subtle background change
- Empty state: "No requests yet" message

**Request Detail (Right Panel):**
- Tab navigation: Headers | Body | Query Params
- **Headers tab:** Key-value table with alternating row colors
- **Body tab:** Syntax-highlighted JSON with collapsible sections
- **Query tab:** Key-value table similar to headers
- Copy buttons for each section

**Real-time Indicator:**
- Pulsing green dot in header showing "Live" status

---

## 4. Functionality Specification

### Backend Features

**Webhook Endpoint:**
- `POST /webhook` - Accepts any incoming webhook
- Captures: method, path, query string, headers, body, timestamp
- Returns 200 OK with JSON acknowledgment
- Also accepts GET, PUT, DELETE for testing

**SSE Endpoint:**
- `GET /events` - Long-lived connection for real-time updates
- Sends new request events as JSON

**API Endpoints:**
- `GET /api/requests` - Returns all captured requests (for initial load)
- `DELETE /api/requests` - Clears all stored requests

### Frontend Features

**On Page Load:**
- Fetch existing requests via `/api/requests`
- Connect to SSE endpoint for live updates

**Request List:**
- Display requests sorted by timestamp (newest first)
- Click to select and view details
- Auto-scroll to top on new request (unless user has scrolled up)

**Request Detail View:**
- Display formatted headers as table
- Display body with JSON pretty-print
- Display query params as table
- "Copy" button for each section

**Clear All:**
- Button to clear all requests via API

**Copy Webhook URL:**
- Click to copy the webhook URL to clipboard
- Show brief "Copied!" feedback

### Edge Cases
- Empty body: Display "No body content"
- Non-JSON body: Display as plain text
- Large payloads: Truncate display at 100KB with indicator
- Binary content: Display "[Binary content]"

---

## 5. Acceptance Criteria

1. ✅ Server starts without errors on `node server.js`
2. ✅ POST to `/webhook` returns 200 and stores the request
3. ✅ Frontend displays list of captured requests
4. ✅ Clicking a request shows full details (headers, body, query)
5. ✅ New webhooks appear in real-time without refresh
6. ✅ Copy buttons work for URL and content sections
7. ✅ Clear All removes all requests
8. ✅ UI is responsive and visually polished
9. ✅ JSON body is syntax-highlighted/pretty-printed

---

## 6. Configuration

**Default Port:** 3000  
**Webhook URL:** `http://localhost:3000/webhook`  
**SSE Endpoint:** `http://localhost:3000/events`