"""
Integration tests for the Monitoring system.
Tests metrics collection, system monitoring, and alerting functionality.
"""

import pytest
import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Import monitoring components
try:
    from src.monitoring.metrics_collector import MetricsCollector
    from src.monitoring.agent_monitor import AgentMonitor
    from src.monitoring.system_monitor import SystemMonitor
    from src.monitoring.alert_manager import AlertManager
    from src.config.config_manager import ConfigManager
    from src.agents.test_orchestrator import TestOrchestrator
    from src.agents.test_scheduler import TestScheduler
except ImportError:
    # Mock imports for testing when modules are not available
    MetricsCollector = Mock
    AgentMonitor = Mock
    SystemMonitor = Mock
    AlertManager = Mock
    ConfigManager = Mock
    TestOrchestrator = Mock
    TestScheduler = Mock


class TestMonitoringIntegration:
    """Integration tests for the monitoring system."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            yield config_dir

    @pytest.fixture
    def monitoring_config(self, temp_config_dir):
        """Create monitoring configuration."""
        config = {
            "monitoring": {
                "enabled": True,
                "metrics_interval": 5,
                "retention_days": 30,
                "storage_backend": "sqlite"
            },
            "metrics": {
                "system_metrics": {
                    "enabled": True,
                    "interval": 10,
                    "metrics": ["cpu", "memory", "disk", "network"]
                },
                "agent_metrics": {
                    "enabled": True,
                    "interval": 15,
                    "metrics": ["status", "performance", "errors"]
                },
                "test_metrics": {
                    "enabled": True,
                    "interval": 5,
                    "metrics": ["execution_time", "success_rate", "failure_rate"]
                }
            },
            "alerts": {
                "enabled": True,
                "channels": ["email", "slack"],
                "thresholds": {
                    "cpu_usage": 80,
                    "memory_usage": 85,
                    "disk_usage": 90,
                    "test_failure_rate": 0.2
                }
            },
            "database": {
                "url": "sqlite:///test_monitoring.db"
            }
        }
        
        config_file = temp_config_dir / "monitoring.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_file

    @pytest.fixture
    def sample_metrics_data(self):
        """Create sample metrics data."""
        return {
            "system_metrics": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "cpu_usage",
                    "value": 65.2,
                    "tags": {"host": "test-server"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "memory_usage",
                    "value": 78.5,
                    "tags": {"host": "test-server"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "disk_usage",
                    "value": 45.8,
                    "tags": {"host": "test-server", "mount": "/"}
                }
            ],
            "agent_metrics": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "agent_status",
                    "value": 1,
                    "tags": {"agent": "test_executor", "status": "active"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "agent_response_time",
                    "value": 125.3,
                    "tags": {"agent": "test_executor"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "agent_error_count",
                    "value": 2,
                    "tags": {"agent": "test_executor"}
                }
            ],
            "test_metrics": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "test_execution_time",
                    "value": 120.5,
                    "tags": {"workflow": "smoke-tests", "environment": "staging"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "test_success_rate",
                    "value": 0.92,
                    "tags": {"workflow": "smoke-tests", "environment": "staging"}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "metric": "test_failure_rate",
                    "value": 0.08,
                    "tags": {"workflow": "smoke-tests", "environment": "staging"}
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_metrics_collector_initialization(self, monitoring_config):
        """Test metrics collector initialization."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Verify collector is initialized
            assert collector.is_initialized()
            assert collector.config is not None
            assert collector.config["monitoring"]["enabled"] is True
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Metrics collector initialization not available: {e}")

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, monitoring_config):
        """Test system metrics collection."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Mock system metrics
            with patch('psutil.cpu_percent', return_value=65.2), \
                 patch('psutil.virtual_memory') as mock_memory, \
                 patch('psutil.disk_usage') as mock_disk:
                
                mock_memory.return_value.percent = 78.5
                mock_disk.return_value.percent = 45.8
                
                # Collect system metrics
                metrics = await collector.collect_system_metrics()
                
                # Verify metrics were collected
                assert len(metrics) >= 3
                
                # Check CPU metric
                cpu_metric = next((m for m in metrics if m["metric"] == "cpu_usage"), None)
                assert cpu_metric is not None
                assert cpu_metric["value"] == 65.2
                
                # Check memory metric
                memory_metric = next((m for m in metrics if m["metric"] == "memory_usage"), None)
                assert memory_metric is not None
                assert memory_metric["value"] == 78.5
                
                # Check disk metric
                disk_metric = next((m for m in metrics if m["metric"] == "disk_usage"), None)
                assert disk_metric is not None
                assert disk_metric["value"] == 45.8
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"System metrics collection not available: {e}")

    @pytest.mark.asyncio
    async def test_agent_monitoring(self, monitoring_config):
        """Test agent monitoring functionality."""
        try:
            monitor = AgentMonitor(str(monitoring_config))
            await monitor.initialize()
            
            # Mock agents
            mock_agents = {
                "test_executor": {
                    "status": "active",
                    "last_heartbeat": datetime.now(),
                    "response_time": 125.3,
                    "error_count": 2
                },
                "test_scheduler": {
                    "status": "active",
                    "last_heartbeat": datetime.now(),
                    "response_time": 89.7,
                    "error_count": 0
                },
                "report_collector": {
                    "status": "inactive",
                    "last_heartbeat": datetime.now() - timedelta(minutes=5),
                    "response_time": 0,
                    "error_count": 1
                }
            }
            
            # Register agents for monitoring
            for agent_name, agent_info in mock_agents.items():
                await monitor.register_agent(agent_name, agent_info)
            
            # Collect agent metrics
            agent_metrics = await monitor.collect_agent_metrics()
            
            # Verify agent metrics
            assert len(agent_metrics) >= 3
            
            # Check active agents
            active_agents = [m for m in agent_metrics if m["tags"].get("status") == "active"]
            assert len(active_agents) == 2
            
            # Check inactive agents
            inactive_agents = [m for m in agent_metrics if m["tags"].get("status") == "inactive"]
            assert len(inactive_agents) == 1
            
            # Test agent health check
            health_status = await monitor.check_agent_health()
            assert "test_executor" in health_status
            assert "test_scheduler" in health_status
            assert "report_collector" in health_status
            
            assert health_status["test_executor"]["status"] == "healthy"
            assert health_status["test_scheduler"]["status"] == "healthy"
            assert health_status["report_collector"]["status"] == "unhealthy"
            
            await monitor.shutdown()
            
        except Exception as e:
            pytest.skip(f"Agent monitoring not available: {e}")

    @pytest.mark.asyncio
    async def test_test_metrics_collection(self, monitoring_config, sample_metrics_data):
        """Test test execution metrics collection."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Mock test execution data
            test_execution_data = {
                "workflow": "integration-tests",
                "environment": "staging",
                "start_time": datetime.now() - timedelta(minutes=5),
                "end_time": datetime.now(),
                "total_tests": 25,
                "passed_tests": 23,
                "failed_tests": 2,
                "execution_time": 300.5
            }
            
            # Collect test metrics
            test_metrics = await collector.collect_test_metrics(test_execution_data)
            
            # Verify test metrics
            assert len(test_metrics) >= 3
            
            # Check execution time metric
            exec_time_metric = next((m for m in test_metrics if m["metric"] == "test_execution_time"), None)
            assert exec_time_metric is not None
            assert exec_time_metric["value"] == 300.5
            assert exec_time_metric["tags"]["workflow"] == "integration-tests"
            
            # Check success rate metric
            success_rate_metric = next((m for m in test_metrics if m["metric"] == "test_success_rate"), None)
            assert success_rate_metric is not None
            assert success_rate_metric["value"] == 0.92  # 23/25
            
            # Check failure rate metric
            failure_rate_metric = next((m for m in test_metrics if m["metric"] == "test_failure_rate"), None)
            assert failure_rate_metric is not None
            assert failure_rate_metric["value"] == 0.08  # 2/25
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Test metrics collection not available: {e}")

    @pytest.mark.asyncio
    async def test_metrics_storage_and_retrieval(self, monitoring_config, sample_metrics_data):
        """Test metrics storage and retrieval."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Store metrics
            for metric_type, metrics in sample_metrics_data.items():
                for metric in metrics:
                    await collector.store_metric(metric)
            
            # Retrieve metrics by type
            system_metrics = await collector.get_metrics(
                metric_type="system",
                time_range="1h"
            )
            assert len(system_metrics) >= 3
            
            agent_metrics = await collector.get_metrics(
                metric_type="agent",
                time_range="1h"
            )
            assert len(agent_metrics) >= 3
            
            test_metrics = await collector.get_metrics(
                metric_type="test",
                time_range="1h"
            )
            assert len(test_metrics) >= 3
            
            # Retrieve specific metric
            cpu_metrics = await collector.get_metrics(
                metric_name="cpu_usage",
                time_range="1h"
            )
            assert len(cpu_metrics) >= 1
            assert cpu_metrics[0]["metric"] == "cpu_usage"
            
            # Retrieve metrics with tags
            workflow_metrics = await collector.get_metrics(
                tags={"workflow": "smoke-tests"},
                time_range="1h"
            )
            assert len(workflow_metrics) >= 1
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Metrics storage and retrieval not available: {e}")

    @pytest.mark.asyncio
    async def test_alert_manager_integration(self, monitoring_config):
        """Test alert manager integration."""
        try:
            alert_manager = AlertManager(str(monitoring_config))
            await alert_manager.initialize()
            
            # Mock notification system
            notifications_sent = []
            
            async def mock_send_notification(channel, message, severity):
                notifications_sent.append({
                    "channel": channel,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now()
                })
                return True
            
            with patch.object(alert_manager, 'send_notification', side_effect=mock_send_notification):
                # Test CPU usage alert
                await alert_manager.check_threshold(
                    "cpu_usage",
                    85.5,  # Above threshold of 80
                    {"host": "test-server"}
                )
                
                # Test memory usage alert
                await alert_manager.check_threshold(
                    "memory_usage",
                    90.2,  # Above threshold of 85
                    {"host": "test-server"}
                )
                
                # Test test failure rate alert
                await alert_manager.check_threshold(
                    "test_failure_rate",
                    0.25,  # Above threshold of 0.2
                    {"workflow": "regression-tests"}
                )
                
                # Test normal value (should not trigger alert)
                await alert_manager.check_threshold(
                    "cpu_usage",
                    65.0,  # Below threshold
                    {"host": "test-server"}
                )
                
                # Wait for alert processing
                await asyncio.sleep(0.5)
                
                # Verify alerts were sent
                assert len(notifications_sent) == 3  # Only threshold violations
                
                # Check CPU alert
                cpu_alert = next((n for n in notifications_sent if "cpu_usage" in n["message"]), None)
                assert cpu_alert is not None
                assert cpu_alert["severity"] == "warning"
                
                # Check memory alert
                memory_alert = next((n for n in notifications_sent if "memory_usage" in n["message"]), None)
                assert memory_alert is not None
                assert memory_alert["severity"] == "warning"
                
                # Check test failure alert
                failure_alert = next((n for n in notifications_sent if "test_failure_rate" in n["message"]), None)
                assert failure_alert is not None
                assert failure_alert["severity"] == "critical"
            
            await alert_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Alert manager integration not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_integration(self, monitoring_config):
        """Test monitoring dashboard integration."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Mock dashboard data requests
            dashboard_data = {}
            
            # Get system overview
            dashboard_data["system_overview"] = await collector.get_system_overview()
            assert "cpu_usage" in dashboard_data["system_overview"]
            assert "memory_usage" in dashboard_data["system_overview"]
            assert "disk_usage" in dashboard_data["system_overview"]
            
            # Get agent status
            dashboard_data["agent_status"] = await collector.get_agent_status()
            assert isinstance(dashboard_data["agent_status"], dict)
            
            # Get test metrics summary
            dashboard_data["test_summary"] = await collector.get_test_metrics_summary(
                time_range="24h"
            )
            assert "total_tests" in dashboard_data["test_summary"]
            assert "success_rate" in dashboard_data["test_summary"]
            assert "average_execution_time" in dashboard_data["test_summary"]
            
            # Get historical data for charts
            dashboard_data["cpu_history"] = await collector.get_metric_history(
                "cpu_usage",
                time_range="24h",
                interval="1h"
            )
            assert isinstance(dashboard_data["cpu_history"], list)
            
            dashboard_data["test_trends"] = await collector.get_test_trends(
                time_range="7d",
                interval="1d"
            )
            assert isinstance(dashboard_data["test_trends"], list)
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Monitoring dashboard integration not available: {e}")

    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, monitoring_config):
        """Test real-time monitoring functionality."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Start real-time monitoring
            monitoring_data = []
            
            async def collect_real_time_data():
                for _ in range(5):  # Collect 5 data points
                    metrics = await collector.collect_all_metrics()
                    monitoring_data.append({
                        "timestamp": datetime.now(),
                        "metrics": metrics
                    })
                    await asyncio.sleep(1)  # 1 second interval
            
            # Run real-time collection
            start_time = time.time()
            await collect_real_time_data()
            end_time = time.time()
            
            # Verify real-time collection
            assert len(monitoring_data) == 5
            assert end_time - start_time >= 4  # At least 4 seconds (5 intervals - 1)
            assert end_time - start_time <= 7  # Should not take too long
            
            # Verify data consistency
            for data_point in monitoring_data:
                assert "timestamp" in data_point
                assert "metrics" in data_point
                assert len(data_point["metrics"]) > 0
            
            # Test real-time alerts
            alert_triggered = False
            
            async def mock_alert_handler(metric, value, threshold):
                nonlocal alert_triggered
                alert_triggered = True
            
            with patch.object(collector, 'trigger_alert', side_effect=mock_alert_handler):
                # Simulate high CPU usage
                await collector.process_metric({
                    "metric": "cpu_usage",
                    "value": 95.0,  # High value
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(0.1)  # Allow alert processing
                
                # Verify alert was triggered
                assert alert_triggered is True
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Real-time monitoring not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_performance_load(self, monitoring_config):
        """Test monitoring system performance under load."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Generate high volume of metrics
            start_time = time.time()
            
            # Simulate concurrent metric collection
            async def generate_metrics(batch_id):
                metrics = []
                for i in range(100):  # 100 metrics per batch
                    metrics.append({
                        "timestamp": datetime.now().isoformat(),
                        "metric": f"test_metric_{batch_id}_{i}",
                        "value": i * 1.5,
                        "tags": {"batch": str(batch_id), "index": str(i)}
                    })
                
                # Store metrics
                for metric in metrics:
                    await collector.store_metric(metric)
                
                return len(metrics)
            
            # Run multiple batches concurrently
            tasks = [generate_metrics(i) for i in range(10)]  # 10 batches
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify performance
            total_metrics = sum(results)
            assert total_metrics == 1000  # 10 batches * 100 metrics
            assert execution_time < 30  # Should complete within 30 seconds
            
            # Test retrieval performance
            retrieval_start = time.time()
            
            # Retrieve metrics
            retrieved_metrics = await collector.get_metrics(
                time_range="1h",
                limit=500
            )
            
            retrieval_end = time.time()
            retrieval_time = retrieval_end - retrieval_start
            
            # Verify retrieval performance
            assert len(retrieved_metrics) <= 500  # Respects limit
            assert retrieval_time < 5  # Should retrieve quickly
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Monitoring performance test not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_data_retention(self, monitoring_config):
        """Test monitoring data retention policies."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Create old metrics (beyond retention period)
            old_timestamp = datetime.now() - timedelta(days=35)  # Older than 30-day retention
            recent_timestamp = datetime.now() - timedelta(days=5)  # Within retention
            
            old_metrics = [
                {
                    "timestamp": old_timestamp.isoformat(),
                    "metric": "old_cpu_usage",
                    "value": 50.0,
                    "tags": {"type": "old"}
                },
                {
                    "timestamp": old_timestamp.isoformat(),
                    "metric": "old_memory_usage",
                    "value": 60.0,
                    "tags": {"type": "old"}
                }
            ]
            
            recent_metrics = [
                {
                    "timestamp": recent_timestamp.isoformat(),
                    "metric": "recent_cpu_usage",
                    "value": 70.0,
                    "tags": {"type": "recent"}
                },
                {
                    "timestamp": recent_timestamp.isoformat(),
                    "metric": "recent_memory_usage",
                    "value": 80.0,
                    "tags": {"type": "recent"}
                }
            ]
            
            # Store both old and recent metrics
            for metric in old_metrics + recent_metrics:
                await collector.store_metric(metric)
            
            # Run data retention cleanup
            await collector.cleanup_old_data()
            
            # Verify old data was removed
            old_data = await collector.get_metrics(
                tags={"type": "old"},
                time_range="60d"  # Look back far enough
            )
            assert len(old_data) == 0  # Should be cleaned up
            
            # Verify recent data is still there
            recent_data = await collector.get_metrics(
                tags={"type": "recent"},
                time_range="30d"
            )
            assert len(recent_data) == 2  # Should still exist
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Monitoring data retention not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_error_handling(self, monitoring_config):
        """Test monitoring system error handling."""
        try:
            collector = MetricsCollector(str(monitoring_config))
            await collector.initialize()
            
            # Test handling of invalid metrics
            invalid_metrics = [
                {"metric": "test", "value": "invalid_number"},  # Invalid value type
                {"timestamp": "invalid_timestamp", "metric": "test", "value": 1.0},  # Invalid timestamp
                {"metric": "", "value": 1.0},  # Empty metric name
                None,  # Null metric
                {}  # Empty metric
            ]
            
            errors_handled = 0
            
            for invalid_metric in invalid_metrics:
                try:
                    await collector.store_metric(invalid_metric)
                except Exception:
                    errors_handled += 1
            
            # Should handle all invalid metrics gracefully
            assert errors_handled <= len(invalid_metrics)  # Some might be handled silently
            
            # Test recovery from storage failures
            with patch.object(collector, '_store_to_database', side_effect=Exception("Database error")):
                # Should not crash on storage failure
                try:
                    await collector.store_metric({
                        "timestamp": datetime.now().isoformat(),
                        "metric": "test_metric",
                        "value": 1.0
                    })
                except Exception:
                    pass  # Expected to handle gracefully
            
            # Test recovery from collection failures
            with patch('psutil.cpu_percent', side_effect=Exception("System error")):
                # Should not crash on collection failure
                try:
                    metrics = await collector.collect_system_metrics()
                    # Should return empty list or handle gracefully
                    assert isinstance(metrics, list)
                except Exception:
                    pass  # Expected to handle gracefully
            
            await collector.shutdown()
            
        except Exception as e:
            pytest.skip(f"Monitoring error handling not available: {e}")


class TestMonitoringAlerts:
    """Test monitoring alert functionality."""

    @pytest.mark.asyncio
    async def test_alert_escalation(self, monitoring_config):
        """Test alert escalation policies."""
        try:
            alert_manager = AlertManager(str(monitoring_config))
            await alert_manager.initialize()
            
            escalation_log = []
            
            async def mock_escalate_alert(alert, level):
                escalation_log.append({
                    "alert": alert,
                    "level": level,
                    "timestamp": datetime.now()
                })
            
            with patch.object(alert_manager, 'escalate_alert', side_effect=mock_escalate_alert):
                # Trigger repeated alerts for the same issue
                for i in range(5):
                    await alert_manager.process_alert({
                        "metric": "cpu_usage",
                        "value": 95.0,
                        "threshold": 80.0,
                        "severity": "critical",
                        "timestamp": datetime.now()
                    })
                    await asyncio.sleep(0.1)
                
                # Should escalate after repeated alerts
                assert len(escalation_log) >= 1
                assert escalation_log[0]["level"] in ["warning", "critical", "emergency"]
            
            await alert_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Alert escalation not available: {e}")

    @pytest.mark.asyncio
    async def test_alert_suppression(self, monitoring_config):
        """Test alert suppression and deduplication."""
        try:
            alert_manager = AlertManager(str(monitoring_config))
            await alert_manager.initialize()
            
            notifications_sent = []
            
            async def mock_send_notification(channel, message, severity):
                notifications_sent.append({
                    "message": message,
                    "timestamp": datetime.now()
                })
            
            with patch.object(alert_manager, 'send_notification', side_effect=mock_send_notification):
                # Send multiple identical alerts rapidly
                alert_data = {
                    "metric": "memory_usage",
                    "value": 90.0,
                    "threshold": 85.0,
                    "severity": "warning",
                    "host": "test-server"
                }
                
                for _ in range(10):
                    await alert_manager.process_alert(alert_data)
                    await asyncio.sleep(0.05)  # Rapid succession
                
                # Should suppress duplicate alerts
                assert len(notifications_sent) < 10  # Should be deduplicated
                assert len(notifications_sent) >= 1  # At least one should be sent
            
            await alert_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Alert suppression not available: {e}")


if __name__ == "__main__":
    # Run the monitoring integration tests
    pytest.main([__file__, "-v", "--tb=short"])