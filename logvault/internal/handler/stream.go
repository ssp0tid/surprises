package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/logvault/logvault/internal/model"
)

type StreamHandler struct {
	broadcaster *Broadcaster
}

type Broadcaster struct {
	mu      sync.RWMutex
	clients map[chan []byte]Filter
}

type Filter struct {
	Level   string
	Service string
	Host   string
}

func NewStreamHandler() *StreamHandler {
	return &StreamHandler{
		broadcaster: &Broadcaster{
			clients: make(map[chan []byte]Filter),
		},
	}
}

func (h *StreamHandler) Register(r chi.Router) {
	r.Get("/api/v1/stream", h.Stream)
}

func (h *StreamHandler) Stream(w http.ResponseWriter, r *http.Request) {
	filter := Filter{
		Level:   r.URL.Query().Get("level"),
		Service: r.URL.Query().Get("service"),
		Host:   r.URL.Query().Get("host"),
	}

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	ch := make(chan []byte, 100)
	h.broadcaster.register(ch, filter)

	lastID := r.Header.Get("Last-Event-ID")
	if lastID != "" {
		_ = lastID
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "none")

	flusher, ok := w.(http.Flusher)
	if !ok {
		return
	}

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			h.broadcaster.unregister(ch)
			return
		case data := <-ch:
			id := time.Now().UnixNano()
			fmt.Fprintf(w, "id: %d\n", id)
			fmt.Fprintf(w, "data: %s\n\n", data)
			flusher.Flush()
		case <-ticker.C:
			fmt.Fprintf(w, ": heartbeat\n\n")
			flusher.Flush()
		}
	}
}

func (b *Broadcaster) register(ch chan []byte, filter Filter) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.clients[ch] = filter
}

func (b *Broadcaster) unregister(ch chan []byte) {
	b.mu.Lock()
	defer b.mu.Unlock()
	delete(b.clients, ch)
}

func (b *Broadcaster) Send(entry *model.LogEntry) {
	data, err := json.Marshal(entry)
	if err != nil {
		return
	}

	b.mu.RLock()
	defer b.mu.RUnlock()

	for ch, filter := range b.clients {
		if filter.matches(entry) {
			select {
			case ch <- data:
			default:
			}
		}
	}
}

func (f *Filter) matches(entry *model.LogEntry) bool {
	if f.Level != "" && string(entry.Level) != f.Level {
		return false
	}
	if f.Service != "" && entry.Service != f.Service {
		return false
	}
	if f.Host != "" && entry.Host != f.Host {
		return false
	}
	return true
}