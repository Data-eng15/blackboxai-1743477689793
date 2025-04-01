import pytest
from unittest.mock import patch, MagicMock
import requests
import psutil
import redis
import psycopg2
from datetime import datetime
from backend.monitoring.health_checker import HealthChecker

@pytest.fixture
def mock_config():
    """Provide mock configuration"""
    return {
        'monitoring': {
            'log_dir': 'test_logs',
            'thresholds': {
                'cpu': {'warning': 70, 'critical': 85},
                'memory': {'warning': 75, 'critical': 90},
                'disk': {'warning': 80, 'critical': 90}
            }
        },
        'database': {
            'url': 'postgresql://user:pass@localhost/db'
        },
        'redis': {
            'url': 'redis://localhost:6379/0'
        },
        'health_checks': {
            'interval': 60,
            'api': {
                'enabled': True,
                'endpoints': [
                    {
                        'url': 'http://localhost:5000/health',
                        'method': 'GET',
                        'expected_status': 200,
                        'timeout': 5
                    }
                ]
            },
            'database': {
                'enabled': True,
                'timeout': 5
            },
            'redis': {
                'enabled': True,
                'timeout': 5
            }
        }
    }

@pytest.fixture
def health_checker(mock_config):
    """Provide HealthChecker instance"""
    with patch('backend.monitoring.health_checker.load_monitoring_config') as mock_load, \
         patch('backend.monitoring.health_checker.AlertManager') as mock_alert:
        mock_load.return_value = mock_config
        return HealthChecker()

def test_api_health_check_success(health_checker):
    """Test successful API health check"""
    with patch('requests.request') as mock_request:
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Test endpoint
        endpoint = {
            'url': 'http://localhost:5000/health',
            'method': 'GET',
            'expected_status': 200
        }
        
        result = health_checker.check_api_health(endpoint)
        assert result == True
        mock_request.assert_called_once()

def test_api_health_check_failure(health_checker):
    """Test failed API health check"""
    with patch('requests.request') as mock_request:
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response
        
        # Test endpoint
        endpoint = {
            'url': 'http://localhost:5000/health',
            'method': 'GET',
            'expected_status': 200
        }
        
        result = health_checker.check_api_health(endpoint)
        assert result == False

def test_api_health_check_timeout(health_checker):
    """Test API health check timeout"""
    with patch('requests.request', side_effect=requests.exceptions.Timeout):
        endpoint = {
            'url': 'http://localhost:5000/health',
            'method': 'GET',
            'expected_status': 200
        }
        
        result = health_checker.check_api_health(endpoint)
        assert result == False

def test_database_health_check_success(health_checker):
    """Test successful database health check"""
    with patch('psycopg2.connect') as mock_connect:
        # Configure mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = health_checker.check_database_health()
        assert result == True
        mock_connect.assert_called_once()

def test_database_health_check_failure(health_checker):
    """Test failed database health check"""
    with patch('psycopg2.connect', side_effect=psycopg2.Error):
        result = health_checker.check_database_health()
        assert result == False

def test_redis_health_check_success(health_checker):
    """Test successful Redis health check"""
    with patch('redis.from_url') as mock_redis:
        # Configure mock
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        result = health_checker.check_redis_health()
        assert result == True
        mock_redis.assert_called_once()

def test_redis_health_check_failure(health_checker):
    """Test failed Redis health check"""
    with patch('redis.from_url', side_effect=redis.ConnectionError):
        result = health_checker.check_redis_health()
        assert result == False

def test_system_resources_check(health_checker):
    """Test system resources check"""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk:
        
        # Configure mocks
        mock_cpu.return_value = 50.0
        mock_memory.return_value.percent = 60.0
        mock_disk.return_value.percent = 70.0
        
        result = health_checker.check_system_resources()
        assert result == True

def test_system_resources_check_critical(health_checker):
    """Test system resources check with critical values"""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk:
        
        # Configure mocks with critical values
        mock_cpu.return_value = 95.0
        mock_memory.return_value.percent = 95.0
        mock_disk.return_value.percent = 95.0
        
        result = health_checker.check_system_resources()
        assert result == True  # Still returns True but should trigger alerts

def test_service_dependencies_check(health_checker):
    """Test checking all service dependencies"""
    with patch.object(health_checker, 'check_api_health') as mock_api, \
         patch.object(health_checker, 'check_database_health') as mock_db, \
         patch.object(health_checker, 'check_redis_health') as mock_redis, \
         patch.object(health_checker, 'check_system_resources') as mock_sys:
        
        # Configure mocks
        mock_api.return_value = True
        mock_db.return_value = True
        mock_redis.return_value = True
        mock_sys.return_value = True
        
        results = health_checker.check_service_dependencies()
        assert all(results.values())

def test_health_check_thread(health_checker):
    """Test health check thread operation"""
    with patch.object(health_checker, 'check_service_dependencies') as mock_check:
        # Configure mock
        mock_check.return_value = {'test': True}
        
        # Start checks
        health_checker.start_checking()
        
        # Wait briefly
        import time
        time.sleep(0.1)
        
        # Stop checks
        health_checker.stop_checking()
        
        assert mock_check.called

def test_error_handling(health_checker, caplog):
    """Test error handling in health checks"""
    with patch.object(health_checker, 'check_service_dependencies',
                     side_effect=Exception('Test error')):
        
        health_checker.run_health_checks()
        assert "Error running health checks: Test error" in caplog.text

def test_alert_triggering(health_checker):
    """Test alert triggering on health check failures"""
    with patch.object(health_checker.alert_manager, 'send_system_alert') as mock_alert:
        # Simulate failed API health check
        endpoint = {
            'url': 'http://localhost:5000/health',
            'method': 'GET',
            'expected_status': 200
        }
        
        with patch('requests.request', side_effect=requests.exceptions.ConnectionError):
            health_checker.check_api_health(endpoint)
            mock_alert.assert_called_once()