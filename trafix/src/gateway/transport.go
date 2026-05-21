package gateway

import (
	"net/http"
	"sync"
	"time"

	"trafix/utils"
)

type Transport struct {
	RoundTripper http.RoundTripper

	mu           sync.Mutex
	numRequests  int64
	numResponses int64
	lastRequest  time.Time
	lastResponse time.Time
}

func (t *Transport) RoundTrip(req *http.Request) (*http.Response, error) {
	t.mu.Lock()
	t.numRequests++
	t.lastRequest = time.Now()
	t.mu.Unlock()

	if t.RoundTripper == nil {
		t.RoundTripper = http.DefaultTransport
	}

	resp, err := t.RoundTripper.RoundTrip(req)

	t.mu.Lock()
	t.numResponses++
	t.lastResponse = time.Now()
	t.mu.Unlock()

	if err != nil {
		utils.GetLogger().
			Error().
			Err(err).
			Str("method", req.Method).
			Str("url", req.URL.String()).
			Msg("transport round trip failed")
		return nil, err
	}

	return resp, nil
}

func (t *Transport) NumRequests() int64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.numRequests
}

func (t *Transport) NumResponses() int64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.numResponses
}

func (t *Transport) LastRequestTime() time.Time {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.lastRequest
}

func (t *Transport) LastResponseTime() time.Time {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.lastResponse
}

func (t *Transport) Reset() {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.numRequests = 0
	t.numResponses = 0
}