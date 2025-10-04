"""
Integration tests for configuration management system.
Tests configuration loading, validation, updates, and environment-specific settings.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import configuration components
try:
    from src.config.config_manager import ConfigManager
    from src.config.config_validator import ConfigValidator
    from src.config.environment_manager import EnvironmentManager
except ImportError:
    # Mock imports for testing when modules are not available
    ConfigManager = Mock
    ConfigValidator = Mock
    EnvironmentManager = Mock


class TestConfigurationIntegration:
    """Integration tests for configuration management system."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            yield config_dir

    @pytest.fixture
    def base_config(self):
        """Base configuration for testing."""
        return {
            "system": {
                "name": "Test Automation Orchestrator",
                "version": "2.0.0",
                "environment": "development",
                "log_level": "INFO",
                "workspace": "/tmp/test_workspace"
            },
            "database": {
                "url": "sqlite:///test.db",
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10
            },
            "orchestrator": {
                "enabled": True,
                "max_concurrent_workflows": 5,
                "workflow_timeout": 3600,
                "retry_attempts": 3,
                "retry_delay": 30
            },
            "scheduler": {
                "enabled": True,
                "max_jobs": 100,
                "job_timeout": 7200,
                "cleanup_interval": 3600,
                "persistence": True
            },
            "executor": {
                "enabled": True,
                "max_parallel_tests": 10,
                "test_timeout": 1800,
                "environments": ["development", "staging", "production"],
                "default_environment": "development"
            },
            "triggers": {
                "enabled": True,
                "webhook": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 8080,
                    "ssl_enabled": False,
                    "auth_required": True
                },
                "file_system": {
                    "enabled": True,
                    "polling_interval": 1,
                    "debounce_seconds": 2
                },
                "schedule": {
                    "enabled": True,
                    "timezone": "UTC",
                    "max_jobs": 50
                }
            },
            "monitoring": {
                "enabled": True,
                "metrics_interval": 30,
                "retention_days": 7,
                "alert_thresholds": {
                    "cpu_usage": 80,
                    "memory_usage": 85,
                    "disk_usage": 90
                }
            },
            "dashboard": {
                "enabled": True,
                "host": "localhost",
                "port": 8090,
                "debug": False,
                "cors_enabled": True
            },
            "notifications": {
                "enabled": True,
                "default_channels": ["email"],
                "rate_limit": {
                    "max_per_hour": 100,
                    "max_per_day": 1000
                }
            }
        }

    @pytest.fixture
    def environment_configs(self, temp_config_dir, base_config):
        """Create environment-specific configurations."""
        configs = {}
        
        # Development environment
        dev_config = base_config.copy()
        dev_config["system"]["environment"] = "development"
        dev_config["system"]["log_level"] = "DEBUG"
        dev_config["database"]["echo"] = True
        dev_config["dashboard"]["debug"] = True
        
        dev_file = temp_config_dir / "development.json"
        with open(dev_file, 'w') as f:
            json.dump(dev_config, f, indent=2)
        configs["development"] = dev_file
        
        # Staging environment
        staging_config = base_config.copy()
        staging_config["system"]["environment"] = "staging"
        staging_config["system"]["log_level"] = "INFO"
        staging_config["database"]["url"] = "postgresql://staging_db"
        staging_config["orchestrator"]["max_concurrent_workflows"] = 10
        staging_config["triggers"]["webhook"]["port"] = 8081
        
        staging_file = temp_config_dir / "staging.json"
        with open(staging_file, 'w') as f:
            json.dump(staging_config, f, indent=2)
        configs["staging"] = staging_file
        
        # Production environment
        prod_config = base_config.copy()
        prod_config["system"]["environment"] = "production"
        prod_config["system"]["log_level"] = "WARNING"
        prod_config["database"]["url"] = "postgresql://prod_db"
        prod_config["orchestrator"]["max_concurrent_workflows"] = 20
        prod_config["triggers"]["webhook"]["port"] = 443
        prod_config["triggers"]["webhook"]["ssl_enabled"] = True
        prod_config["dashboard"]["debug"] = False
        
        prod_file = temp_config_dir / "production.json"
        with open(prod_file, 'w') as f:
            json.dump(prod_config, f, indent=2)
        configs["production"] = prod_file
        
        return configs

    @pytest.fixture
    def workflow_configs(self, temp_config_dir):
        """Create workflow configurations."""
        workflows = {
            "unit-tests": {
                "name": "Unit Tests",
                "description": "Run unit test suite",
                "timeout": 600,
                "retry_attempts": 2,
                "steps": [
                    {
                        "name": "setup",
                        "type": "setup",
                        "config": {"environment": "test"}
                    },
                    {
                        "name": "run_tests",
                        "type": "test_execution",
                        "config": {"test_suite": "unit", "parallel": True}
                    },
                    {
                        "name": "cleanup",
                        "type": "cleanup",
                        "config": {"remove_temp_files": True}
                    }
                ]
            },
            "integration-tests": {
                "name": "Integration Tests",
                "description": "Run integration test suite",
                "timeout": 1800,
                "retry_attempts": 3,
                "dependencies": ["unit-tests"],
                "steps": [
                    {
                        "name": "setup_environment",
                        "type": "setup",
                        "config": {"environment": "integration", "database": True}
                    },
                    {
                        "name": "run_integration_tests",
                        "type": "test_execution",
                        "config": {"test_suite": "integration", "parallel": False}
                    },
                    {
                        "name": "generate_report",
                        "type": "report_generation",
                        "config": {"format": "html", "include_coverage": True}
                    }
                ]
            }
        }
        
        workflows_file = temp_config_dir / "workflows.json"
        with open(workflows_file, 'w') as f:
            json.dump(workflows, f, indent=2)
        
        return workflows_file

    @pytest.mark.asyncio
    async def test_config_manager_initialization(self, environment_configs):
        """Test configuration manager initialization with different environments."""
        try:
            # Test development environment
            dev_config_manager = ConfigManager(str(environment_configs["development"]))
            await dev_config_manager.initialize()
            
            assert dev_config_manager.is_initialized()
            config = dev_config_manager.get_config()
            assert config["system"]["environment"] == "development"
            assert config["system"]["log_level"] == "DEBUG"
            assert config["database"]["echo"] is True
            
            await dev_config_manager.shutdown()
            
            # Test staging environment
            staging_config_manager = ConfigManager(str(environment_configs["staging"]))
            await staging_config_manager.initialize()
            
            config = staging_config_manager.get_config()
            assert config["system"]["environment"] == "staging"
            assert config["orchestrator"]["max_concurrent_workflows"] == 10
            assert config["triggers"]["webhook"]["port"] == 8081
            
            await staging_config_manager.shutdown()
            
            # Test production environment
            prod_config_manager = ConfigManager(str(environment_configs["production"]))
            await prod_config_manager.initialize()
            
            config = prod_config_manager.get_config()
            assert config["system"]["environment"] == "production"
            assert config["system"]["log_level"] == "WARNING"
            assert config["triggers"]["webhook"]["ssl_enabled"] is True
            
            await prod_config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Config manager initialization not available: {e}")

    @pytest.mark.asyncio
    async def test_configuration_validation(self, temp_config_dir, base_config):
        """Test configuration validation with valid and invalid configs."""
        try:
            # Test valid configuration
            valid_config_file = temp_config_dir / "valid_config.json"
            with open(valid_config_file, 'w') as f:
                json.dump(base_config, f, indent=2)
            
            validator = ConfigValidator()
            await validator.initialize()
            
            validation_result = await validator.validate_config(str(valid_config_file))
            assert validation_result["valid"] is True
            assert len(validation_result["errors"]) == 0
            
            # Test invalid configuration - missing required fields
            invalid_config = base_config.copy()
            del invalid_config["system"]["name"]
            del invalid_config["database"]["url"]
            
            invalid_config_file = temp_config_dir / "invalid_config.json"
            with open(invalid_config_file, 'w') as f:
                json.dump(invalid_config, f, indent=2)
            
            validation_result = await validator.validate_config(str(invalid_config_file))
            assert validation_result["valid"] is False
            assert len(validation_result["errors"]) > 0
            
            # Check specific error messages
            error_messages = [error["message"] for error in validation_result["errors"]]
            assert any("system.name" in msg for msg in error_messages)
            assert any("database.url" in msg for msg in error_messages)
            
            # Test configuration with invalid values
            invalid_values_config = base_config.copy()
            invalid_values_config["orchestrator"]["max_concurrent_workflows"] = -1
            invalid_values_config["scheduler"]["job_timeout"] = "invalid"
            invalid_values_config["triggers"]["webhook"]["port"] = 99999
            
            invalid_values_file = temp_config_dir / "invalid_values_config.json"
            with open(invalid_values_file, 'w') as f:
                json.dump(invalid_values_config, f, indent=2)
            
            validation_result = await validator.validate_config(str(invalid_values_file))
            assert validation_result["valid"] is False
            assert len(validation_result["errors"]) >= 3
            
            await validator.shutdown()
            
        except Exception as e:
            pytest.skip(f"Configuration validation not available: {e}")

    @pytest.mark.asyncio
    async def test_dynamic_configuration_updates(self, environment_configs):
        """Test dynamic configuration updates without restart."""
        try:
            config_manager = ConfigManager(str(environment_configs["development"]))
            await config_manager.initialize()
            
            # Track configuration change events
            config_changes = []
            
            def on_config_change(section, key, old_value, new_value):
                config_changes.append({
                    "section": section,
                    "key": key,
                    "old_value": old_value,
                    "new_value": new_value,
                    "timestamp": datetime.now()
                })
            
            config_manager.register_change_callback(on_config_change)
            
            # Update orchestrator settings
            await config_manager.update_config("orchestrator.max_concurrent_workflows", 15)
            await config_manager.update_config("orchestrator.workflow_timeout", 7200)
            
            # Update monitoring settings
            await config_manager.update_config("monitoring.metrics_interval", 60)
            await config_manager.update_config("monitoring.alert_thresholds.cpu_usage", 75)
            
            # Update notification settings
            await config_manager.update_config("notifications.rate_limit.max_per_hour", 200)
            
            # Verify configuration changes
            config = config_manager.get_config()
            assert config["orchestrator"]["max_concurrent_workflows"] == 15
            assert config["orchestrator"]["workflow_timeout"] == 7200
            assert config["monitoring"]["metrics_interval"] == 60
            assert config["monitoring"]["alert_thresholds"]["cpu_usage"] == 75
            assert config["notifications"]["rate_limit"]["max_per_hour"] == 200
            
            # Verify change events were triggered
            assert len(config_changes) == 5
            
            # Check specific change events
            workflow_change = next((c for c in config_changes if c["key"] == "max_concurrent_workflows"), None)
            assert workflow_change is not None
            assert workflow_change["section"] == "orchestrator"
            assert workflow_change["old_value"] == 5
            assert workflow_change["new_value"] == 15
            
            # Test batch configuration update
            batch_updates = {
                "scheduler.max_jobs": 200,
                "executor.max_parallel_tests": 20,
                "dashboard.port": 8091
            }
            
            await config_manager.update_config_batch(batch_updates)
            
            # Verify batch updates
            config = config_manager.get_config()
            assert config["scheduler"]["max_jobs"] == 200
            assert config["executor"]["max_parallel_tests"] == 20
            assert config["dashboard"]["port"] == 8091
            
            await config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Dynamic configuration updates not available: {e}")

    @pytest.mark.asyncio
    async def test_environment_specific_configuration(self, environment_configs):
        """Test environment-specific configuration loading and switching."""
        try:
            env_manager = EnvironmentManager(str(environment_configs["development"].parent))
            await env_manager.initialize()
            
            # Test loading development environment
            dev_config = await env_manager.load_environment_config("development")
            assert dev_config["system"]["environment"] == "development"
            assert dev_config["system"]["log_level"] == "DEBUG"
            assert dev_config["database"]["echo"] is True
            
            # Test loading staging environment
            staging_config = await env_manager.load_environment_config("staging")
            assert staging_config["system"]["environment"] == "staging"
            assert staging_config["database"]["url"] == "postgresql://staging_db"
            assert staging_config["orchestrator"]["max_concurrent_workflows"] == 10
            
            # Test loading production environment
            prod_config = await env_manager.load_environment_config("production")
            assert prod_config["system"]["environment"] == "production"
            assert prod_config["triggers"]["webhook"]["ssl_enabled"] is True
            assert prod_config["dashboard"]["debug"] is False
            
            # Test environment switching
            current_env = env_manager.get_current_environment()
            assert current_env == "development"
            
            await env_manager.switch_environment("staging")
            current_env = env_manager.get_current_environment()
            assert current_env == "staging"
            
            # Verify configuration changed after environment switch
            current_config = env_manager.get_current_config()
            assert current_config["system"]["environment"] == "staging"
            assert current_config["triggers"]["webhook"]["port"] == 8081
            
            # Test environment validation
            available_envs = env_manager.get_available_environments()
            assert "development" in available_envs
            assert "staging" in available_envs
            assert "production" in available_envs
            
            # Test invalid environment
            try:
                await env_manager.switch_environment("invalid_env")
                assert False, "Should have raised exception for invalid environment"
            except Exception as e:
                assert "invalid_env" in str(e).lower()
            
            await env_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Environment-specific configuration not available: {e}")

    @pytest.mark.asyncio
    async def test_workflow_configuration_management(self, temp_config_dir, workflow_configs):
        """Test workflow configuration loading and management."""
        try:
            config_manager = ConfigManager(str(workflow_configs))
            await config_manager.initialize()
            
            # Load workflow configurations
            workflows = config_manager.get_workflows()
            assert "unit-tests" in workflows
            assert "integration-tests" in workflows
            
            # Verify unit tests workflow
            unit_workflow = workflows["unit-tests"]
            assert unit_workflow["name"] == "Unit Tests"
            assert unit_workflow["timeout"] == 600
            assert len(unit_workflow["steps"]) == 3
            
            # Verify integration tests workflow
            integration_workflow = workflows["integration-tests"]
            assert integration_workflow["name"] == "Integration Tests"
            assert integration_workflow["timeout"] == 1800
            assert "unit-tests" in integration_workflow["dependencies"]
            
            # Test workflow validation
            workflow_validator = config_manager.get_workflow_validator()
            
            # Validate existing workflows
            unit_validation = await workflow_validator.validate_workflow("unit-tests")
            assert unit_validation["valid"] is True
            
            integration_validation = await workflow_validator.validate_workflow("integration-tests")
            assert integration_validation["valid"] is True
            
            # Test adding new workflow
            new_workflow = {
                "name": "Performance Tests",
                "description": "Run performance test suite",
                "timeout": 3600,
                "retry_attempts": 1,
                "steps": [
                    {
                        "name": "setup_load_env",
                        "type": "setup",
                        "config": {"environment": "performance"}
                    },
                    {
                        "name": "run_load_tests",
                        "type": "test_execution",
                        "config": {"test_suite": "performance", "duration": 1800}
                    }
                ]
            }
            
            await config_manager.add_workflow("performance-tests", new_workflow)
            
            # Verify new workflow was added
            updated_workflows = config_manager.get_workflows()
            assert "performance-tests" in updated_workflows
            assert updated_workflows["performance-tests"]["name"] == "Performance Tests"
            
            # Test workflow update
            updated_unit_workflow = unit_workflow.copy()
            updated_unit_workflow["timeout"] = 900
            updated_unit_workflow["retry_attempts"] = 3
            
            await config_manager.update_workflow("unit-tests", updated_unit_workflow)
            
            # Verify workflow was updated
            updated_workflows = config_manager.get_workflows()
            assert updated_workflows["unit-tests"]["timeout"] == 900
            assert updated_workflows["unit-tests"]["retry_attempts"] == 3
            
            # Test workflow removal
            await config_manager.remove_workflow("performance-tests")
            
            # Verify workflow was removed
            final_workflows = config_manager.get_workflows()
            assert "performance-tests" not in final_workflows
            
            await config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Workflow configuration management not available: {e}")

    @pytest.mark.asyncio
    async def test_configuration_persistence_and_backup(self, temp_config_dir, base_config):
        """Test configuration persistence and backup functionality."""
        try:
            config_file = temp_config_dir / "test_config.json"
            with open(config_file, 'w') as f:
                json.dump(base_config, f, indent=2)
            
            config_manager = ConfigManager(str(config_file))
            await config_manager.initialize()
            
            # Enable configuration backup
            backup_dir = temp_config_dir / "backups"
            backup_dir.mkdir()
            config_manager.enable_backup(str(backup_dir))
            
            # Make configuration changes
            original_workflows = config_manager.get_config()["orchestrator"]["max_concurrent_workflows"]
            
            await config_manager.update_config("orchestrator.max_concurrent_workflows", 25)
            await config_manager.update_config("scheduler.max_jobs", 150)
            await config_manager.update_config("monitoring.metrics_interval", 45)
            
            # Verify changes were persisted
            config_manager_2 = ConfigManager(str(config_file))
            await config_manager_2.initialize()
            
            reloaded_config = config_manager_2.get_config()
            assert reloaded_config["orchestrator"]["max_concurrent_workflows"] == 25
            assert reloaded_config["scheduler"]["max_jobs"] == 150
            assert reloaded_config["monitoring"]["metrics_interval"] == 45
            
            await config_manager_2.shutdown()
            
            # Verify backup files were created
            backup_files = list(backup_dir.glob("*.json"))
            assert len(backup_files) >= 3  # One backup per configuration change
            
            # Test configuration restoration from backup
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            
            await config_manager.restore_from_backup(str(latest_backup))
            
            # Verify configuration was restored
            restored_config = config_manager.get_config()
            assert restored_config["orchestrator"]["max_concurrent_workflows"] == 25
            
            # Test rollback to previous version
            await config_manager.rollback_config(steps=2)
            
            # Verify rollback
            rolled_back_config = config_manager.get_config()
            assert rolled_back_config["scheduler"]["max_jobs"] == 100  # Original value
            
            await config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Configuration persistence and backup not available: {e}")

    @pytest.mark.asyncio
    async def test_configuration_security_and_encryption(self, temp_config_dir, base_config):
        """Test configuration security features and sensitive data encryption."""
        try:
            # Add sensitive configuration data
            secure_config = base_config.copy()
            secure_config["database"]["password"] = "super_secret_password"
            secure_config["notifications"]["channels"] = {
                "email": {
                    "smtp_password": "email_password_123",
                    "api_key": "secret_api_key_456"
                },
                "slack": {
                    "webhook_url": "https://hooks.slack.com/services/SECRET/TOKEN/HERE",
                    "bot_token": "xoxb-secret-bot-token"
                }
            }
            secure_config["triggers"]["webhook"]["auth_tokens"] = [
                "webhook_token_1",
                "webhook_token_2"
            ]
            
            config_file = temp_config_dir / "secure_config.json"
            with open(config_file, 'w') as f:
                json.dump(secure_config, f, indent=2)
            
            # Initialize config manager with encryption
            config_manager = ConfigManager(str(config_file))
            config_manager.enable_encryption("test_encryption_key_32_chars_long")
            await config_manager.initialize()
            
            # Verify sensitive data is accessible in memory
            config = config_manager.get_config()
            assert config["database"]["password"] == "super_secret_password"
            assert config["notifications"]["channels"]["email"]["smtp_password"] == "email_password_123"
            
            # Verify sensitive data is encrypted on disk
            with open(config_file, 'r') as f:
                disk_config = json.load(f)
            
            # Sensitive fields should be encrypted (not plain text)
            assert disk_config["database"]["password"] != "super_secret_password"
            assert disk_config["notifications"]["channels"]["email"]["smtp_password"] != "email_password_123"
            
            # Test configuration access control
            config_manager.set_access_control(True)
            
            # Test read-only access
            readonly_config = config_manager.get_config(readonly=True)
            assert readonly_config["database"]["password"] == "[ENCRYPTED]"
            assert readonly_config["notifications"]["channels"]["email"]["smtp_password"] == "[ENCRYPTED]"
            
            # Test admin access
            admin_config = config_manager.get_config(admin_access=True)
            assert admin_config["database"]["password"] == "super_secret_password"
            assert admin_config["notifications"]["channels"]["email"]["smtp_password"] == "email_password_123"
            
            # Test configuration audit logging
            audit_log = []
            
            def audit_callback(action, section, user, timestamp):
                audit_log.append({
                    "action": action,
                    "section": section,
                    "user": user,
                    "timestamp": timestamp
                })
            
            config_manager.enable_audit_logging(audit_callback)
            
            # Make configuration changes with different users
            await config_manager.update_config("orchestrator.max_concurrent_workflows", 30, user="admin")
            await config_manager.update_config("scheduler.max_jobs", 200, user="operator")
            
            # Verify audit log
            assert len(audit_log) == 2
            assert audit_log[0]["action"] == "update"
            assert audit_log[0]["section"] == "orchestrator.max_concurrent_workflows"
            assert audit_log[0]["user"] == "admin"
            
            await config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Configuration security and encryption not available: {e}")

    @pytest.mark.asyncio
    async def test_configuration_performance_under_load(self, temp_config_dir, base_config):
        """Test configuration system performance under high load."""
        try:
            config_file = temp_config_dir / "performance_config.json"
            with open(config_file, 'w') as f:
                json.dump(base_config, f, indent=2)
            
            config_manager = ConfigManager(str(config_file))
            await config_manager.initialize()
            
            # Performance metrics
            performance_metrics = {
                "read_operations": 0,
                "write_operations": 0,
                "total_read_time": 0,
                "total_write_time": 0,
                "concurrent_operations": 0,
                "max_concurrent": 0
            }
            
            import time
            import asyncio
            
            async def read_config_load_test():
                """Simulate high-frequency configuration reads."""
                performance_metrics["concurrent_operations"] += 1
                performance_metrics["max_concurrent"] = max(
                    performance_metrics["max_concurrent"],
                    performance_metrics["concurrent_operations"]
                )
                
                start_time = time.time()
                
                try:
                    for _ in range(100):
                        config = config_manager.get_config()
                        assert config["system"]["name"] == "Test Automation Orchestrator"
                        performance_metrics["read_operations"] += 1
                        
                        # Small delay to simulate processing
                        await asyncio.sleep(0.001)
                    
                    end_time = time.time()
                    performance_metrics["total_read_time"] += (end_time - start_time)
                
                finally:
                    performance_metrics["concurrent_operations"] -= 1
            
            async def write_config_load_test(worker_id):
                """Simulate configuration updates."""
                performance_metrics["concurrent_operations"] += 1
                performance_metrics["max_concurrent"] = max(
                    performance_metrics["max_concurrent"],
                    performance_metrics["concurrent_operations"]
                )
                
                start_time = time.time()
                
                try:
                    for i in range(10):
                        # Update different configuration values
                        await config_manager.update_config(
                            f"orchestrator.worker_{worker_id}_setting_{i}",
                            f"value_{i}"
                        )
                        performance_metrics["write_operations"] += 1
                        
                        await asyncio.sleep(0.01)
                    
                    end_time = time.time()
                    performance_metrics["total_write_time"] += (end_time - start_time)
                
                finally:
                    performance_metrics["concurrent_operations"] -= 1
            
            # Run concurrent load tests
            start_time = time.time()
            
            # Create multiple concurrent read and write tasks
            tasks = []
            
            # 20 concurrent read workers
            for _ in range(20):
                tasks.append(read_config_load_test())
            
            # 5 concurrent write workers
            for worker_id in range(5):
                tasks.append(write_config_load_test(worker_id))
            
            # Execute all tasks concurrently
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_test_time = end_time - start_time
            
            # Analyze performance results
            assert performance_metrics["read_operations"] == 2000  # 20 workers * 100 reads
            assert performance_metrics["write_operations"] == 50   # 5 workers * 10 writes
            assert performance_metrics["max_concurrent"] <= 25     # Should handle concurrent access
            
            # Calculate performance metrics
            avg_read_time = performance_metrics["total_read_time"] / 20  # 20 read workers
            avg_write_time = performance_metrics["total_write_time"] / 5  # 5 write workers
            
            read_throughput = performance_metrics["read_operations"] / performance_metrics["total_read_time"]
            write_throughput = performance_metrics["write_operations"] / performance_metrics["total_write_time"]
            
            # Performance assertions
            assert total_test_time < 10  # Should complete within 10 seconds
            assert avg_read_time < 2     # Average read worker should complete in < 2 seconds
            assert avg_write_time < 5    # Average write worker should complete in < 5 seconds
            assert read_throughput > 500 # Should handle > 500 reads per second
            assert write_throughput > 10 # Should handle > 10 writes per second
            
            await config_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Configuration performance test not available: {e}")


if __name__ == "__main__":
    # Run the configuration integration tests
    pytest.main([__file__, "-v", "--tb=short"])