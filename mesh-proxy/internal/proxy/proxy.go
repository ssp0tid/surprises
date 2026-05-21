package proxy

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/rs/zerolog"
	"github.com/surprises/mesh-proxy/internal/config"
	"github.com/surprises/mesh-proxy/internal/delay"
	"github.com/surprises/mesh-proxy/internal/mock"
	"github.com/surprises/mesh-proxy/internal/ratelimit"
	"github.com/surprises/mesh-proxy/internal/router"
)

type Proxy struct {
	cfg        *config.Config
	router    *router.Router
	server   *http.Server
	admin    *http.Server
	logger   zerolog.Logger
	wg       sync.WaitGroup
	stats    *Stats
	limiter  *ratelimit.Limiter
}

type Stats struct {
	mu              sync.RWMutex
	RequestsTotal   int64
	RequestsAllowed int64
	RequestsDenied  int64
}

func New(cfg *config.Config, logger zerolog.Logger) (*Proxy, error) {
	p := &Proxy{
		cfg:   cfg,
		router: router.NewRouter(),
		logger: logger,
		stats: &Stats{},
	}

	limiterCfg := cfg.RateLimit
	if limiterCfg != nil {
		p.limiter = ratelimit.New(limiterCfg.RequestsPerSecond, limiterCfg.Burst, "")
	}

	for _, route := range cfg.Routes {
		if err := p.router.AddFromConfig(route); err != nil {
			return nil, fmt.Errorf("add route %s: %w", route.Name, err)
		}
	}

	return p, nil
}

func (p *Proxy) Serve() error {
	addr := fmt.Sprintf("%s:%d", p.cfg.Server.Host, p.cfg.Server.Port)
	p.server = &http.Server{
		Addr:         addr,
		ReadTimeout:  p.cfg.Server.ReadTimeout,
		WriteTimeout: p.cfg.Server.WriteTimeout,
		IdleTimeout:  p.cfg.Server.IdleTimeout,
		Handler:     p,
	}

	p.logger.Info().Str("addr", addr).Msg("starting proxy server")

	if err := p.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("listen: %w", err)
	}

	return nil
}

func (p *Proxy) StartAdmin() error {
	if !p.cfg.Admin.Enabled {
		p.logger.Info().Msg("admin server disabled")
		return nil
	}

	addr := fmt.Sprintf("%s:%d", p.cfg.Admin.Host, p.cfg.Admin.Port)
	p.admin = &http.Server{
		Addr:    addr,
		Handler: p.adminRouter(),
	}

	p.logger.Info().Str("addr", addr).Msg("starting admin server")

	if err := p.admin.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("admin listen: %w", err)
	}

	return nil
}

func (p *Proxy) adminRouter() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", p.handleHealth)
	mux.HandleFunc("/config", p.handleConfig)
	mux.HandleFunc("/routes", p.handleRoutes)
	mux.HandleFunc("/stats", p.handleStats)
	return mux
}

func (p *Proxy) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (p *Proxy) handleConfig(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"version": p.cfg.Version,
		"server":  p.cfg.Server,
		"routes":  p.cfg.Routes,
	})
}

func (p *Proxy) handleRoutes(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	rules := p.router.GetRules()
	json.NewEncoder(w).Encode(map[string]interface{}{
		"routes": rules,
	})
}

func (p *Proxy) handleStats(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	p.stats.mu.RLock()
	defer p.stats.mu.RUnlock()
	json.NewEncoder(w).Encode(map[string]int64{
		"requests_total":    p.stats.RequestsTotal,
		"requests_allowed": p.stats.RequestsAllowed,
		"requests_denied": p.stats.RequestsDenied,
	})
}

func (p *Proxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	p.stats.mu.Lock()
	p.stats.RequestsTotal++
	p.stats.mu.Unlock()

	rule := p.router.Match(r)
	if rule == nil {
		http.NotFound(w, r)
		return
	}

	p.stats.mu.Lock()
	p.stats.RequestsAllowed++
	p.stats.mu.Unlock()

	if rule.Backend != nil && rule.Backend.URL != "" {
		p.proxyRequest(w, r, rule)
		return
	}

	for _, route := range p.cfg.Routes {
		if route.Name != rule.Name {
			continue
		}

		if route.Mock != nil && route.Mock.Enabled {
			mh, err := mock.New(route.Mock)
			if err != nil {
				p.logger.Error().Err(err).Msg("mock handler error")
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}
			if mh != nil {
				mh.ServeHTTP(w, r)
				return
			}
		}

		if route.Delay != nil {
			 injector := delay.New(route.Delay)
			injector.Wait()
		}

		http.NotFound(w, r)
	}
}

func (p *Proxy) proxyRequest(w http.ResponseWriter, r *http.Request, rule *router.Rule) {
	if rule.Backend == nil || rule.Backend.URL == "" {
		http.NotFound(w, r)
		return
	}

	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout: p.cfg.Defaults.Timeout,
		}).DialContext,
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:    90 * time.Second,
	}

	backendURL, _ := url.Parse(rule.Backend.URL)
	proxy := httputil.NewSingleHostReverseProxy(backendURL)
	proxy.Transport = transport

	for _, route := range p.cfg.Routes {
		if route.Name == rule.Name && route.Delay != nil {
			injector := delay.New(route.Delay)
			injector.Wait()
			break
		}
	}

	proxy.ServeHTTP(w, r)
}

func (p *Proxy) Shutdown(ctx context.Context) error {
	p.logger.Info().Msg("shutting down proxy")

	if p.server != nil {
		if err := p.server.Shutdown(ctx); err != nil {
			p.logger.Error().Err(err).Msg("server shutdown error")
		}
	}

	if p.admin != nil {
		if err := p.admin.Shutdown(ctx); err != nil {
			p.logger.Error().Err(err).Msg("admin shutdown error")
		}
	}

	return nil
}

func (p *Proxy) WaitForSignal() {
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
}

func (p *Proxy) GetStats() *Stats {
	return p.stats
}

func (p *Proxy) GetRouter() *router.Router {
	return p.router
}

func (p *Proxy) GetConfig() *config.Config {
	return p.cfg
}