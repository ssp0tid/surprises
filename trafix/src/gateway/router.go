package gateway

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog"

	"trafix/config"
	"trafix/utils"
)

type Router struct {
	chi     *chi.Mux
	config  *config.Config
	logger  *zerolog.Logger
	proxy   *Proxy
}

func NewRouter(cfg *config.Config) *Router {
	logger := utils.GetLogger()

	proxy := NewProxy(cfg)

	r := &Router{
		chi:    chi.NewRouter(),
		config: cfg,
		logger: logger,
		proxy:  proxy,
	}

	r.setupMiddleware()
	r.setupRoutes()

	return r
}

func (r *Router) setupMiddleware() {
	r.chi.Use(middleware.RequestID)
	r.chi.Use(middleware.RealIP)
	r.chi.Use(middleware.Logger)
	r.chi.Use(middleware.Recoverer)

	if r.config.Middleware.CORS.Enabled {
		r.chi.Use(r.corsMiddleware())
	}
}

func (r *Router) corsMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			origin := req.Header.Get("Origin")
			allowed := false

			for _, o := range r.config.Middleware.CORS.AllowedOrigins {
				if o == origin || o == "*" {
					allowed = true
					break
				}
			}

			if allowed {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
			}

			if req.Method == "OPTIONS" {
				w.WriteHeader(http.StatusNoContent)
				return
			}

			next.ServeHTTP(w, req)
		})
	}
}

func (r *Router) setupRoutes() {
	r.chi.NotFound(r.handleNotFound)

	r.chi.Route("/", func(rdir chi.Router) {
		rdir.Get("/health", r.handleHealth)

		rdir.Route("/api", func(api chi.Router) {
			api.Route("/v1", func(v1 chi.Router) {
				v1.Use(r.pathPrefixMiddleware("/api/v1"))
				v1.Get("/*", r.proxy.ServeHTTP)
				v1.Post("/*", r.proxy.ServeHTTP)
				v1.Put("/*", r.proxy.ServeHTTP)
				v1.Delete("/*", r.proxy.ServeHTTP)
				v1.Patch("/*", r.proxy.ServeHTTP)
				v1.Options("/*", r.proxy.ServeHTTP)
			})
		})
	})
}

func (r *Router) pathPrefixMiddleware(prefix string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			req.URL.Path = r.stripPrefix(req.URL.Path, prefix)
			next.ServeHTTP(w, req)
		})
	}
}

func (r *Router) stripPrefix(path, prefix string) string {
	if len(prefix) == 0 {
		return path
	}

	if len(path) >= len(prefix) && path[:len(prefix)] == prefix {
		if len(path) == len(prefix) {
			return "/"
		}
		return path[len(prefix):]
	}

	return path
}

func (r *Router) handleHealth(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok"}`))
}

func (r *Router) handleNotFound(w http.ResponseWriter, req *http.Request) {
	err := utils.ErrNotFound
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(err.StatusCode())
	w.Write([]byte(`{"error":"` + err.Error() + `", "code":"` + err.Code() + `"}`))
}

func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	r.chi.ServeHTTP(w, req)
}