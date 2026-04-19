package db

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/logvault/logvault/internal/model"
)

type LogFilter struct {
	Level   string    `json:"level,omitempty"`
	Service string    `json:"service,omitempty"`
	Host    string    `json:"host,omitempty"`
	From    time.Time `json:"from,omitempty"`
	To      time.Time `json:"to,omitempty"`
	Query   string    `json:"q,omitempty"`
}

func InsertLog(ctx context.Context, db *DB, logEntry *model.LogEntry) error {
	if db == nil || db.conn == nil {
		return fmt.Errorf("database connection is nil")
	}
	if logEntry == nil {
		return fmt.Errorf("log entry is nil")
	}

	levelStr := string(logEntry.Level)
	metadata := ""
	if logEntry.Metadata != nil {
		metadata = string(logEntry.Metadata)
	}
	raw := logEntry.Raw
	if raw == "" {
		raw = logEntry.Message
	}

	if logEntry.ID == "" {
		logEntry.ID = fmt.Sprintf("%d-%s", logEntry.Timestamp.UnixNano(), logEntry.Service)
	}

	query := fmt.Sprintf(`
	INSERT INTO %s (id, timestamp, level, service, host, message, metadata, _raw)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?)
	`, appLogsTable)

	return db.conn.Exec(ctx, query,
		logEntry.ID,
		logEntry.Timestamp,
		levelStr,
		logEntry.Service,
		logEntry.Host,
		logEntry.Message,
		metadata,
		raw,
	)
}

func InsertBatch(ctx context.Context, db *DB, logs []*model.LogEntry) error {
	if db == nil || db.conn == nil {
		return fmt.Errorf("database connection is nil")
	}
	if len(logs) == 0 {
		return nil
	}

	batch, err := db.conn.PrepareBatch(ctx, fmt.Sprintf("INSERT INTO %s (id, timestamp, level, service, host, message, metadata, _raw)", appLogsTable))
	if err != nil {
		return fmt.Errorf("failed to prepare batch: %w", err)
	}

	for _, log := range logs {
		levelStr := string(log.Level)
		metadata := ""
		if log.Metadata != nil {
			metadata = string(log.Metadata)
		}
		raw := log.Raw
		if raw == "" {
			raw = log.Message
		}

		if log.ID == "" {
			log.ID = fmt.Sprintf("%d-%s", log.Timestamp.UnixNano(), log.Service)
		}

		if err := batch.Append(
			log.ID,
			log.Timestamp,
			levelStr,
			log.Service,
			log.Host,
			log.Message,
			metadata,
			raw,
		); err != nil {
			return fmt.Errorf("failed to append to batch: %w", err)
		}
	}

	return batch.Send()
}

func QueryLogs(ctx context.Context, db *DB, filter LogFilter, limit int, cursor string) ([]*model.LogEntry, string, int, error) {
	if db == nil || db.conn == nil {
		return nil, "", 0, fmt.Errorf("database connection is nil")
	}
	if limit <= 0 {
		limit = 100
	}

	var args []interface{}
	var conditions []string

	if filter.Level != "" {
		conditions = append(conditions, "level = ?")
		args = append(args, filter.Level)
	}
	if filter.Service != "" {
		conditions = append(conditions, "service = ?")
		args = append(args, filter.Service)
	}
	if filter.Host != "" {
		conditions = append(conditions, "host = ?")
		args = append(args, filter.Host)
	}
	if !filter.From.IsZero() {
		conditions = append(conditions, "timestamp >= ?")
		args = append(args, filter.From)
	}
	if !filter.To.IsZero() {
		conditions = append(conditions, "timestamp <= ?")
		args = append(args, filter.To)
	}
	if filter.Query != "" {
		conditions = append(conditions, "(_raw ILIKE ?)")
		args = append(args, "%"+filter.Query+"%")
	}

	whereClause := ""
	if len(conditions) > 0 {
		whereClause = "WHERE " + strings.Join(conditions, " AND ")
	}

	cursorCond := ""
	var lastTimestamp time.Time
	var lastLevel string

	if cursor != "" {
		parts := strings.SplitN(cursor, "_", 2)
		if len(parts) == 2 {
			ts, err := time.Parse(time.RFC3339Nano, parts[0])
			if err == nil {
				lastTimestamp = ts
				lastLevel = parts[1]
			}
		}
		if !lastTimestamp.IsZero() {
			if lastLevel != "" {
				cursorCond = " AND (timestamp > ? OR (timestamp = ? AND level > ?)"
				args = append(args, lastTimestamp, lastTimestamp, lastLevel)
			} else {
				cursorCond = " AND timestamp > ?"
				args = append(args, lastTimestamp)
			}
		}
	}

	sortField := "timestamp"
	sortDir := "DESC"

	newCursor := ""

	q := fmt.Sprintf(`
	SELECT timestamp, level, service, host, message, metadata, _raw
	FROM %s
	%s %s
	ORDER BY %s %s
	LIMIT ?
	`, appLogsTable, whereClause, cursorCond, sortField, sortDir)
	args = append(args, limit+1)

	rows, err := db.conn.Query(ctx, q, args...)
	if err != nil {
		return nil, "", 0, fmt.Errorf("failed to execute query: %w", err)
	}
	defer rows.Close()

	var resultLogs []*model.LogEntry
	for rows.Next() {
		var logEntry model.LogEntry
		var levelStr string
		var metadata, raw string

		if err := rows.Scan(&logEntry.Timestamp, &levelStr, &logEntry.Service, &logEntry.Host, &logEntry.Message, &metadata, &raw); err != nil {
			return nil, "", 0, fmt.Errorf("failed to scan row: %w", err)
		}

		logEntry.Level = model.LogLevel(levelStr)
		logEntry.Metadata = json.RawMessage(metadata)
		logEntry.Raw = raw
		resultLogs = append(resultLogs, &logEntry)

		if len(resultLogs) == limit {
			newCursor = fmt.Sprintf("%s_%s", logEntry.Timestamp.Format(time.RFC3339Nano), logEntry.Level)
			resultLogs = resultLogs[:limit]
			break
		}
	}

	total := len(resultLogs)
	if total == 0 {
		return resultLogs, "", 0, nil
	}

	return resultLogs, newCursor, total, nil
}

func CountLogs(ctx context.Context, db *DB, filter LogFilter) (int, error) {
	if db == nil || db.conn == nil {
		return 0, fmt.Errorf("database connection is nil")
	}

	var args []interface{}
	var conditions []string

	if filter.Level != "" {
		conditions = append(conditions, "level = ?")
		args = append(args, filter.Level)
	}
	if filter.Service != "" {
		conditions = append(conditions, "service = ?")
		args = append(args, filter.Service)
	}
	if filter.Host != "" {
		conditions = append(conditions, "host = ?")
		args = append(args, filter.Host)
	}
	if !filter.From.IsZero() {
		conditions = append(conditions, "timestamp >= ?")
		args = append(args, filter.From)
	}
	if !filter.To.IsZero() {
		conditions = append(conditions, "timestamp <= ?")
		args = append(args, filter.To)
	}
	if filter.Query != "" {
		conditions = append(conditions, "(_raw ILIKE ?)")
		args = append(args, "%"+filter.Query+"%")
	}

	whereClause := ""
	if len(conditions) > 0 {
		whereClause = "WHERE " + strings.Join(conditions, " AND ")
	}

	q := fmt.Sprintf(`
	SELECT count()
	FROM %s
	%s
	`, appLogsTable, whereClause)

	var count int
	row := db.conn.QueryRow(ctx, q, args...)
	if err := row.Scan(&count); err != nil {
		return 0, fmt.Errorf("failed to count logs: %w", err)
	}

	return count, nil
}

func GetLogByID(ctx context.Context, db *DB, id string) (*model.LogEntry, error) {
	if db == nil || db.conn == nil {
		return nil, fmt.Errorf("database connection is nil")
	}

	query := fmt.Sprintf(`
	SELECT id, timestamp, level, service, host, message, metadata, _raw
	FROM %s
	WHERE id = ?
	LIMIT 1
	`, appLogsTable)

	var entry model.LogEntry
	var levelStr, metadata, raw string

	row := db.conn.QueryRow(ctx, query, id)
	if err := row.Scan(&entry.ID, &entry.Timestamp, &levelStr, &entry.Service, &entry.Host, &entry.Message, &metadata, &raw); err != nil {
		return nil, fmt.Errorf("log not found: %w", err)
	}

	entry.Level = model.LogLevel(levelStr)
	entry.Metadata = json.RawMessage(metadata)
	entry.Raw = raw

	return &entry, nil
}