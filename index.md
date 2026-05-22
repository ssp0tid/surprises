# Surprise Projects Index

> Auto-generated index of all projects in ~/projects/surprises/
> Last updated: 2026-04-22 16:18 | Total: 57 projects

---

## Web Applications

### eventbus-cli/
Local pub/sub message broker CLI - publish/subscribe to named channels, real-time SSE streaming, SQLite persistence for replay/audit, JSON Schema validation, pattern-based subscriptions. Node.js TypeScript + better-sqlite3 + Ajv.

### mockflow/
Visual HTTP mock API designer - web UI to define mock endpoints (path, method, status code, response body, headers), test responses in-browser, and run a local mock server that serves defined responses. Import from OpenAPI/Postman. Flask + SQLite.

### habitbeat/
Self-hosted habit tracking with streak analytics, daily check-ins, progress charts, categories, reminders API. Flask + SQLite.

### url-shortener/
Self-hosted URL shortener with click analytics, custom slugs, expiration. Flask single-file.

### bookmark-vault/
Tag-based bookmark manager with full-text search. Flask + SQLite FTS5.

### encrypted-pastebin/
AES-256-GCM encrypted pastebin with burn-after-reading. Flask.

### healthdash/
HTTP endpoint monitoring with uptime tracking. Flask + SQLite + APScheduler.

### recipe-manager/
Personal recipe management with categories, search. Flask.

### uptime-monitor/
URL uptime monitoring with notifications. Flask.

### logvault/
Go + ClickHouse log management with SSE streaming, search. Full-stack.

### kanboardx/
Drag-and-drop Kanban board. Flask single-file (2655 lines).


### markdown-wiki/
Personal markdown wiki with bidirectional [[wiki-link]] linking, #tag organization, full-text search. Preact + Vite + Fastify.

### git-activity-dash/
Flask web app that analyzes local git repositories — commit history, contributor stats, activity heatmaps by hour/day, file change trends, branch info, commit message analysis. GitPython + Pandas + Chart.js.

### servemap/
Local network service discovery and visualization tool - mDNS/DNS-SD browsing, port scanning with service identification, interactive topology graph showing relationships between discovered services. Flask + vis-network.

### devdash/
Local developer dashboard that discovers and monitors local dev servers (Node.js, Python Flask/FastAPI, Go) by scanning for processes listening on localhost ports, displays real-time CPU/memory stats in a web dashboard with TailwindCSS. Flask + psutil.

### statuspage/
Self-hosted status page generator

### codepix/
Code screenshot generator - paste code, select syntax theme, export as PNG with syntax highlighting. Flask + Pygments + Pillow. - create public status pages for services with HTTP/TCP monitoring, uptime tracking (24h/7d/30d), incident management with timelines, component groups, custom branding, auto-incident creation. Flask + SQLite + Chart.js.

---

## CLI Tools

### cron-guard/
CLI cron expression validator - validate expressions, view next N run times, generate human-readable descriptions, detect schedule conflicts. Node.js TypeScript with Commander.js + cron-parser + cronstrue.

### passgen/
Secure password generator with entropy calculation. Rust.

### git-branch-cleanup/
Git branch cleanup CLI - find and delete merged/unmerged branches locally and remotely. Interactive selection, dry-run mode, protected branch safety. Node.js with commander, simple-git, inquirer.

### certcheck/
SSL certificate expiration checker. Python.

### textdiff/
CLI text diff tool with colored output. Python.

### pingplot/
Network latency visualizer with sparklines. Python.

### qrforge/
QR code generator/reader. Python.

### netscout/
Local network scanner with ARP/port scanning. Python.

### packetsniffer/
Network packet analyzer with Scapy. Python.

### httpbench/
HTTP load testing CLI. Go.

### apitest/
Go TUI API testing client. Bubble Tea.

### mockserver/
Zero-config mock API server. Python stdlib.

### markdown-link-checker/
Markdown broken link checker. Node.js.

### slidemd/
Markdown to HTML presentations. Node.js.

### lnfs/
Local network file sharing server. Python Flask.

### totp-auth/
CLI TOTP/HOTP 2FA authenticator with encrypted storage, QR scanning, clipboard support. Python Click + pyotp.

### local-ca/
Self-hosted Certificate Authority management tool - create root/intermediate CAs, generate TLS certificates for local development, manage chains, CSR signing, export PEM/P12/JKS formats. Flask + SQLite + CLI.

### local-llm-chat/
CLI tool to chat with local LLMs (llama.cpp/GGUF compatible) - interactive chat with markdown rendering, conversation history, system prompts, model switching. Python Click + rich + llama-cpp-python.

### shell-script-hub/
Shell script manager CLI - organize, tag, search, and execute shell scripts with templating, execution history logging. Python Click + SQLAlchemy + SQLite.

### webhook-automation-cli/
Local CLI for chaining HTTP requests with variables, conditionals, and workflows. Like a local Zapier/IFTTT. YAML workflow format. Node.js TypeScript CLI with commander.

### http-replay/
HTTP recording proxy server - records requests/responses to SQLite, web UI to view/search, replay with variable substitution, header modification, delay injection. Flask + Click + SQLite.

### dot-sync/
CLI tool for synchronizing dotfiles across machines with AES-256-GCM encryption, git-based storage, conflict resolution, machine-specific configs. Node.js TypeScript with Commander.js.

### mesh-proxy/
Local service mesh proxy for development — traffic routing, mock HTTP responses, delay injection, circuit breaking, rate limiting, and traffic mirroring between microservices. Go + cobra + zerolog.

---

## TUI Applications

### gitviz/
Interactive Git history visualizer. Python Textual.

### logprobe/
High-performance log explorer. Rust TUI.

### weather-dashboard/
Terminal weather dashboard. Python Textual.

### dockerwatch/
Docker container monitoring. Go Bubble Tea.

### crono/
Visual cron job scheduler. Python Textual.

### termtimer/
Terminal timer and alarm clock. Python Textual.


### shellmem/
Shell history manager with fuzzy search. Rust TUI.

### asteroid-runner/
ASCII space shooter roguelike. Python Textual.

### incident-command-center/
Terminal-based incident management for on-call engineers — incident list with P1-P4 severity, timeline tracking, status updates, on-call roster, notes. Python Textual + SQLite.

---

## Utilities


### clipstash/
Clipboard history manager. Flask + SQLite.

### secret-vault/
CLI secrets manager with AES-256-GCM. Go Cobra.

### webhook-inspector/
HTTP request inspector/logger. Python.

### portpilot/
Local port manager/orchestrator for developers - scan open ports with process info, detect port conflicts, simple port forwarding proxy. Python Click CLI + optional Textual TUI.

### dnswarden/
Local DNS server with custom domain resolution, ad/tracker blocking (blocklists), DNS-over-HTTPS proxy, query logging to SQLite/file. YAML config, rate limiting. Python dnslib + FastAPI admin UI.

### mailcatcher/
Local SMTP mail catcher server - captures all incoming emails and provides web dashboard to view rendered emails. SMTP on port 1025, Web UI on port 8080. Python Flask + aiosmtpd.

---

## Data Tools

### audiowave/
CLI audio waveform visualization and frequency spectrum analyzer. Supports MP3, WAV, FLAC, OGG. Python with numpy/scipy/matplotlib.

### local-pipeline/
YAML-based task pipeline/orchestrator with DAG scheduling, dependencies between tasks, cron triggers, execution history in SQLite, parallel task execution, retry logic, web dashboard, REST API with webhook triggers. Python FastAPI + SQLAlchemy.

### termail/
Terminal-based email client with IMAP/SMTP support, inbox management, email composition, folder organization. Python Textual TUI.

### code-sentinel/
AI-powered local code review assistant - analyzes code for bugs, security issues, and anti-patterns using local LLMs (llama.cpp/GGUF). Textual TUI ready. Python Typer + llama-cpp-python.



---
### trafix/
Local HTTP API gateway and traffic inspector - proxy HTTP requests, middleware (rate limiting, auth, logging, CORS), SQLite storage for request/response history, web dashboard for traffic inspection and analytics. Go + chi + SQLite.

## CLI Tools

### codegen-sdk/
CLI tool for generating typed client SDKs from OpenAPI specs - supports TypeScript, Python, Go, and Rust from local files or URLs. Python Click + requests + jinja2.

### regex-lab/
Interactive regex debugger and workbench with real-time matching, syntax highlighting for regex tokens, flag toggles (g/i/m/s/u/y), match visualization with captured groups. Single HTML file with embedded CSS/JS.

### envsync-cli/
Local environment variable sync manager - sync .env files across projects with AES-256-GCM encryption, project groups, variable interpolation, import/export .env files, optional web dashboard. Python Click + rich + cryptography.

## Games

### tetris-terminal/
Classic Tetris game for the terminal with all 7 tetrominoes, wall kicks, ghost piece, scoring, levels, and high score persistence. Python 3 curses (stdlib only).

### tetris-terminal/
Terminal Tetris game with all 7 tetrominoes, ghost piece, wall kicks, scoring, high scores. Python curses (stdlib only).

### maze-runner/
Terminal maze game with generation (recursive backtracker, Kruskal's, Prim's), animated solving (BFS, DFS, A*), and playable mode with timer and high scores. Python 3 curses (stdlib only).

### csvql/
CLI tool to run SQL queries against CSV/TSV files using in-memory SQLite. Supports JOINs across multiple files, auto-detects delimiters and column types, outputs as rich table/CSV/TSV/JSON. Python 3 + rich.

### algo-theater/
Interactive terminal algorithm visualizer — watch sorting, searching, and pathfinding algorithms execute step-by-step with animated bar charts and grids. Python 3 Textual TUI.

### flashforge/
CLI spaced repetition flashcard system with Leitner box algorithm, multiple decks, CSV/Markdown import/export, and progress statistics. Python 3 Click + Rich + SQLite.

### color-palette-studio/
Web-based color palette generator with 6 harmony rules (complementary, analogous, triadic, split-complementary, tetradic, monochromatic), WCAG contrast checking, and export to CSS/SCSS/Tailwind. Flask + SQLite.

### typing-dojo/
Terminal typing speed trainer with WPM tracking, accuracy stats, multiple modes (quick/timed/code), and persistent high scores. Python 3 curses (stdlib only).

### loc-counter/
Fast lines-of-code counter CLI — breaks down source files into code, comments, and blanks by language. Supports 25+ languages, respects .gitignore, outputs as rich ASCII table/JSON/CSV. Python 3 stdlib only.

### markov-poet/
Markov chain text generator that builds models from input text and generates poetry, prose, or haiku. Configurable chain order (1-5), corpus management with SQLite persistence, syllable-aware line breaking. Python 3 stdlib only.

### termchart/
Terminal chart renderer — renders bar charts, line charts, scatter plots, and sparklines from CSV/JSON/stdin using Unicode block and Braille characters. Python 3 stdlib only.

### diskvu/
Interactive terminal disk usage analyzer — ncdu-style directory explorer with proportional bar charts, sorting, threaded scanning with progress, and delete with confirmation. Python 3 curses (stdlib only).

### subtrak/
Subscription expense tracker — web app for tracking recurring subscriptions with spend visualization, category breakdowns, renewal alerts, and analytics dashboard. Python 3 Flask + SQLite + Chart.js + TailwindCSS.

### nonogram-puzzler/
Browser-based Nonogram (Picross) puzzle game with random puzzle generation, three difficulty levels, timer, auto-save, and solution validation. Python 3 Flask + SQLite + vanilla JS.

### pollcraft/
Real-time poll and survey builder with live results via SSE, IP-based duplicate detection, optional comments, and admin management via secret tokens. Python 3 Flask + SQLite + Chart.js + TailwindCSS.

### reqbench/
Self-hosted web-based HTTP request builder and API tester — build requests, inspect responses, save to collections, manage environments with variable interpolation. Python 3 Flask + SQLite + vanilla JS + TailwindCSS CDN.

### pixelforge/
Browser-based pixel art editor with layers, animation frames, drawing tools (pencil, eraser, fill, line, rect, circle, eyedropper), and PNG/GIF export. Python 3 Flask + SQLite + HTML5 Canvas + TailwindCSS CDN.

### chartcraft/
Interactive web-based chart builder — paste CSV/JSON data, pick chart types, customize colors/labels, export as PNG or share via link. Python 3 Flask + SQLite + Chart.js + TailwindCSS CDN.

### invoicely/
Web-based invoice generator with client management, PDF export (WeasyPrint), status tracking, and dashboard analytics. Python 3 Flask + SQLite + TailwindCSS CDN.

*End of Index*
