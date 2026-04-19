package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/logvault/logvault/internal/db"
	"github.com/logvault/logvault/internal/model"
)

type QueryHandler struct {
	db *db.DB
}

func NewQueryHandler(database *db.DB) *QueryHandler {
	return &QueryHandler{db: database}
}

func (h *QueryHandler) Register(r chi.Router) {
	r.Get("/api/v1/logs", h.QueryLogs)
	r.Get("/api/v1/logs/{id}", h.GetLog)
}

func (h *QueryHandler) QueryLogs(w http.ResponseWriter, r *http.Request) {
	params, err := h.parseQueryParams(r)
	if err != nil {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", err.Error())
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	limit := params.Limit
	if limit <= 0 || limit > 1000 {
		limit = 100
	}

	logs, cursor, total, err := h.db.QueryLogs(ctx, db.LogFilter{
		Query:   params.Query,
		Level:   params.Level,
		Service: params.Service,
		Host:   params.Host,
		From:   params.From,
		To:     params.To,
	}, limit, params.Cursor)

	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "query failed")
		return
	}

	if logs == nil {
		logs = []*model.LogEntry{}
	}

	resp := model.PaginatedResponse{
		Logs:   logs,
		Cursor: cursor,
		Total:  total,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *QueryHandler) GetLog(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if id == "" {
		WriteError(w, http.StatusNotFound, "NOT_FOUND", "log id required")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	log, err := h.db.GetLogByID(ctx, id)
	if err != nil {
		WriteError(w, http.StatusNotFound, "NOT_FOUND", "log not found")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(log)
}

func (h *QueryHandler) parseQueryParams(r *http.Request) (*model.LogQueryParams, error) {
	params := &model.LogQueryParams{
		Query:   r.URL.Query().Get("q"),
		Level:   r.URL.Query().Get("level"),
		Service: r.URL.Query().Get("service"),
		Host:   r.URL.Query().Get("host"),
		Cursor: r.URL.Query().Get("cursor"),
		Sort:   r.URL.Query().Get("sort"),
		Order:  r.URL.Query().Get("order"),
	}

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		var limit int
		if _, err := parseInt(limitStr, &limit); err == nil {
			params.Limit = limit
		}
	}

	if fromStr := r.URL.Query().Get("from"); fromStr != "" {
		ts, err := time.Parse(time.RFC3339, fromStr)
		if err == nil {
			params.From = ts
		}
	}

	if toStr := r.URL.Query().Get("to"); toStr != "" {
		ts, err := time.Parse(time.RFC3339, toStr)
		if err == nil {
			params.To = ts
		}
	}

	return params, nil
}

func parseInt(s string, v *int) (bool, error) {
	n, err := strconv.Atoi(s)
	if err != nil {
		return false, err
	}
	*v = n
	return true, nil
}

type LogQueryParams struct {
	Query   string
	Level   string
	Service string
	Host    string
	From    time.Time
	To      time.Time
	Limit   int
	Cursor  string
	Sort    string
	Order   string
}

func (h *QueryHandler) parseQueryParamsOLD(r *http.Request) (string, error) {
	q := r.URL.Query()
	limitStr := q.Get("limit")

	result := LogQueryParams{
		Query:   q.Get("q"),
		Level:   q.Get("level"),
		Service: q.Get("service"),
		Host:   q.Get("host"),
		Cursor: q.Get("cursor"),
		Sort:   q.Get("sort"),
		Order:  q.Get("order"),
	}

	if limitStr != "" {
		var limit int
		if n, err := strings.NewReader(limitStr).Read(nil); n > 0 {
			result.Limit = limit
		} else if err != nil {
			
		}
	}
}