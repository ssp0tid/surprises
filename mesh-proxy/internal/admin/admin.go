package admin

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/surprises/mesh-proxy/internal/config"
	"github.com/surprises/mesh-proxy/internal/proxy"
	"github.com/surprises/mesh-proxy/internal/router"
)

type Handler struct {
	cfg     *config.Config
	proxy   *proxy.Proxy
	router  *router.Router
	server  *http.Server
}

func New(cfg *config.Config, p *proxy.Proxy) *Handler {
	return &Handler{
		cfg:    cfg,
		proxy:  p,
	}
}

func (h *Handler) Router() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", h.handleHealth)
	mux.HandleFunc("/config", h.handleConfig)
	mux.HandleFunc("/routes", h.handleRoutes)
	mux.HandleFunc("/stats", h.handleStats)
	mux.HandleFunc("/reload", h.handleReload)
	mux.HandleFunc("/circuit/breakers", h.handleCircuitBreakers)
	mux.HandleFunc("/loglevel", h.handleLogLevel)
	return mux
}

func (h *Handler) Serve(addr string) error {
	h.server = &http.Server{
		Addr:         addr,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		Handler:      h.Router(),
	}
	return h.server.ListenAndServe()
}

func (h *Handler) Shutdown(ctx context.Context) error {
	if h.server == nil {
		return nil
	}
	return h.server.Shutdown(ctx)
}

func (h *Handler) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok",
		"time":   time.Now().Unix(),
	})
}

func (h *Handler) handleConfig(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if h.cfg == nil {
		http.Error(w, "no config", http.StatusNoContent)
		return
	}
	json.NewEncoder(w).Encode(map[string]interface{}{
		"version": h.cfg.Version,
		"server":  h.cfg.Server,
		"admin":   h.cfg.Admin,
		"routes":  h.cfg.Routes,
	})
}

func (h *Handler) handleRoutes(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if h.router == nil {
		http.Error(w, "no router", http.StatusNoContent)
		return
	}
	rules := h.router.GetRules()
	json.NewEncoder(w).Encode(map[string]interface{}{
		"routes": rules,
	})
}

func (h *Handler) handleStats(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if h.proxy == nil {
		http.Error(w, "no proxy", http.StatusNoContent)
		return
	}
	stats := h.proxy.GetStats()
	json.NewEncoder(w).Encode(map[string]interface{}{
		"requests_total":    stats.RequestsTotal,
		"requests_allowed":  stats.RequestsAllowed,
		"requests_denied":   stats.RequestsDenied,
	})
}

func (h *Handler) handleReload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "reloaded",
		"message": "configuration reloaded successfully",
	})
}

func (h *Handler) handleCircuitBreakers(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"breakers": []interface{}{},
	})
}

func (h *Handler) handleLogLevel(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"level": "info",
		})
	case http.MethodPost:
		w.Header().Set("Content-Type", "application/json")
		var body struct {
			Level string `json:"level"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status": "ok",
			"level":  body.Level,
		})
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

type Response struct {
	Status  string      `json:"status"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func (r *Response) Encode(w http.ResponseWriter) error {
	w.Header().Set("Content-Type", "application/json")
	return json.NewEncoder(w).Encode(r)
}

func JSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

func Error(w http.ResponseWriter, err error, code int) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "error",
		"error":  err.Error(),
	})
}

func Render(w http.ResponseWriter, tmpl string, data interface{}) {
	fmt.Fprintf(w, "template: %s, data: %v", tmpl, data)
}