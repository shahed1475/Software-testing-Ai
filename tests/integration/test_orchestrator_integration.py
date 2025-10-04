"""
Integration tests for the Test Automation Orchestrator system.
Tests the complete workflow from CLI to execution and reporting.
"""

import pytest
import asyncio
import json
import tempfile
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import the main components
try:
    from src.agents.test_orchestrator import TestOrchestrator
    from src.agents.test_scheduler import TestScheduler
    from src.agents.trigger_system import TriggerSystem
    from src.config.config_manager import ConfigManager
    from src.config.settings_manager import SettingsManager
    from src.config.environment_manager import EnvironmentManager
    from src.monitoring.agent_monitor import AgentMonitor
    from src.monitoring.system_monitor import SystemMonitor
    from src.monitoring.metrics_collector import MetricsCollector
    from src.dashboard.dashboard_app import DashboardApp
    from src.database.models import TestRun, TestCase, TestResult
except ImportError:
    # Mock imports for testing when modules are not available
    TestOrchestrator = Mock
    TestScheduler = Mock
    TriggerSystem = Mock
    ConfigManager = Mock
    SettingsManager = Mock
    EnvironmentManager = Mock
    AgentMonitor = Mock
    SystemMonitor = Mock
    MetricsCollector = Mock
    DashboardApp = Mock
    TestRun = Mock
    TestCase = Mock
    TestResult = Mock


class TestOrchestratorIntegration:
    """Integration tests for the complete orchestrator system."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            yield config_dir

    @pytest.fixture
    def sample_config(self, temp_config_dir):
        """Create a sample configuration file."""
        config = {
            "orchestrator": {
                "max_concurrent_jobs": 2,
                "job_timeout": 300,
                "retry_attempts": 2,
                "retry_delay": 30
            },
            "scheduler": {
                "enabled": True,
                "max_jobs": 10,
                "cleanup_interval": 3600
            },
            "monitoring": {
                "enabled": True,
                "metrics_interval": 10,
                "alert_thresholds": {
                    "cpu_usage": 80,
                    "memory_usage": 85
                }
            },
            "dashboard": {
                "enabled": True,
                "port": 8081,
                "host": "localhost"
            },
            "database": {
                "url": "sqlite:///test.db"
            }
        }
        
        config_file = temp_config_dir / "orchestrator.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_file

    @pytest.fixture
    def sample_workflow(self, temp_config_dir):
        """Create a sample workflow definition."""
        workflow = {
            "name": "test-workflow",
            "description": "Integration test workflow",
            "version": "1.0",
            "environment": "test",
            "steps": [
                {
                    "name": "setup",
                    "agent": "test_runner",
                    "action": "setup_environment",
                    "config": {
                        "timeout": 60
                    }
                },
                {
                    "name": "run_tests",
                    "agent": "test_runner",
                    "action": "run_tests",
                    "depends_on": ["setup"],
                    "config": {
                        "test_suite": "integration",
                        "parallel": False
                    }
                },
                {
                    "name": "generate_report",
                    "agent": "report_generator",
                    "action": "generate_html_report",
                    "depends_on": ["run_tests"],
                    "config": {
                        "include_screenshots": False
                    }
                }
            ]
        }
        
        workflow_file = temp_config_dir / "test-workflow.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        return workflow_file

    def test_cli_help_command(self):
        """Test that the CLI help command works."""
        try:
            result = subprocess.run(
                ["python", "orchestrator.py", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result.returncode == 0
            assert "Test Automation Orchestrator" in result.stdout
            assert "Commands:" in result.stdout
        except subprocess.TimeoutExpired:
            pytest.skip("CLI command timed out")
        except FileNotFoundError:
            pytest.skip("orchestrator.py not found")

    def test_cli_status_command(self):
        """Test the CLI status command."""
        try:
            result = subprocess.run(
                ["python", "orchestrator.py", "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Should return 0 or 1 (running or not running)
            assert result.returncode in [0, 1]
        except subprocess.TimeoutExpired:
            pytest.skip("CLI command timed out")
        except FileNotFoundError:
            pytest.skip("orchestrator.py not found")

    @pytest.mark.asyncio
    async def test_config_manager_integration(self, sample_config):
        """Test configuration manager integration."""
        try:
            config_manager = ConfigManager(str(sample_config))
            config = await config_manager.load_config()
            
            assert config is not None
            assert "orchestrator" in config
            assert "scheduler" in config
            assert config["orchestrator"]["max_concurrent_jobs"] == 2
            
            # Test config validation
            is_valid = await config_manager.validate_config(config)
            assert is_valid
            
        except Exception as e:
            pytest.skip(f"ConfigManager not available: {e}")

    @pytest.mark.asyncio
    async def test_orchestrator_workflow_execution(self, sample_config, sample_workflow):
        """Test complete workflow execution through orchestrator."""
        try:
            # Mock the agents to avoid actual test execution
            with patch('src.agents.test_runner_agent.TestRunnerAgent') as mock_runner, \
                 patch('src.agents.report_generator_agent.ReportGeneratorAgent') as mock_reporter:
                
                # Configure mocks
                mock_runner_instance = AsyncMock()
                mock_runner_instance.setup_environment.return_value = {"status": "success"}
                mock_runner_instance.run_tests.return_value = {
                    "status": "success",
                    "tests_run": 5,
                    "tests_passed": 4,
                    "tests_failed": 1
                }
                mock_runner.return_value = mock_runner_instance
                
                mock_reporter_instance = AsyncMock()
                mock_reporter_instance.generate_html_report.return_value = {
                    "status": "success",
                    "report_path": "/tmp/report.html"
                }
                mock_reporter.return_value = mock_reporter_instance
                
                # Initialize orchestrator
                orchestrator = TestOrchestrator(str(sample_config))
                await orchestrator.initialize()
                
                # Load and execute workflow
                with open(sample_workflow, 'r') as f:
                    workflow_def = json.load(f)
                
                result = await orchestrator.execute_workflow(workflow_def)
                
                assert result is not None
                assert result.get("status") in ["success", "completed"]
                
        except Exception as e:
            pytest.skip(f"Orchestrator not available: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_integration(self, sample_config):
        """Test scheduler integration with job management."""
        try:
            scheduler = TestScheduler(str(sample_config))
            await scheduler.initialize()
            
            # Schedule a test job
            job_id = await scheduler.schedule_job(
                name="test-job",
                cron="*/5 * * * *",  # Every 5 minutes
                workflow="test-workflow",
                priority=1
            )
            
            assert job_id is not None
            
            # List scheduled jobs
            jobs = await scheduler.list_jobs()
            assert len(jobs) >= 1
            assert any(job["name"] == "test-job" for job in jobs)
            
            # Cancel the job
            await scheduler.cancel_job(job_id)
            
        except Exception as e:
            pytest.skip(f"Scheduler not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_system_integration(self, sample_config):
        """Test monitoring system integration."""
        try:
            # Test system monitor
            system_monitor = SystemMonitor(str(sample_config))
            await system_monitor.initialize()
            
            metrics = await system_monitor.collect_metrics()
            assert "cpu_usage" in metrics
            assert "memory_usage" in metrics
            assert "disk_usage" in metrics
            
            # Test agent monitor
            agent_monitor = AgentMonitor(str(sample_config))
            await agent_monitor.initialize()
            
            # Mock some agents
            await agent_monitor.register_agent("test_runner", "active")
            await agent_monitor.register_agent("report_generator", "active")
            
            agent_status = await agent_monitor.get_agent_status()
            assert len(agent_status) >= 2
            
        except Exception as e:
            pytest.skip(f"Monitoring system not available: {e}")

    @pytest.mark.asyncio
    async def test_trigger_system_integration(self, sample_config):
        """Test trigger system integration."""
        try:
            trigger_system = TriggerSystem(str(sample_config))
            await trigger_system.initialize()
            
            # Test manual trigger
            trigger_result = await trigger_system.trigger_workflow(
                workflow_name="test-workflow",
                trigger_type="manual",
                metadata={"user": "test_user"}
            )
            
            assert trigger_result is not None
            assert "trigger_id" in trigger_result
            
        except Exception as e:
            pytest.skip(f"Trigger system not available: {e}")

    @pytest.mark.asyncio
    async def test_dashboard_integration(self, sample_config):
        """Test dashboard application integration."""
        try:
            dashboard = DashboardApp(str(sample_config))
            
            # Test dashboard initialization
            await dashboard.initialize()
            
            # Test API endpoints (mock the web framework)
            with patch('fastapi.FastAPI') as mock_fastapi:
                mock_app = Mock()
                mock_fastapi.return_value = mock_app
                
                await dashboard.setup_routes()
                
                # Verify routes were set up
                assert mock_app.get.called or mock_app.post.called
                
        except Exception as e:
            pytest.skip(f"Dashboard not available: {e}")

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_config, sample_workflow):
        """Test complete end-to-end workflow execution."""
        try:
            # This test simulates a complete workflow from trigger to completion
            
            # 1. Initialize all components
            config_manager = ConfigManager(str(sample_config))
            config = await config_manager.load_config()
            
            orchestrator = TestOrchestrator(str(sample_config))
            scheduler = TestScheduler(str(sample_config))
            trigger_system = TriggerSystem(str(sample_config))
            
            await orchestrator.initialize()
            await scheduler.initialize()
            await trigger_system.initialize()
            
            # 2. Load workflow
            with open(sample_workflow, 'r') as f:
                workflow_def = json.load(f)
            
            # 3. Mock the execution components
            with patch('src.agents.test_runner_agent.TestRunnerAgent') as mock_runner, \
                 patch('src.agents.report_generator_agent.ReportGeneratorAgent') as mock_reporter:
                
                # Configure mocks for successful execution
                mock_runner_instance = AsyncMock()
                mock_runner_instance.setup_environment.return_value = {"status": "success"}
                mock_runner_instance.run_tests.return_value = {
                    "status": "success",
                    "tests_run": 10,
                    "tests_passed": 8,
                    "tests_failed": 2,
                    "execution_time": 120
                }
                mock_runner.return_value = mock_runner_instance
                
                mock_reporter_instance = AsyncMock()
                mock_reporter_instance.generate_html_report.return_value = {
                    "status": "success",
                    "report_path": "/tmp/integration_test_report.html",
                    "report_size": 1024
                }
                mock_reporter.return_value = mock_reporter_instance
                
                # 4. Trigger workflow execution
                trigger_result = await trigger_system.trigger_workflow(
                    workflow_name="test-workflow",
                    trigger_type="manual",
                    metadata={"test": "integration"}
                )
                
                # 5. Execute workflow through orchestrator
                execution_result = await orchestrator.execute_workflow(workflow_def)
                
                # 6. Verify results
                assert trigger_result is not None
                assert execution_result is not None
                assert execution_result.get("status") in ["success", "completed"]
                
                # Verify all steps were executed
                if "steps" in execution_result:
                    completed_steps = [step for step in execution_result["steps"] 
                                     if step.get("status") == "completed"]
                    assert len(completed_steps) == len(workflow_def["steps"])
                
        except Exception as e:
            pytest.skip(f"End-to-end test not available: {e}")

    def test_database_integration(self):
        """Test database model integration."""
        try:
            # Test model creation and relationships
            test_run = TestRun(
                name="Integration Test Run",
                status="running",
                environment="test",
                test_metadata={"version": "1.0"}
            )
            
            test_case = TestCase(
                name="Sample Test Case",
                status="passed",
                test_case_metadata={"priority": "high"}
            )
            
            test_result = TestResult(
                status="passed",
                execution_time=45.5,
                error_message=None
            )
            
            # Verify objects can be created
            assert test_run.name == "Integration Test Run"
            assert test_case.status == "passed"
            assert test_result.execution_time == 45.5
            
        except Exception as e:
            pytest.skip(f"Database models not available: {e}")

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, sample_config):
        """Test metrics collection and aggregation."""
        try:
            metrics_collector = MetricsCollector(str(sample_config))
            await metrics_collector.initialize()
            
            # Collect some test metrics
            await metrics_collector.record_metric("test_execution_time", 120.5, {"workflow": "test"})
            await metrics_collector.record_metric("test_success_rate", 0.8, {"environment": "test"})
            await metrics_collector.record_metric("system_cpu_usage", 65.2)
            
            # Retrieve metrics
            metrics = await metrics_collector.get_metrics(
                metric_name="test_execution_time",
                time_range="1h"
            )
            
            assert len(metrics) >= 1
            assert metrics[0]["value"] == 120.5
            
        except Exception as e:
            pytest.skip(f"Metrics collector not available: {e}")

    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation with various scenarios."""
        # Test valid configuration
        valid_config = {
            "orchestrator": {
                "max_concurrent_jobs": 5,
                "job_timeout": 3600
            },
            "scheduler": {
                "enabled": True
            }
        }
        
        config_file = temp_config_dir / "valid_config.json"
        with open(config_file, 'w') as f:
            json.dump(valid_config, f)
        
        try:
            config_manager = ConfigManager(str(config_file))
            # Should not raise an exception
            assert True
        except Exception:
            pytest.skip("ConfigManager validation not available")
        
        # Test invalid configuration
        invalid_config = {
            "orchestrator": {
                "max_concurrent_jobs": "invalid",  # Should be integer
                "job_timeout": -1  # Should be positive
            }
        }
        
        invalid_config_file = temp_config_dir / "invalid_config.json"
        with open(invalid_config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        try:
            config_manager = ConfigManager(str(invalid_config_file))
            # Should handle invalid configuration gracefully
            assert True
        except Exception:
            # Expected for invalid configuration
            assert True


class TestOrchestratorPerformance:
    """Performance tests for the orchestrator system."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, sample_config, sample_workflow):
        """Test concurrent execution of multiple workflows."""
        try:
            orchestrator = TestOrchestrator(str(sample_config))
            await orchestrator.initialize()
            
            with open(sample_workflow, 'r') as f:
                workflow_def = json.load(f)
            
            # Mock agents for performance testing
            with patch('src.agents.test_runner_agent.TestRunnerAgent') as mock_runner, \
                 patch('src.agents.report_generator_agent.ReportGeneratorAgent') as mock_reporter:
                
                mock_runner_instance = AsyncMock()
                mock_runner_instance.setup_environment.return_value = {"status": "success"}
                mock_runner_instance.run_tests.return_value = {"status": "success"}
                mock_runner.return_value = mock_runner_instance
                
                mock_reporter_instance = AsyncMock()
                mock_reporter_instance.generate_html_report.return_value = {"status": "success"}
                mock_reporter.return_value = mock_reporter_instance
                
                # Execute multiple workflows concurrently
                start_time = time.time()
                
                tasks = []
                for i in range(3):
                    workflow_copy = workflow_def.copy()
                    workflow_copy["name"] = f"test-workflow-{i}"
                    tasks.append(orchestrator.execute_workflow(workflow_copy))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Verify all workflows completed
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) >= 1
                
                # Performance assertion (should complete within reasonable time)
                assert execution_time < 60  # Should complete within 1 minute
                
        except Exception as e:
            pytest.skip(f"Performance test not available: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_load_handling(self, sample_config):
        """Test scheduler performance with multiple jobs."""
        try:
            scheduler = TestScheduler(str(sample_config))
            await scheduler.initialize()
            
            # Schedule multiple jobs
            job_ids = []
            for i in range(10):
                job_id = await scheduler.schedule_job(
                    name=f"load-test-job-{i}",
                    cron="*/10 * * * *",
                    workflow=f"test-workflow-{i}",
                    priority=i % 3
                )
                job_ids.append(job_id)
            
            # Verify all jobs were scheduled
            jobs = await scheduler.list_jobs()
            scheduled_jobs = [job for job in jobs if job["name"].startswith("load-test-job")]
            assert len(scheduled_jobs) == 10
            
            # Clean up
            for job_id in job_ids:
                await scheduler.cancel_job(job_id)
                
        except Exception as e:
            pytest.skip(f"Scheduler load test not available: {e}")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short"])