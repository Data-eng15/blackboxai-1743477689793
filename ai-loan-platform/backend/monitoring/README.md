# System Monitoring

This module provides comprehensive system and application monitoring for the AI Loan Platform.

## Features

- Real-time system metrics monitoring
- Process-level metrics collection
- Alert generation and logging
- Metrics visualization
- HTML report generation
- Configurable thresholds
- Graceful shutdown handling

## Components

### Monitor (monitor.py)

The main monitoring system that collects and logs various metrics:

- System metrics (CPU, Memory, Disk, Network)
- Process metrics (CPU usage, Memory usage, Thread count)
- Alert generation based on thresholds
- Real-time metrics queue

#### Usage

```python
from monitoring.monitor import SystemMonitor

# Initialize monitor
monitor = SystemMonitor()

# Start monitoring
monitor.start_monitoring()

# Get latest metrics
metrics = monitor.get_latest_metrics()

# Generate report for time period
report = monitor.generate_report(start_time, end_time)

# Stop monitoring
monitor.stop_monitoring()
```

### Visualizer (visualize.py)

Creates visualizations and reports from collected metrics:

- System metrics plots
- Process metrics plots
- Alert frequency visualization
- HTML report generation

#### Usage

```python
from monitoring.visualize import MetricsVisualizer

# Initialize visualizer
visualizer = MetricsVisualizer()

# Generate plots
visualizer.plot_system_metrics(hours=24)
visualizer.plot_process_metrics(hours=24)
visualizer.plot_alerts(days=7)

# Generate comprehensive report
report_path = visualizer.generate_report()
```

## Metrics Collected

### System Metrics
- CPU usage percentage
- Memory usage (total, available, used)
- Disk usage (total, used, free)
- Network connections and I/O
- System load average

### Process Metrics
- Process CPU usage
- Process memory usage
- Thread count
- File descriptors
- Process status
- Creation time

## Alert Thresholds

Default thresholds that trigger alerts:

- CPU: > 80%
- Memory: > 85%
- Disk: > 90%

## Log Files

Located in the `logs` directory:

- `system_metrics.log`: System-level metrics
- `app_metrics.log`: Application-level metrics
- `alerts.log`: Generated alerts

## Visualization Output

Generated in the `logs` directory:

- `system_metrics.png`: System metrics plots
- `process_metrics.png`: Process metrics plots
- `alerts.png`: Alert frequency visualization
- `metrics_report.html`: Comprehensive HTML report

## Configuration

Monitoring settings can be configured through environment variables:

```bash
MONITOR_LOG_DIR=logs
MONITOR_INTERVAL=60  # seconds
MONITOR_CPU_THRESHOLD=80
MONITOR_MEMORY_THRESHOLD=85
MONITOR_DISK_THRESHOLD=90
```

## Installation

Required packages:
```bash
pip install psutil matplotlib pandas seaborn
```

## Usage Examples

### Basic Monitoring

```python
from monitoring.monitor import SystemMonitor

monitor = SystemMonitor()
monitor.start_monitoring()
```

### Generate Visualizations

```python
from monitoring.visualize import MetricsVisualizer

visualizer = MetricsVisualizer()
visualizer.generate_report(hours=24)
```

### Custom Alert Handling

```python
class CustomMonitor(SystemMonitor):
    def check_thresholds(self, metrics):
        super().check_thresholds(metrics)
        # Add custom threshold checks
        if metrics['network']['connections'] > 1000:
            self.alert_logger.warning("High network connections")
```

## Best Practices

1. Regular Monitoring
   - Keep monitoring running continuously
   - Check reports daily
   - Review alerts promptly

2. Resource Usage
   - Monitor uses minimal system resources
   - Configurable collection intervals
   - Efficient log rotation

3. Alert Management
   - Set appropriate thresholds
   - Configure alert notifications
   - Regular threshold review

4. Data Management
   - Regular log rotation
   - Archive old metrics
   - Clean up old visualizations

## Troubleshooting

### Common Issues

1. High CPU Usage
   - Increase monitoring interval
   - Reduce metrics collection
   - Check system resources

2. Log File Growth
   - Enable log rotation
   - Adjust retention period
   - Monitor disk usage

3. Missing Metrics
   - Check permissions
   - Verify monitor running
   - Check log files

## Contributing

1. Follow coding standards
2. Add tests for new features
3. Update documentation
4. Submit pull request

## Support

For issues and support:
1. Check logs for errors
2. Review documentation
3. Submit issue with details
4. Contact development team