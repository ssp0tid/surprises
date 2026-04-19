CREATE TABLE IF NOT EXISTS app_logs (
    timestamp DateTime64(3),
    level Enum8('DEBUG'=1, 'INFO'=2, 'WARN'=3, 'ERROR'=4, 'FATAL'=5),
    service String,
    host String,
    message String,
    metadata String,
    _raw String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service, timestamp, level)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;