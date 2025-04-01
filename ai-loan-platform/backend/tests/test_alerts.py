import pytest
from unittest.mock import patch, MagicMock
from backend.monitoring.alerts import AlertManager, create_alert_manager
import smtplib
import requests
import json
from datetime import datetime

@pytest.fixture
def alert_config():
    """Provide test configuration for alerts"""
    return {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'test_password',
        'SMTP_FROM_EMAIL': 'alerts@example.com',
        'ALERT_EMAIL_RECIPIENTS': 'admin@example.com,support@example.com',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test',
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'TELEGRAM_CHAT_ID': 'test_chat_id'
    }

@pytest.fixture
def alert_manager(alert_config):
    """Provide AlertManager instance"""
    return AlertManager(alert_config)

def test_email_alert(alert_manager):
    """Test sending email alerts"""
    with patch('smtplib.SMTP') as mock_smtp:
        # Configure mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send test alert
        success = alert_manager.send_email_alert(
            'Test Alert',
            'Test message',
            ['test@example.com']
        )
        
        # Verify
        assert success == True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

def test_slack_alert(alert_manager):
    """Test sending Slack alerts"""
    with patch('requests.post') as mock_post:
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send test alert
        success = alert_manager.send_slack_alert('Test message')
        
        # Verify
        assert success == True
        mock_post.assert_called_once()
        assert mock_post.call_args[1]['headers']['Content-Type'] == 'application/json'

def test_telegram_alert(alert_manager):
    """Test sending Telegram alerts"""
    with patch('requests.post') as mock_post:
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send test alert
        success = alert_manager.send_telegram_alert('Test message', 'test_chat_id')
        
        # Verify
        assert success == True
        mock_post.assert_called_once()
        assert 'chat_id' in mock_post.call_args[1]['json']

def test_multi_channel_alert(alert_manager):
    """Test sending alerts through multiple channels"""
    with patch('smtplib.SMTP') as mock_smtp, \
         patch('requests.post') as mock_post:
        # Configure mocks
        mock_smtp_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_server
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send test alert
        results = alert_manager.send_alert(
            'Test Alert',
            'Test message',
            'warning',
            ['email', 'slack', 'telegram']
        )
        
        # Verify
        assert all(results.values())
        assert len(results) == 3
        mock_smtp_server.send_message.assert_called_once()
        assert mock_post.call_count == 2  # Once for Slack, once for Telegram

def test_system_alert(alert_manager):
    """Test sending system alerts"""
    with patch.object(alert_manager, 'send_alert') as mock_send:
        # Send test alert
        alert_manager.send_system_alert(
            'Database',
            'High Load',
            'Connection pool at 80% capacity'
        )
        
        # Verify
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert 'Database' in args[0]
        assert 'High Load' in args[0]
        assert 'Connection pool' in args[1]

def test_security_alert(alert_manager):
    """Test sending security alerts"""
    with patch.object(alert_manager, 'send_alert') as mock_send:
        # Send test alert
        alert_manager.send_security_alert(
            'Unauthorized Access',
            'Multiple failed login attempts'
        )
        
        # Verify
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert 'Security Alert' in args[0]
        assert 'Unauthorized Access' in args[0]
        assert 'failed login attempts' in args[1]

def test_performance_alert(alert_manager):
    """Test sending performance alerts"""
    with patch.object(alert_manager, 'send_alert') as mock_send:
        # Send test alert
        alert_manager.send_performance_alert(
            'API Response Time',
            2.5,
            1.0,
            'High latency detected'
        )
        
        # Verify
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert 'Performance Alert' in args[0]
        assert 'API Response Time' in args[0]
        assert '2.5' in args[1]
        assert '1.0' in args[1]

def test_alert_manager_creation():
    """Test alert manager creation with config"""
    with patch('os.getenv') as mock_getenv:
        # Configure mock
        mock_getenv.side_effect = lambda x, default=None: 'test_value'
        
        # Create alert manager
        manager = create_alert_manager()
        
        # Verify
        assert manager.email_enabled
        assert manager.slack_enabled
        assert manager.telegram_enabled

def test_alert_manager_without_config():
    """Test alert manager creation without config"""
    with patch('os.getenv') as mock_getenv:
        # Configure mock to return None
        mock_getenv.return_value = None
        
        # Create alert manager
        manager = create_alert_manager()
        
        # Verify
        assert not manager.email_enabled
        assert not manager.slack_enabled
        assert not manager.telegram_enabled

def test_alert_logging(alert_manager, tmp_path):
    """Test alert logging functionality"""
    # Configure log file in temporary directory
    log_file = tmp_path / 'alerts.log'
    handler = alert_manager.logger.handlers[0]
    handler.baseFilename = str(log_file)
    
    # Send test alert
    alert_manager.send_alert('Test Alert', 'Test message')
    
    # Verify log file
    assert log_file.exists()
    log_content = log_file.read_text()
    assert 'Test Alert' in log_content
    assert 'INFO' in log_content

def test_failed_email_alert(alert_manager):
    """Test handling of failed email alerts"""
    with patch('smtplib.SMTP') as mock_smtp:
        # Configure mock to raise exception
        mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException
        
        # Send test alert
        success = alert_manager.send_email_alert(
            'Test Alert',
            'Test message',
            ['test@example.com']
        )
        
        # Verify
        assert success == False

def test_failed_slack_alert(alert_manager):
    """Test handling of failed Slack alerts"""
    with patch('requests.post') as mock_post:
        # Configure mock to return error status
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Send test alert
        success = alert_manager.send_slack_alert('Test message')
        
        # Verify
        assert success == False