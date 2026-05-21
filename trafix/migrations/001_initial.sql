-- Trafix Database Schema
-- Initial migration

-- Requests table
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    query TEXT,

    -- Request headers (JSON)
    request_headers TEXT,

    -- Request body (if present)
    request_body BLOB,
    request_body_size INTEGER DEFAULT 0,

    -- Response
    status_code INTEGER NOT NULL,
    response_headers TEXT,
    response_body BLOB,
    response_body_size INTEGER DEFAULT 0,

    -- Target
    target_url TEXT NOT NULL,

    -- Timing
    duration_ms INTEGER DEFAULT 0,

    -- Client info
    client_ip TEXT,
    user_agent TEXT,

    -- Auth
    api_key_hash TEXT,
    authenticated INTEGER DEFAULT 0,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    indexed_at TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requests_path ON requests(path);
CREATE INDEX IF NOT EXISTS idx_requests_status_code ON requests(status_code);
CREATE INDEX IF NOT EXISTS idx_requests_client_ip ON requests(client_ip);
CREATE INDEX IF NOT EXISTS idx_requests_method ON requests(method);

-- Analytics hourly aggregations
CREATE TABLE IF NOT EXISTS analytics_hourly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hour TEXT NOT NULL,  -- ISO hour: "2026-04-22T15:00"
    path TEXT NOT NULL,

    request_count INTEGER DEFAULT 0,
    authenticated_count INTEGER DEFAULT 0,

    status_2xx INTEGER DEFAULT 0,
    status_3xx INTEGER DEFAULT 0,
    status_4xx INTEGER DEFAULT 0,
    status_5xx INTEGER DEFAULT 0,

    avg_duration_ms REAL DEFAULT 0,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(hour, path)
);

CREATE INDEX IF NOT EXISTS idx_analytics_hourly_hour ON analytics_hourly(hour DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_hourly_path ON analytics_hourly(path);

-- Analytics daily aggregations
CREATE TABLE IF NOT EXISTS analytics_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- ISO date: "2026-04-22"
    path TEXT NOT NULL,

    request_count INTEGER DEFAULT 0,
    authenticated_count INTEGER DEFAULT 0,

    status_2xx INTEGER DEFAULT 0,
    status_3xx INTEGER DEFAULT 0,
    status_4xx INTEGER DEFAULT 0,
    status_5xx INTEGER DEFAULT 0,

    avg_duration_ms REAL DEFAULT 0,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,

    unique_ips INTEGER DEFAULT 0,
    unique_api_keys INTEGER DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(date, path)
);

CREATE INDEX IF NOT EXISTS idx_analytics_daily_date ON analytics_daily(date DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_path ON analytics_daily(path);

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Record this migration
INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_initial');
