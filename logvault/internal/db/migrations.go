package db

import (
	"context"
	"fmt"
	"strings"
)

const (
	appLogsTable = "app_logs"
)

var createTableSQL = fmt.Sprintf(`
CREATE TABLE IF NOT EXISTS %s (
    id String,
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
SETTINGS index_granularity = 8192
`, appLogsTable)

func InitSchema(ctx context.Context, db *DB) error {
	if db == nil || db.conn == nil {
		return fmt.Errorf("database connection is nil")
	}

	exists, err := tableExists(ctx, db, appLogsTable)
	if err != nil {
		return fmt.Errorf("failed to check table existence: %w", err)
	}

	if !exists {
		if err := db.conn.Exec(ctx, createTableSQL); err != nil {
			return fmt.Errorf("failed to create table %s: %w", appLogsTable, err)
		}
	}

	return nil
}

func tableExists(ctx context.Context, db *DB, tableName string) (bool, error) {
	query := `
	SELECT count() > 0
	FROM system.tables
	WHERE database = currentDatabase() AND name = ?
	`

	var exists bool
	row := db.conn.QueryRow(ctx, query, tableName)
	if err := row.Scan(&exists); err != nil {
		return false, err
	}

	return exists, nil
}

func tableHasColumn(ctx context.Context, db *DB, tableName, columnName string) (bool, error) {
	query := `
	SELECT count() > 0
	FROM system.columns
	WHERE database = currentDatabase() AND table = ? AND name = ?
	`

	var exists bool
	row := db.conn.QueryRow(ctx, query, tableName, columnName)
	if err := row.Scan(&exists); err != nil {
		return false, err
	}

	return exists, nil
}

func columnExistsInTableDDL(ctx context.Context, db *DB, tableName, columnName string) (bool, error) {
	query := fmt.Sprintf("SHOW CREATE TABLE %s", tableName)

	row, err := db.conn.Query(ctx, query)
	if err != nil {
		return false, err
	}
	defer row.Close()

	var ddl string
	for row.Next() {
		if err := row.Scan(&ddl); err != nil {
			return false, err
		}
	}

	return strings.Contains(ddl, columnName), nil
}