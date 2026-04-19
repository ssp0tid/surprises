package http

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type Client struct {
	httpClient *http.Client
	timeout    time.Duration
}

type Response struct {
	StatusCode  int
	Headers     http.Header
	Body        string
	BodyBytes   []byte
	Duration    time.Duration
	Error       error
}

func NewClient(timeout time.Duration) *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: timeout,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				return http.ErrUseLastResponse
			},
		},
		timeout: timeout,
	}
}

func (c *Client) DoRequest(method, urlStr string, headers map[string]string, body string) (*Response, error) {
	startTime := time.Now()

	req, err := http.NewRequest(method, urlStr, strings.NewReader(body))
	if err != nil {
		return &Response{Error: err}, err
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	if body != "" && req.Header.Get("Content-Type") == "" {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return &Response{Error: err}, err
	}
	defer resp.Body.Close()

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return &Response{Error: err}, err
	}

	duration := time.Since(startTime)

	responseBody := string(bodyBytes)
	if strings.Contains(resp.Header.Get("Content-Type"), "application/json") {
		responseBody = FormatJSON(bodyBytes)
	}

	return &Response{
		StatusCode:  resp.StatusCode,
		Headers:     resp.Header,
		Body:        responseBody,
		BodyBytes:   bodyBytes,
		Duration:    duration,
		Error:       nil,
	}, nil
}

func FormatJSON(data []byte) string {
	var prettyJSON bytes.Buffer
	err := json.Indent(&prettyJSON, data, "", "  ")
	if err != nil {
		return string(data)
	}
	return prettyJSON.String()
}

func ValidateURL(urlStr string) error {
	_, err := url.ParseRequestURI(urlStr)
	return err
}

func GetStatusText(code int) string {
	texts := map[int]string{
		200: "OK",
		201: "Created",
		204: "No Content",
		301: "Moved Permanently",
		302: "Found",
		304: "Not Modified",
		400: "Bad Request",
		401: "Unauthorized",
		403: "Forbidden",
		404: "Not Found",
		405: "Method Not Allowed",
		500: "Internal Server Error",
		502: "Bad Gateway",
		503: "Service Unavailable",
	}
	if text, ok := texts[code]; ok {
		return text
	}
	return fmt.Sprintf("Status %d", code)
}