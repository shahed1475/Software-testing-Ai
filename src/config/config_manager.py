"""
Configuration Manager

Comprehensive configuration management system for the test automation framework.
"""

import json
import logging
import os
import yaml
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Type, Callable
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Callable] = field(default_factory=dict)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        try:
            # JSON Schema validation
            if self.schema:
                validate(instance=config, schema=self.schema)
            
            # Check required fields
            for field_name in self.required_fields:
                if field_name not in config:
                    raise ConfigValidationError(f"Required field '{field_name}' is missing")
            
            # Custom validation rules
            for field_name, validator in self.validation_rules.items():
                if field_name in config:
                    if not validator(config[field_name]):
                        raise ConfigValidationError(f"Validation failed for field '{field_name}'")
            
            return True
            
        except ValidationError as e:
            raise ConfigValidationError(f"Schema validation failed: {e.message}")
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation error: {e}")
    
    def apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to configuration"""
        result = deepcopy(config)
        
        for key, default_value in self.default_values.items():
            if key not in result:
                result[key] = deepcopy(default_value)
        
        return result


class ConfigManager:
    """
    Comprehensive configuration management system.
    
    Supports multiple formats (JSON, YAML), validation, environment-specific configs,
    and dynamic configuration updates.
    """
    
    def __init__(self, 
                 config_dir: str = "config",
                 environment: str = "development",
                 auto_reload: bool = True,
                 backup_configs: bool = True):
        
        self.config_dir = Path(config_dir)
        self.environment = environment
        self.auto_reload = auto_reload
        self.backup_configs = backup_configs
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration storage
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        self.file_timestamps: Dict[str, float] = {}
        
        # Change callbacks
        self.change_callbacks: Dict[str, List[Callable]] = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Load built-in schemas
        self._load_builtin_schemas()
        
        # Load existing configurations
        self._load_all_configs()
    
    def _load_builtin_schemas(self):
        """Load built-in configuration schemas"""
        
        # Agent configuration schema
        agent_schema = ConfigSchema(
            name="agent",
            description="Agent configuration schema",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "description": {"type": "string"},
                    "timeout": {"type": "number", "minimum": 0},
                    "retry_count": {"type": "integer", "minimum": 0},
                    "retry_delay": {"type": "number", "minimum": 0},
                    "enabled": {"type": "boolean"},
                    "config": {"type": "object"}
                },
                "required": ["name"]
            },
            required_fields=["name"],
            default_values={
                "timeout": 300,
                "retry_count": 3,
                "retry_delay": 1.0,
                "enabled": True,
                "config": {}
            }
        )
        
        # Workflow configuration schema
        workflow_schema = ConfigSchema(
            name="workflow",
            description="Workflow configuration schema",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "description": {"type": "string"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "agent": {"type": "string"},
                                "config": {"type": "object"},
                                "depends_on": {"type": "array", "items": {"type": "string"}},
                                "timeout": {"type": "number"},
                                "retry_count": {"type": "integer"}
                            },
                            "required": ["name", "agent"]
                        }
                    },
                    "schedule": {"type": "object"},
                    "notifications": {"type": "object"},
                    "enabled": {"type": "boolean"}
                },
                "required": ["name", "steps"]
            },
            required_fields=["name", "steps"],
            default_values={
                "enabled": True,
                "schedule": {},
                "notifications": {}
            }
        )
        
        # System configuration schema
        system_schema = ConfigSchema(
            name="system",
            description="System configuration schema",
            schema={
                "type": "object",
                "properties": {
                    "logging": {"type": "object"},
                    "monitoring": {"type": "object"},
                    "database": {"type": "object"},
                    "api": {"type": "object"},
                    "security": {"type": "object"},
                    "performance": {"type": "object"}
                }
            },
            default_values={
                "logging": {
                    "level": "INFO",
                    "format": "detailed",
                    "file_rotation": True
                },
                "monitoring": {
                    "enabled": True,
                    "interval": 5.0,
                    "retention_days": 30
                },
                "api": {
                    "host": "localhost",
                    "port": 8000,
                    "cors_enabled": True
                },
                "performance": {
                    "max_workers": 10,
                    "queue_size": 1000
                }
            }
        )
        
        # Scheduler configuration schema
        scheduler_schema = ConfigSchema(
            name="scheduler",
            description="Scheduler configuration schema",
            schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "max_concurrent_jobs": {"type": "integer", "minimum": 1},
                    "job_timeout": {"type": "number", "minimum": 0},
                    "cleanup_interval": {"type": "number", "minimum": 0},
                    "persistence": {"type": "object"}
                }
            },
            default_values={
                "enabled": True,
                "max_concurrent_jobs": 5,
                "job_timeout": 3600,
                "cleanup_interval": 300,
                "persistence": {
                    "enabled": True,
                    "file": "scheduler_data.json"
                }
            }
        )
        
        # Register schemas
        self.register_schema(agent_schema)
        self.register_schema(workflow_schema)
        self.register_schema(system_schema)
        self.register_schema(scheduler_schema)
    
    def register_schema(self, schema: ConfigSchema):
        """Register a configuration schema"""
        self.schemas[schema.name] = schema
        self.logger.info(f"Registered configuration schema: {schema.name}")
    
    def get_schema(self, schema_name: str) -> Optional[ConfigSchema]:
        """Get configuration schema by name"""
        return self.schemas.get(schema_name)
    
    def list_schemas(self) -> List[str]:
        """List all registered schema names"""
        return list(self.schemas.keys())
    
    def load_config(self, config_name: str, schema_name: Optional[str] = None,
                   validate: bool = True) -> Dict[str, Any]:
        """Load configuration from file"""
        
        # Try different file extensions
        config_file = None
        for ext in ['.json', '.yaml', '.yml']:
            potential_file = self.config_dir / f"{config_name}{ext}"
            if potential_file.exists():
                config_file = potential_file
                break
        
        # Try environment-specific config
        if not config_file:
            for ext in ['.json', '.yaml', '.yml']:
                potential_file = self.config_dir / f"{config_name}.{self.environment}{ext}"
                if potential_file.exists():
                    config_file = potential_file
                    break
        
        if not config_file:
            raise FileNotFoundError(f"Configuration file not found: {config_name}")
        
        # Load configuration
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Store file timestamp for auto-reload
            self.file_timestamps[config_name] = config_file.stat().st_mtime
            
            # Apply schema defaults if schema is specified
            if schema_name and schema_name in self.schemas:
                schema = self.schemas[schema_name]
                config_data = schema.apply_defaults(config_data)
                
                # Validate if requested
                if validate:
                    schema.validate_config(config_data)
            
            # Store in memory
            self.configs[config_name] = config_data
            
            self.logger.info(f"Loaded configuration: {config_name} from {config_file}")
            
            # Trigger change callbacks
            self._trigger_change_callbacks(config_name, config_data)
            
            return deepcopy(config_data)
            
        except Exception as e:
            self.logger.error(f"Error loading configuration {config_name}: {e}")
            raise ConfigValidationError(f"Failed to load configuration {config_name}: {e}")
    
    def save_config(self, config_name: str, config_data: Dict[str, Any],
                   schema_name: Optional[str] = None, format: str = 'json',
                   validate: bool = True) -> bool:
        """Save configuration to file"""
        
        try:
            # Validate if schema is specified
            if validate and schema_name and schema_name in self.schemas:
                schema = self.schemas[schema_name]
                schema.validate_config(config_data)
            
            # Determine file path
            if format.lower() in ['yaml', 'yml']:
                config_file = self.config_dir / f"{config_name}.yaml"
            else:
                config_file = self.config_dir / f"{config_name}.json"
            
            # Backup existing file if enabled
            if self.backup_configs and config_file.exists():
                backup_file = config_file.with_suffix(f"{config_file.suffix}.backup")
                config_file.rename(backup_file)
            
            # Save configuration
            with open(config_file, 'w', encoding='utf-8') as f:
                if format.lower() in ['yaml', 'yml']:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Update in-memory storage
            self.configs[config_name] = deepcopy(config_data)
            self.file_timestamps[config_name] = config_file.stat().st_mtime
            
            self.logger.info(f"Saved configuration: {config_name} to {config_file}")
            
            # Trigger change callbacks
            self._trigger_change_callbacks(config_name, config_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration {config_name}: {e}")
            return False
    
    def get_config(self, config_name: str, reload_if_changed: bool = None) -> Optional[Dict[str, Any]]:
        """Get configuration from memory or load if not present"""
        
        # Use instance setting if not specified
        if reload_if_changed is None:
            reload_if_changed = self.auto_reload
        
        # Check if file has changed and reload if needed
        if reload_if_changed and config_name in self.file_timestamps:
            try:
                config_file = self._find_config_file(config_name)
                if config_file and config_file.exists():
                    current_mtime = config_file.stat().st_mtime
                    if current_mtime > self.file_timestamps[config_name]:
                        self.logger.info(f"Configuration file changed, reloading: {config_name}")
                        return self.load_config(config_name)
            except Exception as e:
                self.logger.error(f"Error checking file timestamp for {config_name}: {e}")
        
        # Return from memory if available
        if config_name in self.configs:
            return deepcopy(self.configs[config_name])
        
        # Try to load if not in memory
        try:
            return self.load_config(config_name)
        except Exception:
            return None
    
    def _find_config_file(self, config_name: str) -> Optional[Path]:
        """Find configuration file for given name"""
        for ext in ['.json', '.yaml', '.yml']:
            # Try regular name
            config_file = self.config_dir / f"{config_name}{ext}"
            if config_file.exists():
                return config_file
            
            # Try environment-specific name
            config_file = self.config_dir / f"{config_name}.{self.environment}{ext}"
            if config_file.exists():
                return config_file
        
        return None
    
    def update_config(self, config_name: str, updates: Dict[str, Any],
                     merge: bool = True, validate: bool = True) -> bool:
        """Update configuration with new values"""
        
        try:
            # Get current config
            current_config = self.get_config(config_name)
            if current_config is None:
                current_config = {}
            
            # Apply updates
            if merge:
                updated_config = self._deep_merge(current_config, updates)
            else:
                updated_config = updates
            
            # Save updated configuration
            return self.save_config(config_name, updated_config, validate=validate)
            
        except Exception as e:
            self.logger.error(f"Error updating configuration {config_name}: {e}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = deepcopy(base)
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def delete_config(self, config_name: str) -> bool:
        """Delete configuration"""
        try:
            # Remove from memory
            if config_name in self.configs:
                del self.configs[config_name]
            
            if config_name in self.file_timestamps:
                del self.file_timestamps[config_name]
            
            # Remove file
            config_file = self._find_config_file(config_name)
            if config_file and config_file.exists():
                if self.backup_configs:
                    backup_file = config_file.with_suffix(f"{config_file.suffix}.deleted")
                    config_file.rename(backup_file)
                else:
                    config_file.unlink()
            
            self.logger.info(f"Deleted configuration: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting configuration {config_name}: {e}")
            return False
    
    def list_configs(self) -> List[str]:
        """List all available configurations"""
        configs = set()
        
        # From memory
        configs.update(self.configs.keys())
        
        # From files
        for ext in ['.json', '.yaml', '.yml']:
            for config_file in self.config_dir.glob(f"*{ext}"):
                name = config_file.stem
                # Remove environment suffix if present
                if f".{self.environment}" in name:
                    name = name.replace(f".{self.environment}", "")
                configs.add(name)
        
        return sorted(list(configs))
    
    def _load_all_configs(self):
        """Load all existing configurations"""
        for config_name in self.list_configs():
            try:
                self.load_config(config_name, validate=False)
            except Exception as e:
                self.logger.warning(f"Failed to load configuration {config_name}: {e}")
    
    def validate_all_configs(self) -> Dict[str, Union[bool, str]]:
        """Validate all configurations against their schemas"""
        results = {}
        
        for config_name in self.list_configs():
            try:
                config_data = self.get_config(config_name)
                if config_data is None:
                    results[config_name] = "Configuration not found"
                    continue
                
                # Try to find matching schema
                schema_name = None
                for name in self.schemas.keys():
                    if name in config_name or config_name.startswith(name):
                        schema_name = name
                        break
                
                if schema_name:
                    schema = self.schemas[schema_name]
                    schema.validate_config(config_data)
                    results[config_name] = True
                else:
                    results[config_name] = "No matching schema found"
                    
            except Exception as e:
                results[config_name] = str(e)
        
        return results
    
    def export_configs(self, format: str = 'json', include_schemas: bool = False) -> str:
        """Export all configurations"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'configs': {}
        }
        
        # Export configurations
        for config_name in self.list_configs():
            config_data = self.get_config(config_name)
            if config_data:
                export_data['configs'][config_name] = config_data
        
        # Export schemas if requested
        if include_schemas:
            export_data['schemas'] = {}
            for schema_name, schema in self.schemas.items():
                export_data['schemas'][schema_name] = asdict(schema)
        
        if format.lower() == 'json':
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format.lower() in ['yaml', 'yml']:
            return yaml.dump(export_data, default_flow_style=False, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_configs(self, data: str, format: str = 'json', 
                      overwrite: bool = False, validate: bool = True) -> Dict[str, bool]:
        """Import configurations from exported data"""
        results = {}
        
        try:
            if format.lower() == 'json':
                import_data = json.loads(data)
            elif format.lower() in ['yaml', 'yml']:
                import_data = yaml.safe_load(data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # Import configurations
            configs = import_data.get('configs', {})
            for config_name, config_data in configs.items():
                try:
                    # Check if config exists and overwrite is disabled
                    if not overwrite and config_name in self.configs:
                        results[config_name] = False
                        continue
                    
                    # Save configuration
                    success = self.save_config(config_name, config_data, validate=validate)
                    results[config_name] = success
                    
                except Exception as e:
                    self.logger.error(f"Error importing configuration {config_name}: {e}")
                    results[config_name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error importing configurations: {e}")
            return {}
    
    def add_change_callback(self, config_name: str, callback: Callable):
        """Add callback for configuration changes"""
        if config_name not in self.change_callbacks:
            self.change_callbacks[config_name] = []
        self.change_callbacks[config_name].append(callback)
    
    def remove_change_callback(self, config_name: str, callback: Callable):
        """Remove configuration change callback"""
        if config_name in self.change_callbacks:
            try:
                self.change_callbacks[config_name].remove(callback)
            except ValueError:
                pass
    
    def _trigger_change_callbacks(self, config_name: str, config_data: Dict[str, Any]):
        """Trigger configuration change callbacks"""
        for callback in self.change_callbacks.get(config_name, []):
            try:
                callback(config_name, config_data)
            except Exception as e:
                self.logger.error(f"Error in change callback for {config_name}: {e}")
    
    def get_environment_config(self, base_config_name: str) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        # Try environment-specific config first
        env_config_name = f"{base_config_name}.{self.environment}"
        env_config = self.get_config(env_config_name)
        
        if env_config:
            return env_config
        
        # Fall back to base config
        base_config = self.get_config(base_config_name)
        return base_config or {}
    
    def create_config_template(self, schema_name: str, config_name: str) -> bool:
        """Create configuration template from schema"""
        if schema_name not in self.schemas:
            self.logger.error(f"Schema not found: {schema_name}")
            return False
        
        schema = self.schemas[schema_name]
        template_config = deepcopy(schema.default_values)
        
        # Add schema metadata
        template_config['_schema'] = {
            'name': schema.name,
            'version': schema.version,
            'description': schema.description
        }
        
        return self.save_config(config_name, template_config, validate=False)
    
    def get_config_info(self, config_name: str) -> Dict[str, Any]:
        """Get information about a configuration"""
        config_file = self._find_config_file(config_name)
        config_data = self.get_config(config_name)
        
        info = {
            'name': config_name,
            'exists': config_data is not None,
            'file_path': str(config_file) if config_file else None,
            'in_memory': config_name in self.configs,
            'size_bytes': 0,
            'last_modified': None,
            'schema_info': None
        }
        
        if config_file and config_file.exists():
            stat = config_file.stat()
            info['size_bytes'] = stat.st_size
            info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Try to find matching schema
        for schema_name, schema in self.schemas.items():
            if schema_name in config_name or config_name.startswith(schema_name):
                info['schema_info'] = {
                    'name': schema.name,
                    'version': schema.version,
                    'description': schema.description
                }
                break
        
        return info
    
    def cleanup(self):
        """Cleanup configuration manager resources"""
        self.configs.clear()
        self.file_timestamps.clear()
        self.change_callbacks.clear()
        self.logger.info("Configuration manager cleanup completed")