import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import json
from collections import defaultdict
from dataclasses import dataclass
from .config_loader import load_monitoring_config
from .alerts import AlertManager

@dataclass
class LogEntry:
    """Represents a parsed log entry"""
    timestamp: datetime
    level: str
    source: str
    message: str
    details: Dict[str, Any]

class LogAnalyzer:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize log analyzer"""
        self.config = load_monitoring_config(config_path)
        self.logger = self._setup_logger()
        self.alert_manager = AlertManager(self.config)
        
        # Compile regex patterns
        self.patterns = {
            'timestamp': re.compile(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3})'),
            'level': re.compile(r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)'),
            'source': re.compile(r'\[(.*?)\]'),
            'ip': re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
            'request': re.compile(r'(GET|POST|PUT|DELETE|PATCH)\s+(\S+)'),
            'status_code': re.compile(r'status_code=(\d{3})'),
            'response_time': re.compile(r'response_time=(\d+\.?\d*)ms')
        }

    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('log_analyzer')
        logger.setLevel(logging.INFO)
        
        log_dir = Path(self.config['monitoring']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'log_analyzer.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        return logger

    def parse_log_entry(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line into structured data"""
        try:
            # Extract timestamp
            timestamp_match = self.patterns['timestamp'].search(line)
            if not timestamp_match:
                return None
            timestamp = datetime.strptime(
                timestamp_match.group(1),
                '%Y-%m-%d %H:%M:%S,%f'
            )
            
            # Extract log level
            level_match = self.patterns['level'].search(line)
            level = level_match.group(1) if level_match else 'UNKNOWN'
            
            # Extract source
            source_match = self.patterns['source'].search(line)
            source = source_match.group(1) if source_match else 'unknown'
            
            # Extract additional details
            details = {
                'ip': None,
                'request_method': None,
                'request_path': None,
                'status_code': None,
                'response_time': None
            }
            
            # IP address
            ip_match = self.patterns['ip'].search(line)
            if ip_match:
                details['ip'] = ip_match.group(0)
            
            # Request details
            request_match = self.patterns['request'].search(line)
            if request_match:
                details['request_method'] = request_match.group(1)
                details['request_path'] = request_match.group(2)
            
            # Status code
            status_match = self.patterns['status_code'].search(line)
            if status_match:
                details['status_code'] = int(status_match.group(1))
            
            # Response time
            time_match = self.patterns['response_time'].search(line)
            if time_match:
                details['response_time'] = float(time_match.group(1))
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                source=source,
                message=line,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing log entry: {str(e)}")
            return None

    def analyze_logs(
        self,
        log_file: Path,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze log file and generate metrics"""
        metrics = {
            'error_count': 0,
            'warning_count': 0,
            'request_count': 0,
            'status_codes': defaultdict(int),
            'response_times': [],
            'endpoints': defaultdict(int),
            'ip_addresses': defaultdict(int),
            'errors': []
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    entry = self.parse_log_entry(line)
                    if not entry:
                        continue
                    
                    # Check time range
                    if start_time and entry.timestamp < start_time:
                        continue
                    if end_time and entry.timestamp > end_time:
                        continue
                    
                    # Count by log level
                    if entry.level == 'ERROR':
                        metrics['error_count'] += 1
                        metrics['errors'].append({
                            'timestamp': entry.timestamp.isoformat(),
                            'message': entry.message
                        })
                    elif entry.level == 'WARNING':
                        metrics['warning_count'] += 1
                    
                    # Request metrics
                    if entry.details['request_method']:
                        metrics['request_count'] += 1
                        endpoint = (
                            f"{entry.details['request_method']} "
                            f"{entry.details['request_path']}"
                        )
                        metrics['endpoints'][endpoint] += 1
                    
                    # Status code metrics
                    if entry.details['status_code']:
                        metrics['status_codes'][
                            str(entry.details['status_code'])
                        ] += 1
                    
                    # Response time metrics
                    if entry.details['response_time']:
                        metrics['response_times'].append(
                            entry.details['response_time']
                        )
                    
                    # IP address metrics
                    if entry.details['ip']:
                        metrics['ip_addresses'][entry.details['ip']] += 1
            
            # Calculate averages and percentiles
            if metrics['response_times']:
                metrics['avg_response_time'] = sum(metrics['response_times']) / len(
                    metrics['response_times']
                )
                metrics['response_times'].sort()
                metrics['p95_response_time'] = metrics['response_times'][
                    int(len(metrics['response_times']) * 0.95)
                ]
            
            # Check for anomalies
            self._check_anomalies(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing logs: {str(e)}")
            raise

    def _check_anomalies(self, metrics: Dict[str, Any]):
        """Check metrics for anomalies and trigger alerts"""
        try:
            # Check error rate
            if metrics['request_count'] > 0:
                error_rate = metrics['error_count'] / metrics['request_count']
                if error_rate > self.config['monitoring']['thresholds']['error_rate']['critical']:
                    self.alert_manager.send_system_alert(
                        'Logs',
                        'High Error Rate',
                        f"Error rate is {error_rate:.2%}"
                    )
            
            # Check response times
            if metrics.get('p95_response_time'):
                if metrics['p95_response_time'] > self.config['monitoring']['thresholds']['api_response_time']['critical']:
                    self.alert_manager.send_system_alert(
                        'Logs',
                        'High Response Time',
                        f"P95 response time is {metrics['p95_response_time']}ms"
                    )
            
            # Check for suspicious IP addresses
            for ip, count in metrics['ip_addresses'].items():
                if count > self.config['monitoring']['thresholds']['request_rate']['critical']:
                    self.alert_manager.send_security_alert(
                        'High Request Rate',
                        f"IP {ip} made {count} requests"
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking anomalies: {str(e)}")

    def generate_report(
        self,
        metrics: Dict[str, Any],
        report_file: Optional[Path] = None
    ) -> str:
        """Generate analysis report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'summary': {
                    'total_requests': metrics['request_count'],
                    'error_rate': (
                        metrics['error_count'] / metrics['request_count']
                        if metrics['request_count'] > 0 else 0
                    ),
                    'avg_response_time': metrics.get('avg_response_time'),
                    'p95_response_time': metrics.get('p95_response_time'),
                    'top_endpoints': dict(
                        sorted(
                            metrics['endpoints'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:5]
                    ),
                    'status_code_distribution': metrics['status_codes']
                }
            }
            
            if report_file:
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

# Example usage
if __name__ == '__main__':
    analyzer = LogAnalyzer()
    try:
        # Analyze last hour's logs
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        log_file = Path('logs/application.log')
        metrics = analyzer.analyze_logs(log_file, start_time, end_time)
        
        # Generate and save report
        report_file = Path('logs/analysis_report.json')
        analyzer.generate_report(metrics, report_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")