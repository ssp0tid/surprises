package gateway

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"github.com/rs/zerolog"

	"trafix/config"
	"trafix/utils"
)

type contextKey string

const (
	RequestIDKey    contextKey = "request_id"
	TargetURLKey    contextKey = "target_url"
	RequestBodyKey  contextKey = "request_body"
	ResponseBodyKey contextKey = "response_body"
	ResponseStatusKey contextKey = "response_status"
)

type Proxy struct {
	config  *config.Config
	logger  *zerolog.Logger
	client  *http.Client
	routes  map[string]*RouteConfig
}

type RouteConfig struct {
	Prefix      string
	TargetBase string
	Strip      bool
}

func NewProxy(cfg *config.Config) *Proxy {
	logger := utils.GetLogger()

	client := &http.Client{
		Timeout: cfg.Proxy.Timeout,
		Transport: &Transport{
			RoundTripper: http.DefaultTransport,
		},
	}

	routes := make(map[string]*RouteConfig)
	routes["/api/v1"] = &RouteConfig{
		Prefix:      "/api/v1",
		TargetBase: cfg.Proxy.TargetBaseURL,
		Strip:      true,
	}

	p := &Proxy{
		config:  cfg,
		logger:  logger,
		client:  client,
		routes:  routes,
	}

	return p
}

func (p *Proxy) getRouteConfig(path string) *RouteConfig {
	for prefix, route := range p.routes {
		if strings.HasPrefix(path, prefix) {
			return route
		}
	}

	return &RouteConfig{
		Prefix:      "",
		TargetBase: p.config.Proxy.TargetBaseURL,
		Strip:      false,
	}
}

func (p *Proxy) resolveTargetURL(req *http.Request) *url.URL {
	path := req.URL.Path

	route := p.getRouteConfig(path)

	target := route.TargetBase
	if route.Strip {
		targetPath := strings.TrimPrefix(path, route.Prefix)
		if targetPath == "" {
			targetPath = "/"
		}
		target = target + targetPath
	} else {
		target = target + path
	}

	query := req.URL.RawQuery
	if query != "" {
		target = target + "?" + query
	}

	targetURL, err := url.Parse(target)
	if err != nil {
		p.logger.Error().Err(err).Str("target", target).Msg("failed to parse target URL")
		return nil
	}

	return targetURL
}

func (p *Proxy) copyHeaders(dst, src *http.Header) {
	for key, values := range *src {
		for _, value := range values {
			if key == "Host" {
				continue
			}
			dst.Add(key, value)
		}
	}
}

func (p *Proxy) addProxyHeaders(req *http.Request, target *url.URL) {
	req.Header.Set("X-Forwarded-For", req.RemoteAddr)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", req.Host)
	req.Header.Set("X-Target-Host", target.Host)
	req.Header.Set("X-Real-IP", req.RemoteAddr)
}

func (p *Proxy) buildProxyRequest(req *http.Request, target *url.URL) *http.Request {
	proxyReq := &http.Request{
		Method:        req.Method,
		URL:          target,
		Proto:        req.Proto,
		ProtoMajor:   req.ProtoMajor,
		ProtoMinor:   req.ProtoMinor,
		Header:      make(http.Header),
		Body:         req.Body,
		Host:        target.Host,
		RequestURI:  target.RequestURI(),
	}

	p.copyHeaders(&proxyReq.Header, &req.Header)
	p.addProxyHeaders(proxyReq, target)

	return proxyReq
}

func (p *Proxy) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	ctx := req.Context()

	requestID := req.Header.Get("X-Request-ID")
	if requestID == "" {
		requestID = uuid.New().String()
	}

	ctx = context.WithValue(ctx, RequestIDKey, requestID)
	req = req.WithContext(ctx)

	logger := p.logger.With().
		Str("request_id", requestID).
		Str("method", req.Method).
		Str("path", req.URL.Path).
		Str("remote_addr", req.RemoteAddr).
		Logger()

	bodyBytes, err := io.ReadAll(req.Body)
	if err != nil {
		logger.Error().Err(err).Msg("failed to read request body")
		p.writeError(w, utils.ErrBadRequestWithMsg("failed to read request body"))
		return
	}

	ctx = context.WithValue(ctx, RequestBodyKey, bodyBytes)
	req = req.WithContext(ctx)

	if req.Body != nil {
		req.Body = io.NopCloser(bytes.NewReader(bodyBytes))
	}

	targetURL := p.resolveTargetURL(req)
	if targetURL == nil {
		p.writeError(w, utils.ErrBadGatewayWithMsg("failed to resolve target URL"))
		return
	}

	ctx = context.WithValue(ctx, TargetURLKey, targetURL.String())
	req = req.WithContext(ctx)

	proxyReq := p.buildProxyRequest(req, targetURL)

	logger.Info().
		Str("target_url", targetURL.String()).
		Msg("forwarding request")

	resp, err := p.client.Do(proxyReq)
	if err != nil {
		logger.Error().Err(err).Str("target_url", targetURL.String()).Msg("failed to forward request")

		if strings.Contains(err.Error(), "timeout") || strings.Contains(err.Error(), "context deadline exceeded") {
			p.writeError(w, utils.ErrTimeoutWithMsg("timeout while forwarding request"))
		} else {
			p.writeError(w, utils.ErrBadGatewayWithMsg("failed to forward request: "+err.Error()))
		}
		return
	}

	defer resp.Body.Close()

	ctx = context.WithValue(ctx, ResponseStatusKey, resp.StatusCode)

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		logger.Error().Err(err).Msg("failed to read response body")
	}

	ctx = context.WithValue(ctx, ResponseBodyKey, respBody)
	req = req.WithContext(ctx)

	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	w.Header().Set("X-Request-ID", requestID)

	if p.config.Middleware.Logging.Enabled {
		maxBodySize := p.config.Middleware.Logging.MaxBodySize
		if len(respBody) > maxBodySize {
			logger.Debug().
				Int("status_code", resp.StatusCode).
				Int("body_size", len(respBody)).
				Msg("response")
		} else {
			logger.Debug().
				Int("status_code", resp.StatusCode).
				Int("body_size", len(respBody)).
				Str("body", string(respBody)).
				Msg("response")
		}
	}

	w.WriteHeader(resp.StatusCode)
	w.Write(respBody)
}

func (p *Proxy) writeError(w http.ResponseWriter, err utils.TrafixError) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(err.StatusCode())

	errorJSON := fmt.Sprintf(`{"error":"%s","code":"%s"}`, err.Error(), err.Code())
	w.Write([]byte(errorJSON))
}

func (p *Proxy) WithTimeout(timeout time.Duration) *Proxy {
	p.client.Timeout = timeout
	return p
}

func (p *Proxy) WithTransport(transport http.RoundTripper) *Proxy {
	p.client.Transport = &Transport{
		RoundTripper: transport,
	}
	return p
}

func (p *Proxy) AddRoute(prefix string, targetBase string, strip bool) {
	p.routes[prefix] = &RouteConfig{
		Prefix:      prefix,
		TargetBase: targetBase,
		Strip:      strip,
	}
}

func (p *Proxy) RemoveRoute(prefix string) {
	delete(p.routes, prefix)
}

func (p *Proxy) GetRoutes() map[string]*RouteConfig {
	return p.routes
}

func (p *Proxy) GetConfig() *config.Config {
	return p.config
}

func (p *Proxy) chiRouter() chi.Router {
	return chi.NewRouter()
}