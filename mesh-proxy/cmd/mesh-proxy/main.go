package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"

	"github.com/rs/zerolog"

	"github.com/surprises/mesh-proxy/internal/config"
	"github.com/surprises/mesh-proxy/internal/proxy"
)

var (
	cfgFile     string
	port      int
	adminPort int
	verbose   bool
)

var rootCmd = &cobra.Command{
	Use:   "mesh-proxy",
	Short: "Local service mesh proxy for traffic control",
	RunE:  run,
}

func init() {
	rootCmd.PersistentFlags().StringVarP(&cfgFile, "config", "c", "configs/default.yaml", "config file path")
	rootCmd.PersistentFlags().IntVarP(&port, "port", "p", 0, "proxy server port (0 = use config)")
	rootCmd.PersistentFlags().IntVar(&adminPort, "admin-port", 0, "admin server port (0 = use config)")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "verbose logging")
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func run(cmd *cobra.Command, args []string) error {
 zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
 var logger zerolog.Logger
 if verbose {
  logger = zerolog.New(os.Stderr).Level(zerolog.DebugLevel).With().Timestamp().Logger()
 } else {
  logger = zerolog.New(os.Stderr).Level(zerolog.InfoLevel).With().Timestamp().Logger()
 }

 logger.Info().Msg("starting mesh-proxy")

 cfg, err := loadConfig(cfgFile, port, adminPort)
 if err != nil {
  return fmt.Errorf("load config: %w", err)
 }

 p, err := proxy.New(cfg, logger)
 if err != nil {
  return fmt.Errorf("create proxy: %w", err)
 }

 ctx, cancel := context.WithCancel(context.Background())
 defer cancel()

 go func() {
  if err := p.Serve(); err != nil {
   logger.Error().Err(err).Msg("proxy server error")
   cancel()
  }
 }()

 if cfg.Admin.Enabled {
  go func() {
   if err := p.StartAdmin(); err != nil {
    logger.Error().Err(err).Msg("admin server error")
    cancel()
   }
  }()
 }

 logger.Info().
  Int("port", cfg.Server.Port).
  Int("admin-port", cfg.Admin.Port).
  Msg("mesh-proxy ready")

 waitForSignal(logger, p, ctx)
 return nil
}

func loadConfig(path string, port, adminPort int) (*config.Config, error) {
 loader := config.NewLoader()

 cfg, err := loader.Load(path)
 if err != nil {
  if !os.IsNotExist(err) {
   return nil, err
  }
  cfg = config.NewDefaultConfig()
 }

 if port > 0 {
  cfg.Server.Port = port
 }
 if adminPort > 0 {
  cfg.Admin.Port = adminPort
 }

 return cfg, nil
}

func waitForSignal(logger zerolog.Logger, p *proxy.Proxy, ctx context.Context) {
 sig := make(chan os.Signal, 1)
 signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
 <-sig

 logger.Info().Msg("shutting down")

 shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
 defer cancel()

 if err := p.Shutdown(shutdownCtx); err != nil {
  logger.Error().Err(err).Msg("shutdown error")
 }

 logger.Info().Msg("stopped")
}