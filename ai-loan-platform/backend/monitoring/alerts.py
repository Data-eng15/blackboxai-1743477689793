import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os

class AlertManager:
    def __init__(self, config: Dict[str, str]):
        """Initialize alert manager with configuration"""
        self.config = config
        self.logger = self._setup_logger()
        
        # Initialize notification channels
        self.email_enabled = bool(config.get('SMTP_HOST'))
        self.slack_enabled = bool(config.get('SLACK_WEBHOOK_URL'))
        self.telegram_enabled = bool(config.get('TELEGRAM_BOT_TOKEN'))

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for alerts"""
        logger = logging.getLogger('alerts')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        fh = logging.FileHandler('logs/alerts.log')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def send_email_alert(
        self, 
        subject: str, 
        message: str, 
        recipients: List[str]
    ) -> bool:
        """Send email alert"""
        if not self.email_enabled:
            self.logger.warning("Email notifications not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['SMTP_FROM_EMAIL']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[AI Loan Platform Alert] {subject}"
            
            # Add timestamp to message
            full_message = f"Time: {datetime.now().isoformat()}\n\n{message}"
            msg.attach(MIMEText(full_message, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(
                self.config['SMTP_HOST'], 
                int(self.config['SMTP_PORT'])
            ) as server:
                server.starttls()
                server.login(
                    self.config['SMTP_USERNAME'],
                    self.config['SMTP_PASSWORD']
                )
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def send_slack_alert(
        self, 
        message: str, 
        channel: Optional[str] = None
    ) -> bool:
        """Send Slack alert"""
        if not self.slack_enabled:
            self.logger.warning("Slack notifications not configured")
            return False
        
        try:
            webhook_url = self.config['SLACK_WEBHOOK_URL']
            
            payload = {
                'text': f"🚨 *AI Loan Platform Alert*\n{message}",
                'username': 'AI Loan Platform Monitor'
            }
            
            if channel:
                payload['channel'] = channel
            
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.logger.info("Slack alert sent successfully")
                return True
            else:
                self.logger.error(
                    f"Failed to send Slack alert. Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")
            return False

    def send_telegram_alert(self, message: str, chat_id: str) -> bool:
        """Send Telegram alert"""
        if not self.telegram_enabled:
            self.logger.warning("Telegram notifications not configured")
            return False
        
        try:
            bot_token = self.config['TELEGRAM_BOT_TOKEN']
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': f"🚨 AI Loan Platform Alert\n\n{message}",
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                self.logger.info("Telegram alert sent successfully")
                return True
            else:
                self.logger.error(
                    f"Failed to send Telegram alert. Status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {str(e)}")
            return False

    def send_alert(
        self,
        subject: str,
        message: str,
        severity: str = 'info',
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Send alert through multiple channels"""
        if channels is None:
            channels = ['email', 'slack', 'telegram']
        
        results = {}
        
        # Add severity and timestamp to message
        formatted_message = (
            f"Severity: {severity.upper()}\n"
            f"Time: {datetime.now().isoformat()}\n"
            f"Message: {message}"
        )
        
        # Send through each enabled channel
        if 'email' in channels and self.email_enabled:
            results['email'] = self.send_email_alert(
                subject,
                formatted_message,
                self.config['ALERT_EMAIL_RECIPIENTS'].split(',')
            )
        
        if 'slack' in channels and self.slack_enabled:
            results['slack'] = self.send_slack_alert(formatted_message)
        
        if 'telegram' in channels and self.telegram_enabled:
            results['telegram'] = self.send_telegram_alert(
                formatted_message,
                self.config['TELEGRAM_CHAT_ID']
            )
        
        # Log alert
        self.logger.info(
            f"Alert sent - Subject: {subject}, "
            f"Severity: {severity}, "
            f"Channels: {channels}, "
            f"Results: {results}"
        )
        
        return results

    def send_system_alert(
        self,
        component: str,
        status: str,
        details: str,
        severity: str = 'warning'
    ) -> Dict[str, bool]:
        """Send system-related alert"""
        subject = f"System Alert: {component} - {status}"
        message = (
            f"Component: {component}\n"
            f"Status: {status}\n"
            f"Details: {details}"
        )
        return self.send_alert(subject, message, severity)

    def send_security_alert(
        self,
        event_type: str,
        details: str,
        severity: str = 'high'
    ) -> Dict[str, bool]:
        """Send security-related alert"""
        subject = f"Security Alert: {event_type}"
        message = (
            f"Event Type: {event_type}\n"
            f"Details: {details}"
        )
        return self.send_alert(subject, message, severity)

    def send_performance_alert(
        self,
        metric: str,
        value: float,
        threshold: float,
        details: str
    ) -> Dict[str, bool]:
        """Send performance-related alert"""
        subject = f"Performance Alert: {metric} Threshold Exceeded"
        message = (
            f"Metric: {metric}\n"
            f"Current Value: {value}\n"
            f"Threshold: {threshold}\n"
            f"Details: {details}"
        )
        return self.send_alert(subject, message, 'warning')

def create_alert_manager(config_path: str = None) -> AlertManager:
    """Create an AlertManager instance with configuration"""
    # Default configuration
    config = {
        'SMTP_HOST': os.getenv('SMTP_HOST'),
        'SMTP_PORT': os.getenv('SMTP_PORT', '587'),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'SMTP_FROM_EMAIL': os.getenv('SMTP_FROM_EMAIL'),
        'ALERT_EMAIL_RECIPIENTS': os.getenv('ALERT_EMAIL_RECIPIENTS'),
        'SLACK_WEBHOOK_URL': os.getenv('SLACK_WEBHOOK_URL'),
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID')
    }
    
    # Load configuration from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return AlertManager(config)

# Example usage
if __name__ == '__main__':
    # Create alert manager
    alert_manager = create_alert_manager()
    
    # Send test alerts
    alert_manager.send_system_alert(
        'Database',
        'High Load',
        'Connection pool at 80% capacity'
    )
    
    alert_manager.send_security_alert(
        'Unauthorized Access',
        'Multiple failed login attempts from IP: 192.168.1.100'
    )
    
    alert_manager.send_performance_alert(
        'API Response Time',
        2.5,
        1.0,
        'API endpoint /api/loan/apply experiencing high latency'
    )