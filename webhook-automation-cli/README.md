# Webhook Automation CLI

A local CLI tool for chaining HTTP requests with variables, conditionals, and workflows.

## Features

- **YAML-based workflows** - Define complex HTTP chains in simple YAML files
- **Variable interpolation** - Use variables from inputs, environment, and previous steps
- **Conditional execution** - Branch logic based on HTTP status codes and values
- **Multiple step types** - HTTP requests, conditions, set variables, delays, logging
- **Built-in error handling** - Validation, timeouts, retry support
- **Security** - SSRF protection to block internal networks

## Installation

```bash
# Clone the repository
cd webhook-automation-cli

# Install dependencies
npm install

# Build the project
npm run build

# Link the CLI globally (optional)
npm link
```

## Quick Start

### Validate a workflow

```bash
webhook validate workflows/example.yaml
```

### Run a workflow

```bash
webhook run workflows/example.yaml
```

### With input variables

```bash
webhook run workflows/example.yaml --input key1=value1 key2=value2
```

### With environment variables

```bash
webhook run workflows/example.yaml --env API_KEY=secret123
```

### Verbose output

```bash
webhook run workflows/example.yaml --verbose
```

## Workflow Format

```yaml
name: "My Workflow"
description: "Description of what this workflow does"
version: "1.0"

settings:
  timeout: 30000

steps:
  - id: step1
    name: "First Step"
    type: http
    request:
      url: "https://api.example.com/data"
      method: GET
      headers:
        Authorization: "Bearer ${API_TOKEN}"

  - id: check-result
    name: "Check Result"
    type: condition
    condition: "{{step1.status}} == 200"

  - id: extract-data
    name: "Extract Data"
    type: set
    vars:
      userId: "{{step1.body.user.id}}"
      name: "{{step1.body.user.name}}"

  - id: log-output
    name: "Log Output"
    type: log
    message: "User: {{vars.name}}"
```

## Step Types

### http

Makes an HTTP request.

```yaml
- id: my-request
  type: http
  request:
    url: "https://api.example.com/endpoint"
    method: GET  # GET, POST, PUT, PATCH, DELETE
    headers:
      Content-Type: "application/json"
    query:
      page: "1"
    body:
      key: "value"
  timeout: 10000
  retries: 3
```

### condition

Evaluates a condition and controls flow.

```yaml
- id: check-status
  type: condition
  condition: "{{previous-step.status}} == 200"
  onTrue: "continue"  # continue, stop, or step ID
  onFalse: "stop"    # stop or step ID
```

### set

Sets variables from responses or static values.

```yaml
- id: set-vars
  type: set
  vars:
    title: "{{http-step.body.title}}"
    count: "10"
```

### delay

Waits for a specified duration.

```yaml
- id: wait
  type: delay
  duration: 5000  # milliseconds
```

### log

Logs a message.

```yaml
- id: log
  type: log
  message: "Processing step {{vars.step}}"
  level: info  # debug, info, warn, error
```

## Variable Syntax

| Type | Syntax | Example |
|------|--------|---------|
| Environment | `${VAR_NAME}` | `${API_KEY}` |
| Input | `{{input.name}}` | `{{input.userId}}` |
| Variable | `{{vars.name}}` | `{{vars.title}}` |
| Step Status | `{{stepId.status}}` | `{{fetch.status}}` |
| Step Body | `{{stepId.body.field}}` | `{{fetch.body.user.name}}` |

## Error Handling

The CLI includes built-in security features:

- **SSRF Protection** - Blocks requests to localhost, private IPs, and cloud metadata endpoints
- **Validation** - All workflows are validated before execution
- **Timeouts** - Configurable timeouts per step and globally
- **Error messages** - Clear error messages with step context

## CLI Commands

- `webhook validate <file>` - Validate a workflow file
- `webhook run <file>` - Run a workflow
- `webhook --help` - Show help
- `webhook --version` - Show version

## License

MIT