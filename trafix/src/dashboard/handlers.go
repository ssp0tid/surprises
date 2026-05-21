package dashboard

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jmoiron/sqlx"

	"trafix/analytics"
	"trafix/config"
	"trafix/storage"
	"trafix/utils"
)

type Handlers struct {
	db       *sqlx.DB
	config   *config.Config
	analytics *analytics.AnalyticsService
	repo     *storage.RequestRepo
}

func NewHandlers(db *sqlx.DB, cfg *config.Config) *Handlers {
	repo := storage.NewRequestRepo(db)
	analyticsSvc := analytics.NewAnalyticsService(db)

	return &Handlers{
		db:       db,
		config:   cfg,
		analytics: analyticsSvc,
		repo:     repo,
	}
}

func (h *Handlers) RegisterRoutes(r chi.Router) {
	r.Get("/health", h.HandleHealth)
	r.Get("/api/requests", h.HandleListRequests)
	r.Get("/api/requests/{id}", h.HandleGetRequest)
	r.Get("/api/analytics", h.HandleAnalytics)
	r.Get("/api/config", h.HandleConfig)
	r.Get("/api/metrics", h.HandleMetrics)
}

func (h *Handlers) HandleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status": "ok",
		"time":  time.Now().UTC().Format(time.RFC3339),
	})
}

func (h *Handlers) HandleListRequests(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")
	method := r.URL.Query().Get("method")
	path := r.URL.Query().Get("path")
	statusStr := r.URL.Query().Get("status")
	search := r.URL.Query().Get("search")

	limit := 50
	offset := 0

	if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
		limit = l
	}
	if o, err := strconv.Atoi(offsetStr); err == nil && o > 0 {
		offset = o
	}

	filter := storage.RequestFilter{
		Limit:        limit,
		Offset:       offset,
		Method:       method,
		Path:         path,
		SearchQuery: search,
	}

	if s, err := strconv.Atoi(statusStr); err == nil && s > 0 {
		filter.StatusCode = s
	}

	result, err := h.repo.ListWithPagination(context.Background(), filter)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error": err.Error(),
		})
		return
	}

	json.NewEncoder(w).Encode(result)
}

func (h *Handlers) HandleGetRequest(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	requestID := chi.URLParam(r, "id")
	if requestID == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "request id required",
		})
		return
	}

	record, err := h.repo.GetByID(context.Background(), requestID)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error": err.Error(),
		})
		return
	}

	if record == nil {
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "request not found",
		})
		return
	}

	json.NewEncoder(w).Encode(record)
}

func (h *Handlers) HandleAnalytics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	windowStr := r.URL.Query().Get("window")
	if windowStr == "" {
		windowStr = "1h"
	}

	window := analytics.AnalyticsWindow(windowStr)
	result, err := h.analytics.GetAnalytics(context.Background(), window)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{
			"error": err.Error(),
		})
		return
	}

	json.NewEncoder(w).Encode(result)
}

func (h *Handlers) HandleConfig(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	conf := map[string]interface{}{
		"server": map[string]interface{}{
			"host": h.config.Server.Host,
			"port": h.config.Server.Port,
		},
		"proxy": map[string]interface{}{
			"host":             h.config.Proxy.Host,
			"port":            h.config.Proxy.Port,
			"target_base_url": h.config.Proxy.TargetBaseURL,
			"timeout":         h.config.Proxy.Timeout.String(),
		},
		"storage": map[string]interface{}{
			"database": h.config.Storage.Database,
		},
		"middleware": map[string]interface{}{
			"rate_limit": map[string]interface{}{
				"enabled": h.config.Middleware.RateLimit.Enabled,
			},
			"auth": map[string]interface{}{
				"enabled": h.config.Middleware.Auth.Enabled,
			},
			"logging": map[string]interface{}{
				"enabled": h.config.Middleware.Logging.Enabled,
			},
			"cors": map[string]interface{}{
				"enabled": h.config.Middleware.CORS.Enabled,
			},
		},
	}

	json.NewEncoder(w).Encode(conf)
}

func (h *Handlers) HandleMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var totalRequests, totalResponses, errorCount int64
	var avgResponseTime float64

	err := h.db.GetContext(context.Background(), &totalRequests,
		"SELECT COUNT(*) FROM requests")
	if err != nil {
		totalRequests = 0
	}

	err = h.db.GetContext(context.Background(), &errorCount,
		"SELECT COUNT(*) FROM requests WHERE status_code >= 400")
	if err != nil {
		errorCount = 0
	}

	err = h.db.GetContext(context.Background(), &avgResponseTime,
		"SELECT COALESCE(AVG(duration_ms), 0) FROM requests")
	if err != nil {
		avgResponseTime = 0
	}

	totalResponses = totalRequests

	metrics := map[string]interface{}{
		"total_requests":      totalRequests,
		"total_responses":     totalResponses,
		"error_count":         errorCount,
		"avg_response_time_ms": avgResponseTime,
		"uptime":              "0s",
		"requests_per_second": 0.0,
	}

	json.NewEncoder(w).Encode(metrics)
}

func (h *Handlers) WriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		utils.GetLogger().Error().Err(err).Msg("failed to encode JSON response")
	}
}

func (h *Handlers) WriteError(w http.ResponseWriter, status int, message string) {
	h.WriteJSON(w, status, map[string]string{
		"error": message,
	})
}

func (h *Handlers) GetDB() *sqlx.DB {
	return h.db
}

func (h *Handlers) GetConfig() *config.Config {
	return h.config
}

func (h *Handlers) GetAnalytics() *analytics.AnalyticsService {
	return h.analytics
}

func (h *Handlers) GetRepo() *storage.RequestRepo {
	return h.repo
}

func (h *Handlers) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Trafix Dashboard")
}