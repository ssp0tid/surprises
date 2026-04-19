package server

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/logvault/logvault/internal/analytics"
	"github.com/logvault/logvault/internal/config"
	"github.com/logvault/logvault/internal/db"
	"github.com/logvault/logvault/internal/handler"
)

type Server struct {
	httpServer *http.Server
	config    *config.Config
}

func New(cfg *config.Config, database *db.DB) (*Server, error) {
	eng := analytics.NewEngine(database)

	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	handler.InstallRoutes(r, cfg, database, eng)

	srv := &Server{
		httpServer: &http.Server{
			Addr:         cfg.Addr(),
			Handler:      r,
			ReadTimeout:  30 * time.Second,
			WriteTimeout: 30 * time.Second,
			IdleTimeout: 120 * time.Second,
		},
		config: cfg,
	}

	return srv, nil
}

func (s *Server) ListenAndServe() error {
	ln, err := net.Listen("tcp", s.httpServer.Addr)
	if err != nil {
		return err
	}

	return s.httpServer.Serve(ln)
}

func (s *Server) Shutdown(ctx context.Context) error {
	return s.httpServer.Shutdown(ctx)
}

func (s *Server) Addr() string {
	return s.httpServer.Addr
}

type routeConfig struct {
	config *config.Config
	db     *db.DB
	engine *analytics.Engine
}

func InstallRoutes(r chi.Router, cfg *config.Config, database *db.DB, eng *analytics.Engine) {
	authHandler := handler.NewAuthHandler(cfg)

	ingestHandler := handler.NewIngestHandler(database, cfg)
	queryHandler := handler.NewQueryHandler(database)
	streamHandler := handler.NewStreamHandler()
	analyticsHandler := handler.NewAnalyticsHandler(database, eng)

	r.Group(func(r chi.Router) {
		r.Use(middleware.WithValue("config", cfg))
		r.Use(middleware.WithValue("db", database))

		r.Mount("/api/v1", func(r chi.Router) chi.Router {
			r.Group(func(r chi.Router) {
				r.Use(middleware.Maybe(authHandler, func(h http.Handler) http.Handler {
					if !cfg.Auth.Enabled {
						return h
					}
					return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
						h.ServeHTTP(w, r)
					})
				}))

				ingestHandler.Register(r)
				queryHandler.Register(r)
				streamHandler.Register(r)
				analyticsHandler.Register(r)
			})

			r.Group(func(r chi.Router) {
				authHandler.Register(r)
			})

			r.Get("/health", healthHandler(database))

			return r
		})

		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprintf(w, "LogVault - Self-hosted Log Management")
		})
	})
}

func healthHandler(database *db.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()

		if err := database.Ping(ctx); err != nil {
			http.Error(w, "Service Unavailable", http.StatusServiceUnavailable)
			return
		}

		w.Write([]byte("OK"))
	}
}