"""
Environment Manager

Environment-specific configuration management for different deployment environments.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import yaml


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    
    name: str
    description: str = ""
    is_production: bool = False
    
    # Database configuration
    database_url: str = ""
    database_pool_size: int = 10
    database_echo: bool = False
    
    # API configuration
    api_host: str = "localhost"
    api_port: int = 8000
    api_debug: bool = True
    api_cors_origins: List[str] = field(default_factory=list)
    
    # Security configuration
    secret_key: str = ""
    jwt_secret: str = ""
    encryption_key: str = ""
    
    # External service URLs
    redis_url: str = ""
    elasticsearch_url: str = ""
    message_queue_url: str = ""
    
    # Logging configuration
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = ""
    
    # Monitoring configuration
    monitoring_enabled: bool = True
    metrics_endpoint: str = ""
    tracing_enabled: bool = False
    
    # Notification configuration
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    
    # CI/CD integration
    github_token: str = ""
    jenkins_url: str = ""
    jenkins_username: str = ""
    jenkins_token: str = ""
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=dict)
    
    # Custom environment variables
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    # Resource limits
    max_workers: int = 10
    memory_limit_mb: int = 1024
    cpu_limit_percent: int = 80
    
    # Storage configuration
    storage_path: str = "data"
    temp_path: str = "temp"
    backup_path: str = "backups"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentConfig':
        """Create from dictionary"""
        # Handle missing fields gracefully
        filtered_data = {}
        for key, value in data.items():
            if hasattr(cls, key):
                filtered_data[key] = value
        
        return cls(**filtered_data)
    
    def validate(self) -> List[str]:
        """Validate environment configuration"""
        errors = []
        
        if not self.name:
            errors.append("Environment name is required")
        
        if self.is_production:
            # Production-specific validations
            if not self.secret_key or self.secret_key == "change-me":
                errors.append("Production environment requires a secure secret key")
            
            if not self.database_url:
                errors.append("Production environment requires database URL")
            
            if self.api_debug:
                errors.append("Debug mode should be disabled in production")
            
            if self.log_level == "DEBUG":
                errors.append("Debug logging should be disabled in production")
        
        # Validate ports
        if self.api_port < 1 or self.api_port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        if self.email_smtp_port < 1 or self.email_smtp_port > 65535:
            errors.append("SMTP port must be between 1 and 65535")
        
        # Validate resource limits
        if self.max_workers < 1:
            errors.append("Max workers must be at least 1")
        
        if self.memory_limit_mb < 128:
            errors.append("Memory limit must be at least 128MB")
        
        if self.cpu_limit_percent < 1 or self.cpu_limit_percent > 100:
            errors.append("CPU limit must be between 1 and 100 percent")
        
        return errors
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "echo": self.database_echo
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "debug": self.api_debug,
            "cors_origins": self.api_cors_origins
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.log_level,
            "to_file": self.log_to_file,
            "file_path": self.log_file_path
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return {
            "email": {
                "smtp_server": self.email_smtp_server,
                "smtp_port": self.email_smtp_port,
                "username": self.email_username,
                "password": self.email_password
            },
            "slack": {
                "webhook_url": self.slack_webhook_url
            },
            "teams": {
                "webhook_url": self.teams_webhook_url
            }
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature_name, False)
    
    def enable_feature(self, feature_name: str):
        """Enable a feature"""
        self.features[feature_name] = True
    
    def disable_feature(self, feature_name: str):
        """Disable a feature"""
        self.features[feature_name] = False


class EnvironmentManager:
    """
    Environment-specific configuration management.
    
    Manages different deployment environments (development, testing, staging, production)
    with their specific configurations and settings.
    """
    
    def __init__(self, 
                 config_dir: str = "config/environments",
                 current_environment: Optional[str] = None):
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine current environment
        self.current_environment = (
            current_environment or 
            os.getenv("ENVIRONMENT") or 
            os.getenv("ENV") or 
            "development"
        )
        
        # Environment storage
        self.environments: Dict[str, EnvironmentConfig] = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Load environments
        self._load_environments()
        
        # Create default environments if none exist
        if not self.environments:
            self._create_default_environments()
    
    def _load_environments(self):
        """Load all environment configurations"""
        for config_file in self.config_dir.glob("*.json"):
            try:
                env_name = config_file.stem
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                env_config = EnvironmentConfig.from_dict(data)
                self.environments[env_name] = env_config
                
                self.logger.info(f"Loaded environment configuration: {env_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading environment {config_file}: {e}")
        
        # Also try YAML files
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                env_name = config_file.stem
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                env_config = EnvironmentConfig.from_dict(data)
                self.environments[env_name] = env_config
                
                self.logger.info(f"Loaded environment configuration: {env_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading environment {config_file}: {e}")
    
    def _create_default_environments(self):
        """Create default environment configurations"""
        
        # Development environment
        dev_config = EnvironmentConfig(
            name="development",
            description="Development environment",
            is_production=False,
            database_url="sqlite:///dev_test_automation.db",
            api_host="localhost",
            api_port=8000,
            api_debug=True,
            api_cors_origins=["*"],
            secret_key="dev-secret-key",
            log_level="DEBUG",
            log_to_file=True,
            log_file_path="logs/development.log",
            monitoring_enabled=True,
            features={
                "debug_mode": True,
                "hot_reload": True,
                "test_data": True
            },
            max_workers=5,
            memory_limit_mb=512,
            storage_path="data/dev",
            temp_path="temp/dev"
        )
        
        # Testing environment
        test_config = EnvironmentConfig(
            name="testing",
            description="Testing environment",
            is_production=False,
            database_url="sqlite:///test_test_automation.db",
            api_host="localhost",
            api_port=8001,
            api_debug=True,
            api_cors_origins=["*"],
            secret_key="test-secret-key",
            log_level="INFO",
            log_to_file=True,
            log_file_path="logs/testing.log",
            monitoring_enabled=True,
            features={
                "debug_mode": False,
                "test_data": True,
                "mock_services": True
            },
            max_workers=3,
            memory_limit_mb=256,
            storage_path="data/test",
            temp_path="temp/test"
        )
        
        # Staging environment
        staging_config = EnvironmentConfig(
            name="staging",
            description="Staging environment",
            is_production=False,
            database_url="postgresql://user:pass@staging-db:5432/test_automation",
            api_host="0.0.0.0",
            api_port=8000,
            api_debug=False,
            api_cors_origins=["https://staging.example.com"],
            secret_key="staging-secret-key-change-me",
            log_level="INFO",
            log_to_file=True,
            log_file_path="logs/staging.log",
            monitoring_enabled=True,
            tracing_enabled=True,
            features={
                "debug_mode": False,
                "test_data": False,
                "performance_monitoring": True
            },
            max_workers=8,
            memory_limit_mb=1024,
            storage_path="data/staging",
            temp_path="temp/staging"
        )
        
        # Production environment
        prod_config = EnvironmentConfig(
            name="production",
            description="Production environment",
            is_production=True,
            database_url="postgresql://user:pass@prod-db:5432/test_automation",
            api_host="0.0.0.0",
            api_port=8000,
            api_debug=False,
            api_cors_origins=["https://app.example.com"],
            secret_key="production-secret-key-change-me",
            log_level="WARNING",
            log_to_file=True,
            log_file_path="logs/production.log",
            monitoring_enabled=True,
            tracing_enabled=True,
            features={
                "debug_mode": False,
                "test_data": False,
                "performance_monitoring": True,
                "security_hardening": True
            },
            max_workers=20,
            memory_limit_mb=2048,
            cpu_limit_percent=70,
            storage_path="data/production",
            temp_path="temp/production",
            backup_path="backups/production"
        )
        
        # Save default environments
        self.environments["development"] = dev_config
        self.environments["testing"] = test_config
        self.environments["staging"] = staging_config
        self.environments["production"] = prod_config
        
        # Save to files
        for env_name, env_config in self.environments.items():
            self.save_environment(env_name, env_config)
        
        self.logger.info("Created default environment configurations")
    
    def get_environment(self, env_name: Optional[str] = None) -> Optional[EnvironmentConfig]:
        """Get environment configuration"""
        env_name = env_name or self.current_environment
        return self.environments.get(env_name)
    
    def get_current_environment(self) -> Optional[EnvironmentConfig]:
        """Get current environment configuration"""
        return self.get_environment(self.current_environment)
    
    def set_current_environment(self, env_name: str) -> bool:
        """Set current environment"""
        if env_name in self.environments:
            self.current_environment = env_name
            self.logger.info(f"Switched to environment: {env_name}")
            return True
        else:
            self.logger.error(f"Environment not found: {env_name}")
            return False
    
    def list_environments(self) -> List[str]:
        """List all available environments"""
        return list(self.environments.keys())
    
    def create_environment(self, env_name: str, config: EnvironmentConfig) -> bool:
        """Create new environment"""
        try:
            # Validate configuration
            errors = config.validate()
            if errors:
                self.logger.error(f"Environment validation failed: {errors}")
                return False
            
            # Set name
            config.name = env_name
            
            # Store in memory
            self.environments[env_name] = config
            
            # Save to file
            return self.save_environment(env_name, config)
            
        except Exception as e:
            self.logger.error(f"Error creating environment {env_name}: {e}")
            return False
    
    def update_environment(self, env_name: str, updates: Dict[str, Any]) -> bool:
        """Update environment configuration"""
        try:
            if env_name not in self.environments:
                self.logger.error(f"Environment not found: {env_name}")
                return False
            
            # Get current config
            current_config = self.environments[env_name]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(current_config, key):
                    setattr(current_config, key, value)
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")
            
            # Validate updated configuration
            errors = current_config.validate()
            if errors:
                self.logger.error(f"Environment validation failed: {errors}")
                return False
            
            # Save updated configuration
            return self.save_environment(env_name, current_config)
            
        except Exception as e:
            self.logger.error(f"Error updating environment {env_name}: {e}")
            return False
    
    def delete_environment(self, env_name: str) -> bool:
        """Delete environment configuration"""
        try:
            if env_name == self.current_environment:
                self.logger.error("Cannot delete current environment")
                return False
            
            if env_name not in self.environments:
                self.logger.error(f"Environment not found: {env_name}")
                return False
            
            # Remove from memory
            del self.environments[env_name]
            
            # Remove file
            config_file = self.config_dir / f"{env_name}.json"
            if config_file.exists():
                config_file.unlink()
            
            yaml_file = self.config_dir / f"{env_name}.yaml"
            if yaml_file.exists():
                yaml_file.unlink()
            
            self.logger.info(f"Deleted environment: {env_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting environment {env_name}: {e}")
            return False
    
    def save_environment(self, env_name: str, config: EnvironmentConfig) -> bool:
        """Save environment configuration to file"""
        try:
            config_file = self.config_dir / f"{env_name}.json"
            
            data = config.to_dict()
            data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved environment configuration: {env_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving environment {env_name}: {e}")
            return False
    
    def validate_environment(self, env_name: str) -> List[str]:
        """Validate environment configuration"""
        if env_name not in self.environments:
            return [f"Environment not found: {env_name}"]
        
        return self.environments[env_name].validate()
    
    def validate_all_environments(self) -> Dict[str, List[str]]:
        """Validate all environment configurations"""
        results = {}
        for env_name in self.environments:
            results[env_name] = self.validate_environment(env_name)
        return results
    
    def export_environment(self, env_name: str, include_sensitive: bool = False) -> Optional[Dict[str, Any]]:
        """Export environment configuration"""
        if env_name not in self.environments:
            return None
        
        config = self.environments[env_name]
        data = config.to_dict()
        
        if not include_sensitive:
            # Remove sensitive information
            sensitive_keys = [
                'secret_key', 'jwt_secret', 'encryption_key',
                'email_password', 'github_token', 'jenkins_token'
            ]
            for key in sensitive_keys:
                if key in data:
                    data[key] = "***HIDDEN***"
        
        return data
    
    def import_environment(self, env_name: str, data: Dict[str, Any], 
                          validate: bool = True) -> bool:
        """Import environment configuration"""
        try:
            config = EnvironmentConfig.from_dict(data)
            config.name = env_name
            
            if validate:
                errors = config.validate()
                if errors:
                    self.logger.error(f"Import validation failed: {errors}")
                    return False
            
            self.environments[env_name] = config
            return self.save_environment(env_name, config)
            
        except Exception as e:
            self.logger.error(f"Error importing environment {env_name}: {e}")
            return False
    
    def clone_environment(self, source_env: str, target_env: str) -> bool:
        """Clone environment configuration"""
        if source_env not in self.environments:
            self.logger.error(f"Source environment not found: {source_env}")
            return False
        
        if target_env in self.environments:
            self.logger.error(f"Target environment already exists: {target_env}")
            return False
        
        try:
            # Clone configuration
            source_config = self.environments[source_env]
            target_config = EnvironmentConfig.from_dict(source_config.to_dict())
            target_config.name = target_env
            target_config.description = f"Cloned from {source_env}"
            
            # Create new environment
            return self.create_environment(target_env, target_config)
            
        except Exception as e:
            self.logger.error(f"Error cloning environment {source_env} to {target_env}: {e}")
            return False
    
    def get_environment_variables(self, env_name: Optional[str] = None) -> Dict[str, str]:
        """Get environment variables for environment"""
        env_config = self.get_environment(env_name)
        if not env_config:
            return {}
        
        env_vars = {
            "ENVIRONMENT": env_config.name,
            "DATABASE_URL": env_config.database_url,
            "API_HOST": env_config.api_host,
            "API_PORT": str(env_config.api_port),
            "LOG_LEVEL": env_config.log_level,
            "SECRET_KEY": env_config.secret_key,
        }
        
        # Add custom environment variables
        env_vars.update(env_config.env_vars)
        
        return env_vars
    
    def apply_environment_variables(self, env_name: Optional[str] = None):
        """Apply environment variables to current process"""
        env_vars = self.get_environment_variables(env_name)
        
        for key, value in env_vars.items():
            if value:  # Only set non-empty values
                os.environ[key] = value
        
        self.logger.info(f"Applied environment variables for: {env_name or self.current_environment}")
    
    def get_config_for_component(self, component: str, env_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for specific component"""
        env_config = self.get_environment(env_name)
        if not env_config:
            return {}
        
        if component == "database":
            return env_config.get_database_config()
        elif component == "api":
            return env_config.get_api_config()
        elif component == "logging":
            return env_config.get_logging_config()
        elif component == "notifications":
            return env_config.get_notification_config()
        else:
            return {}
    
    def is_production_environment(self, env_name: Optional[str] = None) -> bool:
        """Check if environment is production"""
        env_config = self.get_environment(env_name)
        return env_config.is_production if env_config else False
    
    def is_feature_enabled(self, feature_name: str, env_name: Optional[str] = None) -> bool:
        """Check if feature is enabled in environment"""
        env_config = self.get_environment(env_name)
        return env_config.is_feature_enabled(feature_name) if env_config else False
    
    def cleanup(self):
        """Cleanup environment manager resources"""
        self.environments.clear()
        self.logger.info("Environment manager cleanup completed")


# Global environment manager instance
_environment_manager: Optional[EnvironmentManager] = None


def get_environment_manager() -> EnvironmentManager:
    """Get global environment manager instance"""
    global _environment_manager
    if _environment_manager is None:
        _environment_manager = EnvironmentManager()
    return _environment_manager


def get_current_environment() -> Optional[EnvironmentConfig]:
    """Get current environment configuration"""
    return get_environment_manager().get_current_environment()


def get_environment_config(component: str) -> Dict[str, Any]:
    """Get environment configuration for component"""
    return get_environment_manager().get_config_for_component(component)


def is_production() -> bool:
    """Check if running in production environment"""
    return get_environment_manager().is_production_environment()


def is_feature_enabled(feature_name: str) -> bool:
    """Check if feature is enabled in current environment"""
    return get_environment_manager().is_feature_enabled(feature_name)