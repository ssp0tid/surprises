package middleware

import (
	"context"
	"net/http"
	"sync"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/rs/zerolog"
	"golang.org/x/time/rate"

	"trafix/config"
	"trafix/utils"
)

type Middleware struct {
	config *config.Config
	logger zerolog.Logger

	mu           sync.RWMutex
	rateLimiters  map[string]*rate.Limiter
	apiKeys      map[string]bool
}

func NewMiddleware(cfg *config.Config) *Middleware {
	logger := utils.GetLogger()

	apiKeys := make(map[string]bool)
	for _, key := range cfg.Middleware.Auth.APIKeys {
		apiKeys[key] = true
	}

	m := &Middleware{
		config:      cfg,
		logger:      logger,
		rateLimiters: make(map[string]*rate.Limiter),
		apiKeys:     apiKeys,
	}

	return m
}

func (m *Middleware) RateLimit(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		if !m.config.Middleware.RateLimit.Enabled {
			next.ServeHTTP(w, req)
			return
		}

		limiter := m.getRateLimiter(req)

		if !limiter.Allow() {
			m.logger.Warn().
				Str("ip", req.RemoteAddr).
				Msg("rate limit exceeded")

			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusTooManyRequests)
			w.Write([]byte(`{"error":"rate limit exceeded","code":"rate_limited"}`))
			return
		}

		next.ServeHTTP(w, req)
	})
}

func (m *Middleware) getRateLimiter(req *http.Request) *rate.Limiter {
	key := req.RemoteAddr

	m.mu.RLock()
	limiter, ok := m.rateLimiters[key]
	m.mu.RUnlock()

	if ok {
		return limiter
	}

	m.mu.Lock()
	defer m.mu.Unlock()

	if limiter, ok := m.rateLimiters[key]; ok {
		return limiter
	}

	limiter = rate.NewLimiter(
		rate.Limit(m.config.Middleware.RateLimit.RequestsPerSecond),
		m.config.Middleware.RateLimit.Burst,
	)

	m.rateLimiters[key] = limiter

	return limiter
}

func (m *Middleware) Auth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		if !m.config.Middleware.Auth.Enabled {
			next.ServeHTTP(w, req)
			return
		}

		apiKey := req.Header.Get("Authorization")
		if apiKey == "" {
			apiKey = req.URL.Query().Get("api_key")
		}

		if apiKey == "" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte(`{"error":"missing api key","code":"unauthorized"}`))
			return
		}

		m.mu.RLock()
		valid := m.apiKeys[apiKey]
		m.mu.RUnlock()

		if !valid {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte(`{"error":"invalid api key","code":"unauthorized"}`))
			return
		}

		next.ServeHTTP(w, req)
	})
}

func (m *Middleware) Logging(next http.Handler) http.Handler {
	if !m.config.Middleware.Logging.Enabled {
		return next
	}

	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		startTime := time.Now()

		wrapper := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(wrapper, req)

		duration := time.Since(startTime)

		m.logger.Debug().
			Str("method", req.Method).
			Str("path", req.URL.Path).
			Str("remote_addr", req.RemoteAddr).
			Int("status_code", wrapper.statusCode).
			Dur("duration", duration).
			Int64("content_length", wrapper.bodySize).
			Msg("request")
	})
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
	bodySize int64
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(p []byte) (int, error) {
	n, err := rw.ResponseWriter.Write(p)
	rw.bodySize += int64(n)
	return n, err
}

func (m *Middleware) Chain(handlers ...func(http.Handler) http.Handler) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		for i := len(handlers) - 1; i >= 0; i-- {
			next = handlers[i](next)
		}
		return next
	}
}

func (m *Middleware) BuildMiddlewareStack() func(http.Handler) http.Handler {
	return m.Chain(
		m.RateLimit,
		m.Auth,
		m.Logging,
	)
}

func NewChiMiddleware(cfg *config.Config) func(http.Handler) http.Handler {
	m := NewMiddleware(cfg)
	return func(next http.Handler) http.Handler {
		return m.RateLimit(m.Auth(m.Logging(next)))
	}
}

func GetConfig() *config.Config {
	return nil
}

func GetLogger() zerolog.Logger {
	return utils.GetLogger()
}

func GetContextValue(ctx context.Context, key string) interface{} {
	return ctx.Value(contextKey(key))
}

func SetContextValue(ctx context.Context, key string, value interface{}) context.Context {
	return context.WithValue(ctx, contextKey(key), value)
}

type contextKey string

func (c contextKey) String() string {
	return string(c)
}