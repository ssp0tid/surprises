CREATE TABLE IF NOT EXISTS charts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    raw_data TEXT NOT NULL,
    chart_config TEXT NOT NULL,
    thumbnail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
