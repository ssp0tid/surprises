package cmd

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"httpbench/config"
)

func ParseFlags() (*config.Config, error) {
	cfg := &config.Config{
		Method:      "GET",
		Concurrency: 10,
		Duration:   10 * time.Second,
		Requests:   0,
		Rate:       0,
		Timeout:    30 * time.Second,
		Headers:    make(map[string]string),
		Format:     "text",
		Quiet:      false,
	}

	method := flag.String("X", "GET", "HTTP method")
	url := flag.String("url", "", "Target URL to test (required)")
	concurrency := flag.Int("c", 10, "Number of concurrent workers")
	duration := flag.String("d", "10s", "Test duration (e.g., 10s, 1m)")
	requests := flag.Int("n", 0, "Total requests (0 = duration mode)")
	rate := flag.Int("r", 0, "Max RPS per worker (0 = unlimited)")
	timeout := flag.String("t", "30s", "Request timeout")
	headers := flag.String("H", "", "Add header (repeatable)")
	body := flag.String("body", "", "Request body")
	bodyFile := flag.String("f", "", "File containing request body")
	format := flag.String("format", "text", "Output format (text, json)")
	quiet := flag.Bool("q", false, "Minimal output")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: httpbench [options] <url>\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
	}

	flag.Parse()

	// URL is the first positional argument
	args := flag.Args()
	if len(args) > 0 && *url == "" {
		*url = args[0]
	}

	if *url == "" {
		return nil, fmt.Errorf("URL is required")
	}

	// Parse duration
	d, err := time.ParseDuration(*duration)
	if err != nil {
		return nil, fmt.Errorf("invalid duration: %v", err)
	}

	// Parse timeout
	t, err := time.ParseDuration(*timeout)
	if err != nil {
		return nil, fmt.Errorf("invalid timeout: %v", err)
	}

	// Parse headers
	headersMap := make(map[string]string)
	if *headers != "" {
		for _, h := range strings.Split(*headers, ",") {
			h = strings.TrimSpace(h)
			if h == "" {
				continue
			}
			parts := strings.SplitN(h, ":", 2)
			if len(parts) != 2 {
				return nil, fmt.Errorf("invalid header format: %s (expected Key:Value)", h)
			}
			headersMap[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
		}
	}

	cfg.URL = *url
	cfg.Method = strings.ToUpper(*method)
	cfg.Concurrency = *concurrency
	cfg.Duration = d
	cfg.Requests = *requests
	cfg.Rate = *rate
	cfg.Timeout = t
	cfg.Headers = headersMap
	cfg.Body = *body
	cfg.BodyFile = *bodyFile
	cfg.Format = *format
	cfg.Quiet = *quiet

	return cfg, nil
}