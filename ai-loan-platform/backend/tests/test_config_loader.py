import pytest
import json
import os
from backend.monitoring.config_loader import ConfigLoader, ConfigurationError, load_monitoring_config

@pytest.fixture
def valid_config():
    """Provide valid configuration data"""
    return {
        "monitoring": {
            "interval": 60,
            "log_dir": "logs",
            "metrics_retention_days": 30,
            "report_interval": 3600,
            "thresholds": {
                "cpu": {
                    "warning": 70,
                    "critical": 85
                },
                "memory": {
                    "warning": 75,
                    "critical": 90
                },
                "disk": {
                    "warning": 80,
                    "critical": 90
                },
                "api_response_time": {
                    "warning": 1.0,
                    "critical": 2.0
                },
                "error_rate": {
                    "warning": 0.01,
                    "critical": 0.05
                },
                "concurrent_users": {
                    "warning": 1000,
                    "critical": 2000
                }
            }
        },
        "alerts": {
            "email": {
                "enabled": True
            }
        },
        "visualization": {
            "enabled": True
        },
        "logging": {
            "level": "INFO"
        },
        "health_checks": {
            "enabled": True
        },
        "metrics_collection": {
            "enabled": True
        }
    }

@pytest.fixture
def config_file(tmp_path, valid_config):
    """Create temporary config file"""
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(valid_config, f)
    return config_path

def test_load_valid_config(config_file):
    """Test loading valid configuration"""
    loader = ConfigLoader(str(config_file))
    config = loader.load_config()
    
    assert config["monitoring"]["interval"] == 60
    assert config["monitoring"]["log_dir"] == "logs"
    assert config["monitoring"]["thresholds"]["cpu"]["warning"] == 70

def test_missing_config_file():
    """Test handling of missing config file"""
    loader = ConfigLoader("/nonexistent/config.json")
    with pytest.raises(ConfigurationError) as exc:
        loader.load_config()
    assert "not found" in str(exc.value)

def test_invalid_json(tmp_path):
    """Test handling of invalid JSON"""
    config_path = tmp_path / "invalid.json"
    with open(config_path, "w") as f:
        f.write("invalid json")
    
    loader = ConfigLoader(str(config_path))
    with pytest.raises(ConfigurationError) as exc:
        loader.load_config()
    assert "Invalid JSON" in str(exc.value)

def test_invalid_threshold_values(config_file, valid_config):
    """Test validation of threshold values"""
    # Modify config to have invalid thresholds
    valid_config["monitoring"]["thresholds"]["cpu"]["warning"] = 90
    valid_config["monitoring"]["thresholds"]["cpu"]["critical"] = 80
    
    with open(config_file, "w") as f:
        json.dump(valid_config, f)
    
    loader = ConfigLoader(str(config_file))
    with pytest.raises(ConfigurationError) as exc:
        loader.load_config()
    assert "Warning threshold must be less than critical" in str(exc.value)

def test_invalid_interval_values(config_file, valid_config):
    """Test validation of interval values"""
    valid_config["monitoring"]["interval"] = -1
    
    with open(config_file, "w") as f:
        json.dump(valid_config, f)
    
    loader = ConfigLoader(str(config_file))
    with pytest.raises(ConfigurationError) as exc:
        loader.load_config()
    assert "must be positive" in str(exc.value)

def test_environment_variable_substitution(config_file, valid_config, monkeypatch):
    """Test environment variable substitution"""
    # Add environment variable reference
    valid_config["alerts"]["email"]["password"] = "${EMAIL_PASSWORD}"
    monkeypatch.setenv("EMAIL_PASSWORD", "secret123")
    
    with open(config_file, "w") as f:
        json.dump(valid_config, f)
    
    loader = ConfigLoader(str(config_file))
    config = loader.load_config()
    assert config["alerts"]["email"]["password"] == "secret123"

def test_missing_environment_variable(config_file, valid_config):
    """Test handling of missing environment variable"""
    valid_config["alerts"]["email"]["password"] = "${NONEXISTENT_VAR}"
    
    with open(config_file, "w") as f:
        json.dump(valid_config, f)
    
    loader = ConfigLoader(str(config_file))
    with pytest.raises(ConfigurationError) as exc:
        loader.load_config()
    assert "Environment variable not found" in str(exc.value)

def test_get_value(config_file, valid_config):
    """Test getting configuration values"""
    loader = ConfigLoader(str(config_file))
    loader.load_config()
    
    assert loader.get_value("monitoring", "interval") == 60
    assert loader.get_value("nonexistent", default="default") == "default"
    assert loader.get_value("monitoring", "thresholds", "cpu", "warning") == 70

def test_update_config(config_file, valid_config):
    """Test updating configuration"""
    loader = ConfigLoader(str(config_file))
    loader.load_config()
    
    updates = {
        "monitoring": {
            "interval": 120
        }
    }
    
    loader.update_config(updates)
    assert loader.get_value("monitoring", "interval") == 120
    
    # Verify file was updated
    with open(config_file) as f:
        saved_config = json.load(f)
    assert saved_config["monitoring"]["interval"] == 120

def test_create_log_directory(tmp_path, valid_config):
    """Test creation of log directory"""
    config_path = tmp_path / "config.json"
    log_dir = tmp_path / "custom_logs"
    valid_config["monitoring"]["log_dir"] = str(log_dir)
    
    with open(config_path, "w") as f:
        json.dump(valid_config, f)
    
    loader = ConfigLoader(str(config_path))
    loader.load_config()
    
    assert log_dir.exists()
    assert log_dir.is_dir()

def test_helper_function(config_file):
    """Test helper function for loading config"""
    config = load_monitoring_config(str(config_file))
    assert config["monitoring"]["interval"] == 60

def test_deep_update(config_file, valid_config):
    """Test deep update of nested configuration"""
    loader = ConfigLoader(str(config_file))
    loader.load_config()
    
    updates = {
        "monitoring": {
            "thresholds": {
                "cpu": {
                    "warning": 60
                }
            }
        }
    }
    
    loader.update_config(updates)
    assert loader.get_value("monitoring", "thresholds", "cpu", "warning") == 60
    assert loader.get_value("monitoring", "thresholds", "cpu", "critical") == 85  # Unchanged