import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import seaborn as sns

class MetricsVisualizer:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        
        # Set style
        plt.style.use('seaborn')
        sns.set_palette("husl")

    def load_metrics(self, log_file: str, metric_type: str) -> pd.DataFrame:
        """Load metrics from log file into DataFrame"""
        data = []
        log_path = os.path.join(self.log_dir, log_file)
        
        if not os.path.exists(log_path):
            return pd.DataFrame()
        
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    # Parse log line
                    timestamp_str, _, _, metrics_str = line.split(' - ')
                    timestamp = datetime.fromisoformat(timestamp_str)
                    metrics = json.loads(metrics_str)
                    
                    # Flatten metrics for DataFrame
                    if metric_type == 'system':
                        data.append({
                            'timestamp': timestamp,
                            'cpu_percent': metrics['cpu']['percent'],
                            'memory_percent': metrics['memory']['percent'],
                            'disk_percent': metrics['disk']['percent'],
                            'network_connections': metrics['network']['connections']
                        })
                    elif metric_type == 'process':
                        data.append({
                            'timestamp': timestamp,
                            'cpu_percent': metrics['cpu_percent'],
                            'memory_percent': metrics['memory_percent'],
                            'num_threads': metrics['num_threads']
                        })
                except (ValueError, json.JSONDecodeError, KeyError):
                    continue
        
        return pd.DataFrame(data)

    def plot_system_metrics(self, hours: int = 24):
        """Plot system metrics for the last N hours"""
        # Load data
        df = self.load_metrics('system_metrics.log', 'system')
        if df.empty:
            print("No system metrics data available")
            return
        
        # Filter for time range
        start_time = datetime.now() - timedelta(hours=hours)
        df = df[df['timestamp'] >= start_time]
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'System Metrics (Last {hours} Hours)')
        
        # CPU Usage
        axes[0, 0].plot(df['timestamp'], df['cpu_percent'], 'b-')
        axes[0, 0].set_title('CPU Usage')
        axes[0, 0].set_ylabel('Percent')
        axes[0, 0].grid(True)
        
        # Memory Usage
        axes[0, 1].plot(df['timestamp'], df['memory_percent'], 'g-')
        axes[0, 1].set_title('Memory Usage')
        axes[0, 1].set_ylabel('Percent')
        axes[0, 1].grid(True)
        
        # Disk Usage
        axes[1, 0].plot(df['timestamp'], df['disk_percent'], 'r-')
        axes[1, 0].set_title('Disk Usage')
        axes[1, 0].set_ylabel('Percent')
        axes[1, 0].grid(True)
        
        # Network Connections
        axes[1, 1].plot(df['timestamp'], df['network_connections'], 'm-')
        axes[1, 1].set_title('Network Connections')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].grid(True)
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(os.path.join(self.log_dir, 'system_metrics.png'))
        plt.close()

    def plot_process_metrics(self, hours: int = 24):
        """Plot process metrics for the last N hours"""
        # Load data
        df = self.load_metrics('app_metrics.log', 'process')
        if df.empty:
            print("No process metrics data available")
            return
        
        # Filter for time range
        start_time = datetime.now() - timedelta(hours=hours)
        df = df[df['timestamp'] >= start_time]
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Process Metrics (Last {hours} Hours)')
        
        # CPU Usage
        axes[0, 0].plot(df['timestamp'], df['cpu_percent'], 'b-')
        axes[0, 0].set_title('Process CPU Usage')
        axes[0, 0].set_ylabel('Percent')
        axes[0, 0].grid(True)
        
        # Memory Usage
        axes[0, 1].plot(df['timestamp'], df['memory_percent'], 'g-')
        axes[0, 1].set_title('Process Memory Usage')
        axes[0, 1].set_ylabel('Percent')
        axes[0, 1].grid(True)
        
        # Thread Count
        axes[1, 0].plot(df['timestamp'], df['num_threads'], 'r-')
        axes[1, 0].set_title('Thread Count')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].grid(True)
        
        # Memory Usage Distribution
        axes[1, 1].hist(df['memory_percent'], bins=30)
        axes[1, 1].set_title('Memory Usage Distribution')
        axes[1, 1].set_xlabel('Percent')
        axes[1, 1].set_ylabel('Frequency')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(os.path.join(self.log_dir, 'process_metrics.png'))
        plt.close()

    def plot_alerts(self, days: int = 7):
        """Plot alert frequency over time"""
        alerts = []
        alert_log = os.path.join(self.log_dir, 'alerts.log')
        
        if not os.path.exists(alert_log):
            print("No alerts data available")
            return
        
        with open(alert_log, 'r') as f:
            for line in f:
                try:
                    timestamp_str = line.split(' - ')[0]
                    timestamp = datetime.fromisoformat(timestamp_str)
                    alert_type = line.split(' - ')[2].strip()
                    alerts.append({
                        'timestamp': timestamp,
                        'type': alert_type
                    })
                except (ValueError, IndexError):
                    continue
        
        df = pd.DataFrame(alerts)
        if df.empty:
            print("No alerts data available")
            return
        
        # Filter for time range
        start_time = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= start_time]
        
        # Create figure
        plt.figure(figsize=(15, 5))
        plt.title(f'Alert Frequency (Last {days} Days)')
        
        # Group by day and type
        df['date'] = df['timestamp'].dt.date
        alert_counts = df.groupby(['date', 'type']).size().unstack(fill_value=0)
        
        # Plot stacked bar chart
        alert_counts.plot(kind='bar', stacked=True)
        plt.xlabel('Date')
        plt.ylabel('Number of Alerts')
        plt.legend(title='Alert Type')
        plt.xticks(rotation=45)
        
        # Save plot
        plt.tight_layout()
        plt.savefig(os.path.join(self.log_dir, 'alerts.png'))
        plt.close()

    def generate_report(self, hours: int = 24):
        """Generate a comprehensive metrics report"""
        # Generate all plots
        self.plot_system_metrics(hours)
        self.plot_process_metrics(hours)
        self.plot_alerts(hours // 24)
        
        # Create HTML report
        report_path = os.path.join(self.log_dir, 'metrics_report.html')
        with open(report_path, 'w') as f:
            f.write("""
            <html>
            <head>
                <title>Metrics Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    img { max-width: 100%; margin: 20px 0; }
                    .section { margin: 40px 0; }
                </style>
            </head>
            <body>
                <h1>Metrics Report</h1>
                <div class="section">
                    <h2>System Metrics</h2>
                    <img src="system_metrics.png" alt="System Metrics">
                </div>
                <div class="section">
                    <h2>Process Metrics</h2>
                    <img src="process_metrics.png" alt="Process Metrics">
                </div>
                <div class="section">
                    <h2>Alerts</h2>
                    <img src="alerts.png" alt="Alerts">
                </div>
            </body>
            </html>
            """)
        
        return report_path

def main():
    """Main function to generate visualizations"""
    visualizer = MetricsVisualizer()
    report_path = visualizer.generate_report()
    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    main()