package client

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type HTTPClient struct {
	client *http.Client
}

func NewHTTPClient(timeout time.Duration) *HTTPClient {
	return &HTTPClient{
		client: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost:  100,
				IdleConnTimeout:     90 * time.Second,
				TLSHandshakeTimeout: 10 * time.Second,
			},
		},
	}
}

func (c *HTTPClient) Do(method, url string, headers map[string]string, body []byte) (*Result, error) {
	start := time.Now()

	req, err := http.NewRequest(method, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := c.client.Do(req)
	elapsed := time.Since(start)

	if err != nil {
		return &Result{
			Elapsed:      elapsed,
			HasError:     true,
			ErrorMessage: err.Error(),
		}, nil
	}

	defer resp.Body.Close()
	respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))

	return &Result{
		StatusCode:   resp.StatusCode,
		Elapsed:      elapsed,
		HasError:     false,
		ResponseBody: string(respBody),
	}, nil
}

func (c *HTTPClient) DoWithDeadline(method, url string, headers map[string]string, body []byte, deadline time.Time) (*Result, error) {
	start := time.Now()

	req, err := http.NewRequest(method, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	for k, v := range headers {
		req.Header.Set(k, v)
	}

	req.Header.Set("User-Agent", "httpbench/1.0")

	resp, err := c.client.Do(req)
	elapsed := time.Since(start)

	if err != nil {
		return &Result{
			Elapsed:      elapsed,
			HasError:     true,
			ErrorMessage: err.Error(),
		}, nil
	}

	defer resp.Body.Close()
	respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))

	return &Result{
		StatusCode:   resp.StatusCode,
		Elapsed:      elapsed,
		HasError:     false,
		ResponseBody: string(respBody),
	}, nil
}

type Result struct {
	StatusCode   int
	Elapsed      time.Duration
	HasError     bool
	ErrorMessage string
	ResponseBody string
}

func ReadBodyFile(path string) ([]byte, error) {
	if path == "" {
		return nil, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read body file: %w", err)
	}
	return data, nil
}