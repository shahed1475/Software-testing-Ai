"""
Test Orchestrator

Main orchestration system that coordinates all agents and provides
a unified interface for test automation workflows.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from .base_agent import BaseAgent, AgentConfig, AgentStatus
from .test_runner_agent import TestRunnerAgent
from .report_collector_agent import ReportCollectorAgent
from .report_generator_agent import ReportGeneratorAgent
from .notifier_agent import NotifierAgent
from .test_scheduler import TestScheduler, JobConfig, TriggerType


@dataclass
class WorkflowConfig:
    """Configuration for a test workflow"""
    id: str
    name: str
    description: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    environment: str = "default"
    timeout: int = 7200  # 2 hours default
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowExecution:
    """Represents a workflow execution"""
    id: str
    workflow_id: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0
    current_step: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    triggered_by: str = "manual"
    trigger_data: Dict[str, Any] = field(default_factory=dict)


class TestOrchestrator:
    """
    Main orchestrator that coordinates all test automation agents.
    
    Features:
    - Agent lifecycle management
    - Workflow orchestration
    - Event-driven automation
    - Monitoring and health checks
    - Configuration management
    - Integration with scheduler
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Agent instances
        self.test_runner: Optional[TestRunnerAgent] = None
        self.report_collector: Optional[ReportCollectorAgent] = None
        self.report_generator: Optional[ReportGeneratorAgent] = None
        self.notifier: Optional[NotifierAgent] = None
        self.scheduler: Optional[TestScheduler] = None
        
        # Workflow management
        self.workflows: Dict[str, WorkflowConfig] = {}
        self.workflow_executions: Dict[str, WorkflowExecution] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        
        # Event system
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Storage
        self.workflows_file = Path(config.get('workflows_file', 'data/workflows.json'))
        self.executions_file = Path(config.get('workflow_executions.json', 'data/workflow_executions.json'))
        
        # Ensure data directory exists
        self.workflows_file.parent.mkdir(parents=True, exist_ok=True)
        self.executions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_initialized = False
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Load existing data
        self._load_workflows()
        self._load_workflow_executions()
    
    async def initialize(self):
        """Initialize the orchestrator and all agents"""
        if self.is_initialized:
            self.logger.warning("Orchestrator already initialized")
            return
        
        self.logger.info("Initializing Test Orchestrator...")
        
        try:
            # Initialize agents
            await self._initialize_agents()
            
            # Initialize scheduler
            await self._initialize_scheduler()
            
            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.is_initialized = True
            self.logger.info("Test Orchestrator initialized successfully")
            
            # Emit initialization event
            await self._emit_event('orchestrator_initialized', {
                'timestamp': datetime.now().isoformat(),
                'agents_count': len([a for a in [self.test_runner, self.report_collector, 
                                               self.report_generator, self.notifier] if a]),
                'workflows_count': len(self.workflows)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def _initialize_agents(self):
        """Initialize all agents"""
        agent_configs = self.config.get('agents', {})
        
        # Initialize Test Runner Agent
        if 'test_runner' in agent_configs:
            config = AgentConfig(
                name="TestRunner",
                description="Handles test execution across different platforms",
                timeout=agent_configs['test_runner'].get('timeout', 3600),
                retry_attempts=agent_configs['test_runner'].get('retry_attempts', 3),
                metadata=agent_configs['test_runner']
            )
            self.test_runner = TestRunnerAgent(config)
            self.logger.info("Test Runner Agent initialized")
        
        # Initialize Report Collector Agent
        if 'report_collector' in agent_configs:
            config = AgentConfig(
                name="ReportCollector",
                description="Collects test results and artifacts",
                timeout=agent_configs['report_collector'].get('timeout', 1800),
                retry_attempts=agent_configs['report_collector'].get('retry_attempts', 3),
                metadata=agent_configs['report_collector']
            )
            self.report_collector = ReportCollectorAgent(config)
            self.logger.info("Report Collector Agent initialized")
        
        # Initialize Report Generator Agent
        if 'report_generator' in agent_configs:
            config = AgentConfig(
                name="ReportGenerator",
                description="Generates comprehensive test reports",
                timeout=agent_configs['report_generator'].get('timeout', 1800),
                retry_attempts=agent_configs['report_generator'].get('retry_attempts', 3),
                metadata=agent_configs['report_generator']
            )
            self.report_generator = ReportGeneratorAgent(config)
            self.logger.info("Report Generator Agent initialized")
        
        # Initialize Notifier Agent
        if 'notifier' in agent_configs:
            config = AgentConfig(
                name="Notifier",
                description="Handles notifications and alerts",
                timeout=agent_configs['notifier'].get('timeout', 300),
                retry_attempts=agent_configs['notifier'].get('retry_attempts', 3),
                metadata=agent_configs['notifier']
            )
            self.notifier = NotifierAgent(config)
            self.logger.info("Notifier Agent initialized")
    
    async def _initialize_scheduler(self):
        """Initialize the test scheduler"""
        scheduler_config = self.config.get('scheduler', {})
        
        if scheduler_config.get('enabled', True):
            self.scheduler = TestScheduler(scheduler_config)
            
            # Set agent references
            if self.scheduler:
                self.scheduler.set_agents(
                    self.test_runner,
                    self.report_collector,
                    self.report_generator,
                    self.notifier
                )
            
            self.logger.info("Test Scheduler initialized")
    
    def _load_workflows(self):
        """Load workflows from storage"""
        try:
            if self.workflows_file.exists():
                with open(self.workflows_file, 'r') as f:
                    workflows_data = json.load(f)
                
                for workflow_data in workflows_data:
                    workflow = WorkflowConfig(
                        id=workflow_data['id'],
                        name=workflow_data['name'],
                        description=workflow_data.get('description', ''),
                        steps=workflow_data.get('steps', []),
                        environment=workflow_data.get('environment', 'default'),
                        timeout=workflow_data.get('timeout', 7200),
                        retry_policy=workflow_data.get('retry_policy', {}),
                        notification_config=workflow_data.get('notification_config', {}),
                        enabled=workflow_data.get('enabled', True),
                        tags=workflow_data.get('tags', []),
                        created_at=datetime.fromisoformat(workflow_data.get('created_at', datetime.now().isoformat())),
                        updated_at=datetime.fromisoformat(workflow_data.get('updated_at', datetime.now().isoformat()))
                    )
                    self.workflows[workflow.id] = workflow
                
                self.logger.info(f"Loaded {len(self.workflows)} workflows from storage")
        except Exception as e:
            self.logger.error(f"Error loading workflows: {e}")
    
    def _save_workflows(self):
        """Save workflows to storage"""
        try:
            workflows_data = []
            for workflow in self.workflows.values():
                workflows_data.append({
                    'id': workflow.id,
                    'name': workflow.name,
                    'description': workflow.description,
                    'steps': workflow.steps,
                    'environment': workflow.environment,
                    'timeout': workflow.timeout,
                    'retry_policy': workflow.retry_policy,
                    'notification_config': workflow.notification_config,
                    'enabled': workflow.enabled,
                    'tags': workflow.tags,
                    'created_at': workflow.created_at.isoformat(),
                    'updated_at': workflow.updated_at.isoformat()
                })
            
            with open(self.workflows_file, 'w') as f:
                json.dump(workflows_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving workflows: {e}")
    
    def _load_workflow_executions(self):
        """Load workflow executions from storage"""
        try:
            if self.executions_file.exists():
                with open(self.executions_file, 'r') as f:
                    executions_data = json.load(f)
                
                for exec_data in executions_data:
                    execution = WorkflowExecution(
                        id=exec_data['id'],
                        workflow_id=exec_data['workflow_id'],
                        status=exec_data.get('status', 'pending'),
                        started_at=datetime.fromisoformat(exec_data['started_at']) if exec_data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(exec_data['completed_at']) if exec_data.get('completed_at') else None,
                        duration=exec_data.get('duration'),
                        steps_completed=exec_data.get('steps_completed', 0),
                        total_steps=exec_data.get('total_steps', 0),
                        current_step=exec_data.get('current_step'),
                        results=exec_data.get('results', {}),
                        error=exec_data.get('error'),
                        logs=exec_data.get('logs', []),
                        artifacts=exec_data.get('artifacts', []),
                        triggered_by=exec_data.get('triggered_by', 'manual'),
                        trigger_data=exec_data.get('trigger_data', {})
                    )
                    self.workflow_executions[execution.id] = execution
                
                # Keep only recent executions (last 500)
                if len(self.workflow_executions) > 500:
                    sorted_executions = sorted(
                        self.workflow_executions.values(),
                        key=lambda x: x.started_at or datetime.min,
                        reverse=True
                    )
                    self.workflow_executions = {
                        exec.id: exec for exec in sorted_executions[:500]
                    }
                
                self.logger.info(f"Loaded {len(self.workflow_executions)} workflow executions from storage")
        except Exception as e:
            self.logger.error(f"Error loading workflow executions: {e}")
    
    def _save_workflow_executions(self):
        """Save workflow executions to storage"""
        try:
            executions_data = []
            for execution in self.workflow_executions.values():
                executions_data.append({
                    'id': execution.id,
                    'workflow_id': execution.workflow_id,
                    'status': execution.status,
                    'started_at': execution.started_at.isoformat() if execution.started_at else None,
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'duration': execution.duration,
                    'steps_completed': execution.steps_completed,
                    'total_steps': execution.total_steps,
                    'current_step': execution.current_step,
                    'results': execution.results,
                    'error': execution.error,
                    'logs': execution.logs,
                    'artifacts': execution.artifacts,
                    'triggered_by': execution.triggered_by,
                    'trigger_data': execution.trigger_data
                })
            
            with open(self.executions_file, 'w') as f:
                json.dump(executions_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving workflow executions: {e}")
    
    def create_workflow(self, name: str, steps: List[Dict[str, Any]], **kwargs) -> str:
        """Create a new workflow"""
        workflow_id = kwargs.get('workflow_id', str(uuid.uuid4()))
        
        workflow = WorkflowConfig(
            id=workflow_id,
            name=name,
            description=kwargs.get('description', ''),
            steps=steps,
            environment=kwargs.get('environment', 'default'),
            timeout=kwargs.get('timeout', 7200),
            retry_policy=kwargs.get('retry_policy', {}),
            notification_config=kwargs.get('notification_config', {}),
            enabled=kwargs.get('enabled', True),
            tags=kwargs.get('tags', [])
        )
        
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        
        self.logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, triggered_by: str = "manual",
                             trigger_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return None
        
        workflow = self.workflows[workflow_id]
        
        if not workflow.enabled:
            self.logger.warning(f"Workflow is disabled: {workflow.name} ({workflow_id})")
            return None
        
        # Check if workflow is already running
        if workflow_id in self.running_workflows:
            self.logger.warning(f"Workflow is already running: {workflow.name} ({workflow_id})")
            return None
        
        # Create execution
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            total_steps=len(workflow.steps),
            triggered_by=triggered_by,
            trigger_data=trigger_data or {}
        )
        
        self.workflow_executions[execution_id] = execution
        
        # Start execution task
        task = asyncio.create_task(self._execute_workflow_logic(execution))
        self.running_workflows[workflow_id] = task
        
        self.logger.info(f"Started workflow execution: {workflow.name} ({workflow_id}) -> {execution_id}")
        
        # Emit event
        await self._emit_event('workflow_started', {
            'workflow_id': workflow_id,
            'execution_id': execution_id,
            'workflow_name': workflow.name,
            'triggered_by': triggered_by
        })
        
        return execution_id
    
    async def _execute_workflow_logic(self, execution: WorkflowExecution):
        """Execute workflow logic"""
        workflow = self.workflows[execution.workflow_id]
        
        try:
            execution.status = "running"
            execution.started_at = datetime.now()
            self._save_workflow_executions()
            
            self.logger.info(f"Executing workflow: {workflow.name} ({execution.id})")
            
            # Execute each step
            for i, step in enumerate(workflow.steps):
                execution.current_step = step.get('name', f'Step {i+1}')
                execution.logs.append(f"Starting step: {execution.current_step}")
                
                try:
                    step_result = await self._execute_workflow_step(step, execution, workflow)
                    execution.results[f'step_{i+1}'] = step_result
                    execution.steps_completed = i + 1
                    execution.logs.append(f"Completed step: {execution.current_step}")
                    
                    # Save progress
                    self._save_workflow_executions()
                    
                except Exception as step_error:
                    execution.logs.append(f"Step failed: {execution.current_step} - {step_error}")
                    
                    # Check retry policy
                    retry_policy = workflow.retry_policy
                    if retry_policy.get('enabled', False) and step.get('retryable', True):
                        max_retries = retry_policy.get('max_retries', 3)
                        retry_delay = retry_policy.get('delay_seconds', 60)
                        
                        for retry in range(max_retries):
                            execution.logs.append(f"Retrying step: {execution.current_step} (attempt {retry + 1})")
                            await asyncio.sleep(retry_delay)
                            
                            try:
                                step_result = await self._execute_workflow_step(step, execution, workflow)
                                execution.results[f'step_{i+1}'] = step_result
                                execution.steps_completed = i + 1
                                execution.logs.append(f"Step succeeded on retry: {execution.current_step}")
                                break
                            except Exception as retry_error:
                                execution.logs.append(f"Retry failed: {execution.current_step} - {retry_error}")
                                if retry == max_retries - 1:
                                    raise step_error
                    else:
                        raise step_error
            
            execution.status = "completed"
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.current_step = None
            
            self.logger.info(f"Workflow completed successfully: {workflow.name} ({execution.id})")
            
            # Send success notification
            if workflow.notification_config.get('on_success', True) and self.notifier:
                await self.notifier.send_system_alert(
                    alert_type='workflow_success',
                    severity='info',
                    description=f"Workflow '{workflow.name}' completed successfully",
                    component='test_orchestrator',
                    environment=workflow.environment,
                    workflow_id=workflow.id,
                    execution_id=execution.id,
                    duration=execution.duration,
                    channels=workflow.notification_config.get('channels', [])
                )
            
            # Emit event
            await self._emit_event('workflow_completed', {
                'workflow_id': workflow.id,
                'execution_id': execution.id,
                'workflow_name': workflow.name,
                'duration': execution.duration,
                'steps_completed': execution.steps_completed
            })
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.current_step = None
            
            self.logger.error(f"Workflow failed: {workflow.name} ({execution.id}) - {e}")
            
            # Send failure notification
            if workflow.notification_config.get('on_failure', True) and self.notifier:
                await self.notifier.send_system_alert(
                    alert_type='workflow_failure',
                    severity='high',
                    description=f"Workflow '{workflow.name}' failed: {str(e)}",
                    component='test_orchestrator',
                    environment=workflow.environment,
                    workflow_id=workflow.id,
                    execution_id=execution.id,
                    error=str(e),
                    channels=workflow.notification_config.get('channels', [])
                )
            
            # Emit event
            await self._emit_event('workflow_failed', {
                'workflow_id': workflow.id,
                'execution_id': execution.id,
                'workflow_name': workflow.name,
                'error': str(e),
                'steps_completed': execution.steps_completed
            })
        
        finally:
            # Clean up
            if execution.workflow_id in self.running_workflows:
                del self.running_workflows[execution.workflow_id]
            
            self._save_workflow_executions()
    
    async def _execute_workflow_step(self, step: Dict[str, Any], 
                                   execution: WorkflowExecution,
                                   workflow: WorkflowConfig) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get('type')
        step_config = step.get('config', {})
        
        if step_type == 'run_tests':
            if not self.test_runner:
                raise RuntimeError("Test Runner Agent not available")
            
            return await self.test_runner.execute(
                platform=step_config.get('platform', 'local'),
                test_suite=step_config.get('test_suite', 'all'),
                environment=workflow.environment,
                **step_config.get('runner_config', {})
            )
        
        elif step_type == 'collect_results':
            if not self.report_collector:
                raise RuntimeError("Report Collector Agent not available")
            
            return await self.report_collector.execute(
                sources=step_config.get('sources', ['local']),
                **step_config.get('collector_config', {})
            )
        
        elif step_type == 'generate_reports':
            if not self.report_generator:
                raise RuntimeError("Report Generator Agent not available")
            
            # Get collected data from previous step
            collected_data = {}
            if execution.results:
                for step_result in execution.results.values():
                    if step_result.get('data', {}).get('test_results'):
                        collected_data = step_result.get('data', {})
                        break
            
            return await self.report_generator.execute(
                collected_data=collected_data,
                report_types=step_config.get('report_types', ['json', 'html']),
                **step_config.get('generator_config', {})
            )
        
        elif step_type == 'send_notifications':
            if not self.notifier:
                raise RuntimeError("Notifier Agent not available")
            
            return await self.notifier.execute(
                notification_type=step_config.get('notification_type', 'test_result'),
                message_data=step_config.get('message_data', {}),
                channels=step_config.get('channels', [])
            )
        
        elif step_type == 'delay':
            delay_seconds = step_config.get('seconds', 60)
            await asyncio.sleep(delay_seconds)
            return {'delayed_seconds': delay_seconds}
        
        elif step_type == 'custom':
            # Execute custom step logic
            custom_handler = step_config.get('handler')
            if custom_handler and callable(custom_handler):
                return await custom_handler(step_config, execution, workflow)
            else:
                raise RuntimeError(f"Custom step handler not found or not callable")
        
        else:
            raise RuntimeError(f"Unknown step type: {step_type}")
    
    async def _health_check_loop(self):
        """Health check loop for monitoring agents"""
        while self.is_initialized:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all agents"""
        agents = {
            'test_runner': self.test_runner,
            'report_collector': self.report_collector,
            'report_generator': self.report_generator,
            'notifier': self.notifier
        }
        
        health_status = {}
        
        for agent_name, agent in agents.items():
            if agent:
                try:
                    # Simple health check - check if agent can respond
                    status = getattr(agent, 'status', AgentStatus.IDLE)
                    health_status[agent_name] = {
                        'healthy': True,
                        'status': status.value if hasattr(status, 'value') else str(status),
                        'last_check': datetime.now().isoformat()
                    }
                except Exception as e:
                    health_status[agent_name] = {
                        'healthy': False,
                        'error': str(e),
                        'last_check': datetime.now().isoformat()
                    }
            else:
                health_status[agent_name] = {
                    'healthy': False,
                    'error': 'Agent not initialized',
                    'last_check': datetime.now().isoformat()
                }
        
        # Check scheduler health
        if self.scheduler:
            scheduler_status = self.scheduler.get_scheduler_status()
            health_status['scheduler'] = {
                'healthy': scheduler_status.get('running', False),
                'status': scheduler_status,
                'last_check': datetime.now().isoformat()
            }
        
        # Emit health check event
        await self._emit_event('health_check', health_status)
        
        # Log unhealthy agents
        unhealthy_agents = [name for name, status in health_status.items() if not status.get('healthy')]
        if unhealthy_agents:
            self.logger.warning(f"Unhealthy agents detected: {unhealthy_agents}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable):
        """Remove an event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit an event to all registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, event_data)
                    else:
                        handler(event_type, event_data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def start_scheduler(self):
        """Start the test scheduler"""
        if self.scheduler:
            await self.scheduler.start_scheduler()
            self.logger.info("Test scheduler started")
        else:
            self.logger.warning("Scheduler not initialized")
    
    async def stop_scheduler(self):
        """Stop the test scheduler"""
        if self.scheduler:
            await self.scheduler.stop_scheduler()
            self.logger.info("Test scheduler stopped")
    
    async def shutdown(self):
        """Shutdown the orchestrator"""
        self.logger.info("Shutting down Test Orchestrator...")
        
        # Stop scheduler
        await self.stop_scheduler()
        
        # Cancel running workflows
        for task in self.running_workflows.values():
            task.cancel()
        
        if self.running_workflows:
            await asyncio.gather(*self.running_workflows.values(), return_exceptions=True)
        
        # Stop health check
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        self.is_initialized = False
        self.logger.info("Test Orchestrator shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'initialized': self.is_initialized,
            'agents': {
                'test_runner': self.test_runner is not None,
                'report_collector': self.report_collector is not None,
                'report_generator': self.report_generator is not None,
                'notifier': self.notifier is not None
            },
            'scheduler': {
                'initialized': self.scheduler is not None,
                'running': self.scheduler.is_running if self.scheduler else False
            },
            'workflows': {
                'total': len(self.workflows),
                'enabled': len([w for w in self.workflows.values() if w.enabled]),
                'running': len(self.running_workflows)
            },
            'executions': {
                'total': len(self.workflow_executions),
                'recent': len([
                    e for e in self.workflow_executions.values()
                    if e.started_at and e.started_at > datetime.now() - timedelta(hours=24)
                ])
            }
        }