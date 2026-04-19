package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/logvault/logvault/internal/config"
	"github.com/logvault/logvault/internal/db"
	"github.com/logvault/logvault/internal/logparser"
	"github.com/logvault/logvault/internal/model"
)

type IngestHandler struct {
	db     *db.DB
	config *config.Config
}

func NewIngestHandler(database *db.DB, cfg *config.Config) *IngestHandler {
	return &IngestHandler{
		db:     database,
		config: cfg,
	}
}

func (h *IngestHandler) Register(r chi.Router) {
	r.Post("/api/v1/logs", h.IngestLog)
	r.Post("/api/v1/logs/batch", h.IngestBatch)
}

func (h *IngestHandler) IngestLog(w http.ResponseWriter, r *http.Request) {
	var req model.LogEntryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid JSON body")
		return
	}

	if err := h.validateRequest(&req); err != nil {
		WriteError(w, http.StatusBadRequest, "MISSING_FIELD", err.Error())
		return
	}

	entry := h.requestToEntry(&req)

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	if err := h.db.InsertLog(ctx, entry); err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to insert log")
		return
	}

	resp := model.IngestResponse{
		ID:      entry.ID,
		Success: true,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *IngestHandler) IngestBatch(w http.ResponseWriter, r *http.Request) {
	var req model.BatchIngestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid JSON body")
		return
	}

	if len(req.Logs) == 0 {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "no logs provided")
		return
	}

	if len(req.Logs) > h.config.Limits.MaxBatchSize {
		WriteError(w, http.StatusRequestEntityTooLarge, "PAYLOAD_TOO_LARGE", "batch size exceeds limit")
		return
	}

	entries := make([]*model.LogEntry, 0, len(req.Logs))
	for i, logReq := range req.Logs {
		if err := h.validateRequest(&logReq); err != nil {
			WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "log at index "+string(rune('0'+i))+": "+err.Error())
			return
		}
		entries = append(entries, h.requestToEntry(&logReq))
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	if err := h.db.InsertBatch(ctx, entries); err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to insert logs")
		return
	}

	resp := model.BatchIngestResponse{
		Success: true,
		Count:   len(entries),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *IngestHandler) validateRequest(req *model.LogEntryRequest) error {
	if req.Service == "" {
		return &ValidationError{Field: "service", Reason: "required"}
	}
	if req.Host == "" {
		req.Host = "unknown"
	}
	if req.Level == "" {
		req.Level = model.LogLevelInfo
	} else {
		level, err := logparser.ParseLevel(string(req.Level))
		if err == nil {
			req.Level = level
		}
	}
	if len(req.Message) > h.config.Limits.MaxMessageSize {
		req.Message = req.Message[:h.config.Limits.MaxMessageSize]
	}
	return nil
}

func (h *IngestHandler) requestToEntry(req *model.LogEntryRequest) *model.LogEntry {
	ts := time.Now()
	if req.Timestamp != nil {
		ts = *req.Timestamp
	}

	msg := req.Message
	if req.Raw == "" {
		req.Raw = msg
	}

	entry := &model.LogEntry{
		Timestamp: ts,
		Level:     req.Level,
		Service:   req.Service,
		Host:      req.Host,
		Message:   msg,
		Metadata:  req.Metadata,
		Raw:       req.Raw,
	}
	entry.ID = fmt.Sprintf("%d-%s", ts.UnixNano(), req.Service)

	return entry
}