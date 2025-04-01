import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import psutil
import json
import queue
from pathlib import Path
from backend.monitoring.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
    ApplicationMetrics,
    CustomMetrics
)

@pytest.fixture
def mock_config():
    """Provide mock configuration"""
    return {
        'monitoring': {
            'interval': 60,
            'log_dir': 'test_logs',
            'thresholds': {
                'cpu': {'warning': 70, 'critical': 85},
                'memory': {'warning': 75, 'critical': 90},
                'disk': {'warning': 80, 'critical': 90}
            }
        }
    }

@pytest.fixture
def metrics_collector(mock_config, tmp_path):
    """Provide MetricsCollector instance"""
    with patch('backend.monitoring.metrics_collector.load_monitoring_config') as mock_load:
        mock_load.return_value = mock_config
        collector = MetricsCollector()
        collector.metrics_dir = tmp_path / 'metrics'
        collector.metrics_dir.mkdir(parents=True)
        return collector

def test_system_metrics_collection(metrics_collector):
    """Test system metrics collection"""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.net_connections') as mock_net, \
         patch('psutil.getloadavg') as mock_load, \
         patch('psutil.disk_io_counters') as mock_io:
        
        # Configure mocks
        mock_cpu.return_value = 50.0
        mock_memory.return_value.percent = 60.0
        mock_disk.return_value.percent = 70.0
        mock_net.return_value = ['conn1', 'conn2']
        mock_load.return_value = (1.0, 1.5, 2.0)
        mock_io.return_value._asdict.return_value = {'read_bytes': 1000, 'write_bytes': 2000}
        
        # Collect metrics
        metrics = metrics_collector.collect_system_metrics()
        
        # Verify
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 70.0
        assert metrics.network_connections == 2
        assert len(metrics.load_avg) == 3
        assert metrics.io_counters['read_bytes'] == 1000

def test_application_metrics_collection(metrics_collector):
    """Test application metrics collection"""
    with patch('psutil.Process') as mock_process:
        # Configure mock
        process = MagicMock()
        process.cpu_percent.return_value = 30.0
        process.memory_percent.return_value = 40.0
        process.num_threads.return_value = 10
        process.open_files.return_value = ['file1', 'file2']
        process.connections.return_value = ['conn1']
        mock_process.return_value = process
        
        # Collect metrics
        metrics = metrics_collector.collect_application_metrics()
        
        # Verify
        assert isinstance(metrics, ApplicationMetrics)
        assert metrics.process_cpu_percent == 30.0
        assert metrics.process_memory_percent == 40.0
        assert metrics.thread_count == 10
        assert metrics.open_files == 2
        assert metrics.connections == 1

def test_custom_metrics_collection(metrics_collector):
    """Test custom metrics collection"""
    metrics = metrics_collector.collect_custom_metrics()
    
    assert isinstance(metrics, CustomMetrics)
    assert hasattr(metrics, 'loan_applications_count')
    assert hasattr(metrics, 'approval_rate')
    assert hasattr(metrics, 'average_processing_time')
    assert hasattr(metrics, 'active_users')
    assert hasattr(metrics, 'error_rate')

def test_metrics_saving(metrics_collector):
    """Test metrics saving to file"""
    # Create test metrics
    metrics = SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_percent=50.0,
        memory_percent=60.0,
        disk_percent=70.0,
        network_connections=2,
        load_avg=[1.0, 1.5, 2.0],
        io_counters={'read_bytes': 1000, 'write_bytes': 2000}
    )
    
    # Save metrics
    metrics_collector.save_metrics(metrics)
    
    # Verify file exists and contains metrics
    date_str = datetime.now().strftime('%Y%m%d')
    metrics_file = metrics_collector.metrics_dir / f'metrics_{date_str}.json'
    assert metrics_file.exists()
    
    with open(metrics_file) as f:
        saved_metrics = json.loads(f.readline())
        assert saved_metrics['cpu_percent'] == 50.0
        assert saved_metrics['memory_percent'] == 60.0

def test_threshold_checking(metrics_collector, caplog):
    """Test metrics threshold checking"""
    system_metrics = SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_percent=90.0,  # Above critical threshold
        memory_percent=80.0,  # Above warning threshold
        disk_percent=70.0,
        network_connections=2,
        load_avg=[1.0, 1.5, 2.0],
        io_counters={'read_bytes': 1000, 'write_bytes': 2000}
    )
    
    app_metrics = ApplicationMetrics(
        timestamp=datetime.now().isoformat(),
        process_cpu_percent=30.0,
        process_memory_percent=40.0,
        thread_count=10,
        open_files=2,
        connections=1
    )
    
    metrics_collector._check_thresholds(system_metrics, app_metrics)
    
    assert "CPU usage critical: 90.0%" in caplog.text
    assert "Memory usage high: 80.0%" in caplog.text

def test_metrics_collection_thread(metrics_collector):
    """Test metrics collection thread"""
    with patch.object(metrics_collector, 'collect_system_metrics') as mock_system, \
         patch.object(metrics_collector, 'collect_application_metrics') as mock_app, \
         patch.object(metrics_collector, 'collect_custom_metrics') as mock_custom:
        
        # Start collection
        metrics_collector.start_collecting()
        
        # Wait briefly
        import time
        time.sleep(0.1)
        
        # Stop collection
        metrics_collector.stop_collecting()
        
        # Verify metrics were collected
        assert mock_system.called
        assert mock_app.called
        assert mock_custom.called

def test_get_latest_metrics(metrics_collector):
    """Test getting latest metrics from queue"""
    # Add test metrics to queue
    test_metrics = {
        'system': {'cpu_percent': 50.0},
        'application': {'thread_count': 10},
        'custom': {'active_users': 100}
    }
    metrics_collector.metrics_queue.put(test_metrics)
    
    # Get metrics
    latest = metrics_collector.get_latest_metrics()
    
    assert latest == test_metrics
    assert metrics_collector.get_latest_metrics() is None  # Queue should be empty

def test_get_metrics_history(metrics_collector):
    """Test getting metrics history"""
    # Create test metrics files
    start_time = datetime.now() - timedelta(days=1)
    end_time = datetime.now()
    
    # Add test metrics
    for _ in range(3):
        metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            network_connections=2,
            load_avg=[1.0, 1.5, 2.0],
            io_counters={'read_bytes': 1000, 'write_bytes': 2000}
        )
        metrics_collector.save_metrics(metrics)
    
    # Get history
    history = metrics_collector.get_metrics_history(start_time, end_time)
    
    assert len(history) == 3
    assert all('cpu_percent' in metric for metric in history)

def test_error_handling(metrics_collector, caplog):
    """Test error handling in metrics collection"""
    with patch('psutil.cpu_percent', side_effect=Exception('Test error')):
        with pytest.raises(Exception):
            metrics_collector.collect_system_metrics()
        
        assert "Error collecting system metrics" in caplog.text