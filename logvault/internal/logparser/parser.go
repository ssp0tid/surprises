package logparser

import (
	"bytes"
	"encoding/json"
	"errors"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/logvault/logvault/internal/model"
)

const maxMessageSize = 1024 * 1024

var (
	ErrEmptyMessage = errors.New("message cannot be empty")
	ErrMessageTruncated = errors.New("message exceeded 1MB limit and was truncated")
)

type Parser struct {
	defaultService string
	defaultHost   string
}

func NewParser() *Parser {
	return &Parser{
		defaultService: "default",
		defaultHost:   "localhost",
	}
}

func NewParserWithDefaults(service, host string) *Parser {
	if service == "" {
		service = "default"
	}
	if host == "" {
		host = "localhost"
	}
	return &Parser{
		defaultService: service,
		defaultHost:   host,
	}
}

func (p *Parser) Parse(logLine string) (*model.LogEntry, error) {
	sanitized := p.sanitizeInput(logLine)
	if sanitized == "" {
		return nil, ErrEmptyMessage
	}

	if strings.HasPrefix(strings.TrimSpace(sanitized), "{") {
		return p.parseJSON(sanitized)
	}

	return p.parseStructured(sanitized)
}

func (p *Parser) parseJSON(logLine string) (*model.LogEntry, error) {
	var req model.LogEntryRequest
	if err := json.Unmarshal([]byte(logLine), &req); err != nil {
		return p.parseStructured(logLine)
	}

	return p.requestToEntry(&req)
}

func (p *Parser) requestToEntry(req *model.LogEntryRequest) (*model.LogEntry, error) {
	entry := &model.LogEntry{
		Timestamp: req.Timestamp,
		Level:     req.Level,
		Service:  req.Service,
		Host:     req.Host,
		Message:  req.Message,
		Metadata: req.Metadata,
		Raw:      req.Raw,
	}

	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now().UTC()
	}

	if entry.Service == "" {
		entry.Service = p.defaultService
	}

	if entry.Host == "" {
		entry.Host = p.defaultHost
	}

	validLevel, err := ParseLevel(string(entry.Level))
	if err != nil {
		entry.Level = validLevel
	}

	if entry.Message == "" && entry.Raw == "" {
		return nil, ErrEmptyMessage
	}

	if entry.Message == "" {
		entry.Message = entry.Raw
	}

	entry.Message = p.truncateMessage(entry.Message)

	return entry, nil
}

func (p *Parser) parseStructured(logLine string) (*model.LogEntry, error) {
	entry := &model.LogEntry{
		Timestamp: time.Now().UTC(),
		Level:     model.LogLevelInfo,
		Service:  p.defaultService,
		Host:     p.defaultHost,
		Message:  logLine,
	}

	trimmed := strings.TrimSpace(logLine)

	if len(trimmed) > 2 && trimmed[0] == '[' {
		if idx := strings.Index(trimmed, "]"); idx > 1 {
			levelStr := trimmed[1:idx]
			if level, err := ParseLevel(levelStr); err == nil {
				entry.Level = level
				entry.Message = strings.TrimSpace(trimmed[idx+1:])
			}
		}
	}

	if idx := strings.Index(trimmed, ":"); idx > 0 && idx < 20 {
		potentialLevel := strings.TrimSpace(trimmed[:idx])
		if len(potentialLevel) > 0 && len(potentialLevel) < 15 {
			if level, err := ParseLevel(potentialLevel); err == nil {
				entry.Level = level
				entry.Message = strings.TrimSpace(trimmed[idx+1:])
			}
		}
	}

	entry.Message = p.extractTimestamp(trimmed, entry)

	entry.Metadata = p.extractMetadata(entry.Message)

	entry.Message = p.truncateMessage(entry.Message)

	if entry.Message == "" {
		entry.Message = logLine
	}

	return entry, nil
}

func (p *Parser) extractTimestamp(line string, entry *model.LogEntry) string {
	if len(line) >= 20 {
		if t, err := time.Parse(time.RFC3339, line[:20]); err == nil {
			rest := strings.TrimSpace(line[20:])
			if rest != "" {
				entry.Timestamp = t
				return rest
			}
		}
	}

	formats := []string{
		"2006-01-02T15:04:05Z07:00",
		"2006-01-02 15:04:05",
		"2006/01/02 15:04:05",
	}

	for _, format := range formats {
		parts := strings.SplitN(line, " ", 2)
		if len(parts) == 2 {
			if t, err := time.Parse(format, parts[0]); err == nil {
				entry.Timestamp = t
				return strings.TrimSpace(parts[1])
			}
		}
	}

	return line
}

func (p *Parser) extractMetadata(message string) json.RawMessage {
	var meta map[string]interface{}

	segments := strings.FieldsFunc(message, func(r rune) bool {
		return r == ' ' || r == '\t'
	})

	for _, seg := range segments {
		if idx := strings.Index(seg, "="); idx > 0 && idx < len(seg)-1 {
			key := strings.TrimSpace(seg[:idx])
			value := strings.TrimSpace(seg[idx+1:])
			value = strings.Trim(value, "\"")

			if key != "" && isValidKey(key) {
				if meta == nil {
					meta = make(map[string]interface{})
				}
				meta[key] = value
			}
		}
	}

	if len(meta) == 0 {
		return nil
	}

	data, err := json.Marshal(meta)
	if err != nil {
		return nil
	}

	return json.RawMessage(data)
}

func isValidKey(key string) bool {
	if len(key) == 0 || len(key) > 50 {
		return false
	}
	for _, r := range key {
		if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '-') {
			return false
		}
	}
	return true
}

func (p *Parser) sanitizeInput(input string) string {
	if !utf8.ValidString(input) {
		input = strings.ToValidUTF8(input, "")
	}

	input = strings.ToValidUTF8(input, "")

	var buf bytes.Buffer
	for _, r := range input {
		if r == 0 {
			continue
		}
		buf.WriteRune(r)
	}

	result := buf.String()
	lines := strings.Split(result, "\n")
	if len(lines) > 1 {
		result = strings.Join(lines, " ")
		result = strings.TrimSpace(result)
	}

	return result
}

func (p *Parser) truncateMessage(message string) string {
	if len(message) > maxMessageSize {
		truncated := message[:maxMessageSize]
		lastSpace := strings.LastIndex(truncated, " ")
		if lastSpace > maxMessageSize-100 {
			truncated = truncated[:lastSpace]
		}
		return truncated
	}

	return message
}

func (p *Parser) ParseBatch(lines []string) ([]*model.LogEntry, error) {
	if len(lines) == 0 {
		return []*model.LogEntry{}, nil
	}

	entries := make([]*model.LogEntry, 0, len(lines))

	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}

		entry, err := p.Parse(line)
		if err != nil {
			if errors.Is(err, ErrEmptyMessage) {
				continue
			}
			continue
		}

		entries = append(entries, entry)
	}

	return entries, nil
}

func Parse(logLine string) (*model.LogEntry, error) {
	return NewParser().Parse(logLine)
}

func ParseBatch(lines []string) ([]*model.LogEntry, error) {
	return NewParser().ParseBatch(lines)
}