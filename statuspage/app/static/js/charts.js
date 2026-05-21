/**
 * Charts.js - Chart.js utilities for status page uptime visualization
 */

(function() {
    'use strict';

    // Default chart configuration
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: true,
                callbacks: {
                    label: function(context) {
                        return context.parsed.y + '% uptime';
                    }
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 8
                }
            },
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 4
            },
            line: {
                tension: 0.3,
                borderWidth: 2
            }
        }
    };

    // Status colors
    const statusColors = {
        operational: '#22c55e',
        degraded: '#f59e0b',
        down: '#ef4444',
        unknown: '#6b7280'
    };

    /**
     * Create a line chart for uptime data
     */
    function createUptimeChart(canvasId, labels, data, options) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        const mergedOptions = Object.assign({}, defaultOptions, options || {});

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels || [],
                datasets: [{
                    data: data || [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true
                }]
            },
            options: mergedOptions
        });
    }

    /**
     * Create a sparkline chart (mini chart)
     */
    function createSparkline(canvasId, data, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(function(_, i) { return i; }),
                datasets: [{
                    data: data || [],
                    borderColor: color || statusColors.operational,
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: {
                        display: false,
                        beginAtZero: true,
                        max: 100
                    }
                },
                elements: {
                    line: {
                        tension: 0.4
                    }
                }
            }
        });
    }

    /**
     * Create a status bar
     */
    function createStatusBar(elementId, percentage, status) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const color = statusColors[status] || statusColors.unknown;
        const width = Math.max(0, Math.min(100, percentage));

        element.style.width = width + '%';
        element.style.backgroundColor = color;
    }

    /**
     * Initialize all charts on the page
     */
    function initCharts() {
        // Find all chart canvas elements with data attributes
        const chartElements = document.querySelectorAll('[data-chart-type]');

        chartElements.forEach(function(element) {
            const type = element.getAttribute('data-chart-type');
            const labels = JSON.parse(element.getAttribute('data-labels') || '[]');
            const data = JSON.parse(element.getAttribute('data-values') || '[]');

            if (type === 'line') {
                createUptimeChart(element.id, labels, data);
            } else if (type === 'sparkline') {
                const status = element.getAttribute('data-status') || 'operational';
                createSparkline(element.id, data, statusColors[status]);
            }
        });

        // Initialize status bars
        const statusBars = document.querySelectorAll('[data-status-bar]');
        statusBars.forEach(function(bar) {
            const percentage = parseFloat(bar.getAttribute('data-percentage')) || 0;
            const status = bar.getAttribute('data-status') || 'operational';
            createStatusBar(bar.id, percentage, status);
        });
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCharts);
    } else {
        initCharts();
    }

    // Export for manual use
    window.StatusCharts = {
        createUptimeChart: createUptimeChart,
        createSparkline: createSparkline,
        createStatusBar: createStatusBar,
        initCharts: initCharts,
        statusColors: statusColors
    };

})();
