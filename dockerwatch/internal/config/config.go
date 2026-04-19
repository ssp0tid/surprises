package config

import (
	"errors"
	"fmt"
	"io/fs"
	"time"

	"github.com/spf13/viper"
)

type Config struct {
	App       AppConfig
	Docker    DockerConfig
	UI        UIConfig
	Columns   ColumnsConfig
	Shortcuts ShortcutsConfig
}

type AppConfig struct {
	Name             string
	RefreshInterval  time.Duration
	LogBufferSize    int
	MaxHistoryPoints int
}

type DockerConfig struct {
	Host       string
	APIVersion string
	Timeout    time.Duration
	MaxRetries int
}

type UIConfig struct {
	Theme       string
	ColorScheme string
	ShowStopped bool
	ShowSystem  bool
	CompactMode bool
}

type ColumnsConfig struct {
	Visible []string
	Order   []string
}

type ShortcutsConfig struct {
	Quit    string
	Help    string
	Refresh string
	Start   string
	Stop    string
	Restart string
	Logs    string
	Details string
}

func Load(path string) (*Config, error) {
	v := viper.New()
	v.SetConfigFile(path)
	v.SetConfigType("yaml")

	setDefaults(v)

	if err := v.ReadInConfig(); err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return defaultConfig(), nil
		}
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// Post-process duration fields
	cfg.App.RefreshInterval = v.GetDuration("app.refresh_interval")
	cfg.Docker.Timeout = v.GetDuration("docker.timeout")

	return &cfg, nil
}

func (c *Config) Validate() error {
	if c.App.RefreshInterval <= 0 {
		return errors.New("app.refresh_interval must be positive")
	}
	if c.Docker.Timeout <= 0 {
		return errors.New("docker.timeout must be positive")
	}
	if c.Docker.MaxRetries < 0 {
		return errors.New("docker.max_retries must be non-negative")
	}
	if c.App.LogBufferSize <= 0 {
		return errors.New("app.log_buffer_size must be positive")
	}
	if c.App.MaxHistoryPoints <= 0 {
		return errors.New("app.max_history_points must be positive")
	}
	validThemes := map[string]bool{"dark": true, "light": true, "auto": true}
	if !validThemes[c.UI.Theme] {
		return fmt.Errorf("ui.theme must be one of: dark, light, auto")
	}
	return nil
}