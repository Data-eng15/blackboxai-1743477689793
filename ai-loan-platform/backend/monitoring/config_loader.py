import json
import os
import jsonschema
from typing import Dict, Any, Optional
from pathlib import Path

# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["monitoring", "alerts", "visualization", "logging", "health_checks", "metrics_collection"],
    "properties": {
        "monitoring": {
            "type": "object",
            "required": ["interval", "log_dir", "metrics_retention_days", "report_interval", "thresholds"],
            "properties": {
                "interval": {"type": "integer", "minimum": 1},
                "log_dir": {"type": "string"},
                "metrics_retention_days": {"type": "integer", "minimum": 1},
                "report_interval": {"type": "integer", "minimum": 1},
                "thresholds": {
                    "type": "object",
                    "required": ["cpu", "memory", "disk", "api_response_time", "error_rate", "concurrent_users"],
                    "properties": {
                        "cpu": {
                            "type": "object",
                            "required": ["warning", "critical"],
                            "properties": {
                                "warning": {"type": "number", "minimum": 0, "maximum": 100},
                                "critical": {"type": "number", "minimum": 0, "maximum": 100}
                            }
                        }
                    }
                }
            }
        }
    }
}

class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass

class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader with optional path"""
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__),
            'config.json'
        )
        self.config = {}

    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        try:
            # Load configuration file
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Validate configuration
            self._validate_config()
            
            # Process environment variables
            self._process_env_vars()
            
            return self.config
            
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}")
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")

    def _validate_config(self):
        """Validate configuration against schema"""
        jsonschema.validate(instance=self.config, schema=CONFIG_SCHEMA)
        
        # Additional custom validations
        self._validate_thresholds()
        self._validate_intervals()
        self._validate_paths()

    def _validate_thresholds(self):
        """Validate threshold values"""
        thresholds = self.config['monitoring']['thresholds']
        
        for metric, values in thresholds.items():
            if 'warning' in values and 'critical' in values:
                if values['warning'] >= values['critical']:
                    raise ConfigurationError(
                        f"Warning threshold must be less than critical for {metric}"
                    )

    def _validate_intervals(self):
        """Validate monitoring intervals"""
        intervals = [
            self.config['monitoring']['interval'],
            self.config['monitoring']['report_interval']
        ]
        
        for interval in intervals:
            if interval <= 0:
                raise ConfigurationError("Intervals must be positive integers")

    def _validate_paths(self):
        """Validate and create required directories"""
        log_dir = self.config['monitoring']['log_dir']
        
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to create log directory: {str(e)}")

    def _process_env_vars(self):
        """Process environment variables in configuration"""
        def process_value(value):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value is None:
                    raise ConfigurationError(f"Environment variable not found: {env_var}")
                return env_value
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value
        
        self.config = process_value(self.config)

    def get_value(self, *keys: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
        
        deep_update(self.config, updates)
        self._validate_config()
        
        # Save updated configuration
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

def load_monitoring_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Helper function to load monitoring configuration"""
    loader = ConfigLoader(config_path)
    return loader.load_config()

# Example usage
if __name__ == '__main__':
    try:
        # Load configuration
        config = load_monitoring_config()
        print("Configuration loaded successfully")
        
        # Access configuration values
        monitoring_interval = config['monitoring']['interval']
        print(f"Monitoring interval: {monitoring_interval} seconds")
        
        # Update configuration
        updates = {
            'monitoring': {
                'interval': 120
            }
        }
        
        loader = ConfigLoader()
        loader.load_config()
        loader.update_config(updates)
        print("Configuration updated successfully")
        
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")