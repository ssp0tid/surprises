// Package config provides application configuration loaded from environment variables.
package config

import (
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config is the main application configuration.
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Auth     AuthConfig
	Retention RetentionConfig
	Limits   LimitsConfig
}

// ServerConfig holds server-specific configuration.
type ServerConfig struct {
	Host     string
	Port     int
	BaseURL  string
}

// DatabaseConfig holds database-specific configuration.
type DatabaseConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Database string
	TLS      bool
}

// AuthConfig holds authentication-specific configuration.
type AuthConfig struct {
	Enabled   bool
	Username  string
	Password  string
	JWTSecret string
}

// RetentionConfig holds data retention configuration.
type RetentionConfig struct {
	Days int
}

// LimitsConfig holds rate and size limit configuration.
type LimitsConfig struct {
	MaxMessageSize int
	MaxBatchSize   int
	RateLimit      int
}

const envPrefix = "LOGVAULT_"

// Default values.
const (
	DefaultHost           = "0.0.0.0"
	DefaultPort           = 8080
	DefaultBaseURL        = "http://localhost:8080"
	DefaultDBHost         = "localhost"
	DefaultDBPort         = 9000
	DefaultDBUser         = "default"
	DefaultDBPassword     = ""
	DefaultDBName         = "logs"
	DefaultAuthEnabled    = false
	DefaultUsername       = "admin"
	DefaultPassword       = ""
	DefaultJWTSecret      = ""
	DefaultRetentionDays = 90
	DefaultMaxMessageSize = 1048576 // 1MB
	DefaultMaxBatchSize   = 1000
	DefaultRateLimit     = 5000
)

// Load populates Config from environment variables.
func Load() (*Config, error) {
	cfg := &Config{
		Server: ServerConfig{
			Host:    DefaultHost,
			Port:    DefaultPort,
			BaseURL: DefaultBaseURL,
		},
		Database: DatabaseConfig{
			Host:     DefaultDBHost,
			Port:     DefaultDBPort,
			User:     DefaultDBUser,
			Password: DefaultDBPassword,
			Database: DefaultDBName,
			TLS:      false,
		},
		Auth: AuthConfig{
			Enabled:   DefaultAuthEnabled,
			Username:  DefaultUsername,
			Password:  DefaultPassword,
			JWTSecret: DefaultJWTSecret,
		},
		Retention: RetentionConfig{
			Days: DefaultRetentionDays,
		},
		Limits: LimitsConfig{
			MaxMessageSize: DefaultMaxMessageSize,
			MaxBatchSize:   DefaultMaxBatchSize,
			RateLimit:      DefaultRateLimit,
		},
	}

	// Server config
	if v := getEnv("HOST"); v != "" {
		cfg.Server.Host = v
	}
	if v := getEnv("PORT"); v != "" {
		port, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid PORT: %w", err)
		}
		cfg.Server.Port = port
	}
	if v := getEnv("BASE_URL"); v != "" {
		cfg.Server.BaseURL = v
	}

	// Database config
	if v := getEnv("DB_HOST"); v != "" {
		cfg.Database.Host = v
	}
	if v := getEnv("DB_PORT"); v != "" {
		port, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid DB_PORT: %w", err)
		}
		cfg.Database.Port = port
	}
	if v := getEnv("DB_USER"); v != "" {
		cfg.Database.User = v
	}
	if v := getEnv("DB_PASSWORD"); v != "" {
		cfg.Database.Password = v
	}
	if v := getEnv("DB_NAME"); v != "" {
		cfg.Database.Database = v
	}
	if v := getEnv("DB_TLS"); v != "" {
		tls, err := strconv.ParseBool(v)
		if err != nil {
			return nil, fmt.Errorf("invalid DB_TLS: %w", err)
		}
		cfg.Database.TLS = tls
	}

	// Auth config
	if v := getEnv("AUTH_ENABLED"); v != "" {
		enabled, err := strconv.ParseBool(v)
		if err != nil {
			return nil, fmt.Errorf("invalid AUTH_ENABLED: %w", err)
		}
		cfg.Auth.Enabled = enabled
	}
	if v := getEnv("USERNAME"); v != "" {
		cfg.Auth.Username = v
	}
	if v := getEnv("PASSWORD"); v != "" {
		cfg.Auth.Password = v
	}
	if v := getEnv("JWT_SECRET"); v != "" {
		cfg.Auth.JWTSecret = v
	}

	// Retention config
	if v := getEnv("RETENTION_DAYS"); v != "" {
		days, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid RETENTION_DAYS: %w", err)
		}
		cfg.Retention.Days = days
	}

	// Limits config
	if v := getEnv("MAX_MESSAGE_SIZE"); v != "" {
		size, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid MAX_MESSAGE_SIZE: %w", err)
		}
		cfg.Limits.MaxMessageSize = size
	}
	if v := getEnv("MAX_BATCH_SIZE"); v != "" {
		size, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid MAX_BATCH_SIZE: %w", err)
		}
		cfg.Limits.MaxBatchSize = size
	}
	if v := getEnv("RATE_LIMIT"); v != "" {
		limit, err := strconv.Atoi(v)
		if err != nil {
			return nil, fmt.Errorf("invalid RATE_LIMIT: %w", err)
		}
		cfg.Limits.RateLimit = limit
	}

	return cfg, nil
}

// Validate checks for required configuration fields.
// Returns an error if any required field is missing or invalid.
func (c *Config) Validate() error {
	// Validate server config
	if c.Server.Host == "" {
		return errors.New("server host is required")
	}
	if c.Server.Port <= 0 || c.Server.Port > 65535 {
		return errors.New("server port must be between 1 and 65535")
	}
	if c.Server.BaseURL == "" {
		return errors.New("server base URL is required")
	}

	// Validate database config
	if c.Database.Host == "" {
		return errors.New("database host is required")
	}
	if c.Database.Port <= 0 || c.Database.Port > 65535 {
		return errors.New("database port must be between 1 and 65535")
	}
	if c.Database.User == "" {
		return errors.New("database user is required")
	}
	if c.Database.Database == "" {
		return errors.New("database name is required")
	}

	// Validate auth config
	if c.Auth.Enabled {
		if c.Auth.Username == "" {
			return errors.New("auth username is required when auth is enabled")
		}
		if c.Auth.Password == "" {
			return errors.New("auth password is required when auth is enabled")
		}
		if c.Auth.JWTSecret == "" {
			return errors.New("auth JWT secret is required when auth is enabled")
		}
	}

	// Validate retention config
	if c.Retention.Days <= 0 {
		return errors.New("retention days must be greater than 0")
	}

	// Validate limits config
	if c.Limits.MaxMessageSize <= 0 {
		return errors.New("max message size must be greater than 0")
	}
	if c.Limits.MaxBatchSize <= 0 {
		return errors.New("max batch size must be greater than 0")
	}
	if c.Limits.RateLimit <= 0 {
		return errors.New("rate limit must be greater than 0")
	}

	return nil
}

// Addr returns the server address in "host:port" format.
func (s *ServerConfig) Addr() string {
	return fmt.Sprintf("%s:%d", s.Host, s.Port)
}

// DatabaseAddr returns the database address in "host:port" format.
func (d *DatabaseConfig) Addr() string {
	return fmt.Sprintf("%s:%d", d.Host, d.Port)
}

// Duration returns the retention period as a time.Duration.
func (r *RetentionConfig) Duration() time.Duration {
	return time.Duration(r.Days) * 24 * time.Hour
}

// getEnv retrieves an environment variable with the LOGVAULT_ prefix.
// Returns empty string if not set.
func getEnv(key string) string {
	v, _ := os.LookupEnv(envPrefix + key)
	return v
}