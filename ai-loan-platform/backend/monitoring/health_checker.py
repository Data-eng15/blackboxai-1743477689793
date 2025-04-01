import requests
import psutil
import redis
import psycopg2
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import threading
import time
from pathlib import Path
from .config_loader import load_monitoring_config
from .alerts import AlertManager

class HealthChecker:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize health checker"""
        self.config = load_monitoring_config(config_path)
        self.logger = self._setup_logger()
        self.alert_manager = AlertManager(self.config)
        self.stop_event = threading.Event()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('health_checker')
        logger.setLevel(logging.INFO)
        
        log_dir = Path(self.config['monitoring']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'health_checks.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        return logger

    def check_api_health(self, endpoint: Dict[str, Any]) -> bool:
        """Check API endpoint health"""
        try:
            response = requests.request(
                method=endpoint['method'],
                url=endpoint['url'],
                timeout=endpoint.get('timeout', 5)
            )
            
            if response.status_code == endpoint['expected_status']:
                self.logger.info(f"API health check passed: {endpoint['url']}")
                return True
            else:
                self.logger.error(
                    f"API health check failed: {endpoint['url']} "
                    f"(Status: {response.status_code})"
                )
                self.alert_manager.send_system_alert(
                    'API',
                    'Health Check Failed',
                    f"Endpoint {endpoint['url']} returned status {response.status_code}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API health check error: {str(e)}")
            self.alert_manager.send_system_alert(
                'API',
                'Health Check Error',
                f"Failed to connect to {endpoint['url']}: {str(e)}"
            )
            return False

    def check_database_health(self) -> bool:
        """Check database health"""
        try:
            # Connect to database
            conn = psycopg2.connect(
                self.config['database']['url'],
                connect_timeout=self.config['health_checks']['database']['timeout']
            )
            
            # Execute test query
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
            
            conn.close()
            self.logger.info("Database health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Database health check error: {str(e)}")
            self.alert_manager.send_system_alert(
                'Database',
                'Health Check Failed',
                f"Database connection error: {str(e)}"
            )
            return False

    def check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            # Connect to Redis
            redis_client = redis.from_url(
                self.config['redis']['url'],
                socket_timeout=self.config['health_checks']['redis']['timeout']
            )
            
            # Test connection
            redis_client.ping()
            
            self.logger.info("Redis health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis health check error: {str(e)}")
            self.alert_manager.send_system_alert(
                'Redis',
                'Health Check Failed',
                f"Redis connection error: {str(e)}"
            )
            return False

    def check_system_resources(self) -> bool:
        """Check system resource usage"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.config['monitoring']['thresholds']['cpu']['critical']:
                self.alert_manager.send_system_alert(
                    'System',
                    'High CPU Usage',
                    f"CPU usage at {cpu_percent}%"
                )
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.config['monitoring']['thresholds']['memory']['critical']:
                self.alert_manager.send_system_alert(
                    'System',
                    'High Memory Usage',
                    f"Memory usage at {memory.percent}%"
                )
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > self.config['monitoring']['thresholds']['disk']['critical']:
                self.alert_manager.send_system_alert(
                    'System',
                    'High Disk Usage',
                    f"Disk usage at {disk.percent}%"
                )
            
            self.logger.info("System resources check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"System resources check error: {str(e)}")
            return False

    def check_service_dependencies(self) -> Dict[str, bool]:
        """Check all service dependencies"""
        results = {}
        
        # Check API endpoints
        if self.config['health_checks']['api']['enabled']:
            for endpoint in self.config['health_checks']['api']['endpoints']:
                results[f"api_{endpoint['url']}"] = self.check_api_health(endpoint)
        
        # Check database
        if self.config['health_checks']['database']['enabled']:
            results['database'] = self.check_database_health()
        
        # Check Redis
        if self.config['health_checks']['redis']['enabled']:
            results['redis'] = self.check_redis_health()
        
        # Check system resources
        results['system_resources'] = self.check_system_resources()
        
        return results

    def run_health_checks(self):
        """Run continuous health checks"""
        while not self.stop_event.is_set():
            try:
                results = self.check_service_dependencies()
                
                # Log overall status
                all_healthy = all(results.values())
                if all_healthy:
                    self.logger.info("All health checks passed")
                else:
                    failed_services = [
                        service for service, status in results.items()
                        if not status
                    ]
                    self.logger.error(
                        f"Health checks failed for services: {', '.join(failed_services)}"
                    )
                
                # Wait for next check interval
                time.sleep(self.config['health_checks']['interval'])
                
            except Exception as e:
                self.logger.error(f"Error running health checks: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def start_checking(self):
        """Start health checks"""
        self.checker_thread = threading.Thread(target=self.run_health_checks)
        self.checker_thread.start()
        self.logger.info("Health checks started")

    def stop_checking(self):
        """Stop health checks"""
        self.stop_event.set()
        if hasattr(self, 'checker_thread'):
            self.checker_thread.join()
        self.logger.info("Health checks stopped")

# Example usage
if __name__ == '__main__':
    checker = HealthChecker()
    try:
        checker.start_checking()
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        checker.stop_checking()