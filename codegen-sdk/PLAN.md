# codegen-sdk Implementation Plan

## 1. Project Overview

**codegen-sdk** is a CLI tool that generates typed client SDKs from OpenAPI 3.x / Swagger 2.0 specifications or Postman collections, or by introspecting a running API. Supports TypeScript, Python, Go, and Rust.

### Core Features

- Parse OpenAPI 3.x and Swagger 2.0 specs
- Parse Postman Collection v2.1
- Introspect running APIs via OpenAPI generation tools (Swagger UI, RapiDoc)
- Generate type-safe clients in 4 languages
- Validate endpoint definitions and generate proper error types
- Handle authentication flows (API Key, Bearer, OAuth 2.0, Basic)
- Support custom templates for extensibility

---

## 2. File Structure

```
codegen-sdk/
├── Cargo.toml                 # Rust project (core logic)
├── src/
│   ├── main.rs               # CLI entry point
│   ├── lib.rs                # Library root
│   ├── cli/
│   │   ├── mod.rs
│   │   ├── commands/
│   │   │   ├── mod.rs
│   │   │   ├── generate.rs   # Main generate command
│   │   │   ├── validate.rs   # Validate spec command
│   │   │   ├── init.rs       # Initialize config
│   │   │   └── introspect.rs # Introspect running API
│   │   ├── args.rs           # CLI argument definitions
│   │   └── output.rs         # Output formatting
│   ├── parser/
│   │   ├── mod.rs
│   │   ├── openapi/
│   │   │   ├── mod.rs
│   │   │   ├── parser.rs     # OpenAPI spec parsing
│   │   │   ├── schema.rs     # Schema resolution
│   │   │   └── validator.rs  # Spec validation
│   │   ├── postman/
│   │   │   ├── mod.rs
│   │   │   └── parser.rs     # Postman collection parsing
│   │   └── types.rs          # Unified IR (Intermediate Representation)
│   ├── codegen/
│   │   ├── mod.rs
│   │   ├── types.rs          # Codegen type definitions
│   │   ├── renderer.rs       # Template rendering trait
│   │   ├── typescript/
│   │   │   ├── mod.rs
│   │   │   ├── client.rs     # TS client generation
│   │   │   └── types.rs      # TS type generation
│   │   ├── python/
│   │   │   ├── mod.rs
│   │   │   ├── client.rs     # Python client generation
│   │   │   └── types.rs      # Python type generation
│   │   ├── go/
│   │   │   ├── mod.rs
│   │   │   ├── client.rs     # Go client generation
│   │   │   └── types.go      # Go type generation
│   │   └── rust/
│   │       ├── mod.rs
│   │       ├── client.rs     # Rust client generation
│   │       └── types.rs      # Rust type generation
│   ├── introspection/
│   │   ├── mod.rs
│   │   ├── scraper.rs        # HTML/JS scraping
│   │   ├── openapigen.rs     # Integration with openapi-generator
│   │   └── detector.rs       # API detection
│   ├── config/
│   │   ├── mod.rs
│   │   ├── model.rs          # Config struct
│   │   └── loader.rs         # Config file loading
│   ├── templates/
│   │   ├── mod.rs
│   │   ├── embedded.rs       # Embedded templates
│   │   └── custom.rs         # Custom template loading
│   └── utils/
│       ├── mod.rs
│       ├── http.rs           # HTTP client utilities
│       ├── logging.rs        # Logging setup
│       └── errors.rs         # Error utilities
├── templates/                 # Custom template directory
│   ├── typescript/
│   ├── python/
│   ├── go/
│   └── rust/
├── tests/
│   ├── fixtures/
│   │   ├── openapi/
│   │   ├── postman/
│   │   └── generated/
│   ├── integration/
│   └── unit/
├── examples/
├── CONTRIBUTING.md
├── README.md
└── CHANGELOG.md
```

---

## 3. CLI Interface

### Command Structure

```
codegen-sdk <COMMAND> [OPTIONS]
```

### Commands

#### 3.1 `generate` (Primary Command)

```bash
codegen-sdk generate [INPUT] [OPTIONS]
```

**Arguments:**

- `INPUT`: Path to spec file (`.json`, `.yaml`, `.yml`) or URL

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output <DIR>` | Output directory | `./generated` |
| `-l, --language <LANG>` | Target language | `typescript` |
| `--lang <LANG>` | Alias for --language | |
| `-n, --name <NAME>` | Client name (package/module name) | From spec info.title |
| `--namespace <NS>` | Namespace/module path | `Api` |
| `-t, --template <PATH>` | Custom template directory | Built-in |
| `--skip-validation` | Skip spec validation | `false` |
| `--strict` | Strict mode (fail on warnings) | `false` |
| `--auth <TYPE>` | Default auth type override | From spec |
| `--base-url <URL>` | Override base URL | From spec servers |
| `--header <KEY=VALUE>` | Add default headers | |
| `--no-client` | Generate types only, no client | `false` |
| `--force` | Overwrite existing files | `false` |

**Examples:**

```bash
# Generate TypeScript client from OpenAPI spec
codegen-sdk generate openapi.yaml -l typescript -o ./src/api

# Generate Python client from Postman collection
codegen-sdk generate collection.json -l python -n myapi

# Generate Go client with custom template
codegen-sdk generate https://api.example.com/openapi.json -l go -t ./templates/go

# Generate with auth override
codegen-sdk generate api.yaml -l typescript --auth bearer --base-url https://api.example.com
```

#### 3.2 `validate`

```bash
codegen-sdk validate <INPUT> [OPTIONS]
```

**Options:**

| Flag | Description |
|------|-------------|
| `-f, --format <FMT>` | Output format: `text`, `json`, `sarif` |
| `--strict` | Treat warnings as errors |

**Exit Codes:**

- `0`: Valid
- `1`: Validation errors found
- `2`: Parse error (invalid format)

#### 3.3 `init`

```bash
codegen-sdk init [OPTIONS]
```

Creates a `.codegen.yaml` config file in current directory.

**Options:**

| Flag | Description |
|------|-------------|
| `-l, --language <LANG>` | Default language |
| `-o, --output <DIR>` | Default output directory |
| `--force` | Overwrite existing config |

#### 3.4 `introspect`

```bash
codegen-sdk introspect <URL> [OPTIONS]
```

Introspect a running API and generate spec.

**Options:**

| Flag | Description |
|------|-------------|
| `-o, --output <FILE>` | Output spec file |
| `--scraper <TYPE>` | Scraper: `swagger-ui`, `rapidoc`, `auto` |
| `--header <KEY=VALUE>` | Auth headers for introspection |

---

## 4. Configuration File

**File:** `.codegen.yaml` (or `codegen.config.yaml`)

```yaml
# codegen-sdk configuration
version: "1.0"

# Default language
language: typescript

# Output directory
output: ./generated

# Client name
name: my-api-client

# Custom template directory
# template: ./templates/my-template

# Generation options
options:
  # Skip spec validation
  skip-validation: false
  
  # Generate types only (no client)
  types-only: false
  
  # Overwrite existing files
  force: false
  
  # Strict mode (fail on warnings)
  strict: false

# Auth defaults (override spec)
auth:
  type: bearer
  # token: ${API_TOKEN}  # Env var reference

# Base URL override
base-url: https://api.example.com/v1

# Default headers
headers:
  X-Client: codegen-sdk
  X-Request-Id: ${REQUEST_ID}  # Dynamic

# Include/exclude paths (regex)
include:
  - ^/api/v1/
exclude:
  - ^/internal/
  - ^/deprecated/

# Language-specific options
typescript:
  module: esm           # esm, cjs, umd
  out-dir: ./src
  include-comments: true
  rxjs-version: "^7.0.0"
  
python:
  package-name: my_api_client
  version: "0.1.0"
  include-models: true
  
go:
  package-name: api
  generate-interface: true
  with-json-tags: true
  
rust:
  crate-name: api-client
  reqwest-version: "0.11"
  serde-version: "1.0"
```

---

## 5. Spec Parsing Layer

### 5.1 Unified Intermediate Representation (IR)

All specs convert to a unified IR for code generation:

```rust
// src/parser/types.rs

pub struct ApiSpec {
    pub info: ApiInfo,
    pub servers: Vec<Server>,
    pub endpoints: Vec<Endpoint>,
    pub schemas: Vec<Schema>,
    pub security: Vec<SecurityScheme>,
    pub extensions: HashMap<String, Value>,
}

pub struct ApiInfo {
    pub title: String,
    pub version: String,
    pub description: Option<String>,
    pub contact: Option<Contact>,
    pub license: Option<License>,
}

pub struct Endpoint {
    pub path: String,
    pub method: HttpMethod,
    pub operation_id: Option<String>,
    pub summary: Option<String>,
    pub description: Option<String>,
    pub deprecated: bool,
    pub tags: Vec<String>,
    pub parameters: Vec<Parameter>,
    pub request_body: Option<RequestBody>,
    pub responses: Vec<Response>,
    pub security: Vec<Vec<String>>, // ANDed requirements
}

pub enum HttpMethod {
    Get, Post, Put, Patch, Delete, Head, Options,
}

pub struct Parameter {
    pub name: String,
    pub location: ParameterLocation, // path, query, header, cookie
    pub required: bool,
    pub schema: Schema,
    pub description: Option<String>,
    pub deprecated: bool,
}

pub enum ParameterLocation {
    Path,
    Query,
    Header,
    Cookie,
}

pub struct RequestBody {
    pub required: bool,
    pub content: HashMap<String, MediaType>,
    pub description: Option<String>,
}

pub struct Response {
    pub status_code: u16,
    pub description: String,
    pub headers: HashMap<String, Header>,
    pub content: HashMap<String, MediaType>,
}

pub struct Schema {
    pub name: Option<String>, // For named schemas
    pub schema_type: SchemaType,
    pub required: Vec<String>,
    pub description: Option<String>,
    pub deprecated: bool,
    pub default: Option<Value>,
    pub example: Option<Value>,
    pub extensions: HashMap<String, Value>,
}

pub enum SchemaType {
    Integer { format: Option<IntegerFormat> },
    Number { format: Option<NumberFormat> },
    String { format: Option<StringFormat>, enum_values: Option<Vec<String>> },
    Boolean,
    Array { items: Box<Schema> },
    Object {
        properties: HashMap<String, Schema>,
        additional_properties: Option<Box<Schema>>,
    },
    OneOf { schemas: Vec<Schema> },
    AllOf { schemas: Vec<Schema> },
    AnyOf { schemas: Vec<Schema> },
    Ref { path: String }, // $ref resolution
    Enum { values: Vec<Value> },
    Unknown,
}

pub enum IntegerFormat {
    Int32,
    Int64,
    Int,
    Long,
    Integer,
}

pub enum NumberFormat {
    Float,
    Double,
    Number,
}

pub enum StringFormat {
    Email,
    Uri,
    Uuid,
    Date,
    DateTime,
    Binary,
    Byte,
    Password,
    hostname,
    IPv4,
    IPv6,
}

pub struct SecurityScheme {
    pub name: String,
    pub scheme_type: SecuritySchemeType,
    pub description: Option<String>,
    // API Key specific
    pub location: Option<ParameterLocation>, // header, query, cookie
    // OAuth2 specific
    pub flows: Option<Vec<OAuth2Flow>>,
}

pub enum SecuritySchemeType {
    ApiKey { location: ParameterLocation },
    Http { scheme: String }, // basic, bearer
    OAuth2,
    OpenIdConnect { url: String },
}

pub struct OAuth2Flow {
    pub flow_type: OAuth2FlowType,
    pub authorization_url: Option<String>,
    pub token_url: Option<String>,
    pub scopes: HashMap<String, String>,
}

pub enum OAuth2FlowType {
    AuthorizationCode,
    Implicit,
    ClientCredentials,
    Password,
}
```

### 5.2 OpenAPI Parser

**Dependencies:**

- `swagger-parser` (Rust crate) - OpenAPI 3.x validation
- `serde_yaml` - YAML parsing
- `serde_json` - JSON parsing

**Parser Flow:**

```
OpenAPI File → Parse YAML/JSON → Validate Schema → Resolve $ref → Build IR
```

**Key Functions:**

```rust
// src/parser/openapi/parser.rs

pub struct OpenApiParser;

impl OpenApiParser {
    pub fn parse(input: &str) -> Result<ApiSpec, ParseError>;
    pub fn parse_file(path: &Path) -> Result<ApiSpec, ParseError>;
    pub fn parse_url(url: &str) -> Result<ApiSpec, ParseError>;
}

pub struct OpenApiValidator;

impl OpenApiValidator {
    pub fn validate(spec: &ApiSpec) -> Vec<ValidationError>;
}
```

### 5.3 Postman Parser

**Dependencies:**

- `serde_json` - Postman uses JSON format

**Conversion Rules:**

| Postman Concept | OpenAPI Concept |
|-----------------|-----------------|
| Request | Endpoint |
| Method | HttpMethod |
| URL (variables) | Path + Parameters |
| Header | Parameter (header) |
| Query Param | Parameter (query) |
| Body | RequestBody |
| Response | Response |
| Auth | SecurityScheme |

---

## 6. Code Generation Modules

### 6.1 TypeScript Generation

**Output Structure:**

```
typescript/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # Main export
│   ├── client.ts             # Base client class
│   ├── types.ts              # Generated types
│   ├── endpoints/
│   │   ├── users.ts
│   │   └── products.ts
│   └── errors.ts             # Generated error types
└── README.md
```

**Generated Client Features:**

- Axios or Fetch-based HTTP client
- Full TypeScript types for all endpoints
- Proper error types mapped to HTTP status codes
- Request/response interceptors
- Authentication handling (auto-refresh for OAuth2)
- Cancelable requests (AbortController)
- Retry logic with exponential backoff

**Template Example (client.ts):**

```typescript
// Generated client
export class ApiClient {
  private baseUrl: string;
  private headers: Record<string, string>;
  private auth: AuthHandler;
  
  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.headers = config.headers || {};
    this.auth = config.auth;
  }
  
  async getUsers(params?: GetUsersParams): Promise<User[]> {
    const response = await this.request({
      method: 'GET',
      path: '/users',
      params,
    });
    return response.data;
  }
  
  // Each endpoint method
}
```

### 6.2 Python Generation

**Output Structure:**

```
python/
├── pyproject.toml
├── src/
│   └── my_api_client/
│       ├── __init__.py
│       ├── client.py
│       ├── models.py
│       ├── exceptions.py
│       └── endpoints/
│           ├── __init__.py
│           └── users.py
├── tests/
└── README.md
```

**Generated Client Features:**

- `requests` or `httpx` for HTTP
- Pydantic models for request/response types
- TypedDict for response shapes
- Custom exceptions per endpoint/status code
- Context manager for client
- Async support (optional with httpx)

### 6.3 Go Generation

**Output Structure:**

```
go/
├── go.mod
├── client.go                 # HTTP client
├── types.go                  # Generated types
├── endpoints.go              # Endpoint methods
├── errors.go                 # Error types
└── README.md
```

**Generated Client Features:**

- Native `net/http` or generated interfaces
- Strongly typed request/response structs
- Error types implementing `error` interface
- Context support for all requests
- Retry middleware
- Authentication middleware

### 6.4 Rust Generation

**Output Structure:**

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── client.rs
│   ├── types.rs
│   ├── endpoints.rs
│   └── error.rs
└── README.md
```

**Generated Client Features:**

- `reqwest` or `ureq` for HTTP
- `serde` for serialization
- `thiserror` for error types
- `async` / `await` support
- Strong type safety

---

## 7. Error Handling System

### 7.1 Error Taxonomy

```
ApiError (base)
├── NetworkError
│   ├── ConnectionError
│   ├── TimeoutError
│   └── DnsError
├── ValidationError (4xx)
│   ├── BadRequestError (400)
│   ├── UnauthorizedError (401)
│   ├── ForbiddenError (403)
│   ├── NotFoundError (404)
│   ├── ConflictError (409)
│   ├── UnprocessableError (422)
│   └── RateLimitError (429)
├── ServerError (5xx)
│   ├── InternalError (500)
│   ├── BadGatewayError (502)
│   ├── ServiceUnavailableError (503)
│   └── GatewayTimeoutError (504)
└── ParsingError
```

### 7.2 Generated Error Types (per Language)

**TypeScript:**

```typescript
// errors.ts
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public response?: unknown,
    public request?: Request
  ) { ... }
}

export class NotFoundError extends ApiError { ... }
export class UnauthorizedError extends ApiError { ... }
// etc.
```

**Python:**

```python
# exceptions.py
class ApiError(Exception):
    def __init__(self, status_code: int, message: str, response: Optional[dict] = None):
        ...

class NotFoundError(ApiError): ...
class UnauthorizedError(ApiError): ...
# etc.
```

**Go:**

```go
// errors.go
type ApiError struct {
    StatusCode int
    Message    string
    Response   interface{}
}

func (e *ApiError) Error() string { ... }

type NotFoundError struct { ApiError }
type UnauthorizedError struct { ApiError }
// etc.
```

**Rust:**

```rust
// error.rs
#[derive(Debug, thiserror::Error)]
pub enum ApiError {
    #[error("API error: {status_code} - {message}")]
    Api { status_code: u16, message: String },
    
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    
    // Variant per status code
    #[error("Not Found")]
    NotFound,
    #[error("Unauthorized")]
    Unauthorized,
}
```

### 7.3 Validation Errors

Generate specific error types for 422 responses with validation details:

```typescript
// For 422 responses with validation details
export interface ValidationErrorDetail {
  field: string;
  message: string;
  type: 'required' | 'invalid' | 'format' | 'enum';
}

export class UnprocessableError extends ApiError {
  constructor(
    public validationErrors: ValidationErrorDetail[]
  ) { ... }
}
```

---

## 8. Authentication Flow Handling

### 8.1 Supported Auth Types

| Auth Type | TypeScript | Python | Go | Rust |
|-----------|------------|--------|-----|------|
| API Key (header) | ✓ | ✓ | ✓ | ✓ |
| API Key (query) | ✓ | ✓ | ✓ | ✓ |
| API Key (cookie) | ✓ | ✓ | ✓ | ✓ |
| Basic Auth | ✓ | ✓ | ✓ | ✓ |
| Bearer Token | ✓ | ✓ | ✓ | ✓ |
| OAuth 2.0 | ✓ | ✓ | ✓ | ✓ |
| OpenID Connect | ✓ | ✓ | ✓ | - |

### 8.2 Auth Implementation Pattern

**TypeScript:**

```typescript
export class AuthHandler {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private refreshing: Promise<string> | null = null;
  
  async getAuthHeader(): Promise<Record<string, string>> {
    if (!this.config.auth) return {};
    
    switch (this.config.auth.type) {
      case 'bearer':
        return { Authorization: `Bearer ${await this.getToken()}` };
      case 'basic':
        return { Authorization: `Basic ${btoa(this.config.auth.credentials)}` };
      case 'apikey':
        return { [this.config.auth.name]: this.config.auth.value };
      // OAuth2 handled separately
    }
  }
  
  private async getToken(): Promise<string> {
    if (this.token && !this.isExpired(this.token)) {
      return this.token;
    }
    
    if (this.refreshing) {
      return this.refreshing;
    }
    
    this.refreshing = this.refresh();
    return this.refreshing;
  }
}
```

### 8.3 OAuth 2.0 Flow

**Authorization Code (server-side):**

1. Redirect to authorization URL
2. Receive callback with code
3. Exchange code for token
4. Store refresh token
5. Auto-refresh on 401

**Client Credentials:**

1. Exchange client_id/client_secret for token
2. Store and auto-refresh

---

## 9. Edge Cases and Error Scenarios

### 9.1 Spec Quality Issues

| Issue | Handling |
|-------|----------|
| Missing operationId | Generate from path + method (e.g., `getUsers`) |
| Duplicate operationId | Append hash suffix |
| Missing response schema | Use `any` / `interface{}` / `interface{}` |
| Circular $ref | Resolve with cycle detection, use type alias |
| Invalid $ref path | Warn and skip |
| Ambiguous schema (oneOf/anyOf) | Generate union types with guard |
| Polymorphic schemas (discriminator) | Generate base + sub-types |
| Nullable fields | Use optional/nullable types |
| Default values | Include in type, add validation |

### 9.2 Network Issues

| Issue | Handling |
|-------|----------|
| Connection timeout | Configurable timeout, retry with backoff |
| SSL errors | Option to disable cert verification (warn) |
| Redirect loops | Detect and fail after N redirects |
| Large responses | Stream support, size limits |
| Compression | Auto-handle gzip/deflate |

### 9.3 Generation Issues

| Issue | Handling |
|-------|----------|
| Reserved keywords | Prefix with underscore or escape |
| Invalid characters | Sanitize identifiers |
| Very long names | Truncate with hash |
| Too many endpoints | Split into multiple files |
| Circular type dependencies | Generate type aliases |

### 9.4 Runtime Issues

| Issue | Handling |
|-------|----------|
| 401 on request | Try refresh token, fail if fails |
| 429 rate limit | Respect Retry-After header |
| 5xx errors | Configurable retry count |
| Partial response | Type-safe partial parsing |

---

## 10. Dependencies

### 10.1 Rust Crates (Cargo.toml)

```toml
[package]
name = "codegen-sdk"
version = "0.1.0"
edition = "2021"

[dependencies]
# CLI
clap = { version = "4.0", features = ["derive", "env"] }
clap_complete = "4.0"

# Async
tokio = { version = "1.0", features = ["full"] }

# Parsing
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
serde_yaml = "0.9"

# Validation
validator = { version = "0.16", features = ["derive"] }

# HTTP (for introspection)
reqwest = { version = "0.11", features = ["json"] }

# Template
mininja = "0.3"
tera = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Error handling
thiserror = "1.0"
anyhow = "1.0"

# Utils
async-trait = "0.1"
chrono = "0.4"
dirs = "4.0"
walkdir = "2.0"
regex = "1.0"
url = "2.0"

# Config
toml = "0.5"

[dev-dependencies]
assert_cmd = "2.0"
predicates = "3.0"
insta = "1.0"
```

### 10.2 Build Tools

- `cargo-binstall` for binary installation
- `cross` for cross-compilation
- `cargo-dist` for release builds

---

## 11. API Design

### 11.1 Public CLI API

```rust
// Exposed as library for embedding
use codegen_sdk::{generate, Config, Language};

pub async fn generate_client(
    spec: &str,
    language: Language,
    output: &Path,
    config: Config,
) -> Result<GenerationResult, Error>;
```

### 11.2 Internal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  (clap args → commands → generate/validate/introspect)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Parser Layer                           │
│  (openapi::Parser → postman::Parser → types::IR)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Validation Layer                          │
│  (validate spec, check auth, verify endpoints)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Codegen Layer                             │
│  (typescript::Generator, python::Generator, etc.)          │
│  (Renderer → Template → Output)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Output Layer                           │
│  (write files, show diff, format output)                    │
└─────────────────────────────────────────────────────────────┘
```

### 11.3 Key Traits

```rust
// Parser trait
pub trait SpecParser {
    fn parse(input: &str) -> Result<ApiSpec, ParseError>;
    fn parse_file(path: &Path) -> Result<ApiSpec, ParseError>;
}

// Generator trait
pub trait CodeGenerator {
    fn generate(&self, spec: &ApiSpec, config: &CodegenConfig) -> Result<GeneratedCode, Error>;
    fn language(&self) -> Language;
}

// Renderer trait
pub trait TemplateRenderer {
    fn render(&self, template: &str, context: &Context) -> Result<String, Error>;
}
```

---

## 12. Testing Strategy

### 12.1 Test Categories

| Category | Location | Description |
|----------|----------|-------------|
| Unit | `tests/unit/` | Individual parser/codegen functions |
| Fixtures | `tests/fixtures/` | Sample specs and expected output |
| Integration | `tests/integration/` | End-to-end generation tests |
| Snapshots | `tests/snapshots/` | Generated code snapshots |

### 12.2 Test Fixtures

```
tests/fixtures/
├── openapi/
│   ├── petstore.yaml         # Standard OpenAPI 3.0
│   ├── auth.yaml             # All auth types
│   ├── complex.yaml          # oneOf, anyOf, discriminator
│   └── uspto.yaml            # Real-world example
├── postman/
│   └── collection.json       # Postman collection
└── expected/
    ├── typescript/
    ├── python/
    ├── go/
    └── rust/
```

---

## 13. Roadmap

### Phase 1: Core (v0.1.0)

- [ ] Basic CLI structure with clap
- [ ] OpenAPI 3.0 parsing
- [ ] TypeScript code generation
- [ ] Basic error types
- [ ] Simple auth (API Key, Bearer)

### Phase 2: Multi-language (v0.2.0)

- [ ] Python code generation
- [ ] Go code generation
- [ ] Rust code generation
- [ ] Postman collection parsing

### Phase 3: Advanced Features (v0.3.0)

- [ ] Introspect running APIs
- [ ] OAuth 2.0 flow handling
- [ ] Custom templates
- [ ] Config file support

### Phase 4: Polish (v0.4.0)

- [ ] Extensive validation
- [ ] Error recovery
- [ ] Performance optimization
- [ ] Documentation

---

## 14. Success Criteria

- [ ] Generate valid, compilable code in all 4 languages
- [ ] Handle 95%+ of OpenAPI 3.0 features
- [ ] CLI responds in <500ms for generation
- [ ] 100% type coverage in generated TypeScript
- [ ] Pass all generated code through language linters