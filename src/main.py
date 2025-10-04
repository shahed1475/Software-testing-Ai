#!/usr/bin/env python3
"""
Main entry point for the Test Automation Orchestrator.
Provides CLI interface for managing agents, workflows, and system operations.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import click
import json
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.agents.test_orchestrator import TestOrchestrator
    from src.agents.test_scheduler import TestScheduler
    from src.agents.trigger_system import TriggerSystem
    from src.dashboard.dashboard_app import DashboardApp
    from src.config.settings_manager import get_settings_manager, get_settings
    from src.config.environment_manager import EnvironmentManager
    from src.monitoring.logger_config import LoggerConfig, setup_logging
    from src.monitoring.agent_monitor import AgentMonitor
    from src.monitoring.system_monitor import SystemMonitor
    from src.monitoring.metrics_collector import MetricsCollector
except ImportError as e:
    print(f"Warning: Some modules could not be imported: {e}")
    print("The system will run with limited functionality.")
    # Define placeholder classes for missing components
    class TestOrchestrator:
        async def get_status(self): return {"status": "unavailable"}
        async def list_workflows(self): return []
        async def create_workflow(self, config): return "mock_id"
        async def execute_workflow(self, wf_id, params): return "mock_exec_id"
        async def stop(self): pass
    
    class TestScheduler:
        def get_status(self): return {"status": "unavailable"}
        def list_jobs(self): return []
        def create_job(self, config): return "mock_job_id"
        async def stop(self): pass
    
    class TriggerSystem:
        async def stop(self): pass
    
    class DashboardApp:
        def __init__(self, **kwargs): pass
        async def run(self, **kwargs): 
            print("Dashboard not available - missing dependencies")
        async def stop(self): pass
    
    class AgentMonitor:
        async def start(self): pass
        async def stop(self): pass
    
    class SystemMonitor:
        async def start(self): pass
        async def stop(self): pass
        def get_metrics(self): 
            return type('Metrics', (), {
                'cpu_percent': 0.0, 'memory_percent': 0.0, 
                'disk_percent': 0.0, 'health_score': 100.0
            })()
    
    class MetricsCollector:
        async def start(self): pass
        async def stop(self): pass
    
    def get_settings_manager():
        return type('SettingsManager', (), {'save': lambda: None, 'validate': lambda: None})()
    
    def get_settings():
        return type('Settings', (), {'to_dict': lambda: {}})()
    
    class EnvironmentManager:
        def get_environment(self, env): 
            return type('EnvConfig', (), {'to_dict': lambda: {}})()
        def validate_environment(self, env): pass
        def environment_exists(self, env): return False
        def create_environment(self, env, config): pass
    
    class LoggerConfig:
        def get_logger(self, name): 
            import logging
            return logging.getLogger(name)
    
    def setup_logging(config): pass


class OrchestratorCLI:
    """Main CLI class for the Test Automation Orchestrator."""
    
    def __init__(self):
        self.orchestrator: Optional[TestOrchestrator] = None
        self.scheduler: Optional[TestScheduler] = None
        self.trigger_system: Optional[TriggerSystem] = None
        self.dashboard: Optional[DashboardApp] = None
        self.agent_monitor: Optional[AgentMonitor] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.metrics_collector: Optional[MetricsCollector] = None
        self.logger = None
        
    async def initialize_system(self, environment: str = "development"):
        """Initialize the orchestrator system."""
        try:
            # Setup logging
            logger_config = LoggerConfig()
            setup_logging(logger_config)
            self.logger = logger_config.get_logger("main")
            
            self.logger.info(f"Initializing Test Automation Orchestrator in {environment} environment")
            
            # Load environment configuration
            env_manager = EnvironmentManager()
            env_config = env_manager.get_environment(environment)
            
            # Initialize monitoring components
            self.agent_monitor = AgentMonitor()
            self.system_monitor = SystemMonitor()
            self.metrics_collector = MetricsCollector()
            
            # Initialize core components
            self.orchestrator = TestOrchestrator()
            self.scheduler = TestScheduler()
            self.trigger_system = TriggerSystem()
            
            # Initialize dashboard
            self.dashboard = DashboardApp(
                orchestrator=self.orchestrator,
                scheduler=self.scheduler,
                trigger_system=self.trigger_system,
                agent_monitor=self.agent_monitor,
                system_monitor=self.system_monitor,
                metrics_collector=self.metrics_collector
            )
            
            # Start monitoring
            await self.agent_monitor.start()
            await self.system_monitor.start()
            await self.metrics_collector.start()
            
            self.logger.info("System initialization completed successfully")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize system: {e}")
            else:
                print(f"Failed to initialize system: {e}")
            raise
    
    async def shutdown_system(self):
        """Shutdown the orchestrator system gracefully."""
        if self.logger:
            self.logger.info("Shutting down Test Automation Orchestrator")
        
        # Stop components in reverse order
        if self.dashboard:
            await self.dashboard.stop()
        
        if self.trigger_system:
            await self.trigger_system.stop()
        
        if self.scheduler:
            await self.scheduler.stop()
        
        if self.orchestrator:
            await self.orchestrator.stop()
        
        # Stop monitoring
        if self.metrics_collector:
            await self.metrics_collector.stop()
        
        if self.system_monitor:
            await self.system_monitor.stop()
        
        if self.agent_monitor:
            await self.agent_monitor.stop()
        
        if self.logger:
            self.logger.info("System shutdown completed")


# Global CLI instance
cli_instance = OrchestratorCLI()


@click.group()
@click.option('--environment', '-e', default='development', 
              help='Environment to run in (development, testing, staging, production)')
@click.option('--config-file', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, environment, config_file, verbose):
    """Test Automation Orchestrator CLI - Manage your test automation system."""
    ctx.ensure_object(dict)
    ctx.obj['environment'] = environment
    ctx.obj['config_file'] = config_file
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--port', '-p', default=8080, help='Port to run dashboard on')
@click.option('--host', '-h', default='localhost', help='Host to bind dashboard to')
@click.option('--background', '-b', is_flag=True, help='Run in background')
@click.pass_context
def start(ctx, port, host, background):
    """Start the orchestrator system with dashboard."""
    async def _start():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            
            if background:
                click.echo(f"Starting orchestrator in background on {host}:{port}")
                # In a real implementation, you'd use a process manager like systemd
                click.echo("Background mode not fully implemented. Use a process manager.")
            else:
                click.echo(f"Starting orchestrator dashboard on http://{host}:{port}")
                await cli_instance.dashboard.run(host=host, port=port)
                
        except KeyboardInterrupt:
            click.echo("\nShutting down...")
        except Exception as e:
            click.echo(f"Error starting system: {e}", err=True)
            sys.exit(1)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_start())


@cli.command()
@click.pass_context
def stop(ctx):
    """Stop the orchestrator system."""
    async def _stop():
        await cli_instance.shutdown_system()
        click.echo("Orchestrator stopped successfully")
    
    asyncio.run(_stop())


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and health."""
    async def _status():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            
            # Get system status
            orchestrator_status = await cli_instance.orchestrator.get_status()
            scheduler_status = cli_instance.scheduler.get_status()
            
            # Display status
            click.echo("=== Test Automation Orchestrator Status ===")
            click.echo(f"Environment: {ctx.obj['environment']}")
            click.echo(f"Timestamp: {datetime.now().isoformat()}")
            click.echo()
            
            click.echo("Orchestrator:")
            click.echo(f"  Status: {orchestrator_status.get('status', 'unknown')}")
            click.echo(f"  Active Workflows: {len(orchestrator_status.get('workflows', []))}")
            click.echo(f"  Active Agents: {len(orchestrator_status.get('agents', []))}")
            click.echo()
            
            click.echo("Scheduler:")
            click.echo(f"  Status: {scheduler_status.get('status', 'unknown')}")
            click.echo(f"  Active Jobs: {len(scheduler_status.get('jobs', []))}")
            click.echo(f"  Pending Executions: {len(scheduler_status.get('pending_executions', []))}")
            click.echo()
            
            # System metrics
            if cli_instance.system_monitor:
                metrics = cli_instance.system_monitor.get_metrics()
                click.echo("System Metrics:")
                click.echo(f"  CPU Usage: {metrics.cpu_percent:.1f}%")
                click.echo(f"  Memory Usage: {metrics.memory_percent:.1f}%")
                click.echo(f"  Disk Usage: {metrics.disk_percent:.1f}%")
                click.echo(f"  Health Score: {metrics.health_score:.1f}/100")
            
        except Exception as e:
            click.echo(f"Error getting status: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_status())


@cli.group()
def workflow():
    """Manage workflows."""
    pass


@workflow.command('list')
@click.pass_context
def workflow_list(ctx):
    """List all workflows."""
    async def _list():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            workflows = await cli_instance.orchestrator.list_workflows()
            
            if not workflows:
                click.echo("No workflows found.")
                return
            
            click.echo("=== Workflows ===")
            for workflow in workflows:
                click.echo(f"ID: {workflow['id']}")
                click.echo(f"Name: {workflow['name']}")
                click.echo(f"Status: {workflow['status']}")
                click.echo(f"Created: {workflow['created_at']}")
                click.echo("---")
                
        except Exception as e:
            click.echo(f"Error listing workflows: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_list())


@workflow.command('create')
@click.argument('name')
@click.option('--config', '-c', help='Workflow configuration JSON file')
@click.pass_context
def workflow_create(ctx, name, config):
    """Create a new workflow."""
    async def _create():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            
            workflow_config = {"name": name, "steps": []}
            if config:
                with open(config, 'r') as f:
                    workflow_config.update(json.load(f))
            
            workflow_id = await cli_instance.orchestrator.create_workflow(workflow_config)
            click.echo(f"Workflow created successfully with ID: {workflow_id}")
            
        except Exception as e:
            click.echo(f"Error creating workflow: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_create())


@workflow.command('execute')
@click.argument('workflow_id')
@click.option('--params', '-p', help='Execution parameters as JSON string')
@click.pass_context
def workflow_execute(ctx, workflow_id, params):
    """Execute a workflow."""
    async def _execute():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            
            execution_params = {}
            if params:
                execution_params = json.loads(params)
            
            execution_id = await cli_instance.orchestrator.execute_workflow(
                workflow_id, execution_params
            )
            click.echo(f"Workflow execution started with ID: {execution_id}")
            
        except Exception as e:
            click.echo(f"Error executing workflow: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_execute())


@cli.group()
def schedule():
    """Manage scheduled jobs."""
    pass


@schedule.command('list')
@click.pass_context
def schedule_list(ctx):
    """List all scheduled jobs."""
    async def _list():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            jobs = cli_instance.scheduler.list_jobs()
            
            if not jobs:
                click.echo("No scheduled jobs found.")
                return
            
            click.echo("=== Scheduled Jobs ===")
            for job in jobs:
                click.echo(f"ID: {job.id}")
                click.echo(f"Name: {job.name}")
                click.echo(f"Schedule: {job.schedule}")
                click.echo(f"Status: {job.status.value}")
                click.echo(f"Next Run: {job.next_run}")
                click.echo("---")
                
        except Exception as e:
            click.echo(f"Error listing jobs: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_list())


@schedule.command('create')
@click.argument('name')
@click.argument('schedule')
@click.argument('workflow_id')
@click.option('--params', '-p', help='Job parameters as JSON string')
@click.pass_context
def schedule_create(ctx, name, schedule, workflow_id, params):
    """Create a new scheduled job."""
    async def _create():
        try:
            await cli_instance.initialize_system(ctx.obj['environment'])
            
            job_params = {}
            if params:
                job_params = json.loads(params)
            
            job_config = {
                "name": name,
                "schedule": schedule,
                "workflow_id": workflow_id,
                "parameters": job_params
            }
            
            job_id = cli_instance.scheduler.create_job(job_config)
            click.echo(f"Scheduled job created successfully with ID: {job_id}")
            
        except Exception as e:
            click.echo(f"Error creating scheduled job: {e}", err=True)
        finally:
            await cli_instance.shutdown_system()
    
    asyncio.run(_create())


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command('show')
@click.option('--environment', '-e', help='Environment to show config for')
@click.pass_context
def config_show(ctx, environment):
    """Show current configuration."""
    env = environment or ctx.obj['environment']
    
    try:
        settings = get_settings()
        env_manager = EnvironmentManager()
        env_config = env_manager.get_environment(env)
        
        click.echo(f"=== Configuration for {env} ===")
        click.echo("Settings:")
        click.echo(json.dumps(settings.to_dict(), indent=2))
        click.echo("\nEnvironment Config:")
        click.echo(json.dumps(env_config.to_dict(), indent=2))
        
    except Exception as e:
        click.echo(f"Error showing configuration: {e}", err=True)


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate all configurations."""
    try:
        settings_manager = get_settings_manager()
        settings_manager.validate()
        
        env_manager = EnvironmentManager()
        env_manager.validate_environment(ctx.obj['environment'])
        
        click.echo("All configurations are valid.")
        
    except Exception as e:
        click.echo(f"Configuration validation failed: {e}", err=True)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize a new orchestrator project."""
    try:
        # Create directory structure
        directories = [
            "config",
            "workflows", 
            "logs",
            "data",
            "reports"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            click.echo(f"Created directory: {directory}")
        
        # Create default configuration files
        settings_manager = get_settings_manager()
        settings_manager.save()
        click.echo("Created default settings configuration")
        
        env_manager = EnvironmentManager()
        for env in ["development", "testing", "staging", "production"]:
            if not env_manager.environment_exists(env):
                env_manager.create_environment(env, {})
                click.echo(f"Created {env} environment configuration")
        
        click.echo("\nOrchestrator project initialized successfully!")
        click.echo("Run 'python -m src.main start' to start the system.")
        
    except Exception as e:
        click.echo(f"Error initializing project: {e}", err=True)


if __name__ == '__main__':
    cli()