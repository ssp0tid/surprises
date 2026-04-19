package db

import (
	"context"
	"fmt"
	"time"

	"github.com/ClickHouse/clickhouse-go/v2"
	"github.com/ClickHouse/clickhouse-go/v2/lib/driver"
	"github.com/logvault/logvault/internal/config"
)

type DB struct {
	conn driver.Conn
	cfg  *config.DatabaseConfig
}

func NewClient(cfg *config.DatabaseConfig) (*DB, error) {
	if cfg == nil {
		return nil, fmt.Errorf("database config is required")
	}

	opts := &clickhouse.Options{
		Addr: []string{fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)},
		Auth: clickhouse.Auth{
			Database: cfg.Database,
			Username: cfg.User,
			Password: cfg.Password,
		},
		Settings: clickhouse.Settings{
			"max_execution_time": 60,
		},
		DialTimeout: 5 * time.Second,
	}

	if !cfg.TLS {
		opts.TLS = nil
	}

	conn, err := clickhouse.Open(opts)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to ClickHouse: %w", err)
	}

	return &DB{
		conn: conn,
		cfg:  cfg,
	}, nil
}

func (db *DB) Close() error {
	if db.conn != nil {
		return db.conn.Close()
	}
	return nil
}

func (db *DB) Ping(ctx context.Context) error {
	if db.conn == nil {
		return fmt.Errorf("connection is nil")
	}
	return db.conn.Ping(ctx)
}

func (db *DB) Query(ctx context.Context, query string, args ...interface{}) (driver.Rows, error) {
	if db.conn == nil {
		return nil, fmt.Errorf("connection is nil")
	}
	return db.conn.Query(ctx, query, args...)
}

func (db *DB) Exec(ctx context.Context, query string, args ...interface{}) error {
	if db.conn == nil {
		return fmt.Errorf("connection is nil")
	}
	return db.conn.Exec(ctx, query, args...)
}

func (db *DB) Conn() driver.Conn {
	return db.conn
}

func (db *DB) GetLogByID(ctx context.Context, id string) (*model.LogEntry, error) {
	return GetLogByID(ctx, db, id)
}