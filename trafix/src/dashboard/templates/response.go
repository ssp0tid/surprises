package templates

import (
	"encoding/json"
	"fmt"
	"html/template"
	"time"

	"trafix/storage"
)

type ResponseTemplate struct{}

func NewResponseTemplate() *ResponseTemplate {
	return &ResponseTemplate{}
}

func (t *ResponseTemplate) RenderRequestList(data *storage.RequestListResponse) string {
	if len(data.Data) == 0 {
		return `<tr><td colspan="6" class="loading">No requests found</td></tr>`
	}

	result := ""
	for _, req := range data.Data {
		statusClass := getStatusClass(req.StatusCode)
		result += fmt.Sprintf(`
		<tr>
			<td>%s</td>
			<td>%s</td>
			<td>%s</td>
			<td>%s</td>
			<td class="%s">%d</td>
			<td>%dms</td>
		</tr>`,
			formatTime(req.CreatedAt),
			req.Method,
			escapeHTML(req.Path),
			escapeHTML(req.TargetURL),
			statusClass,
			req.StatusCode,
			req.DurationMs,
		)
	}
	return result
}

func (t *ResponseTemplate) RenderRequestDetail(req *storage.RequestRecord) string {
	return fmt.Sprintf(`
	<div class="detail-section">
		<h3>Request</h3>
		<table class="detail-table">
			<tr><td>ID</td><td>%s</td></tr>
			<tr><td>Method</td><td>%s</td></tr>
			<tr><td>Path</td><td>%s</td></tr>
			<tr><td>Target URL</td><td>%s</td></tr>
			<tr><td>Client IP</td><td>%s</td></tr>
			<tr><td>User Agent</td><td>%s</td></tr>
			<tr><td>Timestamp</td><td>%s</td></tr>
		</table>
	</div>
	<div class="detail-section">
		<h3>Response</h3>
		<table class="detail-table">
			<tr><td>Status Code</td><td class="%s">%d</td></tr>
			<tr><td>Duration</td><td>%dms</td></tr>
			<tr><td>Response Size</td><td>%d bytes</td></tr>
		</table>
	</div>`,
		escapeHTML(req.RequestID),
		escapeHTML(req.Method),
		escapeHTML(req.Path),
		escapeHTML(req.TargetURL),
		escapeHTML(req.ClientIP),
		escapeHTML(req.UserAgent),
		formatTime(req.CreatedAt),
		getStatusClass(req.StatusCode),
		req.StatusCode,
		req.DurationMs,
		req.ResponseBodySize,
	)
}

func (t *ResponseTemplate) RenderAnalytics(analytics map[string]interface{}) string {
	byPath := analytics["by_path"]
	byStatus := analytics["by_status"]
	responseTime := analytics["response_time"]
	topIPs := analytics["top_ips"]

	pathsHTML := renderPaths(byPath)
	statusHTML := renderStatus(byStatus)
	percentilesHTML := renderPercentiles(responseTime)
	ipsHTML := renderTopIPs(topIPs)

	return pathsHTML + statusHTML + percentilesHTML + ipsHTML
}

func getStatusClass(statusCode int) string {
	switch {
	case statusCode >= 200 && statusCode < 300:
		return "status-2xx"
	case statusCode >= 300 && statusCode < 400:
		return "status-3xx"
	case statusCode >= 400 && statusCode < 500:
		return "status-4xx"
	case statusCode >= 500:
		return "status-5xx"
	default:
		return ""
	}
}

func formatTime(timestamp string) string {
	if timestamp == "" {
		return "-"
	}
	t, err := time.Parse(time.RFC3339, timestamp)
	if err != nil {
		return timestamp
	}
	return t.Format("2006-01-02 15:04:05")
}

func escapeHTML(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

func renderPaths(data interface{}) string {
	if data == nil {
		return ""
	}
	return ""
}

func renderStatus(data interface{}) string {
	if data == nil {
		return ""
	}
	return ""
}

func renderPercentiles(data interface{}) string {
	if data == nil {
		return ""
	}
	return ""
}

func renderTopIPs(data interface{}) string {
	if data == nil {
		return ""
	}
	return ""
}