// Package models provides data structures for DockerWatch.
//
// This package contains core domain models for container management,
// including container metadata, resource statistics, logs, and health checks.
package models

import "time"

// Stats represents resource usage statistics for a container at a point in time.
type Stats struct {
	ContainerID string
	Timestamp   time.Time
	CPU         CPUStats
	Memory      MemoryStats
	Network     NetworkStats
	Disk        DiskStats
	PIDs        int
}

// CPUStats holds CPU usage information.
type CPUStats struct {
	Percentage   float64   // Calculated CPU %
	Usage        uint64    // Total CPU usage (nanoseconds)
	SystemUsage  uint64    // System CPU usage
	OnlineCPUs   int       // Number of online CPUs
	PerCoreUsage []float64 // Per-core percentages
}

// MemoryStats holds memory usage information.
type MemoryStats struct {
	Usage      uint64  // Current memory usage (bytes)
	Limit      uint64  // Memory limit (bytes)
	Percentage float64 // Usage percentage
	SwapUsage  uint64  // Swap usage (bytes)
	SwapLimit  uint64  // Swap limit (bytes)
}

// NetworkStats holds network I/O statistics.
type NetworkStats struct {
	RxBytes    uint64           // Bytes received
	TxBytes    uint64           // Bytes transmitted
	RxPackets  uint64           // Packets received
	TxPackets  uint64           // Packets transmitted
	RxErrors   uint64           // Receive errors
	TxErrors   uint64           // Transmit errors
	Interfaces []InterfaceStats // For multi-interface support
}

// InterfaceStats holds per-network-interface statistics.
type InterfaceStats struct {
	Name    string
	RxBytes uint64
	TxBytes uint64
}

// DiskStats holds block I/O statistics.
type DiskStats struct {
	ReadBytes                  uint64
	WriteBytes                 uint64
	IoServiceBytesRecursive   []IOCounter
}

// IOCounter represents an I/O operation counter.
type IOCounter struct {
	Major, Minor uint64
	Op           string
	Value        uint64
}