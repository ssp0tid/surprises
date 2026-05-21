package utils

import (
	"io"
	"os"
	"strings"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/pkgerrors"
)

var logger zerolog.Logger

func init() {
	zerolog.ErrorStackMarshaler = pkgerrors.MarshalStack
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	logger = zerolog.New(os.Stdout).With().Timestamp().Caller().Logger()
}

func NewLogger() zerolog.Logger {
	return logger
}

func GetLogger() *zerolog.Logger {
	return &logger
}

func SetLogLevel(level string) {
	var lvl zerolog.Level
	switch strings.ToLower(level) {
	case "debug":
		lvl = zerolog.DebugLevel
	case "info":
		lvl = zerolog.InfoLevel
	case "warn":
		lvl = zerolog.WarnLevel
	case "error":
		lvl = zerolog.ErrorLevel
	case "fatal":
		lvl = zerolog.FatalLevel
	case "panic":
		lvl = zerolog.PanicLevel
	default:
		lvl = zerolog.InfoLevel
	}
	zerolog.SetGlobalLevel(lvl)
}

type LevelWriter struct {
	Debug io.Writer
	Info  io.Writer
	Warn  io.Writer
	Error io.Writer
}

func (w LevelWriter) Write(p []byte) (n int, err error) {
	return w.Info.Write(p)
}

func NewConsoleWriter() io.Writer {
	return zerolog.ConsoleWriter{
		Out:        os.Stdout,
		TimeFormat: "2006-01-02 15:04:05",
	}
}

func GlobalLogger() *zerolog.Logger {
	return &logger
}