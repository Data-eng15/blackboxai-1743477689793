import psutil
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import threading
import queue
from dataclasses import dataclass, asdict
from .config_loader import load_monitoring_config

@dataclass
class SystemMetrics:
    """System-level metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    load_avg: List[float]
    io_counters: Dict[str, int]

@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    timestamp: str
    process_cpu_percent: float
    process_memory_percent: float
    thread_count: int
    open_files: int
    connections: int

@dataclass
class CustomMetrics:
    """Custom business metrics"""
    timestamp: str
    loan_applications_count: int
    approval_rate: float
    average_processing_time: float
    active_users: int
    error_rate: float

class MetricsCollector:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize metrics collector"""
        self.config = load_monitoring_config(config_path)
        self.logger = self._setup_logger()
        self.metrics_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Create metrics directory
        self.metrics_dir = Path(self.config['monitoring']['log_dir']) / 'metrics'
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('metrics_collector')
        logger.setLevel(logging.INFO)
        
        log_dir = Path(self.config['monitoring']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'metrics_collector.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        return logger

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        try:
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage('/').percent,
                network_connections=len(psutil.net_connections()),
                load_avg=psutil.getloadavg(),
                io_counters=psutil.disk_io_counters()._asdict()
            )
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            raise

    def collect_application_metrics(self, pid: Optional[int] = None) -> ApplicationMetrics:
        """Collect application-level metrics"""
        try:
            process = psutil.Process(pid) if pid else psutil.Process()
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                process_cpu_percent=process.cpu_percent(),
                process_memory_percent=process.memory_percent(),
                thread_count=process.num_threads(),
                open_files=len(process.open_files()),
                connections=len(process.connections())
            )
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {str(e)}")
            raise

    def collect_custom_metrics(self) -> CustomMetrics:
        """Collect custom business metrics"""
        # This would typically integrate with your application's metrics
        # For demonstration, using placeholder values
        try:
            return CustomMetrics(
                timestamp=datetime.now().isoformat(),
                loan_applications_count=0,
                approval_rate=0.0,
                average_processing_time=0.0,
                active_users=0,
                error_rate=0.0
            )
        except Exception as e:
            self.logger.error(f"Error collecting custom metrics: {str(e)}")
            raise

    def save_metrics(self, metrics: Any):
        """Save metrics to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d')
            metrics_file = self.metrics_dir / f'metrics_{timestamp}.json'
            
            # Convert metrics to dictionary
            metrics_dict = asdict(metrics)
            
            # Append to file
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(metrics_dict) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {str(e)}")
            raise

    def collect_metrics(self):
        """Main metrics collection loop"""
        while not self.stop_event.is_set():
            try:
                # Collect all metrics
                system_metrics = self.collect_system_metrics()
                app_metrics = self.collect_application_metrics()
                custom_metrics = self.collect_custom_metrics()
                
                # Save metrics
                self.save_metrics(system_metrics)
                self.save_metrics(app_metrics)
                self.save_metrics(custom_metrics)
                
                # Add to queue for real-time monitoring
                self.metrics_queue.put({
                    'system': system_metrics,
                    'application': app_metrics,
                    'custom': custom_metrics
                })
                
                # Check thresholds
                self._check_thresholds(system_metrics, app_metrics)
                
                # Wait for next collection interval
                time.sleep(self.config['monitoring']['interval'])
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def _check_thresholds(
        self,
        system_metrics: SystemMetrics,
        app_metrics: ApplicationMetrics
    ):
        """Check metrics against thresholds"""
        thresholds = self.config['monitoring']['thresholds']
        
        # Check CPU usage
        if system_metrics.cpu_percent > thresholds['cpu']['critical']:
            self.logger.critical(f"CPU usage critical: {system_metrics.cpu_percent}%")
        elif system_metrics.cpu_percent > thresholds['cpu']['warning']:
            self.logger.warning(f"CPU usage high: {system_metrics.cpu_percent}%")
        
        # Check memory usage
        if system_metrics.memory_percent > thresholds['memory']['critical']:
            self.logger.critical(
                f"Memory usage critical: {system_metrics.memory_percent}%"
            )
        elif system_metrics.memory_percent > thresholds['memory']['warning']:
            self.logger.warning(f"Memory usage high: {system_metrics.memory_percent}%")
        
        # Check disk usage
        if system_metrics.disk_percent > thresholds['disk']['critical']:
            self.logger.critical(f"Disk usage critical: {system_metrics.disk_percent}%")
        elif system_metrics.disk_percent > thresholds['disk']['warning']:
            self.logger.warning(f"Disk usage high: {system_metrics.disk_percent}%")

    def start_collecting(self):
        """Start metrics collection"""
        self.collector_thread = threading.Thread(target=self.collect_metrics)
        self.collector_thread.start()
        self.logger.info("Metrics collection started")

    def stop_collecting(self):
        """Stop metrics collection"""
        self.stop_event.set()
        if hasattr(self, 'collector_thread'):
            self.collector_thread.join()
        self.logger.info("Metrics collection stopped")

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get latest metrics from queue"""
        try:
            return self.metrics_queue.get_nowait()
        except queue.Empty:
            return None

    def get_metrics_history(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get metrics history for a time period"""
        metrics = []
        try:
            # Get all metrics files in the date range
            date_range = [
                start_time.strftime('%Y%m%d'),
                end_time.strftime('%Y%m%d')
            ]
            
            for metrics_file in self.metrics_dir.glob('metrics_*.json'):
                file_date = metrics_file.stem.split('_')[1]
                if date_range[0] <= file_date <= date_range[1]:
                    with open(metrics_file) as f:
                        for line in f:
                            metric = json.loads(line)
                            timestamp = datetime.fromisoformat(metric['timestamp'])
                            if start_time <= timestamp <= end_time:
                                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics history: {str(e)}")
            return []

# Example usage
if __name__ == '__main__':
    collector = MetricsCollector()
    try:
        collector.start_collecting()
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        collector.stop_collecting()