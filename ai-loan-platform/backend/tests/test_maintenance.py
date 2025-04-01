import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import gzip
import json
from backend.monitoring.maintenance import MonitoringMaintenance

@pytest.fixture
def mock_config():
    """Provide mock configuration"""
    return {
        'monitoring': {
            'log_dir': 'test_logs',
            'metrics_retention_days': 30
        },
        'logging': {
            'file': {
                'max_size': 1048576  # 1MB
            }
        }
    }

@pytest.fixture
def maintenance(mock_config, tmp_path):
    """Provide MonitoringMaintenance instance"""
    with patch('backend.monitoring.maintenance.load_monitoring_config') as mock_load:
        mock_load.return_value = mock_config
        maintenance = MonitoringMaintenance()
        # Override directories to use temporary path
        maintenance.log_dir = tmp_path / 'logs'
        maintenance.archive_dir = tmp_path / 'logs' / 'archive'
        maintenance.backup_dir = tmp_path / 'logs' / 'backup'
        # Create directories
        maintenance.log_dir.mkdir(parents=True)
        maintenance.archive_dir.mkdir(parents=True)
        maintenance.backup_dir.mkdir(parents=True)
        return maintenance

def create_test_files(directory: Path, count: int, days_old: int):
    """Create test files with specified age"""
    files = []
    for i in range(count):
        file_path = directory / f'test_{i}.log'
        file_path.touch()
        # Set file modification time
        mtime = datetime.now() - timedelta(days=days_old)
        os.utime(file_path, (mtime.timestamp(), mtime.timestamp()))
        files.append(file_path)
    return files

def test_cleanup_old_logs(maintenance):
    """Test cleaning up old log files"""
    # Create test files
    old_files = create_test_files(maintenance.log_dir, 3, 40)  # 40 days old
    new_files = create_test_files(maintenance.log_dir, 2, 10)  # 10 days old
    
    # Clean up old files
    cleaned_count = maintenance.cleanup_old_logs(30)
    
    assert cleaned_count == 3
    # Check old files are archived
    for file in old_files:
        assert not file.exists()
        archive_file = maintenance.archive_dir / f"{file.stem}_{datetime.now().strftime('%Y%m%d')}.gz"
        assert archive_file.exists()
    # Check new files remain
    for file in new_files:
        assert file.exists()

def test_cleanup_old_metrics(maintenance):
    """Test cleaning up old metrics files"""
    metrics_dir = maintenance.log_dir / 'metrics'
    metrics_dir.mkdir()
    
    # Create test metrics files
    old_metrics = create_test_files(metrics_dir, 2, 40)
    new_metrics = create_test_files(metrics_dir, 1, 10)
    
    cleaned_count = maintenance.cleanup_old_metrics(30)
    
    assert cleaned_count == 2
    for file in old_metrics:
        assert not file.exists()
    for file in new_metrics:
        assert file.exists()

def test_cleanup_old_reports(maintenance):
    """Test cleaning up old report files"""
    reports_dir = maintenance.log_dir / 'reports'
    reports_dir.mkdir()
    
    # Create test report files
    old_reports = create_test_files(reports_dir, 2, 40)
    new_reports = create_test_files(reports_dir, 1, 10)
    
    cleaned_count = maintenance.cleanup_old_reports(30)
    
    assert cleaned_count == 2
    for file in old_reports:
        assert not file.exists()
    for file in new_reports:
        assert file.exists()

def test_archive_log_file(maintenance):
    """Test archiving individual log file"""
    # Create test log file
    log_file = maintenance.log_dir / 'test.log'
    log_file.write_text('Test log content')
    
    maintenance._archive_log_file(log_file)
    
    # Check original file is removed
    assert not log_file.exists()
    
    # Check archive file exists and contains correct content
    archive_file = maintenance.archive_dir / f"test_{datetime.now().strftime('%Y%m%d')}.gz"
    assert archive_file.exists()
    with gzip.open(archive_file, 'rt') as f:
        content = f.read()
        assert content == 'Test log content'

def test_create_backup(maintenance):
    """Test creating backup of monitoring data"""
    # Create some test data
    (maintenance.log_dir / 'test1.log').write_text('Test log 1')
    (maintenance.log_dir / 'test2.log').write_text('Test log 2')
    
    backup_path = maintenance.create_backup()
    
    assert backup_path.exists()
    assert backup_path.suffix == '.gz'
    assert 'monitoring_backup_' in backup_path.name

def test_restore_backup(maintenance):
    """Test restoring from backup"""
    # Create original test files
    (maintenance.log_dir / 'original.log').write_text('Original content')
    
    # Create backup
    backup_path = maintenance.create_backup()
    
    # Remove original files
    shutil.rmtree(maintenance.log_dir)
    maintenance.log_dir.mkdir()
    
    # Restore from backup
    success = maintenance.restore_backup(backup_path)
    
    assert success
    restored_file = maintenance.log_dir / 'original.log'
    assert restored_file.exists()
    assert restored_file.read_text() == 'Original content'

def test_rotate_logs(maintenance):
    """Test log rotation"""
    # Create large log file
    log_file = maintenance.log_dir / 'test.log'
    log_file.write_bytes(b'x' * (maintenance.config['logging']['file']['max_size'] + 1))
    
    maintenance.rotate_logs()
    
    # Check original file is rotated
    assert not log_file.exists()
    rotated_files = list(maintenance.log_dir.glob('test_*.log'))
    assert len(rotated_files) == 1

def test_error_handling(maintenance):
    """Test error handling"""
    with pytest.raises(Exception):
        # Try to restore non-existent backup
        maintenance.restore_backup(Path('nonexistent.tar.gz'))

def test_cleanup_with_no_files(maintenance):
    """Test cleanup with no files"""
    assert maintenance.cleanup_old_logs() == 0
    assert maintenance.cleanup_old_metrics() == 0
    assert maintenance.cleanup_old_reports() == 0

def test_backup_with_no_files(maintenance):
    """Test backup with no files"""
    backup_path = maintenance.create_backup()
    assert backup_path.exists()

def test_rotate_logs_with_small_files(maintenance):
    """Test log rotation with files below size threshold"""
    log_file = maintenance.log_dir / 'small.log'
    log_file.write_text('Small log file')
    
    maintenance.rotate_logs()
    
    # File should not be rotated
    assert log_file.exists()
    rotated_files = list(maintenance.log_dir.glob('small_*.log'))
    assert len(rotated_files) == 0

def test_concurrent_backup_restore(maintenance):
    """Test backup and restore operations don't interfere"""
    # Create test files
    (maintenance.log_dir / 'file1.log').write_text('Content 1')
    (maintenance.log_dir / 'file2.log').write_text('Content 2')
    
    # Create backup
    backup_path = maintenance.create_backup()
    
    # Create new file while backup exists
    (maintenance.log_dir / 'file3.log').write_text('Content 3')
    
    # Restore backup
    maintenance.restore_backup(backup_path)
    
    # Check restored state
    assert (maintenance.log_dir / 'file1.log').exists()
    assert (maintenance.log_dir / 'file2.log').exists()
    assert not (maintenance.log_dir / 'file3.log').exists()