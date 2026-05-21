# eventbus-cli Implementation Plan

## 1. Project Overview

**eventbus-cli** — A CLI tool for local event-driven architecture acting as a pub/sub message broker.

### Core Features

- **Named Channels**: Publish/subscribe to topic-based channels
- **Real-time Delivery**: SSE streaming + CLI polling mode
- **Persistence**: SQLite for event replay and audit
- **Event Schemas**: JSON Schema validation with Ajv
- **Filtering**: Content-based + pattern subscriptions (glob/regex)

---

## 2. File Structure

```
eventbus-cli/
├── bin/
│   └── eventbus.js          # Entry point
├── src/
│   ├── index.ts           # CLI entry
│   ├── commands/
│   │   ├── publish.ts    # `eventbus publish`
│   │   ├── subscribe.ts # `eventbus subscribe`
│   │   ├── listen.ts    # `eventbus listen` (SSE mode)
│   │   ├── replay.ts    # `eventbus replay`
│   │   ├── schema.ts   # `eventbus schema`
│   │   └── server.ts   # `eventbus server` (daemon mode)
│   ├── lib/
│   │   ├── broker.ts    # Core pub/sub logic
│   │   ├── channel.ts  # Channel management
│   │   ├── event.ts    # Event model + validation
│   │   ├── storage.ts  # SQLite persistence
│   │   └── schema-registry.ts # Schema registry
│   └── utils/
│       ├── logger.ts
│       ├── config.ts
│       └── signals.ts   # Graceful shutdown
├── test/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── data/
│   └── eventbus.db      # SQLite DB (auto-created)
├── package.json
├── tsconfig.json
└── README.md
```

---

## 3. Dependencies

### Runtime
| Package | Purpose |
|---------|---------|
| `commander` | CLI argument parsing |
| `better-sqlite3` | SQLite (sync, fast) |
| `ajv` | JSON Schema validation |
| `event-emission` | Type-safe EventEmitter |
| `micromatch` | Glob pattern matching |
| `chalk` | Colored CLI output |
| `ora` | Spinner |
| `inquirer` | Interactive prompts |
| `get-port` | Find available port |
| `http-terminator` | Graceful HTTP shutdown |

### Dev
| Package | Purpose |
|---------|---------|
| `typescript` | TypeScript |
| `vitest` | Testing |
| `tsx` | Run TypeScript |
| `eslint` / `prettier` | Lint/format |

---

## 4. Data Model

### Event Schema

```typescript
interface Event {
  id: number;           // Auto-increment
  channel: string;      // e.g., "users.*"
  type: string;        // e.g., "user.created"
  payload: object;     // JSON payload
  metadata?: object;    // Optional metadata
  timestamp: string;   // ISO 8601
  version: number;     // Schema version (v1, v2...)
}
```

### SQLite Schema

```sql
CREATE TABLE events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  channel     TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload    TEXT NOT NULL,     -- JSON
  metadata   TEXT,             -- JSON
  timestamp  TEXT NOT NULL DEFAULT (datetime('now')),
  version    TEXT NOT NULL DEFAULT 'v1'
);

CREATE INDEX idx_channel ON events(channel, timestamp);
CREATE INDEX idx_type ON events(event_type, timestamp);
CREATE INDEX idx_timestamp ON events(timestamp);

CREATE TABLE channels (
  name       TEXT PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE schemas (
  event_type TEXT PRIMARY KEY,
  version    TEXT NOT NULL,
  schema      TEXT NOT NULL,     -- JSON Schema
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Schema Validation Rules

- `channel`: Letters, dots, asterisks only (`[a-zA-Z0-9.*]+`)
- `event_type`: dots allowed (`[a-zA-Z0-9.]+`)
- `payload`: Valid JSON object
- `timestamp`: ISO 8601 format

---

## 5. API Design

### Commands

#### `eventbus publish <channel> <type> [payload]`

```bash
# Simple publish
eventbus publish users user.created '{"userId": 123, "email": "foo@bar.com"}'

# With metadata
eventbus publish orders order.created '{"orderId": 456}' --meta '{"source": "api"}'

# From file
eventbus publish users user.created --file event.json

# Quiet mode
eventbus publish users user.created '{}' -q
```

#### `eventbus subscribe <channel-pattern> [--filter <filter>]`

```bash
# Subscribe to channel
eventbus subscribe users.*

# Subscribe with content filter (JMESPath-lite)
eventbus subscribe orders.* --filter "amount > 100"

# One-shot mode (no streaming)
eventbus subscribe users.* --once

# JSON output
eventbus subscribe users.* --json

# Count only (no output)
eventbus subscribe users.* --count
```

#### `eventbus listen <channel> [options]`

```bash
# SSE streaming (default: localhost:8080)
eventbus listen users.*

# Custom port
eventbus listen users.* --port 3000

# With auth token
eventbus listen users.* --token secret123

# All channels
eventbus listen "*" --port 8081
```

```
# SSE endpoint
GET /events?channel=users.*&token=secret123

# Response: text/event-stream
event: user.created
data: {"eventType":"user.created","channel":"users","payload":{...}}

retry: 5000
```

#### `eventbus replay <channel> [--from <timestamp>] [--to <timestamp>]`

```bash
# Replay all events for channel
eventbus replay users.*

# Time range
eventbus replay users.* --from 2026-01-01 --to 2026-04-22

# Limit results
eventbus replay users.* --limit 100

# As JSON lines
eventbus replay users.* --json

# Replay to timestamp
eventbus replay users.* --to 2026-04-22T10:00:00Z
```

#### `eventbus schema <command> [args]`

```bash
# Register schema
eventbus schema add user.created v1 --schema '{}'

# Register from file
eventbus schema add user.created v1 --file schema.json

# List schemas
eventbus schema list

# Get schema
eventbus schema get user.created

# Validate event
eventbus schema validate user.created --data '{}'
```

#### `eventbus server [options]`

```bash
# Start daemon (background)
eventbus server --daemon

# With config
eventbus server --port 8080 --db /path/to/db

# With API key
eventbus server --api-key secret

# PID file
eventbus server --pid /var/run/eventbus.pid
```

### Server API (HTTP)

```
GET  /channels              # List channels
POST /publish              # Publish event
GET  /events?channel=...   # SSE stream
GET  /events?channel=...&from=...&to=... # Replay
GET  /schemas              # List schemas
POST /schema               # Register schema
```

---

## 6. Core Implementation

### Channel Matching (Glob Patterns)

```typescript
import { micromatch } from 'micromatch';  // * matches any segment
import { glob } from 'glob';              // ** matches recursively

function matchChannel(eventChannel: string, subPattern: string): boolean {
  // Exact match
  if (eventChannel === subPattern) return true;

  // Glob match: users.* → users.foo, users.bar
  if (subPattern.includes('*')) {
    // Convert to micromatch format (escape dots in channel names)
    const pattern = subPattern
      .replace(/\./g, '\\.')
      .replace(/\*\*/g, '**')
      .replace(/\*/g, '*');
    return micromatch(eventChannel, pattern);
  }

  return false;
}
```

### Content Filtering

```typescript
interface FilterAST {
  type: 'comparison' | 'logical';
  operator?: '>' | '<' | '>=' | '<=' | '==' | '!=';
  field?: string;
  value?: any;
  left?: FilterAST;
  right?: FilterAST;
  operator2?: 'and' | 'or';
}

// JMESPath-like subset:
// user.id == 123
// amount > 100
// status == "active" and type == "premium"
```

### Event Validation (Ajv)

```typescript
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const ajv = new Ajv({ allErrors: true, verbose: true });
addFormats(ajv);

function validateEvent(event: unknown, schemaName: string): void {
  const registry = SchemaRegistry.get();
  const entry = registry.get(schemaName);
  if (!entry) return; // Allow unregistered events

  const validate = ajv.compile(JSON.parse(entry.schema));
  if (!validate(event)) {
    throw new SchemaValidationError(validate.errors);
  }
}
```

### Broker Core

```typescript
class EventBroker {
  private channels: Map<string, Set<Subscriber>>;
  private storage: Storage;
  private schemaRegistry: SchemaRegistry;

  async publish(channel: string, type: string, payload: object, meta?: object): Promise<Event> {
    const event: Event = {
      id: 0,
      channel,
      type,
      payload,
      metadata: meta,
      timestamp: new Date().toISOString(),
      version: 'v1'
    };

    validateEvent(event, type); // May throw

    // Persist
    await this.storage.insert(event);

    // Deliver to subscribers
    this.deliver(event);

    return event;
  }

  subscribe(pattern: string, callback: (event: Event) => void): Subscription {
    const sub = new Subscription(pattern, callback);
    for (const channel of this.channels.keys()) {
      if (matchChannel(channel, pattern)) {
        this.channels.get(channel)!.add(sub);
      }
    }
    return sub;
  }

  private deliver(event: Event): void {
    for (const [pattern, subs] of this.channels) {
      if (matchChannel(event.channel, pattern)) {
        for (const sub of subs) {
          if (filterEvent(event, sub.filter)) {
            sub.callback(event);
          }
        }
      }
    }
  }
}
```

### SSE Streaming

```typescript
// src/commands/server.ts
import http from 'http';

function createSSEServer(broker: EventBroker) {
  return http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    if (!url.pathname.startsWith('/events')) {
      res.statusCode = 404;
      res.end();
      return;
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });

    const channel = url.searchParams.get('channel') || '*';
    const sub = broker.subscribe(channel, (event) => {
      res.write(`event: ${event.type}\n`);
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    });

    req.on('close', () => sub.unsubscribe());
  });
}
```

---

## 7. Error Handling

### Error Types

```typescript
class EventbusError extends Error {
  constructor(message: string, public code: string) {
    super(message);
  }
}

class ChannelNotFoundError extends EventbusError {
  constructor(channel: string) {
    super(`Channel not found: ${channel}`, 'CHANNEL_NOT_FOUND');
  }
}

class SchemaValidationError extends EventbusError {
  constructor(public errors: Error[]) {
    super(`Schema validation failed: ${errors.length} error(s)`, 'INVALID_EVENT');
  }
}

class DuplicateChannelError extends EventbusError {
  constructor(channel: string) {
    super(`Channel already exists: ${channel}`, 'DUPLICATE_CHANNEL');
  }
}

class InvalidPatternError extends EventbusError {
  constructor(pattern: string) {
    super(`Invalid channel pattern: ${pattern}`, 'INVALID_PATTERN');
  }
}
```

### Error Codes

| Code | HTTP | Meaning |
|------|------|----------|
| `INVALID_CHANNEL` | 400 | Invalid channel name |
| `INVALID_EVENT` | 400 | Event validation failed |
| `CHANNEL_NOT_FOUND` | 404 | Channel doesn't exist |
| `DUPLICATE_CHANNEL` | 409 | Channel already exists |
| `INVALID_PATTERN` | 400 | Invalid glob pattern |
| `SERVER_ERROR` | 500 | Internal server error |

---

## 8. Edge Cases

### 1. High-Volume Events

```bash
# Batch publish (multiple in one command)
eventbus publish users user.created '[{"id":1},{"id":2}]'

# Use server mode for high throughput
# Server handles batching internally
```

**Mitigation:** WAL mode, batch inserts, prepared statements.

### 2. Slow Subscribers

```bash
# Timeout for subscriber
eventbus subscribe users.* --timeout 30s
```

**Mitigation:** Channel buffer with overflow, client-side backpressure.

### 3. Schema Evolution

```bash
# Versioned schemas
eventbus schema add user.created v1 --schema '{...}'
eventbus schema add user.created v2 --schema '{...}'
```

**Mitigation:** Multiple schema versions, migration utility for data.

### 4. Reconnection

```bash
# Retry on disconnect
# SSE clients should handle retry: automatically
```

**Mitigation:** SSE `retry:` field, client reconnection logic.

### 5. Channel Explosions

```bash
# users.* subscribed by multiple clients
# Each gets their own buffer
```

**Mitigation:** Subscriber isolation per client.

### 6. Database Lock Contention

```sql
-- WAL mode enables concurrent reads during writes
PRAGMA journal_mode = WAL;
```

**Mitigation:** Write-ahead logging, read replicas not needed for local CLI.

---

## 9. Configuration

### Default Locations

| File | Location |
|------|----------|
| Database | `./data/eventbus.db` or `~/.eventbus/data.db` |
| Config | `~/.eventbus/config.json` |
| PID | `~/.eventbus/eventbus.pid` |
| Log | `~/.eventbus/logs/` |

### Config Schema

```json
{
  "server": {
    "host": "localhost",
    "port": 8080,
    "apiKey": null
  },
  "storage": {
    "path": "~/.eventbus/data.db",
    "wal": true,
    "busyTimeout": 5000
  },
  "logging": {
    "level": "info",
    "path": "~/.eventbus/logs"
  }
}
```

---

## 10. Usage Examples

### Basic Workflow

```bash
# Start server (background)
eventbus server --daemon --port 8080

# Register a schema
eventbus schema add user.created v1 --schema '{
  "type": "object",
  "properties": {
    "userId": {"type": "integer"},
    "email": {"type": "string", "format": "email"}
  },
  "required": ["userId"]
}'

# Subscribe in one terminal
eventbus subscribe users.*

# Publish in another
eventbus publish users user.created '{"userId": 123, "email": "foo@bar.com"}'

# Replay events
eventbus replay users.* --from 2026-01-01
```

### With SSE

```bash
# Listen mode (SSE client)
eventbus listen users.*

# Or use curl
curl -N http://localhost:8080/events?channel=users.*
```

### Filtered Subscription

```bash
# Subscriptions can include filters using dot notation:
eventbus subscribe 'orders.*' --filter 'payload.amount > 100'
```

---

## 11. Implementation Priority

| Phase | Components | Commands |
|-------|-----------|----------|
| 1 | `event.ts`, `storage.ts` | `publish` |
| 2 | `broker.ts`, `channel.ts` | `subscribe`, `listen` |
| 3 | `schema-registry.ts` | `schema` |
| 4 | `replay.ts`, `server.ts` | `replay` |
| 5 | Error handling, config, tests | Full CLI |

---

## 12. Summary

| Aspect | Choice |
|--------|--------|
| Language | TypeScript |
| Storage | SQLite (better-sqlite3, WAL mode) |
| Validation | Ajv with JSON Schema |
| Patterns | Glob (micromatch) |
| Real-time | SSE over HTTP |
| CLI | Commander |
| Error handling | Typed errors with codes |
| Daemon | PID file + signal handling |

This plan provides a complete roadmap for implementing **eventbus-cli**.