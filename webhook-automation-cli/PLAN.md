# Webhook Automation CLI - Implementation Plan

## 1. Project Overview

**Project Name**: Webhook Automation CLI  
**Type**: Local CLI tool for chaining HTTP requests with variables, conditionals, and workflows  
**Analogy**: A local Zapier/IFTTT - enables users to define automated workflows that chain HTTP requests, transform responses, apply conditional logic, and branch based on results

### Core Value Proposition
- Execute complex multi-step HTTP workflows from YAML definitions
- Define variables extracted from API responses for use in subsequent requests
- Apply conditional logic to route workflow execution paths
- Support workflows: linear sequences, parallel branches, loops
- No external service dependencies - runs entirely locally

---

## 2. File Structure

```
webhook-automation-cli/
├── bin/
│   └── webhook-cli.js          # Entry point (shebang: node)
├── src/
│   ├── cli/
│   │   ├── index.js          # CLI argument parsing
│   │   ├── commands/
│   │   │   ├── run.js        # 'run' command
│   │   │   ├── validate.js   # 'validate' command
│   │   │   ├── init.js       # 'init' command - scaffold workflow
│   │   │   └── list.js       # 'list' command - list workflows
│   │   └── options.js        # Global CLI options
│   ├── core/
│   │   ├── engine.js         # Workflow execution engine
│   │   ├── executor.js      # Single step execution
│   │   ├── variableStore.js # Variable storage and resolution
│   │   └── stateMachine.js  # Workflow state management
│   ├── parser/
│   │   ├── yaml.js          # YAML parsing
│   │   ├── schema.js         # JSON Schema validation
│   │   └── interpolator.js  # Variable interpolation
│   ├── steps/
│   │   ├── http.js          # HTTP request step
│   │   ├── condition.js    # Conditional step
│   │   ├── transform.js    # Transform step
│   │   ├── delay.js         # Delay step
│   │   ├── set.js           # Set variable step
│   │   └── log.js           # Logging step
│   ├── error/
│   │   └── errors.js        # Custom error classes
│   └── util/
│       ├── http.js          # HTTP client (fetch wrapper)
│       ├── logger.js       # Logging utility
│       └── retry.js         # Retry logic
├── workflows/               # User workflow definitions
│   ├── .gitkeep
│   └── examples/            # Example workflows
├── templates/               # Workflow templates
│   └── basic.yaml
├── config/
│   └── default.yaml         # Default configuration
├── package.json
├── tsconfig.json           # TypeScript configuration
├── jest.config.js          # Test configuration
├── eslint.config.js       # Linting configuration
├── .gitignore
└── README.md
```

### Alternative Structure (Monolithic for Simpler Projects)
```
webhook-automation-cli/
├── src/
│   ├── index.ts            # Entry point
│   ├── types.ts            # Type definitions
│   ├── workflow.ts         # Workflow definition & execution
│   ├── step.ts            # Step definitions
│   ├── engine.ts           # Execution engine
│   ├── http.ts             # HTTP client
│   ├── variables.ts        # Variable resolution
│   ├── condition.ts        # Condition evaluation
│   └── cli.ts             # CLI
├── workflows/
├��─ package.json
├── tsconfig.json
└── tsconfig.build.json
```

---

## 3. Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `commander` | ^12.x | CLI argument parsing |
| `fetch` (node built-in) | - | HTTP requests |
| `yaml` | ^2.x | YAML parsing/serialization |
| `ajv` | ^8.x | JSON Schema validation |
| `ora` | ^7.x | Spinner for CLI progress |
| `chalk` | ^5.x | Color terminal output |
| `dotenv` | ^16.x | Environment variable loading |
| `axios` | ^1.x | Alternative HTTP client (optional) |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | ^5.x | Type safety |
| `ts-node` | ^10.x | TypeScript execution |
| `jest` | ^29.x | Testing |
| `eslint` | ^8.x | Linting |
| `prettier` | ^3.x | Code formatting |
| `@types/node` | ^20.x | Node types |
| `typescript` | ^5.x | TypeScript compiler |

### Optional Enhancement Dependencies

| Package | Purpose |
|---------|---------|
| `enquirer` | Interactive prompts |
| `listr` | Progress task list |
| `cli-table3` | Table output |
| `inquirer` | Interactive CLI |

---

## 4. YAML Workflow Format

### Complete Schema

```yaml
# workflow.yaml
name: "GitHub Issue to Slack Notification"
version: "1.0"              # Schema version
description: "Monitors GitHub issues and notifies Slack"

# Workflow settings
settings:
  timeout: 30000            # Global timeout (ms)
  retry:
    maxAttempts: 3          # Retry attempts
    delay: 1000              # Delay between retries (ms)
    backoff: "exponential"  # linear, exponential
  env:                      # Environment variables for this workflow
    GITHUB_TOKEN: "${GITHUB_TOKEN}"
    SLACK_WEBHOOK: "${SLACK_WEBHOOK}"

# Input variables (from CLI args or file)
input:
  issueId: "${ISSUE_ID}"    # Required input variable

# Workflow steps
steps:
  # Step 1: Fetch GitHub Issue
  - id: fetch-issue
    name: "Fetch GitHub Issue"
    type: http
    request:
      url: "https://api.github.com/repos/${OWNER}/${REPO}/issues/${issueId}"
      method: GET
      headers:
        Accept: "application/vnd.github.v3+json"
        Authorization: "Bearer ${GITHUB_TOKEN}"
    retries: 2
    timeout: 10000

  # Step 2: Check if issue exists
  - id: check-issue
    name: "Check Issue Exists"
    type: condition
    condition: "step.fetch-issue.status == 200"
    onTrue: "continue"
    onFalse:
      - id: notify-error
        name: "Notify Issue Not Found"
        type: http
        request:
          url: "${SLACK_WEBHOOK}"
          method: POST
          headers:
            Content-Type: "application/json"
          body:
            text: "Issue ${issueId} not found"
        stopOnError: true

  # Step 3: Extract variables from response
  - id: extract-data
    name: "Extract Issue Data"
    type: set
   vars:
      title: "{{steps.fetch-issue.body.title}}"
      state: "{{steps.fetch-issue.body.state}}"
      author: "{{steps.fetch-issue.body.user.login}}"
      labels: "{{steps.fetch-issue.body.labels[*].name}}"
      createdAt: "{{steps.fetch-issue.body.created_at}}"

  # Step 4: Check if issue is open
  - id: check-state
    name: "Check Issue State"
    type: condition
    condition: "vars.state == 'open'"
    onTrue: "continue"
    onFalse:
      - id: skip-notification
        name: "Skip Closed Issue"
        type: log
        message: "Issue is closed, skipping notification"
        stop: true

  # Step 5: Send Slack notification
  - id: notify-slack
    name: "Notify Slack"
    type: http
    request:
      url: "${SLACK_WEBHOOK}"
      method: POST
      headers:
        Content-Type: "application/json"
      body: |
        {
          "text": "New Issue: *${vars.title}*",
          "blocks": [
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "*${vars.title}*\nAuthor: ${vars.author}\nLabels: ${vars.labels}"
              }
            }
          ]
        }
    retries: 1
    timeout: 15000

  # Step 6: Log completion
  - id: log-complete
    name: "Log Completion"
    type: log
    message: "Workflow complete - notified Slack about issue ${vars.title}"

# Error handling workflow
errorHandler:
  - name: "Notify on Failure"
    type: http
    request:
      url: "${SLACK_WEBHOOK}"
      method: POST
      body:
        text: "Workflow failed: {{error.message}}"
```

### Step Types

#### 4.1 HTTP Request Step

```yaml
- id: my-request
  name: "Description"
  type: http
  request:
    url: "https://api.example.com/endpoint"
    method: GET|POST|PUT|PATCH|DELETE
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${TOKEN}"
    query:                 # Query string parameters
      page: 1
      limit: 10
    body:                  # Request body (for POST/PUT/PATCH)
      key: "value"
      nested:
        foo: "bar"
  # Response handling
  response:
    # Store full response
    saveAs: "response"    # Variable name for full response
    # Store specific fields (JSONPath or jq syntax)
    body:
      id: ".id"
      name: ".name"
      items: ".data[].name"
  # HTTP options
  timeout: 30000         # Request timeout (ms)
  retries:
    maxAttempts: 3         # Number of retries
    delay: 1000           # Base delay
    backoff: "exponential"
  # SSL options
  insecure: false         # Allow self-signed certs
  # Conditional execution
  condition: "vars.shouldExecute == true"
```

#### 4.2 Condition Step

```yaml
- id: check-status
  name: "Check Status Code"
  type: condition
  condition: "steps.http-step.status == 200"
  # Control flow
  onTrue: "continue"       # continue, stop, or step ID
  onFalse: "stop"         # stop or step ID
  onFalse:                # Execute multiple steps on false
    - id: handle-error
      type: log
      message: "Request failed"
```

**Condition Expression Support**:
- Comparisons: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `startsWith`, `endsWith`
- Boolean: `and`, `or`, `not`
- Variables: `{{vars.name}}`, `{{steps.stepId.status}}`
- JSONPath: `{{steps.step.body.data[0].id}}`
- Regex: `matches(/pattern/)`

#### 4.3 Set Variable Step

```yaml
- id: set-vars
  name: "Set Variables"
  type: set
  vars:
    # Direct value
    simpleVar: "value"
    # Interpolated from response
    title: "{{steps.http-step.body.title}}"
    # Computed
    fullName: "{{vars.firstName}} {{vars.lastName}}"
    # JSONPath
    firstItem: "{{steps.http-step.body.items[0].name}}"
    # Conditional expression
    statusText: "{{vars.isActive ? 'Active' : 'Inactive'}}"
    # Array from response
    allNames: "{{steps.http-step.body.users[*].name}}"
```

#### 4.4 Delay Step

```yaml
- id: wait-for-rate-limit
  name: "Wait for Rate Limit"
  type: delay
  duration: 5000           # milliseconds
  # Or dynamic
  duration: "{{vars.waitTime}}"
```

#### 4.5 Transform Step

```yaml
- id: transform-data
  name: "Transform Data"
  type: transform
  input: "{{steps.http-step.body}}"
  # Using JSONPath or template
  output: |
    {{#each items}}
    {
      "name": "{{this.name}}",
      "value": {{this.value}}
    }
    {{/each}}
  # Or jq-style
  query: ".data[] | select(.active == true)"
```

#### 4.6 Log Step

```yaml
- id: log-progress
  name: "Log Progress"
  type: log
  message: "Processing item {{vars.currentItem}}"
  level: info             # debug, info, warn, error
```

#### 4.7 Iterate/Loop Step (Advanced)

```yaml
- id: process-items
  name: "Process All Items"
  type: iterate
  over: "{{steps.fetch-items.body.items}}"
  itemVar: "item"
  indexVar: "index"
  steps:
    - id: process-item
      type: http
      request:
        url: "https://api.example.com/process"
        method: POST
        body:
          id: "{{vars.item.id}}"
```

---

## 5. Variable System

### Variable Types

| Type | Syntax | Example |
|------|--------|---------|
| Environment | `${ENV_NAME}` | `${GITHUB_TOKEN}` |
| Input | `${input.name}` | `${input.issueId}` |
| Step Response | `{{steps.stepId.status}}` | `{{steps.fetch.status}}` |
| Step Body | `{{steps.stepId.body.field}}` | `{{steps.fetch.body.title}}` |
| User Variable | `{{vars.name}}` | `{{vars.title}}` |
| Previous Step | `{{prev.body}}` | `{{prev.status}}` |

### Variable Resolution Order

1. **Built-in Variables** - `{{workflow.name}}`, `{{workflow.version}}`
2. **Input Variables** - `{{input.*}}`
3. **Environment Variables** - `${ENV_NAME}`
4. **User Variables** - `{{vars.*}}` (from `set` steps)
5. **Step Variables** - `{{steps.*}}`

### Variable Interpolation Syntax

```yaml
# Simple variable
{{vars.name}}

# Nested property
{{steps.http-step.body.user.name}}

# Array access
{{steps.fetch.body.items[0].name}}

# Array spread
{{steps.fetch.body.items[*].id}}

# Conditional
{{vars.isActive ? 'yes' : 'no'}}

# Array filter
{{steps.fetch.body.items[?(@.status=="active")].name}}

# Default value
{{vars.missing | 'default'}}
```

---

## 6. Core Engine Architecture

### Execution Model

```
┌─────────────────┐
│  Load Workflow  │
└─���──────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate YAML  │
│  (JSON Schema)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Resolve Env    │
│  Variables     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse Steps    │
│  Build DAG      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Initialize    │
│  State Machine │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Execute Steps │
│  (Linear/      │
│   Parallel)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Handle Errors │
│  or Complete   │
└─────────────────┘
```

### Class Design

```typescript
// src/core/engine.ts
class WorkflowEngine {
  constructor(config: EngineConfig)
  async execute(workflow: Workflow, context: ExecutionContext): Promise<ExecutionResult>
  async validate(workflow: Workflow): Promise<ValidationResult>
}

// src/core/executor.ts
class StepExecutor {
  constructor(httpClient: HttpClient, variableStore: VariableStore)
  async execute(step: Step, context: ExecutionContext): Promise<StepResult>
}

// src/core/variableStore.ts
class VariableStore {
  get(path: string): any
  set(path: string, value: any): void
  interpolate(template: string): string
}

// src/core/stateMachine.ts
class StateMachine {
  constructor(steps: Step[])
  currentStep(): Step | null
  next(): Step | null
  jumpTo(stepId: string): void
  canContinue(): boolean
}
```

---

## 7. Error Handling

### Error Types

```typescript
// src/error/errors.ts

class WorkflowError extends Error {
  stepId?: string
  workflowName: string
}

class ValidationError extends WorkflowError {
  errors: ValidationError[]
}

class StepExecutionError extends WorkflowError {
  statusCode?: number
  response?: any
  retryable: boolean
}

class TimeoutError extends StepExecutionError {}

class ConditionError extends WorkflowError {
  condition: string
  evaluated: any
}

class VariableResolutionError extends WorkflowError {
  variable: string
}

class CyclicDependencyError extends WorkflowError {
  cycle: string[]
}
```

### Error Handling Strategy

| Error Type | Default Behavior | Configurable |
|------------|-----------------|--------------|
| Network Error | Retry with backoff | Via `retries` config |
| HTTP 4xx | Stop workflow | `continueOnError`, `onError` step |
| HTTP 5xx | Retry then stop | Via `retries` config |
| Timeout | Retry then stop | Via `timeout`, `retries` |
| Condition Failed | Continue (false branch) | Automatic |
| Variable Not Found | Stop with error | `default` value |
| Validation Error | Stop before execution | N/A |

### Retry Configuration

```yaml
settings:
  retry:
    maxAttempts: 3
    delay: 1000              # Initial delay (ms)
    backoff: "exponential"   # linear, exponential, fixed
    maxDelay: 30000         # Cap on delay
    retryableStatuses:      # HTTP statuses to retry
      - 408
      - 429
      - 500
      - 502
      - 503
      - 504
    retryableErrors:       # Error types to retry
      - "ECONNRESET"
      - "ETIMEDOUT"
      - "ENOTFOUND"
```

### Global Error Handler

```yaml
errorHandler:
  - name: "Log Error"
    type: log
    message: "Error: {{error.message}}"
    level: error

  - name: "Notify Failure"
    condition: "${SLACK_WEBHOOK}"
    type: http
    request:
      url: "${SLACK_WEBHOOK}"
      method: POST
      body:
        text: "Workflow {{workflow.name}} failed: {{error.message}}"
```

---

## 8. Edge Cases

### 8.1 Circular Dependencies

**Problem**: Step A references Step B, Step B references Step A  
**Solution**: Detect cycles in step graph before execution

```yaml
# Detect and reject
- id: step-a
  type: condition
  condition: "{{steps.step-b.body.success}}"
  onTrue: "step-b"

- id: step-b
  type: set
  vars:
    value: "{{steps.step-a.body.data}}"
```

### 8.2 Infinite Loops

**Problem**: Workflow loops forever  
**Solution**: Maximum step execution limit

```yaml
settings:
  maxSteps: 100           # Maximum steps to execute
  maxIterations: 10      # Maximum loop iterations
  loopDetection: true    # Detect repeated patterns
```

### 8.3 Rate Limiting

**Problem**: API rate limits exceeded  
**Solution**: Built-in rate limit handling

```yaml
- id: api-request
  type: http
  request:
    url: "https://api.example.com/data"
  rateLimit:
    requests: 10           # Requests
    window: 60000         # Per window (ms)
    wait: true            # Wait instead of fail
```

### 8.4 Large Response Bodies

**Problem**: Response too large to store in memory  
**Solution**: Stream response, limit size

```yaml
- id: download-file
  type: http
  request:
    url: "https://api.example.com/file"
    method: GET
  response:
    maxSize: 10485760       # 10MB limit
    saveTo: "./downloads"  # Stream to file
```

### 8.5 Long-Running Workflows

**Problem**: Workflow takes hours/days  
**Solution**: Checkpoint/save state

```yaml
settings:
  checkpointInterval: 60   # Save every N steps
  checkpointFile: "./state.json"
  # Resume from checkpoint
  resume: true
```

### 8.6 Sensitive Data in Logs

**Problem**: Tokens/passwords logged  
**Solution**: Auto-mask secrets

```yaml
settings:
  maskSecrets:
    - "**TOKEN**"
    - "**PASSWORD**"
    - "Authorization"
    - "access_token"
  maskPatterns:
    - "/sk_live_[a-zA-Z0-9]+/"
```

### 8.7 Concurrent Workflow Execution

**Problem**: Need to run multiple workflows  
**Solution**: Workflow queue

```yaml
# CLI
webhook run workflow.yaml --parallel 3

# Queue config
settings:
  queue:
    maxConcurrent: 5
    queuePolicy: "drop-oldest"  # drop-oldest, reject, wait
```

### 8.8 Webhook/Callback Support

**Problem**: Need to wait for external callback  
**Solution**: Long polling or webhook endpoint

```yaml
- id: await-callback
  type: wait
  webhook:                 # Expose webhook endpoint
    port: 3000
    path: "/webhook/github"
    timeout: 300000       # 5 minutes
  # Or poll
  poll:
    url: "https://api.example.com/status/${jobId}"
    interval: 5000
    timeout: 300000
```

### 8.9 Missing/Null Values

**Problem**: Response field missing  
**Solution**: Default values

```yaml
- id: get-user
  type: set
  vars:
    name: "{{steps.fetch.body.user.name | 'Anonymous'}}"
    email: "{{steps.fetch.body.user.email}}"
    # Null coalesce
    displayName: "{{vars.name || 'No Name'}}"
```

### 8.10 Schema Versioning

**Problem**: Old workflow files incompatible  
**Solution**: Version header

```yaml
# workflow.yaml
version: "1.0"             # Required - schema version
schema: "https://schemas.example.com/workflow/v1.json"

# Backward compatibility
settings:
  legacyMode: false         # Allow old syntax
  autoMigrate: true        # Auto-upgrade on load
```

---

## 9. CLI Commands

### Command Structure

```bash
# Run a workflow
webhook run <workflow-file> [options]
webhook run github-issue.yaml --input issueId=123
webhook run github-issue.yaml --env GITHUB_TOKEN=xxx

# Validate a workflow
webhook validate <workflow-file>
webhook validate --schema v1

# Initialize a new workflow
webhook init my-workflow
webhook init my-workflow --template basic

# List workflows
webhook list
webhook list --path ./workflows

# Show version
webhook --version

# Global options
--verbose          # Verbose output
--config <file>   # Config file
--env <file>      # env file to load
```

### Environment Variables

```bash
# Set via CLI
export WEBHOOK_CONFIG=./config.yaml
export WEBHOOK_TIMEOUT=60000

# .env file
GITHUB_TOKEN=xxx
SLACK_WEBHOOK=https://...
```

---

## 10. Implementation Roadmap

### Phase 1: Core Engine (Week 1-2)
- [ ] Project setup (package.json, TypeScript config)
- [ ] CLI argument parsing (commander)
- [ ] YAML parsing
- [ ] JSON Schema validation
- [ ] Variable store and interpolation
- [ ] Basic HTTP execution

### Phase 2: Step Types (Week 2-3)
- [ ] HTTP step implementation
- [ ] Condition step implementation
- [ ] Set variable step
- [ ] Delay step
- [ ] Log step

### Phase 3: Advanced Features (Week 3-4)
- [ ] Retry logic
- [ ] Error handling
- [ ] Conditional expressions
- [ ] JSONPath support
- [ ] Loop/iterate step

### Phase 4: Polish (Week 4-5)
- [ ] CLI progress output
- [ ] Checkpoint/resume
- [ ] Logging with levels
- [ ] Example workflows
- [ ] Documentation

### Phase 5: Production Ready (Week 5-6)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Error messages
- [ ] Performance optimization
- [ ] Release

---

## 15. Security Considerations (Critical)

### SSRF Prevention (CRITICAL)

Server-Side Request Forgery prevention is essential - users may inadvertently or maliciously target internal infrastructure.

```typescript
// Blocked hosts and IP ranges
const BLOCKED_HOSTS = [
  'localhost',
  '127.0.0.1',
  '0.0.0.0',
  '::1',
  // AWS metadata endpoint
  '169.254.169.254',
  // GCP metadata
  'metadata.google.internal',
  // Azure metadata
  '169.254.169.254',
  // Internal RFC 1918 ranges
  '10.0.0.0/8',
  '172.16.0.0/12',
  '192.168.0.0/16',
  // Link-local
  '169.254.0.0/16',
];

function validateUrl(url: string): boolean {
  const parsed = new URL(url);
  
  // Block blocked hostnames
  if (BLOCKED_HOSTS.includes(parsed.hostname)) return false;
  
  // Block IP ranges
  const ip = parsed.hostname;
  if (ip.match(/^10\./)) return false;
  if (ip.match(/^172\.(1[6-9]|2[0-9]|3[0-1])\./)) return false;
  if (ip.match(/^192\.168\./)) return false;
  
  // Only allow http/https
  if (!['http:', 'https:'].includes(parsed.protocol)) return false;
  
  return true;
}

// Usage in HTTP step
beforeRequest((request) => {
  if (!validateUrl(request.url)) {
    throw new SecurityError(`URL blocked: ${request.url}`);
  }
});
```

### Secrets Handling

```yaml
# SECRETS SHOULD NEVER BE IN YAML
# BAD - will be in git history, logs
steps:
  - request:
      headers:
        Authorization: "Bearer sk_live_xxx"  # NEVER

# GOOD - environment variables
steps:
  - request:
      headers:
        Authorization: "Bearer ${GITHUB_TOKEN}"  # External

# Configuration
settings:
  # Warn if these patterns found in YAML
  secretPatterns:
    - "sk_live_"
    - "AKIA[0-9A-Z]{16}"
    - "ghp_[a-zA-Z0-9]{36}"
  
  # Auto-mask these in logs
  maskFields:
    - "Authorization"
    - "X-API-Key"
    - "password"
    - "token"
    - "secret"
```

### URL Allowlist (Enterprise)

```yaml
settings:
  allowedDomains:
    - "api.github.com"
    - "slack.com"
    - "api.example.com"
  # Or explicit blocklist
  blockedDomains:
    - "internal.company.local"
```

---

## 16. Clarifications Needed Before Implementation

| Question | Options | Recommendation |
|----------|---------|----------------|
| **Execution Model** | Sequential / Parallel | Start sequential, add parallel later |
| **Storage** | File / SQLite / None | File-based JSON logs |
| **Secrets** | Env vars only / Vault / AWS Secrets | Env vars for MVP |
| **Platforms** | Current OS / Cross-platform | Current OS first |
| **Triggers** | Manual only / File watch / Cron / Webhook | Manual for MVP |
| **Auth Methods** | API Key / Basic / OAuth2 | OAuth2 post-MVP |
| **Mock Mode** | Yes / No | Essential for testing |
| **Concurrency** | 1 / N workflows | Start with 1 |

---

## 17. Error Hierarchy

```
WorkflowError (base)
├── NetworkError
│   ├── TimeoutError
│   ├── ConnectionError
│   ├── DNSError
│   └── TLSError
├── HTTPError
│   ├── StatusCodeError (4xx, 5xx)
│   └── ResponseParsingError
├── ValidationError
│   ├── SchemaValidationError
│   └── VariableNotFoundError
├── ExecutionError
│   ├── ConditionEvaluationError
│   ├── StepFailedError
│   └── CyclicDependencyError
├── SecurityError
│   ├── SSRFBlockedError
│   └── SecretLeakError
└── ConfigurationError
    ├── YAMLParsingError
    └── InvalidSchemaError
```

---

## 18. Implementation Priority

### MVP (v1.0) - Week 1-2
- [ ] YAML parsing + HTTP execution
- [ ] Variable interpolation (`${var}`, `{{steps.X}}`)
- [ ] Sequential step execution
- [ ] Basic error handling
- [ ] CLI: `run`, `validate`

### v1.1 - Week 3
- [ ] Conditionals (`type: condition`)
- [ ] Retry logic with backoff
- [ ] Response validation
- [ ] Logs/history

### v1.2 - Week 4
- [ ] Parallel execution
- [ ] Circuit breaker
- [ ] Delay step
- [ ] Iterate/loop step

### v1.3+ - Week 5+
- [ ] Secret management integration
- [ ] OAuth2/JWT support
- [ ] Webhook triggers
- [ ] Cron scheduling

---

## 11. Testing Strategy

### Unit Tests
- Variable interpolation
- Condition evaluation
- Step parsing
- Error handling

### Integration Tests
- Full workflow execution
- CLI commands
- Error scenarios

### Example Test Workflows
```yaml
# test-linear.yaml
steps:
  - id: step1
    type: http
    request:
      url: "https://httpbin.org/get"
      method: GET

  - id: step2
    type: condition
    condition: "{{steps.step1.status}} == 200"
    onTrue: "step3"

  - id: step3
    type: log
    message: "Success"
```

---

## 12. Performance Considerations

### Caching
- Cache environment variable resolution
- Cache schema validation

### Streaming
- Stream large responses
- Stream logs

### Limits
- Default timeout: 30s
- Max response size: 10MB
- Max workflow steps: 100
- Max concurrent workflows: 5

---

## 13. Security Considerations

### Secrets Handling
- Never log secrets
- Use environment variables for tokens
- Support secret masking
- Warn on secrets in YAML

### Input Validation
- Validate all URLs
- Sanitize interpolated values
- Limit recursion depth

### Network Security
- HTTPS only by default
- Certificate validation
- Proxy support

---

## 14. Future Enhancements

- [ ] GraphQL support
- [ ] WebSocket support
- [ ] AWS Lambda integration
- [ ] Schedule workflows (cron)
- [ ] Webhook triggers
- [ ] Workflow templates marketplace
- [ ] Visual workflow editor (web UI)
- [ ] History/analytics
- [ ] Team collaboration