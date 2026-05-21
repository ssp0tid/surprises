# MockFlow Implementation Plan

## 1. Project Overview

MockFlow is a visual web-based HTTP mock API designer that allows developers to create, manage, and test mock API endpoints through an intuitive drag-and-drop interface. It serves as a local or hosted mock server that simulates real API behavior without requiring actual backend implementation.

Target users include frontend developers who need to work independently of backend services, QA engineers testing API integrations, and development teams prototyping API designs before implementing the actual backend. MockFlow bridges the gap between API specification and implementation by providing immediate mock responses that mirror production behavior.

## 2. Core Features

### 2.1 Mock Endpoint Management

The foundation of MockFlow lies in its endpoint creation and management capabilities. Users can define endpoints across all standard HTTP methods including GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS. Each endpoint requires a path definition with support for path parameters using colon syntax like `/users/:id` and query parameter handling. The system supports multiple response variants per endpoint, enabling different responses based on conditions or request characteristics.

### 2.2 Response Configuration

Each mock endpoint can define comprehensive response details including HTTP status codes (200, 201, 400, 401, 403, 404, 500, etc.), response headers with custom key-value pairs, and response body content. The body supports multiple content types including JSON, XML, plain text, and HTML. Response latency simulation allows users to configure delay in milliseconds to mimic real network conditions.

### 2.3 Dynamic Responses

MockFlow provides powerful dynamic response capabilities through variable substitution using double curly brace syntax like `{{request.body.field}}` or `{{timestamp}}`. Built-in variables include `{{uuid}}` for generating unique identifiers, `{{timestamp}}` for current Unix time, `{{random.number}}` for numeric randomization, and `{{random.string}}` for arbitrary strings. Conditional responses enable different outputs based on request attributes such as headers, query parameters, or body content.

### 2.4 Request Logging and Inspection

The logging system captures every incoming request with full details including timestamp, HTTP method, path, query parameters, request headers, and request body. Log entries display the matched endpoint, response sent, and response time. Users can filter logs by endpoint, method, status code, or date range. Log retention settings allow configuration of how long logs are preserved.

### 2.5 Project and Workspace Management

Multiple projects or workspaces enable organization of mock APIs by application or team. Each project maintains its own set of endpoints, responses, and logs. Project-level settings include base URL configuration, default response latency, and environment variables. Team collaboration features include project sharing and role-based access control.

### 2.6 Import and Export

Import capabilities support OpenAPI/Swagger specifications for converting existing API definitions into mock endpoints. Postman collection import enables migration from existing Postman setups. Export options include OpenAPI specification generation, Postman collection format, and raw JSON endpoint definitions. Server configuration export allows sharing complete mock server setups.

### 2.7 Server Control

MockFlow runs as a configurable mock server with port binding options. Users can start, stop, and restart the mock server from the interface. Server status displays active endpoint count, total requests served, and uptime statistics. The system supports running multiple server instances on different ports for parallel testing scenarios.

### 2.8 Request Matching and Prioritization

Advanced matching rules enable complex endpoint resolution beyond simple path matching. Users can define header matching conditions, body content matching, and query parameter requirements. Priority ordering determines which endpoint definition matches when multiple candidates exist. Regex path matching provides additional flexibility for dynamic endpoint patterns.

## 3. Architecture

### 3.1 Frontend Architecture

The frontend uses vanilla JavaScript with a component-based architecture to keep the bundle lightweight and avoid unnecessary dependencies. This approach provides full control over the user experience while maintaining fast load times. Components are organized around specific features with shared utilities for common operations. The interface communicates with the backend exclusively through REST API calls, enabling clear separation of concerns and easy backend replacement if needed.

### 3.2 Backend Architecture

The Flask backend follows a layered architecture with routes handling HTTP requests, services containing business logic, and models managing data access. The application initializes with a SQLite database using SQLAlchemy ORM for database operations. The mock server runs as a separate thread within the Flask application, intercepting requests and matching them against defined endpoints before returning configured responses.

### 3.3 Database Design

SQLite provides the database layer with tables for projects, endpoints, responses, logs, and server configuration. The schema uses foreign key relationships to maintain data integrity. Migrations are managed through Flask-Migrate for schema version control. The database file stores in the application data directory with automatic backup capabilities.

### 3.4 API Communication

The frontend and backend communicate through a RESTful API with JSON payloads. Authentication uses API keys passed in headers. The mock server exposes configurable ports (default 8080) while the management interface runs on the Flask development server (default 5000). CORS configuration allows cross-origin requests from the frontend.

## 4. Database Schema

### 4.1 Projects Table

The projects table stores workspace configurations with fields for id (primary key, integer, auto-increment), name (text, required, maximum 255 characters), description (text, optional), base_url (text, optional, default empty string), created_at (timestamp, auto-set on creation), updated_at (timestamp, auto-set on modification), and settings (JSON, optional, stores environment variables and preferences).

### 4.2 Endpoints Table

The endpoints table defines mock API routes with fields for id (primary key), project_id (foreign key to projects, required), path (text, required, maximum 500 characters), method (text, required, enum values: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS), description (text, optional), enabled (boolean, default true), priority (integer, default 0, higher values match first), match_headers (JSON, optional, conditions for header matching), match_body (JSON, optional, conditions for body matching), match_query (JSON, optional, conditions for query parameter matching), created_at (timestamp), and updated_at (timestamp).

### 4.3 Responses Table

The responses table stores response configurations linked to endpoints with fields for id (primary key), endpoint_id (foreign key to endpoints, required), name (text, required for identification), status_code (integer, required, default 200), headers (JSON, optional, response header key-value pairs), body (text, optional, response body content), content_type (text, optional, default application/json), delay_ms (integer, optional, default 0, response delay in milliseconds), is_default (boolean, default false, used when no conditions match), conditions (JSON, optional, rules determining when this response applies), created_at (timestamp), and updated_at (timestamp).

### 4.4 Logs Table

The logs table captures request history with fields for id (primary key), endpoint_id (foreign key to endpoints, nullable for unmatched requests), project_id (foreign key to projects), method (text, required), path (text, required), query_params (JSON, optional), request_headers (JSON, optional), request_body (text, optional), response_status (integer), response_headers (JSON, optional), response_body (text, optional), matched (boolean, indicates if request matched an endpoint), response_time_ms (integer), created_at (timestamp, auto-set).

### 4.5 Server Config Table

The server_config table stores mock server settings with fields for id (primary key), project_id (foreign key to projects), port (integer, default 8080), host (text, default 0.0.0.0), enabled (boolean, default false), cors_enabled (boolean, default true), cors_origins (text, optional, comma-separated list), log_requests (boolean, default true), created_at (timestamp), and updated_at (timestamp).

## 5. Backend API Endpoints

### 5.1 Project Management

The project endpoints include GET /api/projects for listing all projects with pagination, GET /api/projects/{id} for retrieving a single project with its endpoints, POST /api/projects for creating a new project, PUT /api/projects/{id} for updating project details, DELETE /api/projects/{id} for deleting a project and all associated data, and GET /api/projects/{id}/export for exporting project configuration.

### 5.2 Endpoint Management

The endpoint CRUD operations include GET /api/projects/{project_id}/endpoints for listing all endpoints in a project, GET /api/endpoints/{id} for retrieving endpoint details with responses, POST /api/projects/{project_id}/endpoints for creating a new endpoint, PUT /api/endpoints/{id} for updating endpoint configuration, DELETE /api/endpoints/{id} for deleting an endpoint, POST /api/endpoints/{id}/test for testing an endpoint definition, and PUT /api/endpoints/reorder for updating endpoint priority order.

### 5.3 Response Management

Response operations include GET /api/endpoints/{endpoint_id}/responses for listing all responses for an endpoint, GET /api/responses/{id} for retrieving a response definition, POST /api/endpoints/{endpoint_id}/responses for adding a new response, PUT /api/responses/{id} for updating a response, DELETE /api/responses/{id} for deleting a response, and PUT /api/responses/{id}/set-default for marking a response as the default.

### 5.4 Logging

Log endpoints include GET /api/projects/{project_id}/logs for retrieving request logs with filtering, GET /api/logs/{id} for retrieving a single log entry details, DELETE /api/projects/{project_id}/logs for clearing logs for a project, and GET /api/projects/{project_id}/logs/export for exporting logs.

### 5.5 Server Control

Server management endpoints include GET /api/projects/{project_id}/server for getting server status, POST /api/projects/{project_id}/server/start for starting the mock server, POST /api/projects/{project_id}/server/stop for stopping the mock server, and PUT /api/projects/{project_id}/server/config for updating server configuration.

### 5.6 Import Operations

Import endpoints include POST /api/projects/import/openapi for importing from OpenAPI specification, POST /api/projects/import/postman for importing from Postman collection, and POST /api/projects/{project_id}/import/json for importing from JSON definition.

## 6. Frontend UI/UX

### 6.1 Page Structure

The interface consists of several key views. The dashboard serves as the home page showing project overview, recent activity, and quick actions. The project view displays all endpoints within a selected project with filtering and search capabilities. The endpoint editor provides the main workspace for creating and editing endpoint and response configurations. The logs viewer shows request history with detailed inspection capabilities. The settings page handles project configuration, server settings, and user preferences.

### 6.2 Key Components

The sidebar navigation provides project switching, main menu access, and server status indicator. The endpoint list displays all endpoints with method badges, path information, and toggle controls for enabling or disabling. The endpoint editor form includes fields for path input with method selector, response configuration panels with tabbed interface for headers, body, and conditions, and dynamic variable insertion tools. The response builder offers a code editor with syntax highlighting for JSON and other formats, a preview panel showing rendered output, and latency configuration controls. The log inspector provides a table view with sortable columns, a detail panel showing full request and response information, and filtering controls for refining log displays.

### 6.3 User Flow

The typical user workflow begins with creating a new project or selecting an existing one from the dashboard. From the project view, users create endpoints by clicking the add button, selecting the HTTP method, entering the path, and saving. Each endpoint can have multiple responses configured with conditions or set as default. The mock server starts with a single click, and all incoming requests appear in real-time in the logs view. Users can inspect any request to verify the mock behavior matches expectations.

## 7. Implementation Phases

### 7.1 Phase One: MVP

The first phase delivers a minimum viable product with core functionality. This includes project creation and management, basic endpoint CRUD operations with single response per endpoint, simple GET and POST method support, a JSON response body editor, basic server start and stop functionality, simple request logging with method, path, and timestamp, and a clean, functional interface with sidebar navigation and endpoint list view.

### 7.2 Phase Two: Advanced Features

The second phase expands capabilities with multiple response variants per endpoint, dynamic variable substitution, conditional responses based on request attributes, additional HTTP method support, request header and query parameter matching, OpenAPI and Postman import functionality, endpoint search and filtering, and log export capabilities.

### 7.3 Phase Three: Polish

The final phase focuses on refinement and additional features including regex path matching, request body matching conditions, multiple server instances support, real-time log streaming, enhanced response preview with variable substitution rendering, keyboard shortcuts for common actions, keyboard-accessible navigation, comprehensive keyboard shortcuts documentation, performance optimization for large endpoint collections, and automated testing capabilities.

## 8. File Structure

The project follows this directory structure:

```
mockflow/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py      # Project API endpoints
│   │   ├── endpoints.py     # Endpoint API endpoints
│   │   ├── responses.py     # Response API endpoints
│   │   ├── logs.py          # Log API endpoints
│   │   └── server.py        # Server control endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── mock_server.py   # Mock HTTP server implementation
│   │   ├── matcher.py       # Request matching logic
│   │   └── importer.py      # Import functionality
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
├── static/
│   ├── css/
│   │   ├── style.css        # Main stylesheet
│   │   └── components.css   # Component styles
│   ├── js/
│   │   ├── app.js           # Main application entry
│   │   ├── api.js           # API client
│   │   ├── router.js        # Client-side routing
│   │   ├── components/      # UI components
│   │   │   ├── sidebar.js
│   │   │   ├── endpoint-list.js
│   │   │   ├── endpoint-editor.js
│   │   │   ├── response-builder.js
│   │   │   └── log-viewer.js
│   │   └── utils/           # Frontend utilities
│   └── assets/              # Images, icons
├── templates/
│   └── index.html           # Main HTML template
├── migrations/              # Flask-Migrate migrations
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API endpoint tests
│   ├── test_mock_server.py  # Mock server tests
│   └── test_matcher.py      # Matching logic tests
├── .env                     # Environment variables
├── config.py                # Runtime configuration
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── package.json             # Frontend dependencies
```
