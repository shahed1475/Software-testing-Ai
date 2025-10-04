"""
Settings Manager

Application-wide settings management with type safety and validation.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Type, get_type_hints
from datetime import datetime
import threading


@dataclass
class Settings:
    """Base settings class with common configuration"""
    
    # Application settings
    app_name: str = "Test Automation Framework"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "detailed"
    log_file_rotation: bool = True
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # API settings
    api_host: str = "localhost"
    api_port: int = 8000
    api_cors_enabled: bool = True
    api_cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_rate_limit: int = 100  # requests per minute
    
    # Database settings
    database_url: str = "sqlite:///test_automation.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    
    # Performance settings
    max_workers: int = 10
    queue_size: int = 1000
    timeout_default: int = 300
    retry_count_default: int = 3
    retry_delay_default: float = 1.0
    
    # Monitoring settings
    monitoring_enabled: bool = True
    monitoring_interval: float = 5.0
    metrics_retention_days: int = 30
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage": 80.0,
        "memory_usage": 85.0,
        "disk_usage": 90.0,
        "error_rate": 5.0
    })
    
    # Scheduler settings
    scheduler_enabled: bool = True
    scheduler_max_concurrent_jobs: int = 5
    scheduler_job_timeout: int = 3600
    scheduler_cleanup_interval: int = 300
    
    # Notification settings
    notifications_enabled: bool = True
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_use_tls: bool = True
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    
    # File storage settings
    storage_base_path: str = "data"
    storage_max_file_size: int = 100 * 1024 * 1024  # 100MB
    storage_cleanup_enabled: bool = True
    storage_retention_days: int = 90
    
    # Test execution settings
    test_timeout_default: int = 1800  # 30 minutes
    test_parallel_execution: bool = True
    test_max_parallel: int = 5
    test_artifact_retention_days: int = 30
    
    # Dashboard settings
    dashboard_enabled: bool = True
    dashboard_auto_refresh: int = 30  # seconds
    dashboard_theme: str = "light"
    dashboard_items_per_page: int = 20
    
    # Integration settings
    ci_cd_integration_enabled: bool = False
    github_token: str = ""
    jenkins_url: str = ""
    jenkins_username: str = ""
    jenkins_token: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary"""
        # Get type hints for validation
        type_hints = get_type_hints(cls)
        
        # Filter data to only include known fields
        filtered_data = {}
        for key, value in data.items():
            if hasattr(cls, key):
                # Basic type conversion
                expected_type = type_hints.get(key)
                if expected_type and not isinstance(value, expected_type):
                    try:
                        if expected_type == bool and isinstance(value, str):
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        elif expected_type in (int, float, str):
                            value = expected_type(value)
                    except (ValueError, TypeError):
                        pass  # Keep original value if conversion fails
                
                filtered_data[key] = value
        
        return cls(**filtered_data)
    
    def validate(self) -> List[str]:
        """Validate settings and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.app_name:
            errors.append("app_name is required")
        
        if not self.secret_key or self.secret_key == "your-secret-key-change-in-production":
            if self.environment == "production":
                errors.append("secret_key must be changed in production")
        
        # Validate numeric ranges
        if self.api_port < 1 or self.api_port > 65535:
            errors.append("api_port must be between 1 and 65535")
        
        if self.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        if self.queue_size < 1:
            errors.append("queue_size must be at least 1")
        
        if self.timeout_default < 1:
            errors.append("timeout_default must be at least 1")
        
        if self.retry_count_default < 0:
            errors.append("retry_count_default must be non-negative")
        
        if self.monitoring_interval <= 0:
            errors.append("monitoring_interval must be positive")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of: {valid_log_levels}")
        
        # Validate environment
        valid_environments = ["development", "testing", "staging", "production"]
        if self.environment not in valid_environments:
            errors.append(f"environment must be one of: {valid_environments}")
        
        # Validate email settings if notifications are enabled
        if self.notifications_enabled and self.email_smtp_server:
            if not self.email_username:
                errors.append("email_username is required when email notifications are enabled")
            if self.email_smtp_port < 1 or self.email_smtp_port > 65535:
                errors.append("email_smtp_port must be between 1 and 65535")
        
        return errors
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "echo": self.database_echo
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "cors_enabled": self.api_cors_enabled,
            "cors_origins": self.api_cors_origins,
            "rate_limit": self.api_rate_limit
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.log_level,
            "format": self.log_format,
            "file_rotation": self.log_file_rotation,
            "max_size": self.log_max_size,
            "backup_count": self.log_backup_count
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return {
            "enabled": self.monitoring_enabled,
            "interval": self.monitoring_interval,
            "retention_days": self.metrics_retention_days,
            "alert_thresholds": self.alert_thresholds
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return {
            "enabled": self.notifications_enabled,
            "email": {
                "smtp_server": self.email_smtp_server,
                "smtp_port": self.email_smtp_port,
                "username": self.email_username,
                "password": self.email_password,
                "use_tls": self.email_use_tls
            },
            "slack": {
                "webhook_url": self.slack_webhook_url
            },
            "teams": {
                "webhook_url": self.teams_webhook_url
            }
        }


class SettingsManager:
    """
    Application-wide settings management system.
    
    Provides centralized settings management with environment-specific overrides,
    validation, and change notifications.
    """
    
    def __init__(self, 
                 settings_file: str = "settings.json",
                 environment: Optional[str] = None,
                 auto_save: bool = True):
        
        self.settings_file = Path(settings_file)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.auto_save = auto_save
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Settings storage
        self._settings: Optional[Settings] = None
        self._change_callbacks: List[callable] = []
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Load settings
        self.load_settings()
    
    def load_settings(self) -> Settings:
        """Load settings from file or create defaults"""
        with self._lock:
            try:
                if self.settings_file.exists():
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Apply environment-specific overrides
                    env_data = data.get('environments', {}).get(self.environment, {})
                    if env_data:
                        # Merge environment-specific settings
                        base_data = data.get('default', {})
                        merged_data = {**base_data, **env_data}
                    else:
                        merged_data = data.get('default', data)
                    
                    self._settings = Settings.from_dict(merged_data)
                    self.logger.info(f"Loaded settings from {self.settings_file}")
                else:
                    # Create default settings
                    self._settings = Settings()
                    self._settings.environment = self.environment
                    
                    if self.auto_save:
                        self.save_settings()
                    
                    self.logger.info("Created default settings")
                
                # Validate settings
                errors = self._settings.validate()
                if errors:
                    self.logger.warning(f"Settings validation errors: {errors}")
                
                # Trigger change callbacks
                self._trigger_change_callbacks()
                
                return self._settings
                
            except Exception as e:
                self.logger.error(f"Error loading settings: {e}")
                # Fall back to defaults
                self._settings = Settings()
                self._settings.environment = self.environment
                return self._settings
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        with self._lock:
            try:
                if not self._settings:
                    return False
                
                # Prepare data structure with environment support
                data = {
                    "default": self._settings.to_dict(),
                    "environments": {
                        "development": {},
                        "testing": {},
                        "staging": {},
                        "production": {}
                    },
                    "metadata": {
                        "last_updated": datetime.now().isoformat(),
                        "version": self._settings.app_version
                    }
                }
                
                # Ensure parent directory exists
                self.settings_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save to file
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Saved settings to {self.settings_file}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving settings: {e}")
                return False
    
    def get_settings(self) -> Settings:
        """Get current settings"""
        with self._lock:
            if not self._settings:
                self.load_settings()
            return self._settings
    
    def update_settings(self, **kwargs) -> bool:
        """Update settings with new values"""
        with self._lock:
            try:
                if not self._settings:
                    self.load_settings()
                
                # Update settings
                for key, value in kwargs.items():
                    if hasattr(self._settings, key):
                        setattr(self._settings, key, value)
                    else:
                        self.logger.warning(f"Unknown setting: {key}")
                
                # Validate updated settings
                errors = self._settings.validate()
                if errors:
                    self.logger.error(f"Settings validation failed: {errors}")
                    return False
                
                # Auto-save if enabled
                if self.auto_save:
                    self.save_settings()
                
                # Trigger change callbacks
                self._trigger_change_callbacks()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating settings: {e}")
                return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get individual setting value"""
        settings = self.get_settings()
        return getattr(settings, key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set individual setting value"""
        return self.update_settings(**{key: value})
    
    def reset_to_defaults(self) -> bool:
        """Reset settings to defaults"""
        with self._lock:
            try:
                self._settings = Settings()
                self._settings.environment = self.environment
                
                if self.auto_save:
                    self.save_settings()
                
                self._trigger_change_callbacks()
                self.logger.info("Reset settings to defaults")
                return True
                
            except Exception as e:
                self.logger.error(f"Error resetting settings: {e}")
                return False
    
    def validate_settings(self) -> List[str]:
        """Validate current settings"""
        settings = self.get_settings()
        return settings.validate()
    
    def export_settings(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export settings as dictionary"""
        settings = self.get_settings()
        data = settings.to_dict()
        
        if not include_sensitive:
            # Remove sensitive information
            sensitive_keys = [
                'secret_key', 'email_password', 'github_token',
                'jenkins_token', 'slack_webhook_url', 'teams_webhook_url'
            ]
            for key in sensitive_keys:
                if key in data:
                    data[key] = "***HIDDEN***"
        
        return data
    
    def import_settings(self, data: Dict[str, Any], validate: bool = True) -> bool:
        """Import settings from dictionary"""
        with self._lock:
            try:
                # Create new settings from data
                new_settings = Settings.from_dict(data)
                
                # Validate if requested
                if validate:
                    errors = new_settings.validate()
                    if errors:
                        self.logger.error(f"Import validation failed: {errors}")
                        return False
                
                # Apply new settings
                self._settings = new_settings
                
                if self.auto_save:
                    self.save_settings()
                
                self._trigger_change_callbacks()
                self.logger.info("Imported settings successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error importing settings: {e}")
                return False
    
    def add_change_callback(self, callback: callable):
        """Add callback for settings changes"""
        with self._lock:
            if callback not in self._change_callbacks:
                self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: callable):
        """Remove settings change callback"""
        with self._lock:
            try:
                self._change_callbacks.remove(callback)
            except ValueError:
                pass
    
    def _trigger_change_callbacks(self):
        """Trigger settings change callbacks"""
        for callback in self._change_callbacks:
            try:
                callback(self._settings)
            except Exception as e:
                self.logger.error(f"Error in settings change callback: {e}")
    
    def get_environment_settings(self) -> Dict[str, Any]:
        """Get environment-specific settings"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return data.get('environments', {}).get(self.environment, {})
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting environment settings: {e}")
            return {}
    
    def set_environment_setting(self, key: str, value: Any) -> bool:
        """Set environment-specific setting"""
        try:
            # Load current file data
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"default": {}, "environments": {}}
            
            # Ensure environment section exists
            if "environments" not in data:
                data["environments"] = {}
            
            if self.environment not in data["environments"]:
                data["environments"][self.environment] = {}
            
            # Set the value
            data["environments"][self.environment][key] = value
            data["metadata"] = {
                "last_updated": datetime.now().isoformat(),
                "version": self.get_setting("app_version", "1.0.0")
            }
            
            # Save back to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Reload settings to apply changes
            self.load_settings()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting environment setting: {e}")
            return False
    
    def get_config_for_component(self, component: str) -> Dict[str, Any]:
        """Get configuration for specific component"""
        settings = self.get_settings()
        
        if component == "database":
            return settings.get_database_config()
        elif component == "api":
            return settings.get_api_config()
        elif component == "logging":
            return settings.get_logging_config()
        elif component == "monitoring":
            return settings.get_monitoring_config()
        elif component == "notifications":
            return settings.get_notification_config()
        else:
            return {}
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def cleanup(self):
        """Cleanup settings manager resources"""
        with self._lock:
            self._change_callbacks.clear()
            self.logger.info("Settings manager cleanup completed")


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_settings() -> Settings:
    """Get current application settings"""
    return get_settings_manager().get_settings()


def update_settings(**kwargs) -> bool:
    """Update application settings"""
    return get_settings_manager().update_settings(**kwargs)


def get_setting(key: str, default: Any = None) -> Any:
    """Get individual setting value"""
    return get_settings_manager().get_setting(key, default)