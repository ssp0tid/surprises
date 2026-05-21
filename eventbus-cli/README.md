# eventbus-cli

A CLI tool for local event-driven architecture acting as a pub/sub message broker.

## Features

- **Named Channels**: Publish/subscribe to topic-based channels with glob patterns
- **Real-time Delivery**: SSE streaming + CLI polling mode
- **Persistence**: SQLite for event replay and audit
- **Event Schemas**: JSON Schema validation with Ajv
- **Filtering**: Content-based subscriptions

## Installation

```bash
git clone <repository-url>
cd eventbus-cli
npm install
npm run build
npm link
```

Or run directly without linking:

```bash
npm run dev -- <command>
```

## Usage

### Start Server

```bash
eventbus server --port 8080
```

Run as daemon:

```bash
eventbus server --daemon --port 8080
```

### Publish Events

```bash
eventbus publish <channel> <type> <payload>
```

Examples:

```bash
eventbus publish users user.created '{"userId": 123, "email": "foo@bar.com"}'
eventbus publish orders order.created '{"orderId": 456}' --meta '{"source": "api"}'
eventbus publish users user.created --file event.json
```

### Subscribe to Events

```bash
eventbus subscribe <channel-pattern>
```

Examples:

```bash
eventbus subscribe users.*
eventbus subscribe orders.* --filter "payload.amount > 100"
eventbus subscribe users.* --once
eventbus subscribe users.* --json
```

### Listen via SSE

```bash
eventbus listen <channel>
```

Examples:

```bash
eventbus listen users.* --port 3000 --token secret123
```

### Replay Events

```bash
eventbus replay <channel>
```

Examples:

```bash
eventbus replay users.*
eventbus replay users.* --from 2026-01-01 --to 2026-04-22
eventbus replay users.* --limit 100 --json
```

### Manage Schemas

```bash
eventbus schema <command>
```

Commands:

```bash
eventbus schema add user.created v1 --schema '{"type": "object", "properties": {"userId": {"type": "integer"}}}'
eventbus schema list
eventbus schema get user.created v1
eventbus schema validate user.created --data '{"userId": 123}'
```

## API Endpoints

When server is running:

- `GET /events?channel=<pattern>` - SSE stream
- `POST /publish` - Publish event
- `GET /channels` - List channels
- `GET /schemas` - List schemas
- `GET /events?channel=...&from=...&to=...` - Replay events

## Configuration

Default config location: `~/.eventbus/config.json`

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

## Development

```bash
npm run dev          # Run in development mode
npm run build       # Compile TypeScript
npm test           # Run tests
npm run lint        # Lint code
```

## License

MIT
