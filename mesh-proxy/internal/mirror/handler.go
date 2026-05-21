package mirror

import (
	"bytes"
	"io"
	"math/rand"
	"net/http"
	"strings"
	"time"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type Handler struct {
	target     string
	percentage float64
	client    *http.Client
	rand      *rand.Rand
	enabled   bool
}

func New(cfg *types.MirrorConfig) (*Handler, error) {
	if cfg == nil || !cfg.Enabled {
		return nil, nil
	}

	return &Handler{
		target:     cfg.Target,
		percentage: cfg.Percentage,
		enabled:   cfg.Enabled,
		client: &http.Client{
			Timeout: 5 * time.Second,
		},
		rand: rand.New(rand.NewSource(time.Now().UnixNano())),
	}, nil
}

func (h *Handler) Mirror(req *http.Request) {
	if h == nil || !h.enabled {
		return
	}

	if h.percentage < 100 && h.rand.Float64()*100 > h.percentage {
		return
	}

	body, _ := io.ReadAll(req.Body)
	req.Body = io.NopCloser(bytes.NewReader(body))

	mirrorURL := h.target + req.URL.Path
	mirrorReq, err := http.NewRequest(req.Method, mirrorURL, bytes.NewReader(body))
	if err != nil {
		return
	}

	for k, v := range req.Header {
		mirrorReq.Header[k] = v
	}
	mirrorReq.Header.Set("X-Mirror-Service", "true")

	go func() {
		resp, err := h.client.Do(mirrorReq)
		if err != nil {
			return
		}
		defer resp.Body.Close()
		io.Copy(io.Discard, resp.Body)
	}()
}

func (h *Handler) IsEnabled() bool {
	return h != nil && h.enabled
}

func CopyRequest(src *http.Request, targetURL string) (*http.Request, error) {
	body, err := io.ReadAll(src.Body)
	if err != nil {
		return nil, err
	}
	src.Body = io.NopCloser(bytes.NewReader(body))

	req, err := http.NewRequest(src.Method, targetURL+src.URL.Path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}

	for k, v := range src.Header {
		req.Header[k] = v
	}

	return req, nil
}

func ExtractPath(url string) string {
	if idx := strings.Index(url, "://"); idx != -1 {
		pathStart := strings.Index(url[idx+2:], "/")
		if pathStart != -1 {
			return url[idx+2+pathStart:]
		}
	}
	return "/"
}