package main

import (
	"fmt"
	"os"

	"httpbench/cmd"
	"httpbench/metrics"
	"httpbench/output"
	"httpbench/worker"
)

func main() {
	cfg, err := cmd.ParseFlags()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	if err := cfg.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "Validation error: %v\n", err)
		os.Exit(1)
	}

	collector := metrics.NewCollector()
	pool := worker.NewPool(cfg, collector)

	duration := pool.Run()

	stats := collector.GetStats()

	formatter := output.GetFormatter(cfg)
	output := formatter.Format(stats, cfg, duration)

	fmt.Println(output)
}