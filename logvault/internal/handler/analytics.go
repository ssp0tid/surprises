package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/logvault/logvault/internal/analytics"
	"github.com/logvault/logvault/internal/db"
	"github.com/logvault/logvault/internal/model"
)

type AnalyticsHandler struct {
	db     *db.DB
	engine *analytics.Engine
}

func NewAnalyticsHandler(database *db.DB, eng *analytics.Engine) *AnalyticsHandler {
	return &AnalyticsHandler{
		db:     database,
		engine: eng,
	}
}

func (h *AnalyticsHandler) Register(r chi.Router) {
	r.Get("/api/v1/analytics/summary", h.Summary)
	r.Get("/api/v1/analytics/volume", h.Volume)
	r.Get("/api/v1/analytics/levels", h.Levels)
	r.Get("/api/v1/analytics/services", h.Services)
}

func (h *AnalyticsHandler) Summary(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	result, err := h.engine.Summary(ctx)
	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to get summary")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *AnalyticsHandler) Volume(w http.ResponseWriter, r *http.Request) {
	interval := r.URL.Query().Get("interval")
	if interval == "" {
		interval = "1h"
	}

	fromStr := r.URL.Query().Get("from")
	toStr := r.URL.Query().Get("to")

	from := time.Now().Add(-24 * time.Hour)
	to := time.Now()

	if fromStr != "" {
		if parsed, err := time.Parse(time.RFC3339, fromStr); err == nil {
			from = parsed
		} else {
			WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid 'from' time format, use RFC3339")
			return
		}
	}

	if toStr != "" {
		if parsed, err := time.Parse(time.RFC3339, toStr); err == nil {
			to = parsed
		} else {
			WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid 'to' time format, use RFC3339")
			return
		}
	}

	if from.After(to) {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "'from' time must be before 'to' time")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	result, err := h.engine.Volume(ctx, interval, from, to)
	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to get volume")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *AnalyticsHandler) Levels(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	result, err := h.engine.LevelDistribution(ctx)
	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to get levels")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *AnalyticsHandler) Services(w http.ResponseWriter, r *http.Request) {
	fromStr := r.URL.Query().Get("from")
	toStr := r.URL.Query().Get("to")

	from := time.Now().Add(-24 * time.Hour)
	to := time.Now()

	if fromStr != "" {
		if parsed, err := time.Parse(time.RFC3339, fromStr); err == nil {
			from = parsed
		} else {
			WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid 'from' time format, use RFC3339")
			return
		}
	}

	if toStr != "" {
		if parsed, err := time.Parse(time.RFC3339, toStr); err == nil {
			to = parsed
		} else {
			WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "invalid 'to' time format, use RFC3339")
			return
		}
	}

	if from.After(to) {
		WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "'from' time must be before 'to' time")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	result, err := h.engine.ServiceBreakdown(ctx, from, to)
	if err != nil {
		WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to get services")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *AnalyticsHandler) Health(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	if err := h.db.Ping(ctx); err != nil {
		WriteError(w, http.StatusServiceUnavailable, "SERVICE_UNAVAILABLE", "database unavailable")
		return
	}

	resp := map[string]string{"status": "healthy", "database": "ok"}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}