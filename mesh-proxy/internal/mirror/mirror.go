package mirror

import (
	"bytes"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/http/httputil"
	"strings"
	"time"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type MirroredRequest struct {
	Target      string
	Percentage float64
	PercentageHeader string
}

func New(cfg *types.MirrorConfig) *MirroredRequest {
	if cfg == nil || !cfg.Enabled {
		return nil
	}

	m := &MirroredRequest{
		Target:      cfg.Target,
		Percentage:  cfg.Percentage,
		PercentageHeader: cfg.PercentageHeader,
	}

	if m.Percentage == 0 {
		m.Percentage = 100.0
	}

	return m
}

func (m *MirroredRequest) ShouldMirror(r *http.Request) bool {
	if m == nil || m.Target == "" {
		return false
	}

	if m.PercentageHeader != "" {
		if headerVal := r.Header.Get(m.PercentageHeader); headerVal != "" {
			var pct float64
			fmt.Sscanf(headerVal, "%f", &pct)
			if pct > 0 && rand.Float64()*100 > (100 - pct) {
				return true
			}
			return false
		}
	}

	if m.Percentage >= 100.0 {
		return true
	}

	if m.Percentage <= 0 {
		return false
	}

	return rand.Float64()*100 < m.Percentage
}

func (m *MirroredRequest) MirrorRequest(r *http.Request) error {
	if m == nil || m.Target == "" {
		return nil
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		return fmt.Errorf("read body: %w", err)
	}
	r.Body = io.NopCloser(bytes.NewReader(body))

	targetURL := m.Target
	if !strings.HasPrefix(targetURL, "http") {
		targetURL = "http://" + targetURL
	}

	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	req := r.Clone(r.Context())
	req.URL.Scheme = "http"
	if strings.HasPrefix(m.Target, "http://") {
		req.URL.Scheme = "http"
	} else if strings.HasPrefix(m.Target, "https://") {
		req.URL.Scheme = "https"
	}
	req.URL.Host = strings.TrimPrefix(strings.TrimPrefix(m.Target, "http://"), "https://")

	if len(body) > 0 {
		req.Body = io.NopCloser(bytes.NewReader(body))
		req.ContentLength = int64(len(body))
	}

	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	go func() {
		_, err := client.Do(req)
		if err != nil {
			fmt.Printf("mirror error: %v\n", err)
		}
	}()

	return nil
}

type MirrorHandler struct {
	mirrors map[string]*MirroredRequest
}

func NewHandler() *MirrorHandler {
	return &MirrorHandler{
		mirrors: make(map[string]*MirroredRequest),
	}
}

func (h *MirrorHandler) AddRoute(name string, cfg *types.MirrorConfig) {
	if cfg == nil || !cfg.Enabled {
		return
	}
	h.mirrors[name] = New(cfg)
}

func (h *MirrorHandler) Mirror(routeName string, w http.ResponseWriter, r *http.Request) {
	mirror, ok := h.mirrors[routeName]
	if !ok {
		return
	}

	if !mirror.ShouldMirror(r) {
		return
	}

	if err := mirror.MirrorRequest(r); err != nil {
		fmt.Printf("mirror request error: %v\n", err)
	}
}

func (h *MirrorHandler) GetMirrors() map[string]*MirroredRequest {
	return h.mirrors
}