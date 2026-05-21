package router

import (
	"net/http"
	"strings"

	"github.com/surprises/mesh-proxy/pkg/types"
)

// Rule represents a single route rule.
type Rule struct {
	Name      string
	Priority int
	Enabled  bool
	Criteria types.RouteMatch
	Backend  *types.BackendConfig
}

// matchPath handles wildcard matching for routes.
func matchPath(pattern, path string) bool {
	if strings.HasSuffix(pattern, "/*") {
		prefix := strings.TrimSuffix(pattern, "/*")
		return strings.HasPrefix(path, prefix)
	}
	// Handle exact match or empty pattern (matches all)
	if pattern == "" || pattern == "*" {
		return true
	}
	return pattern == path
}

// Match determines if a request matches a route rule.
func (r *Rule) Matches(req *http.Request) bool {
	if r.Criteria.Path != "" {
		if !matchPath(r.Criteria.Path, req.URL.Path) {
			return false
		}
	}
	if r.Criteria.PathPrefix != "" {
		if !strings.HasPrefix(req.URL.Path, r.Criteria.PathPrefix) {
			return false
		}
	}

	if len(r.Criteria.Methods) > 0 {
		found := false
		for _, m := range r.Criteria.Methods {
			if req.Method == m {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	for k, v := range r.Criteria.Headers {
		if req.Header.Get(k) != v {
			return false
		}
	}

	return true
}