"""
Test Scheduler

Handles scheduled test runs with cron-like functionality and on-demand triggers.
Supports various scheduling patterns, job management, and integration with test agents.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import croniter
from pathlib import Path
import uuid

from .base_agent import BaseAgent, AgentConfig, AgentStatus
from .test_runner_agent import TestRunnerAgent
from .report_collector_agent import ReportCollectorAgent
from .report_generator_agent import ReportGeneratorAgent
from .notifier_agent import NotifierAgent


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """Job trigger types"""
    CRON = "cron"
    INTERVAL = "interval"
    ON_DEMAND = "on_demand"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"
    GIT_PUSH = "git_push"


@dataclass
class JobConfig:
    """Configuration for a scheduled job"""
    id: str
    name: str
    description: str = ""
    trigger_type: TriggerType = TriggerType.CRON
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    test_config: Dict[str, Any] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 3600  # 1 hour default
    tags: List[str] = field(default_factory=list)
    environment: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class JobExecution:
    """Represents a job execution instance"""
    id: str
    job_id: str
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    triggered_by: str = "scheduler"
    trigger_data: Dict[str, Any] = field(default_factory=dict)


class TestScheduler:
    """
    Test scheduler that manages scheduled and on-demand test runs.
    
    Features:
    - Cron-like scheduling
    - Interval-based scheduling
    - On-demand triggers
    - Webhook triggers
    - File system watching
    - Git push triggers
    - Job management and monitoring
    - Retry logic
    - Notification integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Job storage
        self.jobs: Dict[str, JobConfig] = {}
        self.executions: Dict[str, JobExecution] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        
        # Agents
        self.test_runner: Optional[TestRunnerAgent] = None
        self.report_collector: Optional[ReportCollectorAgent] = None
        self.report_generator: Optional[ReportGeneratorAgent] = None
        self.notifier: Optional[NotifierAgent] = None
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Storage paths
        self.jobs_file = Path(config.get('jobs_file', 'data/scheduled_jobs.json'))
        self.executions_file = Path(config.get('executions_file', 'data/job_executions.json'))
        
        # Ensure data directory exists
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self.executions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing jobs and executions
        self._load_jobs()
        self._load_executions()
    
    def set_agents(self, test_runner: TestRunnerAgent, 
                   report_collector: ReportCollectorAgent,
                   report_generator: ReportGeneratorAgent,
                   notifier: NotifierAgent):
        """Set the agent instances"""
        self.test_runner = test_runner
        self.report_collector = report_collector
        self.report_generator = report_generator
        self.notifier = notifier
    
    def _load_jobs(self):
        """Load jobs from storage"""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                for job_data in jobs_data:
                    job_config = JobConfig(
                        id=job_data['id'],
                        name=job_data['name'],
                        description=job_data.get('description', ''),
                        trigger_type=TriggerType(job_data['trigger_type']),
                        trigger_config=job_data.get('trigger_config', {}),
                        test_config=job_data.get('test_config', {}),
                        notification_config=job_data.get('notification_config', {}),
                        enabled=job_data.get('enabled', True),
                        max_retries=job_data.get('max_retries', 3),
                        timeout=job_data.get('timeout', 3600),
                        tags=job_data.get('tags', []),
                        environment=job_data.get('environment', 'default'),
                        created_at=datetime.fromisoformat(job_data.get('created_at', datetime.now().isoformat())),
                        updated_at=datetime.fromisoformat(job_data.get('updated_at', datetime.now().isoformat()))
                    )
                    self.jobs[job_config.id] = job_config
                
                self.logger.info(f"Loaded {len(self.jobs)} jobs from storage")
        except Exception as e:
            self.logger.error(f"Error loading jobs: {e}")
    
    def _save_jobs(self):
        """Save jobs to storage"""
        try:
            jobs_data = []
            for job in self.jobs.values():
                jobs_data.append({
                    'id': job.id,
                    'name': job.name,
                    'description': job.description,
                    'trigger_type': job.trigger_type.value,
                    'trigger_config': job.trigger_config,
                    'test_config': job.test_config,
                    'notification_config': job.notification_config,
                    'enabled': job.enabled,
                    'max_retries': job.max_retries,
                    'timeout': job.timeout,
                    'tags': job.tags,
                    'environment': job.environment,
                    'created_at': job.created_at.isoformat(),
                    'updated_at': job.updated_at.isoformat()
                })
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving jobs: {e}")
    
    def _load_executions(self):
        """Load executions from storage"""
        try:
            if self.executions_file.exists():
                with open(self.executions_file, 'r') as f:
                    executions_data = json.load(f)
                
                for exec_data in executions_data:
                    execution = JobExecution(
                        id=exec_data['id'],
                        job_id=exec_data['job_id'],
                        status=JobStatus(exec_data['status']),
                        started_at=datetime.fromisoformat(exec_data['started_at']) if exec_data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(exec_data['completed_at']) if exec_data.get('completed_at') else None,
                        duration=exec_data.get('duration'),
                        result=exec_data.get('result'),
                        error=exec_data.get('error'),
                        retry_count=exec_data.get('retry_count', 0),
                        logs=exec_data.get('logs', []),
                        artifacts=exec_data.get('artifacts', []),
                        triggered_by=exec_data.get('triggered_by', 'scheduler'),
                        trigger_data=exec_data.get('trigger_data', {})
                    )
                    self.executions[execution.id] = execution
                
                # Keep only recent executions (last 1000)
                if len(self.executions) > 1000:
                    sorted_executions = sorted(
                        self.executions.values(),
                        key=lambda x: x.started_at or datetime.min,
                        reverse=True
                    )
                    self.executions = {
                        exec.id: exec for exec in sorted_executions[:1000]
                    }
                
                self.logger.info(f"Loaded {len(self.executions)} executions from storage")
        except Exception as e:
            self.logger.error(f"Error loading executions: {e}")
    
    def _save_executions(self):
        """Save executions to storage"""
        try:
            executions_data = []
            for execution in self.executions.values():
                executions_data.append({
                    'id': execution.id,
                    'job_id': execution.job_id,
                    'status': execution.status.value,
                    'started_at': execution.started_at.isoformat() if execution.started_at else None,
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'duration': execution.duration,
                    'result': execution.result,
                    'error': execution.error,
                    'retry_count': execution.retry_count,
                    'logs': execution.logs,
                    'artifacts': execution.artifacts,
                    'triggered_by': execution.triggered_by,
                    'trigger_data': execution.trigger_data
                })
            
            with open(self.executions_file, 'w') as f:
                json.dump(executions_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving executions: {e}")
    
    def create_job(self, name: str, trigger_type: TriggerType, 
                   trigger_config: Dict[str, Any], test_config: Dict[str, Any],
                   **kwargs) -> str:
        """Create a new scheduled job"""
        job_id = kwargs.get('job_id', str(uuid.uuid4()))
        
        job = JobConfig(
            id=job_id,
            name=name,
            description=kwargs.get('description', ''),
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            test_config=test_config,
            notification_config=kwargs.get('notification_config', {}),
            enabled=kwargs.get('enabled', True),
            max_retries=kwargs.get('max_retries', 3),
            timeout=kwargs.get('timeout', 3600),
            tags=kwargs.get('tags', []),
            environment=kwargs.get('environment', 'default')
        )
        
        self.jobs[job_id] = job
        self._save_jobs()
        
        self.logger.info(f"Created job: {name} ({job_id})")
        return job_id
    
    def update_job(self, job_id: str, **kwargs) -> bool:
        """Update an existing job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Update fields
        for field_name, value in kwargs.items():
            if hasattr(job, field_name):
                setattr(job, field_name, value)
        
        job.updated_at = datetime.now()
        self._save_jobs()
        
        self.logger.info(f"Updated job: {job.name} ({job_id})")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        if job_id not in self.jobs:
            return False
        
        # Cancel running execution if any
        if job_id in self.running_jobs:
            self.running_jobs[job_id].cancel()
            del self.running_jobs[job_id]
        
        job_name = self.jobs[job_id].name
        del self.jobs[job_id]
        self._save_jobs()
        
        self.logger.info(f"Deleted job: {job_name} ({job_id})")
        return True
    
    def get_job(self, job_id: str) -> Optional[JobConfig]:
        """Get a job by ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(self, enabled_only: bool = False, 
                  tags: Optional[List[str]] = None) -> List[JobConfig]:
        """List jobs with optional filtering"""
        jobs = list(self.jobs.values())
        
        if enabled_only:
            jobs = [job for job in jobs if job.enabled]
        
        if tags:
            jobs = [job for job in jobs if any(tag in job.tags for tag in tags)]
        
        return jobs
    
    def get_execution(self, execution_id: str) -> Optional[JobExecution]:
        """Get an execution by ID"""
        return self.executions.get(execution_id)
    
    def list_executions(self, job_id: Optional[str] = None, 
                       status: Optional[JobStatus] = None,
                       limit: int = 100) -> List[JobExecution]:
        """List executions with optional filtering"""
        executions = list(self.executions.values())
        
        if job_id:
            executions = [exec for exec in executions if exec.job_id == job_id]
        
        if status:
            executions = [exec for exec in executions if exec.status == status]
        
        # Sort by start time (most recent first)
        executions.sort(
            key=lambda x: x.started_at or datetime.min,
            reverse=True
        )
        
        return executions[:limit]
    
    async def trigger_job(self, job_id: str, triggered_by: str = "manual",
                         trigger_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Trigger a job execution"""
        if job_id not in self.jobs:
            self.logger.error(f"Job not found: {job_id}")
            return None
        
        job = self.jobs[job_id]
        
        if not job.enabled:
            self.logger.warning(f"Job is disabled: {job.name} ({job_id})")
            return None
        
        # Check if job is already running
        if job_id in self.running_jobs:
            self.logger.warning(f"Job is already running: {job.name} ({job_id})")
            return None
        
        # Create execution
        execution_id = str(uuid.uuid4())
        execution = JobExecution(
            id=execution_id,
            job_id=job_id,
            triggered_by=triggered_by,
            trigger_data=trigger_data or {}
        )
        
        self.executions[execution_id] = execution
        
        # Start execution task
        task = asyncio.create_task(self._execute_job(execution))
        self.running_jobs[job_id] = task
        
        self.logger.info(f"Triggered job: {job.name} ({job_id}) -> {execution_id}")
        return execution_id
    
    async def _execute_job(self, execution: JobExecution):
        """Execute a job"""
        job = self.jobs[execution.job_id]
        
        try:
            execution.status = JobStatus.RUNNING
            execution.started_at = datetime.now()
            self._save_executions()
            
            self.logger.info(f"Starting job execution: {job.name} ({execution.id})")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._run_job_logic(job, execution),
                timeout=job.timeout
            )
            
            execution.status = JobStatus.COMPLETED
            execution.result = result
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.info(f"Job completed successfully: {job.name} ({execution.id})")
            
            # Send success notification
            if job.notification_config.get('on_success', True):
                await self._send_job_notification(job, execution, 'success')
            
        except asyncio.TimeoutError:
            execution.status = JobStatus.FAILED
            execution.error = f"Job timed out after {job.timeout} seconds"
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.error(f"Job timed out: {job.name} ({execution.id})")
            
            # Send failure notification
            if job.notification_config.get('on_failure', True):
                await self._send_job_notification(job, execution, 'failure')
            
        except Exception as e:
            execution.status = JobStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.error(f"Job failed: {job.name} ({execution.id}) - {e}")
            
            # Retry logic
            if execution.retry_count < job.max_retries:
                execution.retry_count += 1
                execution.status = JobStatus.PENDING
                execution.started_at = None
                execution.completed_at = None
                execution.duration = None
                
                self.logger.info(f"Retrying job: {job.name} ({execution.id}) - Attempt {execution.retry_count + 1}")
                
                # Retry after delay
                await asyncio.sleep(min(60 * execution.retry_count, 300))  # Exponential backoff, max 5 minutes
                await self._execute_job(execution)
                return
            else:
                # Send failure notification
                if job.notification_config.get('on_failure', True):
                    await self._send_job_notification(job, execution, 'failure')
        
        finally:
            # Clean up
            if execution.job_id in self.running_jobs:
                del self.running_jobs[execution.job_id]
            
            self._save_executions()
    
    async def _run_job_logic(self, job: JobConfig, execution: JobExecution) -> Dict[str, Any]:
        """Run the actual job logic"""
        test_config = job.test_config
        result = {}
        
        # Step 1: Run tests
        if self.test_runner:
            execution.logs.append("Starting test execution...")
            
            test_result = await self.test_runner.execute(
                platform=test_config.get('platform', 'local'),
                test_suite=test_config.get('test_suite', 'all'),
                environment=job.environment,
                **test_config.get('runner_config', {})
            )
            
            result['test_execution'] = test_result
            execution.logs.append(f"Test execution completed: {test_result.get('status')}")
        
        # Step 2: Collect results
        if self.report_collector and result.get('test_execution'):
            execution.logs.append("Collecting test results...")
            
            collection_result = await self.report_collector.execute(
                sources=test_config.get('result_sources', ['local']),
                test_run_id=result['test_execution'].get('run_id'),
                **test_config.get('collector_config', {})
            )
            
            result['collection'] = collection_result
            execution.logs.append(f"Result collection completed: {len(collection_result.get('data', {}).get('test_results', []))} results")
        
        # Step 3: Generate reports
        if self.report_generator and result.get('collection'):
            execution.logs.append("Generating reports...")
            
            report_result = await self.report_generator.execute(
                collected_data=result['collection'].get('data', {}),
                report_types=test_config.get('report_types', ['json', 'html']),
                **test_config.get('generator_config', {})
            )
            
            result['reports'] = report_result
            execution.artifacts.extend(report_result.get('data', {}).get('generated_files', []))
            execution.logs.append(f"Report generation completed: {len(report_result.get('data', {}).get('generated_files', []))} files")
        
        # Step 4: Send notifications
        if self.notifier and job.notification_config.get('send_results', False):
            execution.logs.append("Sending result notifications...")
            
            notification_result = await self.notifier.send_test_result_notification(
                test_run={
                    'id': execution.id,
                    'name': job.name,
                    'environment': job.environment,
                    'duration': execution.duration or 0
                },
                summary=result.get('collection', {}).get('data', {}).get('summary', {}),
                channels=job.notification_config.get('channels', [])
            )
            
            result['notifications'] = notification_result
            execution.logs.append(f"Notifications sent: {len(notification_result.get('successful_channels', []))} channels")
        
        return result
    
    async def _send_job_notification(self, job: JobConfig, execution: JobExecution, 
                                   notification_type: str):
        """Send job status notification"""
        if not self.notifier:
            return
        
        try:
            if notification_type == 'success':
                await self.notifier.send_test_success_notification(
                    test_run={
                        'id': execution.id,
                        'name': job.name,
                        'environment': job.environment,
                        'duration': execution.duration or 0
                    },
                    summary=execution.result.get('collection', {}).get('data', {}).get('summary', {}),
                    channels=job.notification_config.get('channels', [])
                )
            elif notification_type == 'failure':
                await self.notifier.send_system_alert(
                    alert_type='job_failure',
                    severity='high',
                    description=f"Scheduled job '{job.name}' failed: {execution.error}",
                    component='test_scheduler',
                    environment=job.environment,
                    job_id=job.id,
                    execution_id=execution.id,
                    channels=job.notification_config.get('channels', [])
                )
        except Exception as e:
            self.logger.error(f"Error sending job notification: {e}")
    
    async def start_scheduler(self):
        """Start the scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Test scheduler started")
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel running jobs
        for task in self.running_jobs.values():
            task.cancel()
        
        if self.running_jobs:
            await asyncio.gather(*self.running_jobs.values(), return_exceptions=True)
        
        self.running_jobs.clear()
        self.logger.info("Test scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info("Scheduler loop started")
        
        try:
            while self.is_running:
                current_time = datetime.now()
                
                # Check each job for scheduling
                for job in self.jobs.values():
                    if not job.enabled:
                        continue
                    
                    if job.id in self.running_jobs:
                        continue  # Job is already running
                    
                    should_run = False
                    
                    if job.trigger_type == TriggerType.CRON:
                        should_run = self._should_run_cron_job(job, current_time)
                    elif job.trigger_type == TriggerType.INTERVAL:
                        should_run = self._should_run_interval_job(job, current_time)
                    
                    if should_run:
                        await self.trigger_job(job.id, triggered_by="scheduler")
                
                # Sleep for a minute before next check
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            self.logger.info("Scheduler loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in scheduler loop: {e}")
    
    def _should_run_cron_job(self, job: JobConfig, current_time: datetime) -> bool:
        """Check if a cron job should run"""
        try:
            cron_expression = job.trigger_config.get('cron')
            if not cron_expression:
                return False
            
            # Get last execution time
            last_execution = None
            for execution in self.executions.values():
                if (execution.job_id == job.id and 
                    execution.started_at and 
                    execution.triggered_by == "scheduler"):
                    if not last_execution or execution.started_at > last_execution:
                        last_execution = execution.started_at
            
            # If no previous execution, check if we should run now
            if not last_execution:
                cron = croniter.croniter(cron_expression, current_time)
                next_run = cron.get_prev(datetime)
                # Run if the previous scheduled time was within the last minute
                return (current_time - next_run).total_seconds() < 60
            
            # Check if it's time for next execution
            cron = croniter.croniter(cron_expression, last_execution)
            next_run = cron.get_next(datetime)
            
            return current_time >= next_run
            
        except Exception as e:
            self.logger.error(f"Error checking cron job {job.id}: {e}")
            return False
    
    def _should_run_interval_job(self, job: JobConfig, current_time: datetime) -> bool:
        """Check if an interval job should run"""
        try:
            interval_seconds = job.trigger_config.get('interval_seconds')
            if not interval_seconds:
                return False
            
            # Get last execution time
            last_execution = None
            for execution in self.executions.values():
                if (execution.job_id == job.id and 
                    execution.started_at and 
                    execution.triggered_by == "scheduler"):
                    if not last_execution or execution.started_at > last_execution:
                        last_execution = execution.started_at
            
            # If no previous execution, run now
            if not last_execution:
                return True
            
            # Check if interval has passed
            time_since_last = (current_time - last_execution).total_seconds()
            return time_since_last >= interval_seconds
            
        except Exception as e:
            self.logger.error(f"Error checking interval job {job.id}: {e}")
            return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'total_jobs': len(self.jobs),
            'enabled_jobs': len([job for job in self.jobs.values() if job.enabled]),
            'running_jobs': len(self.running_jobs),
            'total_executions': len(self.executions),
            'recent_executions': len([
                exec for exec in self.executions.values()
                if exec.started_at and exec.started_at > datetime.now() - timedelta(hours=24)
            ])
        }
    
    def get_job_statistics(self, job_id: str, days: int = 30) -> Dict[str, Any]:
        """Get job execution statistics"""
        if job_id not in self.jobs:
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        job_executions = [
            exec for exec in self.executions.values()
            if (exec.job_id == job_id and 
                exec.started_at and 
                exec.started_at > cutoff_date)
        ]
        
        if not job_executions:
            return {'total_executions': 0}
        
        successful = len([exec for exec in job_executions if exec.status == JobStatus.COMPLETED])
        failed = len([exec for exec in job_executions if exec.status == JobStatus.FAILED])
        
        durations = [exec.duration for exec in job_executions if exec.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_executions': len(job_executions),
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / len(job_executions)) * 100 if job_executions else 0,
            'average_duration': avg_duration,
            'last_execution': max(job_executions, key=lambda x: x.started_at or datetime.min).started_at.isoformat() if job_executions else None
        }