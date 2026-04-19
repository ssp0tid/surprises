package app

import (
	"time"

	"github.com/apitest/apitest/internal/http"
)

type HTTPClient struct {
	client *http.Client
}

func NewHTTPClient() *HTTPClient {
	return &HTTPClient{
		client: http.NewClient(30 * time.Second),
	}
}

func (c *HTTPClient) DoRequest(method, urlStr string, headers map[string]string, body string) (*http.Response, error) {
	return c.client.DoRequest(method, urlStr, headers, body)
}