package delay

import (
	"math/rand"
	"time"

	"github.com/surprises/mesh-proxy/pkg/types"
)

type Injector struct {
	config *types.DelayConfig
	rand   *rand.Rand
}

func New(cfg *types.DelayConfig) *Injector {
	return &Injector{
		config: cfg,
		rand:   rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (i *Injector) Delay() time.Duration {
	if i.config == nil {
		return 0
	}

	var delay time.Duration

	if i.config.Fixed > 0 {
		delay = i.config.Fixed
	} else if i.config.Min > 0 && i.config.Max > 0 {
		rangeNs := i.config.Max.Nanoseconds() - i.config.Min.Nanoseconds()
		delay = i.config.Min + time.Duration(i.rand.Int63n(rangeNs))
	}

	if i.config.Jitter > 0 {
		jitterNs := i.config.Jitter.Nanoseconds()
		jitter := time.Duration(i.rand.Int63n(jitterNs*2)) - i.config.Jitter
		delay += jitter
	}

	return delay
}

func (i *Injector) Wait() {
	delay := i.Delay()
	if delay > 0 {
		time.Sleep(delay)
	}
}