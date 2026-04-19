package config

import (
	"time"

	"github.com/spf13/viper"
)

func setDefaults(v *viper.Viper) {
	v.SetDefault("app.name", "DockerWatch")
	v.SetDefault("app.refresh_interval", "2s")
	v.SetDefault("app.log_buffer_size", 1000)
	v.SetDefault("app.max_history_points", 60)

	v.SetDefault("docker.host", "")
	v.SetDefault("docker.api_version", "")
	v.SetDefault("docker.timeout", "10s")
	v.SetDefault("docker.max_retries", 3)

	v.SetDefault("ui.theme", "dark")
	v.SetDefault("ui.color_scheme", "default")
	v.SetDefault("ui.show_stopped", true)
	v.SetDefault("ui.show_system", false)
	v.SetDefault("ui.compact_mode", false)

	v.SetDefault("columns.visible", []string{"name", "status", "cpu", "memory", "network", "uptime"})
	v.SetDefault("columns.order", []string{"name", "status", "cpu", "memory", "network", "uptime"})

	v.SetDefault("shortcuts.quit", "q")
	v.SetDefault("shortcuts.help", "?")
	v.SetDefault("shortcuts.refresh", "r")
	v.SetDefault("shortcuts.start", "s")
	v.SetDefault("shortcuts.stop", "x")
	v.SetDefault("shortcuts.restart", "R")
	v.SetDefault("shortcuts.logs", "l")
	v.SetDefault("shortcuts.details", "Enter")
}

func defaultConfig() *Config {
	v := viper.New()
	setDefaults(v)

	cfg := &Config{
		App: AppConfig{
			Name:             "DockerWatch",
			RefreshInterval:  2 * time.Second,
			LogBufferSize:    1000,
			MaxHistoryPoints: 60,
		},
		Docker: DockerConfig{
			Host:       "",
			APIVersion: "",
			Timeout:    10 * time.Second,
			MaxRetries: 3,
		},
		UI: UIConfig{
			Theme:       "dark",
			ColorScheme: "default",
			ShowStopped: true,
			ShowSystem:  false,
			CompactMode: false,
		},
		Columns: ColumnsConfig{
			Visible: []string{"name", "status", "cpu", "memory", "network", "uptime"},
			Order:   []string{"name", "status", "cpu", "memory", "network", "uptime"},
		},
		Shortcuts: ShortcutsConfig{
			Quit:    "q",
			Help:    "?",
			Refresh: "r",
			Start:   "s",
			Stop:    "x",
			Restart: "R",
			Logs:    "l",
			Details: "Enter",
		},
	}

	return cfg
}