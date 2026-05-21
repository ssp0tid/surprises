package storage

import (
	"context"
	"database/sql"

	"github.com/jmoiron/sqlx"
	"github.com/mattn/go-sqlite3"

	"trafix/config"
	"trafix/utils"
)

type DB struct {
	db  *sqlx.DB
	cfg *config.Config
}

func NewDB(cfg *config.Config) (*DB, error) {
	logger := utils.GetLogger()

	sqlite3.SQLiteCompiledFormat()

	db, err := sqlx.Open("sqlite3", cfg.Storage.Database)
	if err != nil {
		logger.Error().Err(err).Str("database", cfg.Storage.Database).Msg("failed to open database")
		return nil, err
	}

	db.SetMaxOpenConns(cfg.Storage.MaxConnections)
	db.SetMaxIdleConns(cfg.Storage.MaxConnections / 2)

	if err := db.Ping(); err != nil {
		logger.Error().Err(err).Msg("failed to ping database")
		return nil, err
	}

	d := &DB{
		db:  db,
		cfg: cfg,
	}

	if err := d.migrate(); err != nil {
		logger.Error().Err(err).Msg("failed to migrate database")
		return nil, err
	}

	logger.Info().Str("database", cfg.Storage.Database).Msg("database initialized")

	return d, nil
}

func (d *DB) migrate() error {
	schema := `
	CREATE TABLE IF NOT EXISTS requests (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		request_id TEXT NOT NULL UNIQUE,
		method TEXT NOT NULL,
		path TEXT NOT NULL,
		target_url TEXT NOT NULL,
		status_code INTEGER NOT NULL,
		request_body_size INTEGER,
		response_body_size INTEGER,
		duration_ms INTEGER,
		ip_address TEXT,
		user_agent TEXT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp);
	CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status_code);
	CREATE INDEX IF NOT EXISTS idx_requests_path ON requests(path);
	`

	_, err := d.db.Exec(schema)
	return err
}

func (d *DB) DB() *sqlx.DB {
	return d.db
}

func (d *DB) Close() error {
	return d.db.Close()
}

func (d *DB) Ping() error {
	return d.db.Ping()
}

type RequestRecord struct {
	ID              int64  `db:"id"`
	RequestID      string `db:"request_id"`
	Method         string `db:"method"`
	Path           string `db:"path"`
	TargetURL      string `db:"target_url"`
	StatusCode     int    `db:"status_code"`
	RequestBodySize int    `db:"request_body_size"`
	ResponseBodySize int  `db:"response_body_size"`
	DurationMs     int    `db:"duration_ms"`
	IPAddress      string `db:"ip_address"`
	UserAgent     string `db:"user_agent"`
	Timestamp     string `db:"timestamp"`
}

func (d *DB) InsertRequest(ctx context.Context, record *RequestRecord) error {
	query := `
	INSERT INTO requests (
		request_id, method, path, target_url, status_code,
		request_body_size, response_body_size, duration_ms,
		ip_address, user_agent
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	_, err := d.db.ExecContext(ctx, query,
		record.RequestID,
		record.Method,
		record.Path,
		record.TargetURL,
		record.StatusCode,
		record.RequestBodySize,
		record.ResponseBodySize,
		record.DurationMs,
		record.IPAddress,
		record.UserAgent,
	)

	return err
}

func (d *DB) GetRequests(ctx context.Context, limit int) ([]RequestRecord, error) {
	var records []RequestRecord
	query := "SELECT * FROM requests ORDER BY timestamp DESC LIMIT ?"
	err := d.db.SelectContext(ctx, &records, query, limit)
	return records, err
}

func (d *DB) GetRequestByID(ctx context.Context, requestID string) (*RequestRecord, error) {
	var record RequestRecord
	query := "SELECT * FROM requests WHERE request_id = ?"
	err := d.db.GetContext(ctx, &record, query, requestID)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	return &record, err
}