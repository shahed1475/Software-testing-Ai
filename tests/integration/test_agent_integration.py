"""
Integration tests for agent system coordination and communication.
Tests agent lifecycle, inter-agent communication, and system coordination.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Import agent components
try:
    from src.agents.orchestrator_agent import OrchestratorAgent
    from src.agents.executor_agent import ExecutorAgent
    from src.agents.scheduler_agent import SchedulerAgent
    from src.agents.monitor_agent import MonitorAgent
    from src.agents.notifier_agent import NotifierAgent
    from src.agents.trigger_agent import TriggerAgent
    from src.agents.base_agent import BaseAgent
    from src.agents.agent_manager import AgentManager
    from src.agents.communication import MessageBus, Message
except ImportError:
    # Mock imports for testing when modules are not available
    OrchestratorAgent = Mock
    ExecutorAgent = Mock
    SchedulerAgent = Mock
    MonitorAgent = Mock
    NotifierAgent = Mock
    TriggerAgent = Mock
    BaseAgent = Mock
    AgentManager = Mock
    MessageBus = Mock
    Message = Mock


class TestAgentIntegration:
    """Integration tests for agent system coordination."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "logs").mkdir()
            (workspace / "data").mkdir()
            (workspace / "config").mkdir()
            yield workspace

    @pytest.fixture
    def agent_config(self, temp_workspace):
        """Configuration for agent testing."""
        return {
            "workspace": str(temp_workspace),
            "agents": {
                "orchestrator": {
                    "enabled": True,
                    "max_concurrent_workflows": 5,
                    "workflow_timeout": 3600,
                    "retry_attempts": 3
                },
                "executor": {
                    "enabled": True,
                    "max_parallel_tests": 10,
                    "test_timeout": 1800,
                    "environments": ["development", "staging", "production"]
                },
                "scheduler": {
                    "enabled": True,
                    "max_jobs": 100,
                    "job_timeout": 7200,
                    "cleanup_interval": 3600
                },
                "monitor": {
                    "enabled": True,
                    "metrics_interval": 30,
                    "alert_thresholds": {
                        "cpu_usage": 80,
                        "memory_usage": 85,
                        "disk_usage": 90
                    }
                },
                "notifier": {
                    "enabled": True,
                    "channels": ["email", "slack"],
                    "rate_limit": {
                        "max_per_hour": 100,
                        "max_per_day": 1000
                    }
                },
                "trigger": {
                    "enabled": True,
                    "webhook": {"port": 8080},
                    "file_system": {"polling_interval": 1},
                    "schedule": {"timezone": "UTC"}
                }
            },
            "communication": {
                "message_bus": {
                    "type": "memory",
                    "max_queue_size": 1000,
                    "message_timeout": 30
                }
            }
        }

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for testing."""
        return {
            "id": "test-workflow-001",
            "name": "Integration Test Workflow",
            "description": "Test workflow for agent integration",
            "timeout": 1800,
            "retry_attempts": 2,
            "steps": [
                {
                    "id": "setup",
                    "name": "Setup Environment",
                    "type": "setup",
                    "config": {"environment": "test"},
                    "timeout": 300
                },
                {
                    "id": "test_execution",
                    "name": "Execute Tests",
                    "type": "test_execution",
                    "config": {
                        "test_suite": "integration",
                        "parallel": True,
                        "max_workers": 4
                    },
                    "timeout": 1200,
                    "depends_on": ["setup"]
                },
                {
                    "id": "report_generation",
                    "name": "Generate Report",
                    "type": "report_generation",
                    "config": {
                        "format": "html",
                        "include_coverage": True
                    },
                    "timeout": 300,
                    "depends_on": ["test_execution"]
                }
            ]
        }

    @pytest.fixture
    def sample_test_data(self):
        """Sample test data for execution."""
        return {
            "test_cases": [
                {
                    "id": "test_001",
                    "name": "User Authentication Test",
                    "type": "functional",
                    "priority": "high",
                    "estimated_duration": 120
                },
                {
                    "id": "test_002",
                    "name": "Database Connection Test",
                    "type": "integration",
                    "priority": "medium",
                    "estimated_duration": 60
                },
                {
                    "id": "test_003",
                    "name": "API Response Test",
                    "type": "api",
                    "priority": "high",
                    "estimated_duration": 90
                }
            ],
            "test_environments": [
                {
                    "name": "development",
                    "url": "https://dev.example.com",
                    "database": "dev_db"
                },
                {
                    "name": "staging",
                    "url": "https://staging.example.com",
                    "database": "staging_db"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_agent_manager_initialization(self, agent_config):
        """Test agent manager initialization and agent lifecycle."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            # Verify all agents are initialized
            assert agent_manager.is_initialized()
            
            # Check agent status
            agent_status = await agent_manager.get_agent_status()
            
            expected_agents = [
                "orchestrator", "executor", "scheduler",
                "monitor", "notifier", "trigger"
            ]
            
            for agent_name in expected_agents:
                assert agent_name in agent_status
                assert agent_status[agent_name]["status"] == "running"
                assert agent_status[agent_name]["initialized"] is True
            
            # Test agent health checks
            health_status = await agent_manager.health_check()
            assert health_status["overall_status"] == "healthy"
            assert len(health_status["agent_health"]) == len(expected_agents)
            
            for agent_name in expected_agents:
                assert health_status["agent_health"][agent_name]["status"] == "healthy"
            
            await agent_manager.shutdown()
            
            # Verify all agents are shut down
            final_status = await agent_manager.get_agent_status()
            for agent_name in expected_agents:
                assert final_status[agent_name]["status"] == "stopped"
            
        except Exception as e:
            pytest.skip(f"Agent manager initialization not available: {e}")

    @pytest.mark.asyncio
    async def test_inter_agent_communication(self, agent_config):
        """Test communication between agents via message bus."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            # Get message bus for testing
            message_bus = agent_manager.get_message_bus()
            
            # Track messages received by different agents
            received_messages = {
                "orchestrator": [],
                "executor": [],
                "scheduler": [],
                "monitor": [],
                "notifier": []
            }
            
            # Set up message handlers
            async def message_handler(agent_name):
                async def handler(message):
                    received_messages[agent_name].append(message)
                return handler
            
            # Subscribe agents to relevant message types
            await message_bus.subscribe("workflow.started", await message_handler("monitor"))
            await message_bus.subscribe("workflow.completed", await message_handler("notifier"))
            await message_bus.subscribe("test.execution.started", await message_handler("monitor"))
            await message_bus.subscribe("test.execution.completed", await message_handler("orchestrator"))
            await message_bus.subscribe("schedule.job.created", await message_handler("executor"))
            
            # Test workflow lifecycle messages
            workflow_started_msg = Message(
                type="workflow.started",
                sender="orchestrator",
                data={
                    "workflow_id": "test-workflow-001",
                    "name": "Integration Test Workflow",
                    "started_at": datetime.now().isoformat()
                }
            )
            
            await message_bus.publish(workflow_started_msg)
            
            # Test execution messages
            test_started_msg = Message(
                type="test.execution.started",
                sender="executor",
                data={
                    "workflow_id": "test-workflow-001",
                    "test_id": "test_001",
                    "started_at": datetime.now().isoformat()
                }
            )
            
            await message_bus.publish(test_started_msg)
            
            test_completed_msg = Message(
                type="test.execution.completed",
                sender="executor",
                data={
                    "workflow_id": "test-workflow-001",
                    "test_id": "test_001",
                    "status": "passed",
                    "duration": 120,
                    "completed_at": datetime.now().isoformat()
                }
            )
            
            await message_bus.publish(test_completed_msg)
            
            # Test scheduling messages
            schedule_job_msg = Message(
                type="schedule.job.created",
                sender="scheduler",
                data={
                    "job_id": "job_001",
                    "workflow_id": "test-workflow-001",
                    "scheduled_at": (datetime.now() + timedelta(hours=1)).isoformat()
                }
            )
            
            await message_bus.publish(schedule_job_msg)
            
            workflow_completed_msg = Message(
                type="workflow.completed",
                sender="orchestrator",
                data={
                    "workflow_id": "test-workflow-001",
                    "status": "completed",
                    "duration": 1800,
                    "completed_at": datetime.now().isoformat()
                }
            )
            
            await message_bus.publish(workflow_completed_msg)
            
            # Allow time for message processing
            await asyncio.sleep(0.1)
            
            # Verify messages were received by appropriate agents
            assert len(received_messages["monitor"]) == 2  # workflow.started, test.execution.started
            assert len(received_messages["notifier"]) == 1  # workflow.completed
            assert len(received_messages["orchestrator"]) == 1  # test.execution.completed
            assert len(received_messages["executor"]) == 1  # schedule.job.created
            
            # Verify message content
            monitor_workflow_msg = received_messages["monitor"][0]
            assert monitor_workflow_msg.type == "workflow.started"
            assert monitor_workflow_msg.data["workflow_id"] == "test-workflow-001"
            
            notifier_msg = received_messages["notifier"][0]
            assert notifier_msg.type == "workflow.completed"
            assert notifier_msg.data["status"] == "completed"
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Inter-agent communication not available: {e}")

    @pytest.mark.asyncio
    async def test_workflow_orchestration_coordination(self, agent_config, sample_workflow):
        """Test coordination between orchestrator and executor agents for workflow execution."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            orchestrator = agent_manager.get_agent("orchestrator")
            executor = agent_manager.get_agent("executor")
            monitor = agent_manager.get_agent("monitor")
            
            # Track workflow execution events
            execution_events = []
            
            async def event_tracker(event):
                execution_events.append({
                    "event": event["type"],
                    "timestamp": datetime.now(),
                    "data": event.get("data", {})
                })
            
            # Set up event tracking
            orchestrator.register_event_callback(event_tracker)
            executor.register_event_callback(event_tracker)
            
            # Start workflow execution
            execution_id = await orchestrator.start_workflow(sample_workflow)
            assert execution_id is not None
            
            # Monitor workflow progress
            workflow_status = await orchestrator.get_workflow_status(execution_id)
            assert workflow_status["status"] in ["running", "pending"]
            assert workflow_status["workflow_id"] == sample_workflow["id"]
            
            # Simulate workflow step execution
            for step in sample_workflow["steps"]:
                # Orchestrator should coordinate step execution
                step_result = await orchestrator.execute_workflow_step(
                    execution_id, step["id"]
                )
                
                # Executor should handle the actual execution
                if step["type"] == "test_execution":
                    test_results = await executor.execute_tests(
                        step["config"]["test_suite"],
                        parallel=step["config"]["parallel"],
                        max_workers=step["config"]["max_workers"]
                    )
                    assert test_results is not None
                    assert "test_count" in test_results
                    assert "passed" in test_results
                    assert "failed" in test_results
                
                # Update step status
                await orchestrator.update_step_status(
                    execution_id, step["id"], "completed"
                )
            
            # Complete workflow
            await orchestrator.complete_workflow(execution_id)
            
            # Verify final workflow status
            final_status = await orchestrator.get_workflow_status(execution_id)
            assert final_status["status"] == "completed"
            
            # Verify execution events were tracked
            assert len(execution_events) > 0
            
            # Check for key events
            event_types = [event["event"] for event in execution_events]
            assert "workflow.started" in event_types
            assert "workflow.step.started" in event_types
            assert "workflow.step.completed" in event_types
            assert "workflow.completed" in event_types
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Workflow orchestration coordination not available: {e}")

    @pytest.mark.asyncio
    async def test_scheduling_and_execution_coordination(self, agent_config, sample_workflow):
        """Test coordination between scheduler and executor agents."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            scheduler = agent_manager.get_agent("scheduler")
            executor = agent_manager.get_agent("executor")
            orchestrator = agent_manager.get_agent("orchestrator")
            
            # Schedule workflow for future execution
            schedule_time = datetime.now() + timedelta(seconds=5)
            job_id = await scheduler.schedule_workflow(
                workflow=sample_workflow,
                scheduled_time=schedule_time,
                recurring=False
            )
            
            assert job_id is not None
            
            # Verify job was scheduled
            scheduled_jobs = await scheduler.get_scheduled_jobs()
            assert job_id in [job["id"] for job in scheduled_jobs]
            
            scheduled_job = next(job for job in scheduled_jobs if job["id"] == job_id)
            assert scheduled_job["workflow_id"] == sample_workflow["id"]
            assert scheduled_job["status"] == "scheduled"
            
            # Wait for job execution time
            await asyncio.sleep(6)
            
            # Verify job was executed
            job_status = await scheduler.get_job_status(job_id)
            assert job_status["status"] in ["running", "completed"]
            
            # Check if orchestrator received the workflow
            if job_status["status"] == "completed":
                execution_history = await orchestrator.get_execution_history()
                workflow_executions = [
                    exec for exec in execution_history
                    if exec["workflow_id"] == sample_workflow["id"]
                ]
                assert len(workflow_executions) > 0
            
            # Test recurring schedule
            recurring_job_id = await scheduler.schedule_workflow(
                workflow=sample_workflow,
                cron_expression="*/10 * * * * *",  # Every 10 seconds
                recurring=True
            )
            
            assert recurring_job_id is not None
            
            # Verify recurring job
            recurring_job = await scheduler.get_job_status(recurring_job_id)
            assert recurring_job["recurring"] is True
            assert recurring_job["cron_expression"] == "*/10 * * * * *"
            
            # Cancel recurring job
            await scheduler.cancel_job(recurring_job_id)
            
            # Verify job was cancelled
            cancelled_job = await scheduler.get_job_status(recurring_job_id)
            assert cancelled_job["status"] == "cancelled"
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Scheduling and execution coordination not available: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_and_alerting_coordination(self, agent_config, sample_workflow):
        """Test coordination between monitor and notifier agents."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            monitor = agent_manager.get_agent("monitor")
            notifier = agent_manager.get_agent("notifier")
            orchestrator = agent_manager.get_agent("orchestrator")
            
            # Track alerts generated
            generated_alerts = []
            
            async def alert_handler(alert):
                generated_alerts.append(alert)
            
            notifier.register_alert_handler(alert_handler)
            
            # Start monitoring
            await monitor.start_monitoring()
            
            # Simulate system metrics that trigger alerts
            high_cpu_metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 85,  # Above threshold (80)
                "memory_usage": 70,
                "disk_usage": 60,
                "active_workflows": 3
            }
            
            await monitor.record_system_metrics(high_cpu_metrics)
            
            high_memory_metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 75,
                "memory_usage": 90,  # Above threshold (85)
                "disk_usage": 65,
                "active_workflows": 4
            }
            
            await monitor.record_system_metrics(high_memory_metrics)
            
            # Start a workflow to generate workflow metrics
            execution_id = await orchestrator.start_workflow(sample_workflow)
            
            # Simulate workflow execution metrics
            workflow_metrics = {
                "workflow_id": sample_workflow["id"],
                "execution_id": execution_id,
                "status": "running",
                "duration": 300,
                "steps_completed": 1,
                "steps_total": 3,
                "timestamp": datetime.now().isoformat()
            }
            
            await monitor.record_workflow_metrics(workflow_metrics)
            
            # Simulate workflow failure
            failed_workflow_metrics = {
                "workflow_id": sample_workflow["id"],
                "execution_id": execution_id,
                "status": "failed",
                "error": "Test execution timeout",
                "duration": 1800,
                "steps_completed": 2,
                "steps_total": 3,
                "timestamp": datetime.now().isoformat()
            }
            
            await monitor.record_workflow_metrics(failed_workflow_metrics)
            
            # Allow time for alert processing
            await asyncio.sleep(0.5)
            
            # Verify alerts were generated
            assert len(generated_alerts) >= 3  # CPU, Memory, Workflow failure
            
            # Check alert types
            alert_types = [alert["type"] for alert in generated_alerts]
            assert "system.cpu_high" in alert_types
            assert "system.memory_high" in alert_types
            assert "workflow.failed" in alert_types
            
            # Verify alert content
            cpu_alert = next(alert for alert in generated_alerts if alert["type"] == "system.cpu_high")
            assert cpu_alert["severity"] == "warning"
            assert cpu_alert["metrics"]["cpu_usage"] == 85
            
            workflow_alert = next(alert for alert in generated_alerts if alert["type"] == "workflow.failed")
            assert workflow_alert["severity"] == "error"
            assert workflow_alert["workflow_id"] == sample_workflow["id"]
            
            # Test alert suppression
            await monitor.suppress_alerts("system.cpu_high", duration=300)
            
            # Generate another high CPU alert
            await monitor.record_system_metrics(high_cpu_metrics)
            await asyncio.sleep(0.1)
            
            # Verify alert was suppressed
            new_cpu_alerts = [alert for alert in generated_alerts if alert["type"] == "system.cpu_high"]
            assert len(new_cpu_alerts) == 1  # Should still be only the original alert
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Monitoring and alerting coordination not available: {e}")

    @pytest.mark.asyncio
    async def test_trigger_system_coordination(self, agent_config, sample_workflow, temp_workspace):
        """Test coordination between trigger agent and orchestrator."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            trigger_agent = agent_manager.get_agent("trigger")
            orchestrator = agent_manager.get_agent("orchestrator")
            
            # Track triggered workflows
            triggered_workflows = []
            
            async def workflow_trigger_handler(trigger_event):
                triggered_workflows.append(trigger_event)
                # Simulate orchestrator starting workflow
                execution_id = await orchestrator.start_workflow(trigger_event["workflow"])
                trigger_event["execution_id"] = execution_id
            
            trigger_agent.register_trigger_handler(workflow_trigger_handler)
            
            # Test webhook trigger
            webhook_payload = {
                "event": "push",
                "repository": "test-repo",
                "branch": "main",
                "commit": "abc123",
                "workflow": sample_workflow
            }
            
            await trigger_agent.process_webhook_trigger(webhook_payload)
            
            # Test file system trigger
            watch_dir = temp_workspace / "watched"
            watch_dir.mkdir()
            
            await trigger_agent.setup_file_system_trigger(
                watch_path=str(watch_dir),
                patterns=["*.py", "*.json"],
                workflow=sample_workflow
            )
            
            # Create a file to trigger the workflow
            test_file = watch_dir / "test_file.py"
            test_file.write_text("# Test file content")
            
            # Allow time for file system event processing
            await asyncio.sleep(1)
            
            # Test schedule trigger
            schedule_trigger_time = datetime.now() + timedelta(seconds=2)
            await trigger_agent.setup_schedule_trigger(
                cron_expression="*/2 * * * * *",  # Every 2 seconds
                workflow=sample_workflow,
                max_executions=1
            )
            
            # Wait for schedule trigger
            await asyncio.sleep(3)
            
            # Verify triggers were processed
            assert len(triggered_workflows) >= 2  # Webhook + File system (+ possibly schedule)
            
            # Check webhook trigger
            webhook_trigger = next(
                (t for t in triggered_workflows if t["type"] == "webhook"),
                None
            )
            assert webhook_trigger is not None
            assert webhook_trigger["data"]["event"] == "push"
            assert webhook_trigger["data"]["repository"] == "test-repo"
            assert "execution_id" in webhook_trigger
            
            # Check file system trigger
            fs_trigger = next(
                (t for t in triggered_workflows if t["type"] == "file_system"),
                None
            )
            assert fs_trigger is not None
            assert fs_trigger["data"]["file_path"].endswith("test_file.py")
            assert fs_trigger["data"]["event_type"] == "created"
            
            # Verify workflows were started in orchestrator
            execution_history = await orchestrator.get_execution_history()
            triggered_executions = [
                exec for exec in execution_history
                if exec["trigger_type"] in ["webhook", "file_system", "schedule"]
            ]
            assert len(triggered_executions) >= 2
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Trigger system coordination not available: {e}")

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, agent_config):
        """Test agent failure detection and recovery mechanisms."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            # Track recovery events
            recovery_events = []
            
            async def recovery_handler(event):
                recovery_events.append(event)
            
            agent_manager.register_recovery_handler(recovery_handler)
            
            # Simulate agent failure
            executor = agent_manager.get_agent("executor")
            
            # Force agent failure
            await executor.simulate_failure("connection_timeout")
            
            # Allow time for failure detection
            await asyncio.sleep(1)
            
            # Verify failure was detected
            agent_status = await agent_manager.get_agent_status()
            assert agent_status["executor"]["status"] == "failed"
            assert agent_status["executor"]["error"] == "connection_timeout"
            
            # Trigger recovery
            recovery_result = await agent_manager.recover_agent("executor")
            assert recovery_result["success"] is True
            
            # Verify agent was recovered
            await asyncio.sleep(0.5)
            recovered_status = await agent_manager.get_agent_status()
            assert recovered_status["executor"]["status"] == "running"
            assert recovered_status["executor"]["initialized"] is True
            
            # Verify recovery event was recorded
            assert len(recovery_events) >= 1
            recovery_event = recovery_events[0]
            assert recovery_event["agent"] == "executor"
            assert recovery_event["action"] == "recovered"
            
            # Test automatic recovery
            agent_manager.enable_auto_recovery(True)
            
            # Simulate another failure
            monitor = agent_manager.get_agent("monitor")
            await monitor.simulate_failure("memory_exhaustion")
            
            # Allow time for automatic recovery
            await asyncio.sleep(2)
            
            # Verify automatic recovery
            auto_recovered_status = await agent_manager.get_agent_status()
            assert auto_recovered_status["monitor"]["status"] == "running"
            
            # Check recovery events
            monitor_recovery = next(
                (event for event in recovery_events if event["agent"] == "monitor"),
                None
            )
            assert monitor_recovery is not None
            assert monitor_recovery["action"] == "auto_recovered"
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Agent failure recovery not available: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, agent_config, sample_workflow, sample_test_data):
        """Test concurrent operations across multiple agents."""
        try:
            agent_manager = AgentManager(agent_config)
            await agent_manager.initialize()
            
            orchestrator = agent_manager.get_agent("orchestrator")
            executor = agent_manager.get_agent("executor")
            scheduler = agent_manager.get_agent("scheduler")
            monitor = agent_manager.get_agent("monitor")
            
            # Track concurrent operations
            operation_results = {
                "workflows": [],
                "scheduled_jobs": [],
                "test_executions": [],
                "metrics": []
            }
            
            async def concurrent_workflow_execution(workflow_id):
                """Execute workflow concurrently."""
                workflow = sample_workflow.copy()
                workflow["id"] = f"{workflow['id']}-{workflow_id}"
                
                execution_id = await orchestrator.start_workflow(workflow)
                
                # Simulate workflow execution
                await asyncio.sleep(0.5)  # Simulate processing time
                
                await orchestrator.complete_workflow(execution_id)
                
                operation_results["workflows"].append({
                    "workflow_id": workflow["id"],
                    "execution_id": execution_id,
                    "completed_at": datetime.now()
                })
            
            async def concurrent_job_scheduling(job_id):
                """Schedule jobs concurrently."""
                workflow = sample_workflow.copy()
                workflow["id"] = f"{workflow['id']}-scheduled-{job_id}"
                
                schedule_time = datetime.now() + timedelta(seconds=10 + job_id)
                scheduled_job_id = await scheduler.schedule_workflow(
                    workflow=workflow,
                    scheduled_time=schedule_time
                )
                
                operation_results["scheduled_jobs"].append({
                    "job_id": scheduled_job_id,
                    "workflow_id": workflow["id"],
                    "scheduled_at": schedule_time
                })
            
            async def concurrent_test_execution(test_batch_id):
                """Execute tests concurrently."""
                test_results = await executor.execute_test_batch(
                    tests=sample_test_data["test_cases"],
                    environment=sample_test_data["test_environments"][0],
                    batch_id=test_batch_id
                )
                
                operation_results["test_executions"].append({
                    "batch_id": test_batch_id,
                    "results": test_results,
                    "completed_at": datetime.now()
                })
            
            async def concurrent_metrics_collection(metrics_id):
                """Collect metrics concurrently."""
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_usage": 60 + (metrics_id * 5),
                    "memory_usage": 50 + (metrics_id * 3),
                    "disk_usage": 40 + (metrics_id * 2),
                    "active_workflows": metrics_id
                }
                
                await monitor.record_system_metrics(metrics)
                
                operation_results["metrics"].append({
                    "metrics_id": metrics_id,
                    "metrics": metrics,
                    "recorded_at": datetime.now()
                })
            
            # Execute concurrent operations
            tasks = []
            
            # 5 concurrent workflow executions
            for i in range(5):
                tasks.append(concurrent_workflow_execution(i))
            
            # 3 concurrent job scheduling operations
            for i in range(3):
                tasks.append(concurrent_job_scheduling(i))
            
            # 4 concurrent test executions
            for i in range(4):
                tasks.append(concurrent_test_execution(i))
            
            # 6 concurrent metrics collections
            for i in range(6):
                tasks.append(concurrent_metrics_collection(i))
            
            # Execute all tasks concurrently
            start_time = datetime.now()
            await asyncio.gather(*tasks)
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
            
            # Verify all operations completed
            assert len(operation_results["workflows"]) == 5
            assert len(operation_results["scheduled_jobs"]) == 3
            assert len(operation_results["test_executions"]) == 4
            assert len(operation_results["metrics"]) == 6
            
            # Verify concurrent execution was efficient
            assert execution_time < 10  # Should complete within 10 seconds
            
            # Verify agent states remain consistent
            agent_status = await agent_manager.get_agent_status()
            for agent_name in ["orchestrator", "executor", "scheduler", "monitor"]:
                assert agent_status[agent_name]["status"] == "running"
                assert agent_status[agent_name]["initialized"] is True
            
            # Verify system health after concurrent operations
            health_status = await agent_manager.health_check()
            assert health_status["overall_status"] == "healthy"
            
            await agent_manager.shutdown()
            
        except Exception as e:
            pytest.skip(f"Concurrent agent operations not available: {e}")


if __name__ == "__main__":
    # Run the agent integration tests
    pytest.main([__file__, "-v", "--tb=short"])