import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json
import gzip
from .config_loader import load_monitoring_config

class MonitoringMaintenance:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize maintenance manager"""
        self.config = load_monitoring_config(config_path)
        self.logger = self._setup_logger()
        
        # Create required directories
        self.log_dir = Path(self.config['monitoring']['log_dir'])
        self.archive_dir = self.log_dir / 'archive'
        self.backup_dir = self.log_dir / 'backup'
        
        for directory in [self.log_dir, self.archive_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('monitoring_maintenance')
        logger.setLevel(logging.INFO)
        
        log_dir = Path(self.config['monitoring']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'maintenance.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(handler)
        return logger

    def cleanup_old_logs(self, days: int = None) -> int:
        """Clean up log files older than specified days"""
        if days is None:
            days = self.config['monitoring']['metrics_retention_days']
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        try:
            # Process each log file
            for log_file in self.log_dir.glob('*.log'):
                if self._is_file_old(log_file, cutoff_date):
                    # Archive the log file
                    self._archive_log_file(log_file)
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old log files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {str(e)}")
            raise

    def cleanup_old_metrics(self, days: int = None) -> int:
        """Clean up metrics files older than specified days"""
        if days is None:
            days = self.config['monitoring']['metrics_retention_days']
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        try:
            metrics_dir = self.log_dir / 'metrics'
            if not metrics_dir.exists():
                return 0
            
            # Process each metrics file
            for metrics_file in metrics_dir.glob('metrics_*.json'):
                if self._is_file_old(metrics_file, cutoff_date):
                    # Archive the metrics file
                    self._archive_metrics_file(metrics_file)
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old metrics files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old metrics: {str(e)}")
            raise

    def cleanup_old_reports(self, days: int = None) -> int:
        """Clean up report files older than specified days"""
        if days is None:
            days = self.config['monitoring']['metrics_retention_days']
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        try:
            reports_dir = self.log_dir / 'reports'
            if not reports_dir.exists():
                return 0
            
            # Process each report file
            for report_file in reports_dir.glob('report_*.json'):
                if self._is_file_old(report_file, cutoff_date):
                    # Archive the report file
                    self._archive_report_file(report_file)
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old report files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old reports: {str(e)}")
            raise

    def _is_file_old(self, file_path: Path, cutoff_date: datetime) -> bool:
        """Check if file is older than cutoff date"""
        return datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date

    def _archive_log_file(self, log_file: Path):
        """Archive a log file"""
        try:
            # Create archive filename
            archive_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d')}.gz"
            archive_path = self.archive_dir / archive_name
            
            # Compress and archive
            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            log_file.unlink()
            
            self.logger.info(f"Archived log file: {log_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error archiving log file {log_file.name}: {str(e)}")
            raise

    def _archive_metrics_file(self, metrics_file: Path):
        """Archive a metrics file"""
        try:
            # Create archive filename
            archive_name = f"{metrics_file.stem}_{datetime.now().strftime('%Y%m%d')}.gz"
            archive_path = self.archive_dir / archive_name
            
            # Compress and archive
            with open(metrics_file, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            metrics_file.unlink()
            
            self.logger.info(f"Archived metrics file: {metrics_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error archiving metrics file {metrics_file.name}: {str(e)}")
            raise

    def _archive_report_file(self, report_file: Path):
        """Archive a report file"""
        try:
            # Create archive filename
            archive_name = f"{report_file.stem}_{datetime.now().strftime('%Y%m%d')}.gz"
            archive_path = self.archive_dir / archive_name
            
            # Compress and archive
            with open(report_file, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            report_file.unlink()
            
            self.logger.info(f"Archived report file: {report_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error archiving report file {report_file.name}: {str(e)}")
            raise

    def create_backup(self) -> Path:
        """Create backup of all monitoring data"""
        try:
            # Create backup filename
            backup_name = f"monitoring_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            backup_path = self.backup_dir / backup_name
            
            # Create backup archive
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'gztar',
                self.log_dir,
                '.'
            )
            
            self.logger.info(f"Created backup: {backup_name}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from backup"""
        try:
            # Verify backup file exists
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create temporary directory
            temp_dir = self.log_dir / 'temp_restore'
            temp_dir.mkdir(exist_ok=True)
            
            # Extract backup
            shutil.unpack_archive(str(backup_path), str(temp_dir))
            
            # Remove current files
            for item in self.log_dir.glob('*'):
                if item.name != 'temp_restore':
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            
            # Move restored files
            for item in temp_dir.glob('*'):
                shutil.move(str(item), str(self.log_dir))
            
            # Clean up
            temp_dir.rmdir()
            
            self.logger.info(f"Restored from backup: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {str(e)}")
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def rotate_logs(self):
        """Rotate current log files"""
        try:
            for log_file in self.log_dir.glob('*.log'):
                if log_file.stat().st_size > self.config['logging']['file']['max_size']:
                    # Create rotated filename
                    rotated_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    rotated_path = self.log_dir / rotated_name
                    
                    # Rotate file
                    shutil.move(str(log_file), str(rotated_path))
                    
                    self.logger.info(f"Rotated log file: {log_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error rotating logs: {str(e)}")
            raise

# Example usage
if __name__ == '__main__':
    maintenance = MonitoringMaintenance()
    try:
        # Clean up old files
        maintenance.cleanup_old_logs()
        maintenance.cleanup_old_metrics()
        maintenance.cleanup_old_reports()
        
        # Create backup
        backup_path = maintenance.create_backup()
        
        # Rotate logs
        maintenance.rotate_logs()
        
    except Exception as e:
        print(f"Error: {str(e)}")