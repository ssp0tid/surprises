package app

import "time"

type Request struct {
	ID        string            `json:"id"`
	Name      string            `json:"name"`
	Method    string            `json:"method"`
	URL       string            `json:"url"`
	Headers   map[string]string `json:"headers"`
	Body      string            `json:"body,omitempty"`
	BodyType  string            `json:"body_type"`
	CreatedAt time.Time         `json:"created_at"`
	UpdatedAt time.Time         `json:"updated_at"`
}

type RequestHistory struct {
	ID          string    `json:"id"`
	Request     Request   `json:"request"`
	StatusCode  int       `json:"status_code"`
	Duration    int64     `json:"duration_ms"`
	ResponseLen int       `json:"response_len"`
	Timestamp   time.Time `json:"timestamp"`
}

type Collection struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	Description string     `json:"description"`
	Requests    []Request  `json:"requests"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

func NewRequest() Request {
	return Request{
		ID:        "",
		Name:      "",
		Method:    "GET",
		URL:       "",
		Headers:   make(map[string]string),
		Body:      "",
		BodyType:  "json",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}