package logparser

import (
	"strings"

	"github.com/logvault/logvault/internal/model"
)

type LogLevel string

const (
	LevelDebug LogLevel = "DEBUG"
	LevelInfo  LogLevel = "INFO"
	LevelWarn  LogLevel = "WARN"
	LevelError LogLevel = "ERROR"
	LevelFatal LogLevel = "FATAL"
)

var LevelPriority = map[LogLevel]int{
	LevelDebug: 0,
	LevelInfo:  1,
	LevelWarn:  2,
	LevelError: 3,
	LevelFatal: 4,
}

func ParseLevel(s string) (model.LogLevel, error) {
	if s == "" {
		return model.LogLevelInfo, nil
	}

	normalized := strings.ToUpper(strings.TrimSpace(s))

	switch normalized {
	case "DEBUG", "DEBUg", "DEBG", "DBG":
		return model.LogLevelDebug, nil
	case "INFO", "INF", "INFORMATION":
		return model.LogLevelInfo, nil
	case "WARN", "WARNING", "WRN":
		return model.LogLevelWarn, nil
	case "ERROR", "ERR", "ERRO", "ERRL":
		return model.LogLevelError, nil
	case "FATAL", "FTL", "CRITICAL", "CRIT":
		return model.LogLevelFatal, nil
	default:
		return model.LogLevelInfo, nil
	}
}

func IsValid(level model.LogLevel) bool {
	switch level {
	case model.LogLevelDebug, model.LogLevelInfo, model.LogLevelWarn, model.LogLevelError, model.LogLevelFatal:
		return true
	default:
		return false
	}
}

func GetPriority(level model.LogLevel) int {
	priority, ok := LevelPriority[LogLevel(level)]
	if !ok {
		return 0
	}
	return priority
}