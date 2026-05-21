package mock

import (
	"io"
	"net/http"
	"os"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type Handler struct {
	StatusCode int
	Headers   http.Header
	Body      []byte
}

func New(cfg *types.MockConfig) (*Handler, error) {
	if cfg == nil || !cfg.Enabled {
		return nil, nil
	}

	body := []byte(cfg.Body)
	if cfg.BodyFile != "" {
		var err error
		body, err = os.ReadFile(cfg.BodyFile)
		if err != nil {
			return nil, err
		}
	}

	return &Handler{
		StatusCode: cfg.StatusCode,
		Headers:   convertHeaders(cfg.Headers),
		Body:     body,
	}, nil
}

func convertHeaders(m map[string]string) http.Header {
	h := make(http.Header)
	for k, v := range m {
		h.Set(k, v)
	}
	return h
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if h == nil {
		return
	}

	for k, v := range h.Headers {
		w.Header()[k] = v
	}

	w.WriteHeader(h.StatusCode)
	w.Write(h.Body)
}

func (h *Handler) IsEnabled() bool {
	return h != nil && h.StatusCode > 0
}

type middleware struct {
	handler *Handler
	next    http.Handler
}

func Middleware(h *Handler) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return &middleware{handler: h, next: next}
	}
}

func (m *middleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if m.handler != nil && m.handler.IsEnabled() {
		m.handler.ServeHTTP(w, r)
		return
	}
	m.next.ServeHTTP(w, r)
}

type mockResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (m *mockResponseWriter) WriteHeader(code int) {
	m.statusCode = code
	m.ResponseWriter.WriteHeader(code)
}

func (m *mockResponseWriter) Write(b []byte) (int, error) {
	if m.statusCode == 0 {
		m.statusCode = http.StatusOK
	}
	return m.ResponseWriter.Write(b)
}

func WrapResponseWriter(w http.ResponseWriter) http.ResponseWriter {
	if _, ok := w.(*mockResponseWriter); ok {
		return w
	}
	return &mockResponseWriter{ResponseWriter: w}
}

func ReadBody(r *http.Request) ([]byte, error) {
	if r.Body == nil {
		return nil, nil
	}
	return io.ReadAll(r.Body)
}