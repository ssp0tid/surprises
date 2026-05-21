package proxy

import (
	"io"
	"net/http"
	"time"

	"github.com/rs/zerolog"
	"github.com/surprises/mesh-proxy/internal/delay"
	"github.com/surprises/mesh-proxy/internal/mock"
)

type Handler struct {
	proxy     *Proxy
	logger    zerolog.Logger
	startTime time.Time
}

func NewHandler(p *Proxy, logger zerolog.Logger) *Handler {
	return &Handler{
		proxy:     p,
		logger:    logger,
		startTime: time.Now(),
	}
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	h.logger.Debug().
		Str("method", r.Method).
		Str("path", r.URL.Path).
		Str("remote", r.RemoteAddr).
		Msg("request")


	route := h.proxy.router.Match(r)
	if route == nil {
		h.logger.Debug().Msg("no route matched")
		http.NotFound(w, r)
		return
	}

	if !route.Enabled {
		h.logger.Debug().Str("route", route.Name).Msg("route disabled")
		http.NotFound(w, r)
		return
	}

	for _, cfgRoute := range h.proxy.cfg.Routes {
		if cfgRoute.Name != route.Name {
			continue
		}

		if cfgRoute.RateLimit != nil && h.proxy.limiter != nil {
			if err := h.proxy.limiter.Allow(r); err != nil {
				h.logger.Warn().Err(err).Msg("rate limited")
				w.Header().Set("X-RateLimit-Reset", "1")
				http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
				return
			}
		}

		if cfgRoute.Mock != nil && cfgRoute.Mock.Enabled {
			mh, err := mock.New(cfgRoute.Mock)
			if err != nil {
				h.logger.Error().Err(err).Msg("mock handler error")
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}
			if mh != nil {
				mh.ServeHTTP(w, r)
				return
			}
		}

		if cfgRoute.Delay != nil {
			injector := delay.New(cfgRoute.Delay)
			injector.Wait()
		}

		if cfgRoute.Backend != nil && cfgRoute.Backend.URL != "" {
			h.proxyRequest(w, r, cfgRoute.Backend.URL, cfgRoute.Timeout)
			return
		}

		break
	}

	http.NotFound(w, r)
}

func (h *Handler) proxyRequest(w http.ResponseWriter, r *http.Request, backendURL string, timeout time.Duration) {
	req, err := http.NewRequestWithContext(r.Context(), r.Method, backendURL+r.URL.Path, r.Body)
	if err != nil {
		h.logger.Error().Err(err).Msg("create request error")
		http.Error(w, "Bad Gateway", http.StatusBadGateway)
		return
	}

	for k, v := range r.Header {
		req.Header[k] = v
	}

	client := &http.Client{
		Timeout: timeout,
	}

	resp, err := client.Do(req)
	if err != nil {
		h.logger.Error().Err(err).Msg("backend request error")
		http.Error(w, "Bad Gateway", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	for k, v := range resp.Header {
		w.Header()[k] = v
	}

	w.WriteHeader(resp.StatusCode)
	io.Copy(w, resp.Body)
}

func (h *Handler) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok","uptime":` + time.Since(h.startTime).String() + `}`))
}

func (h *Handler) handleConfig(w http.ResponseWriter, r *http.Request) {
	h.proxy.handleConfig(w, r)
}

func (h *Handler) handleRoutes(w http.ResponseWriter, r *http.Request) {
	h.proxy.handleRoutes(w, r)
}

func (h *Handler) handleStats(w http.ResponseWriter, r *http.Request) {
	h.proxy.handleStats(w, r)
}

type contextKey string

const (
	contextKeyRoute    contextKey = "route"
	contextKeyDelay  contextKey = "delay"
	contextKeyStart  contextKey = "start"
)