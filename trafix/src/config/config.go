package config

import (
	"fmt"
	"time"

	"github.com/spf13/viper"
)

type Config struct {
	Server      ServerConfig      `mapstructure:"server"`
	Dashboard   DashboardConfig  `mapstructure:"dashboard"`
	Proxy       ProxyConfig      `mapstructure:"proxy"`
	Storage     StorageConfig   `mapstructure:"storage"`
	Middleware  MiddlewareConfig `mapstructure:"middleware"`
}

type ServerConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	LogLevel string `mapstructure:"log_level"`
}

type DashboardConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
}

type ProxyConfig struct {
	Host          string        `mapstructure:"host"`
	Port         int           `mapstructure:"port"`
	TargetBaseURL string       `mapstructure:"target_base_url"`
	Timeout      time.Duration `mapstructure:"timeout"`
}

type StorageConfig struct {
	Database      string `mapstructure:"database"`
	MaxConnections int   `mapstructure:"max_connections"`
}

type MiddlewareConfig struct {
	RateLimit RateLimitConfig   `mapstructure:"rate_limit"`
	Auth     AuthConfig       `mapstructure:"auth"`
	Logging  LoggingConfig    `mapstructure:"logging"`
	CORS     CORSConfig      `mapstructure:"cors"`
}

type RateLimitConfig struct {
	Enabled           bool   `mapstructure:"enabled"`
	RequestsPerSecond int   `mapstructure:"requests_per_second"`
	Burst            int    `mapstructure:"burst"`
}

type AuthConfig struct {
	Enabled bool     `mapstructure:"enabled"`
	APIKeys []string `mapstructure:"api_keys"`
}

type LoggingConfig struct {
	Enabled    bool `mapstructure:"enabled"`
	MaxBodySize int  `mapstructure:"max_body_size"`
}

type CORSConfig struct {
	Enabled          bool   `mapstructure:"enabled"`
	AllowedOrigins  []string `mapstructure:"allowed_origins"`
}

func Load() (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("../..")
	viper.AddConfigPath("/etc/trafix")

	viper.SetDefault("server.host", "127.0.0.1")
	viper.SetDefault("server.port", 8080)
	viper.SetDefault("server.log_level", "info")

	viper.SetDefault("dashboard.host", "127.0.0.1")
	viper.SetDefault("dashboard.port", 8081)
	viper.SetDefault("dashboard.username", "admin")
	viper.SetDefault("dashboard.password", "changeme")

	viper.SetDefault("proxy.host", "127.0.0.1")
	viper.SetDefault("proxy.port", 8082)
	viper.SetDefault("proxy.target_base_url", "http://localhost:3000")
	viper.SetDefault("proxy.timeout", "30s")

	viper.SetDefault("storage.database", "./trafix.db")
	viper.SetDefault("storage.max_connections", 10)

	viper.SetDefault("middleware.rate_limit.enabled", true)
	viper.SetDefault("middleware.rate_limit.requests_per_second", 100)
	viper.SetDefault("middleware.rate_limit.burst", 20)
	viper.SetDefault("middleware.auth.enabled", false)
	viper.SetDefault("middleware.logging.enabled", true)
	viper.SetDefault("middleware.logging.max_body_size", 10240)
	viper.SetDefault("middleware.cors.enabled", false)

	viper.SetEnvPrefix("TRAFIX")
	viper.AutomaticEnv()

	viper.BindEnv("server.host", "TRAFIX_SERVER_HOST")
	viper.BindEnv("server.port", "TRAFIX_SERVER_PORT")
	viper.BindEnv("server.log_level", "TRAFIX_LOG_LEVEL")

	viper.BindEnv("proxy.target_base_url", "TRAFIX_PROXY_TARGET")
	viper.BindEnv("proxy.timeout", "TRAFIX_PROXY_TIMEOUT")

	viper.BindEnv("storage.database", "TRAFIX_STORAGE_DB")
	viper.BindEnv("storage.max_connections", "TRAFIX_STORAGE_MAX_CONN")

	viper.BindEnv("middleware.rate_limit.enabled", "TRAFIX_RATE_LIMIT_ENABLED")
	viper.BindEnv("middleware.rate_limit.requests_per_second", "TRAFIX_RATE_LIMIT_RPS")
	viper.BindEnv("middleware.rate_limit.burst", "TRAFIX_RATE_LIMIT_BURST")

	viper.BindEnv("middleware.auth.enabled", "TRAFIX_AUTH_ENABLED")
	viper.BindEnv("middleware.auth.api_keys", "TRAFIX_AUTH_API_KEYS")

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			return &Config{
				Server: ServerConfig{
					Host:     viper.GetString("server.host"),
					Port:     viper.GetInt("server.port"),
					LogLevel: viper.GetString("server.log_level"),
				},
				Dashboard: DashboardConfig{
					Host:     viper.GetString("dashboard.host"),
					Port:     viper.GetInt("dashboard.port"),
					Username: viper.GetString("dashboard.username"),
					Password: viper.GetString("dashboard.password"),
				},
				Proxy: ProxyConfig{
					Host:          viper.GetString("proxy.host"),
					Port:         viper.GetInt("proxy.port"),
					TargetBaseURL: viper.GetString("proxy.target_base_url"),
					Timeout:      viper.GetDuration("proxy.timeout"),
				},
				Storage: StorageConfig{
					Database:      viper.GetString("storage.database"),
					MaxConnections: viper.GetInt("storage.max_connections"),
				},
				Middleware: MiddlewareConfig{
					RateLimit: RateLimitConfig{
						Enabled:           viper.GetBool("middleware.rate_limit.enabled"),
						RequestsPerSecond: viper.GetInt("middleware.rate_limit.requests_per_second"),
						Burst:            viper.GetInt("middleware.rate_limit.burst"),
					},
					Auth: AuthConfig{
						Enabled: viper.GetBool("middleware.auth.enabled"),
						APIKeys: viper.GetStringSlice("middleware.auth.api_keys"),
					},
					Logging: LoggingConfig{
						Enabled:   viper.GetBool("middleware.logging.enabled"),
						MaxBodySize: viper.GetInt("middleware.logging.max_body_size"),
					},
					CORS: CORSConfig{
						Enabled:         viper.GetBool("middleware.cors.enabled"),
						AllowedOrigins: viper.GetStringSlice("middleware.cors.allowed_origins"),
					},
				},
			}, nil
		}
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return &cfg, nil
}