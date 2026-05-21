-- Code Time Tracker Database Schema
-- Version: 1.0.0

-- Projects (user-defined categorizations)
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    keywords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Time sessions (continuous active periods)
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds INTEGER,
    window_title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Idle periods (auto-detected gaps)
CREATE TABLE IF NOT EXISTS idle_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration_seconds INTEGER NOT NULL
);

-- Settings (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_project_time ON sessions(project_id, start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);