import logging
import psutil
import time
import os
from datetime import datetime
import json
from typing import Dict, List, Any
import threading
import queue
import signal
import sys

class SystemMonitor:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize loggers
        self.setup_loggers()
        
        # Initialize metrics queue
        self.metrics_queue = queue.Queue()
        
        # Initialize stop event
        self.stop_event = threading.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def setup_loggers(self):
        """Set up different loggers for various metrics"""
        # System metrics logger
        self.sys_logger = logging.getLogger('system_metrics')
        self.sys_logger.setLevel(logging.INFO)
        sys_handler = logging.FileHandler(os.path.join(self.log_dir, 'system_metrics.log'))
        sys_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.sys_logger.addHandler(sys_handler)
        
        # Application metrics logger
        self.app_logger = logging.getLogger('app_metrics')
        self.app_logger.setLevel(logging.INFO)
        app_handler = logging.FileHandler(os.path.join(self.log_dir, 'app_metrics.log'))
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.app_logger.addHandler(app_handler)
        
        # Alert logger
        self.alert_logger = logging.getLogger('alerts')
        self.alert_logger.setLevel(logging.WARNING)
        alert_handler = logging.FileHandler(os.path.join(self.log_dir, 'alerts.log'))
        alert_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.alert_logger.addHandler(alert_handler)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'network': {
                'connections': len(psutil.net_connections()),
                'stats': psutil.net_io_counters()._asdict()
            }
        }

    def get_process_metrics(self, pid: int = None) -> Dict[str, Any]:
        """Collect process metrics"""
        if pid is None:
            pid = os.getpid()
        
        try:
            process = psutil.Process(pid)
            return {
                'timestamp': datetime.now().isoformat(),
                'pid': pid,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,
                'status': process.status(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except psutil.NoSuchProcess:
            return None

    def check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts"""
        # CPU threshold (80%)
        if metrics['cpu']['percent'] > 80:
            self.alert_logger.warning(
                f"High CPU usage: {metrics['cpu']['percent']}%"
            )
        
        # Memory threshold (85%)
        if metrics['memory']['percent'] > 85:
            self.alert_logger.warning(
                f"High memory usage: {metrics['memory']['percent']}%"
            )
        
        # Disk threshold (90%)
        if metrics['disk']['percent'] > 90:
            self.alert_logger.warning(
                f"High disk usage: {metrics['disk']['percent']}%"
            )

    def collect_metrics(self):
        """Continuously collect metrics"""
        while not self.stop_event.is_set():
            try:
                # Collect system metrics
                sys_metrics = self.get_system_metrics()
                self.sys_logger.info(json.dumps(sys_metrics))
                self.check_thresholds(sys_metrics)
                
                # Collect process metrics
                proc_metrics = self.get_process_metrics()
                if proc_metrics:
                    self.app_logger.info(json.dumps(proc_metrics))
                
                # Add to metrics queue for real-time monitoring
                self.metrics_queue.put({
                    'system': sys_metrics,
                    'process': proc_metrics
                })
                
                # Wait for next collection interval
                time.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.alert_logger.error(f"Error collecting metrics: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def start_monitoring(self):
        """Start the monitoring process"""
        self.monitor_thread = threading.Thread(target=self.collect_metrics)
        self.monitor_thread.start()
        print("Monitoring started...")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.stop_event.set()
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        print("Monitoring stopped.")

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down monitor...")
        self.stop_monitoring()
        sys.exit(0)

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics from the queue"""
        try:
            return self.metrics_queue.get_nowait()
        except queue.Empty:
            return None

    def generate_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate a metrics report for a specific time period"""
        report = {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'metrics': {
                'system': [],
                'application': [],
                'alerts': []
            }
        }
        
        # Read and parse log files
        for log_file, metric_type in [
            ('system_metrics.log', 'system'),
            ('app_metrics.log', 'application'),
            ('alerts.log', 'alerts')
        ]:
            log_path = os.path.join(self.log_dir, log_file)
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    for line in f:
                        try:
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if start_time <= timestamp <= end_time:
                                report['metrics'][metric_type].append(line.strip())
                        except (ValueError, IndexError):
                            continue
        
        return report

def main():
    """Main function to run the monitor"""
    monitor = SystemMonitor()
    try:
        monitor.start_monitoring()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()

if __name__ == '__main__':
    main()