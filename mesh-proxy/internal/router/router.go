package router

import (
	"net/http"
	"sort"
	"sync"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type Router struct {
	rules   []*Rule
	mu      sync.RWMutex
	matcher *Matcher
}

type Matcher struct{}

func NewRouter() *Router {
	return &Router{
		rules:   make([]*Rule, 0),
		matcher: &Matcher{},
	}
}

func (r *Router) AddRule(rule *Rule) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.rules = append(r.rules, rule)
	sort.Slice(r.rules, func(i, j int) bool {
		return r.rules[i].Priority > r.rules[j].Priority
	})

	return nil
}

func (r *Router) AddFromConfig(cfg *types.Route) error {
	rule := &Rule{
		Name:      cfg.Name,
		Priority:  cfg.Priority,
		Enabled:   cfg.Enabled,
		Criteria:  cfg.Criteria,
		Backend:   cfg.Backend,
	}
	return r.AddRule(rule)
}

func (r *Router) Match(req *http.Request) *Rule {
	r.mu.RLock()
	defer r.mu.RUnlock()

	for _, rule := range r.rules {
		if !rule.Enabled {
			continue
		}
		if rule.Matches(req) {
			return rule
		}
	}
	return nil
}

func (r *Router) GetRules() []*Rule {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]*Rule, len(r.rules))
	copy(result, r.rules)
	return result
}

func (r *Router) Enable(name string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	for _, rule := range r.rules {
		if rule.Name == name {
			rule.Enabled = true
			return nil
		}
	}
	return nil
}

func (r *Router) Disable(name string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	for _, rule := range r.rules {
		if rule.Name == name {
			rule.Enabled = false
			return nil
		}
	}
	return nil
}