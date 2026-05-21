package dashboard

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog"

	"trafix/config"
	"trafix/utils"
)

type Server struct {
	config *config.Config
	logger zerolog.Logger
	server *http.Server
}

func NewServer(cfg *config.Config) *Server {
	logger := utils.GetLogger()

	addr := fmt.Sprintf("%s:%d", cfg.Dashboard.Host, cfg.Dashboard.Port)

	mux := chi.NewRouter()

	s := &Server{
		config: cfg,
		logger: logger,
		server: &http.Server{
			Addr:         addr,
			Handler:      mux,
			ReadTimeout:  10 * time.Second,
			WriteTimeout: 10 * time.Second,
			IdleTimeout: 60 * time.Second,
		},
	}

	s.setupRoutes()

	return s
}

func (s *Server) setupRoutes() {
	mux := s.server.Handler.(*chi.Mux)

	mux.Use(middleware.RequestID)
	mux.Use(middleware.RealIP)
	mux.Use(middleware.Logger)
	mux.Use(middleware.Recoverer)
	mux.Use(s.authMiddleware())

	mux.Get("/health", s.handleHealth)
	mux.Get("/metrics", s.handleMetrics)
	mux.Get("/config", s.handleConfig)
}

func (s *Server) authMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			username, password, ok := req.BasicAuth()
			if !ok || username != s.config.Dashboard.Username || password != s.config.Dashboard.Password {
				w.Header().Set("WWW-Authenticate", `Basic realm="Trafix Dashboard"`)
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}
			next.ServeHTTP(w, req)
		})
	}
}

func (s *Server) handleHealth(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (s *Server) handleMetrics(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	metrics := map[string]interface{}{
		"total_requests":   0,
		"total_responses":  0,
		"error_count":      0,
		"uptime":           "0s",
		"avg_response_time": "0ms",
		"requests_per_second": 0.0,
	}

	json.NewEncoder(w).Encode(metrics)
}

func (s *Server) handleConfig(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	conf := map[string]interface{}{
		"server": map[string]interface{}{
			"host": s.config.Server.Host,
			"port": s.config.Server.Port,
		},
		"proxy": map[string]interface{}{
			"host":            s.config.Proxy.Host,
			"port":           s.config.Proxy.Port,
			"target_base_url": s.config.Proxy.TargetBaseURL,
		},
		"storage": map[string]interface{}{
			"database": s.config.Storage.Database,
		},
	}

	json.NewEncoder(w).Encode(conf)
}

func (s *Server) Start() error {
	s.logger.Info().Str("addr", s.server.Addr).Msg("Starting dashboard server")
	return s.server.ListenAndServe()
}

func (s *Server) Stop() error {
	s.logger.Info().Msg("Stopping dashboard server")
	return s.server.Close()
}

func (s *Server) GetAddr() string {
	return s.server.Addr
}