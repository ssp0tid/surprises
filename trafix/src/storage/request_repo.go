package storage

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
)

type RequestRecord struct {
	ID               int64     `db:"id"`
	RequestID        string   `db:"request_id"`
	Method          string   `db:"method"`
	Path            string   `db:"path"`
	Query           string   `db:"query"`
	RequestHeaders  string   `db:"request_headers"`
	RequestBody    []byte   `db:"request_body"`
	RequestBodySize int      `db:"request_body_size"`
	StatusCode     int      `db:"status_code"`
	ResponseHeaders string `db:"response_headers"`
	ResponseBody   []byte   `db:"response_body"`
	ResponseBodySize int    `db:"response_body_size"`
	TargetURL      string   `db:"target_url"`
	DurationMs     int     `db:"duration_ms"`
	ClientIP       string   `db:"client_ip"`
	UserAgent      string   `db:"user_agent"`
	APIKeyHash    string   `db:"api_key_hash"`
	Authenticated bool    `db:"authenticated"`
	CreatedAt      string   `db:"created_at"`
	IndexedAt     *string  `db:"indexed_at"`
}

type RequestFilter struct {
	Limit        int
	Offset       int
	Method       string
	Path         string
	StatusCode   int
	ClientIP    string
	StartDate   time.Time
	EndDate     time.Time
	SearchQuery string
}

type Pagination struct {
	Limit  int `json:"limit"`
	Offset int `json:"offset"`
	Total  int `json:"total"`
}

type RequestListResponse struct {
	Data       []RequestRecord `json:"data"`
	Pagination Pagination    `json:"pagination"`
}

type RequestRepo struct {
	db *sqlx.DB
}

func NewRequestRepo(db *sqlx.DB) *RequestRepo {
	return &RequestRepo{db: db}
}

func (r *RequestRepo) SaveRequest(ctx context.Context, record *RequestRecord) error {
	record.RequestID = uuid.New().String()
	record.CreatedAt = time.Now().UTC().Format(time.RFC3339)

	headersJSON, err := json.Marshal(record.RequestHeaders)
	if err != nil {
		record.RequestHeaders = "{}"
	} else {
		record.RequestHeaders = string(headersJSON)
	}

	respHeadersJSON, err := json.Marshal(record.ResponseHeaders)
	if err != nil {
		record.ResponseHeaders = "{}"
	} else {
		record.ResponseHeaders = string(respHeadersJSON)
	}

	query := `
	INSERT INTO requests (
		request_id, method, path, query,
		request_headers, request_body, request_body_size,
		status_code, response_headers, response_body, response_body_size,
		target_url, duration_ms, client_ip, user_agent,
		api_key_hash, authenticated, created_at
	) VALUES (
		:request_id, :method, :path, :query,
		:request_headers, :request_body, :request_body_size,
		:status_code, :response_headers, :response_body, :response_body_size,
		:target_url, :duration_ms, :client_ip, :user_agent,
		:api_key_hash, :authenticated, :created_at
	)`

	_, err = r.db.NamedExecContext(ctx, query, record)
	return err
}

func (r *RequestRepo) GetByID(ctx context.Context, requestID string) (*RequestRecord, error) {
	var record RequestRecord
	query := "SELECT * FROM requests WHERE request_id = ?"

	err := r.db.GetContext(ctx, &record, query, requestID)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (r *RequestRepo) List(ctx context.Context, filter RequestFilter) ([]RequestRecord, error) {
	var records []RequestRecord

	baseQuery := "SELECT * FROM requests"
	whereClause, args := r.buildWhereClause(filter)

	if whereClause != "" {
		baseQuery += " WHERE " + whereClause
	}

	baseQuery += " ORDER BY created_at DESC"

	if filter.Limit > 0 {
		baseQuery += " LIMIT ?"
		args = append(args, filter.Limit)
	} else {
		baseQuery += " LIMIT 50"
	}

	if filter.Offset > 0 {
		baseQuery += " OFFSET ?"
		args = append(args, filter.Offset)
	}

	err := r.db.SelectContext(ctx, &records, baseQuery, args...)
	return records, err
}

func (r *RequestRepo) Count(ctx context.Context, filter RequestFilter) (int, error) {
	var count int

	baseQuery := "SELECT COUNT(*) FROM requests"
	whereClause, args := r.buildWhereClause(filter)

	if whereClause != "" {
		baseQuery += " WHERE " + whereClause
	}

	err := r.db.GetContext(ctx, &count, baseQuery, args...)
	return count, err
}

func (r *RequestRepo) ListWithPagination(ctx context.Context, filter RequestFilter) (*RequestListResponse, error) {
	records, err := r.List(ctx, filter)
	if err != nil {
		return nil, err
	}

	total, err := r.Count(ctx, filter)
	if err != nil {
		return nil, err
	}

	limit := filter.Limit
	if limit <= 0 {
		limit = 50
	}

	offset := filter.Offset
	if offset < 0 {
		offset = 0
	}

	return &RequestListResponse{
		Data: records,
		Pagination: Pagination{
			Limit:  limit,
			Offset: offset,
			Total:  total,
		},
	}, nil
}

func (r *RequestRepo) buildWhereClause(filter RequestFilter) (string, []interface{}) {
	var conditions []string
	var args []interface{}

	if filter.Method != "" {
		conditions = append(conditions, "method = ?")
		args = append(args, filter.Method)
	}

	if filter.Path != "" {
		conditions = append(conditions, "path LIKE ?")
		args = append(args, "%"+filter.Path+"%")
	}

	if filter.StatusCode > 0 {
		conditions = append(conditions, "status_code = ?")
		args = append(args, filter.StatusCode)
	}

	if filter.ClientIP != "" {
		conditions = append(conditions, "client_ip = ?")
		args = append(args, filter.ClientIP)
	}

	if !filter.StartDate.IsZero() {
		conditions = append(conditions, "created_at >= ?")
		args = append(args, filter.StartDate.Format(time.RFC3339))
	}

	if !filter.EndDate.IsZero() {
		conditions = append(conditions, "created_at <= ?")
		args = append(args, filter.EndDate.Format(time.RFC3339))
	}

	if filter.SearchQuery != "" {
		conditions = append(conditions, "(path LIKE ? OR request_id LIKE ?)")
		searchPattern := "%" + filter.SearchQuery + "%"
		args = append(args, searchPattern, searchPattern)
	}

	if len(conditions) == 0 {
		return "", nil
	}

	return fmt.Sprintf("%s", conditions[0]), args
}

func (r *RequestRepo) DeleteOldRequests(ctx context.Context, olderThan time.Duration) (int64, error) {
	cutoff := time.Now().UTC().Add(-olderThan)
	query := "DELETE FROM requests WHERE created_at < ?"

	result, err := r.db.ExecContext(ctx, query, cutoff.Format(time.RFC3339))
	if err != nil {
		return 0, err
	}

	return result.RowsAffected()
}