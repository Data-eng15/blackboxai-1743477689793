import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import json
from backend.monitoring.log_analyzer import LogAnalyzer, LogEntry

@pytest.fixture
def mock_config():
    """Provide mock configuration"""
    return {
        'monitoring': {
            'log_dir': 'test_logs',
            'thresholds': {
                'error_rate': {
                    'warning': 0.01,
                    'critical': 0.05
                },
                'api_response_time': {
                    'warning': 1000,
                    'critical': 2000
                },
                'request_rate': {
                    'warning': 100,
                    'critical': 200
                }
            }
        }
    }

@pytest.fixture
def log_analyzer(mock_config):
    """Provide LogAnalyzer instance"""
    with patch('backend.monitoring.log_analyzer.load_monitoring_config') as mock_load, \
         patch('backend.monitoring.log_analyzer.AlertManager') as mock_alert:
        mock_load.return_value = mock_config
        return LogAnalyzer()

@pytest.fixture
def sample_log_lines():
    """Provide sample log lines"""
    return [
        '2023-08-01 10:00:00,123 - INFO - [app] - Request from 192.168.1.100: GET /api/health status_code=200 response_time=50.5ms',
        '2023-08-01 10:01:00,456 - ERROR - [app] - Database connection failed',
        '2023-08-01 10:02:00,789 - WARNING - [app] - High memory usage detected',
        '2023-08-01 10:03:00,012 - INFO - [app] - Request from 192.168.1.101: POST /api/loan/apply status_code=201 response_time=150.2ms'
    ]

def test_parse_log_entry(log_analyzer):
    """Test parsing individual log entries"""
    log_line = '2023-08-01 10:00:00,123 - INFO - [app] - Request from 192.168.1.100: GET /api/health status_code=200 response_time=50.5ms'
    
    entry = log_analyzer.parse_log_entry(log_line)
    
    assert isinstance(entry, LogEntry)
    assert entry.level == 'INFO'
    assert entry.source == 'app'
    assert entry.details['ip'] == '192.168.1.100'
    assert entry.details['request_method'] == 'GET'
    assert entry.details['request_path'] == '/api/health'
    assert entry.details['status_code'] == 200
    assert entry.details['response_time'] == 50.5

def test_parse_invalid_log_entry(log_analyzer):
    """Test parsing invalid log entry"""
    log_line = 'Invalid log entry'
    entry = log_analyzer.parse_log_entry(log_line)
    assert entry is None

def test_analyze_logs(log_analyzer, sample_log_lines, tmp_path):
    """Test log analysis"""
    # Create test log file
    log_file = tmp_path / 'test.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(sample_log_lines))
    
    # Analyze logs
    metrics = log_analyzer.analyze_logs(log_file)
    
    assert metrics['error_count'] == 1
    assert metrics['warning_count'] == 1
    assert metrics['request_count'] == 2
    assert metrics['status_codes']['200'] == 1
    assert metrics['status_codes']['201'] == 1
    assert len(metrics['response_times']) == 2
    assert len(metrics['endpoints']) == 2
    assert len(metrics['ip_addresses']) == 2

def test_analyze_logs_with_time_range(log_analyzer, sample_log_lines, tmp_path):
    """Test log analysis with time range"""
    # Create test log file
    log_file = tmp_path / 'test.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(sample_log_lines))
    
    # Set time range
    start_time = datetime(2023, 8, 1, 10, 0, 0)
    end_time = datetime(2023, 8, 1, 10, 2, 0)
    
    # Analyze logs
    metrics = log_analyzer.analyze_logs(log_file, start_time, end_time)
    
    assert metrics['request_count'] == 1
    assert metrics['error_count'] == 1
    assert metrics['warning_count'] == 0

def test_check_anomalies(log_analyzer):
    """Test anomaly detection"""
    metrics = {
        'request_count': 1000,
        'error_count': 100,
        'p95_response_time': 3000,
        'ip_addresses': {
            '192.168.1.100': 300
        }
    }
    
    with patch.object(log_analyzer.alert_manager, 'send_system_alert') as mock_system_alert, \
         patch.object(log_analyzer.alert_manager, 'send_security_alert') as mock_security_alert:
        
        log_analyzer._check_anomalies(metrics)
        
        # Should trigger alerts for high error rate, response time, and request rate
        assert mock_system_alert.call_count == 2
        assert mock_security_alert.call_count == 1

def test_generate_report(log_analyzer, tmp_path):
    """Test report generation"""
    metrics = {
        'request_count': 1000,
        'error_count': 10,
        'warning_count': 5,
        'status_codes': {'200': 950, '500': 50},
        'response_times': [100, 200, 300],
        'endpoints': {'/api/health': 500, '/api/status': 500},
        'ip_addresses': {'192.168.1.100': 1000},
        'avg_response_time': 200,
        'p95_response_time': 290
    }
    
    report_file = tmp_path / 'report.json'
    report_json = log_analyzer.generate_report(metrics, report_file)
    
    # Verify report content
    report = json.loads(report_json)
    assert 'timestamp' in report
    assert 'metrics' in report
    assert 'summary' in report
    assert report['summary']['total_requests'] == 1000
    assert report['summary']['error_rate'] == 0.01
    assert len(report['summary']['top_endpoints']) == 2

def test_error_handling(log_analyzer, tmp_path):
    """Test error handling"""
    # Test with non-existent file
    with pytest.raises(Exception):
        log_analyzer.analyze_logs(tmp_path / 'nonexistent.log')

def test_response_time_calculation(log_analyzer, tmp_path):
    """Test response time calculations"""
    log_lines = [
        '2023-08-01 10:00:00,123 - INFO - [app] - Request: GET /api/test response_time=100ms',
        '2023-08-01 10:00:01,123 - INFO - [app] - Request: GET /api/test response_time=200ms',
        '2023-08-01 10:00:02,123 - INFO - [app] - Request: GET /api/test response_time=300ms'
    ]
    
    log_file = tmp_path / 'test.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_lines))
    
    metrics = log_analyzer.analyze_logs(log_file)
    
    assert metrics['avg_response_time'] == 200
    assert metrics['p95_response_time'] == 300

def test_ip_address_tracking(log_analyzer, tmp_path):
    """Test IP address tracking"""
    log_lines = [
        '2023-08-01 10:00:00,123 - INFO - [app] - Request from 192.168.1.100: GET /api/test',
        '2023-08-01 10:00:01,123 - INFO - [app] - Request from 192.168.1.100: GET /api/test',
        '2023-08-01 10:00:02,123 - INFO - [app] - Request from 192.168.1.101: GET /api/test'
    ]
    
    log_file = tmp_path / 'test.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_lines))
    
    metrics = log_analyzer.analyze_logs(log_file)
    
    assert metrics['ip_addresses']['192.168.1.100'] == 2
    assert metrics['ip_addresses']['192.168.1.101'] == 1

def test_endpoint_tracking(log_analyzer, tmp_path):
    """Test endpoint tracking"""
    log_lines = [
        '2023-08-01 10:00:00,123 - INFO - [app] - Request: GET /api/test1',
        '2023-08-01 10:00:01,123 - INFO - [app] - Request: GET /api/test1',
        '2023-08-01 10:00:02,123 - INFO - [app] - Request: POST /api/test2'
    ]
    
    log_file = tmp_path / 'test.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_lines))
    
    metrics = log_analyzer.analyze_logs(log_file)
    
    assert metrics['endpoints']['GET /api/test1'] == 2
    assert metrics['endpoints']['POST /api/test2'] == 1