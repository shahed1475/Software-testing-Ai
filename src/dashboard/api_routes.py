"""
API Routes for Dashboard

Provides REST API endpoints for managing the test automation system.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from aiohttp import web


class APIRoutes:
    """
    API routes handler for the dashboard.
    
    Provides REST endpoints for:
    - Agent management
    - Workflow management
    - Scheduler operations
    - Trigger management
    - System status and health
    """
    
    def __init__(self, orchestrator=None, trigger_system=None):
        self.orchestrator = orchestrator
        self.trigger_system = trigger_system
        self.logger = logging.getLogger(__name__)
    
    # Agent Management
    async def list_agents(self, request):
        """List all agents and their status"""
        try:
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            agents_status = {}
            for agent_name, agent in self.orchestrator.agents.items():
                agents_status[agent_name] = {
                    'name': agent_name,
                    'status': agent.status.value if hasattr(agent, 'status') else 'unknown',
                    'config': agent.config.__dict__ if hasattr(agent, 'config') else {},
                    'last_execution': getattr(agent, 'last_execution', None),
                    'health': await self._get_agent_health(agent)
                }
            
            return web.json_response({
                'agents': agents_status,
                'total': len(agents_status)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list agents: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_agent(self, request):
        """Get specific agent details"""
        try:
            agent_id = request.match_info['agent_id']
            
            if not self.orchestrator or agent_id not in self.orchestrator.agents:
                return web.json_response({'error': 'Agent not found'}, status=404)
            
            agent = self.orchestrator.agents[agent_id]
            
            return web.json_response({
                'id': agent_id,
                'name': agent_id,
                'status': agent.status.value if hasattr(agent, 'status') else 'unknown',
                'config': agent.config.__dict__ if hasattr(agent, 'config') else {},
                'last_execution': getattr(agent, 'last_execution', None),
                'health': await self._get_agent_health(agent),
                'logs': getattr(agent, 'logs', [])[-50:]  # Last 50 log entries
            })
            
        except Exception as e:
            self.logger.error(f"Failed to get agent {request.match_info.get('agent_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def restart_agent(self, request):
        """Restart a specific agent"""
        try:
            agent_id = request.match_info['agent_id']
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            # This would need to be implemented in the orchestrator
            if hasattr(self.orchestrator, 'restart_agent'):
                result = await self.orchestrator.restart_agent(agent_id)
                return web.json_response({'success': True, 'result': result})
            else:
                return web.json_response({'error': 'Agent restart not implemented'}, status=501)
            
        except Exception as e:
            self.logger.error(f"Failed to restart agent {request.match_info.get('agent_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # Workflow Management
    async def list_workflows(self, request):
        """List all workflows"""
        try:
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            workflows = self.orchestrator.list_workflows()
            
            return web.json_response({
                'workflows': workflows,
                'total': len(workflows)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def create_workflow(self, request):
        """Create a new workflow"""
        try:
            data = await request.json()
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            workflow_id = await self.orchestrator.create_workflow(data)
            
            return web.json_response({
                'success': True,
                'workflow_id': workflow_id
            }, status=201)
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_workflow(self, request):
        """Get specific workflow details"""
        try:
            workflow_id = request.match_info['workflow_id']
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            workflow = self.orchestrator.get_workflow(workflow_id)
            
            if not workflow:
                return web.json_response({'error': 'Workflow not found'}, status=404)
            
            return web.json_response(workflow)
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow {request.match_info.get('workflow_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def update_workflow(self, request):
        """Update a workflow"""
        try:
            workflow_id = request.match_info['workflow_id']
            data = await request.json()
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            success = await self.orchestrator.update_workflow(workflow_id, data)
            
            if not success:
                return web.json_response({'error': 'Workflow not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow {request.match_info.get('workflow_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def delete_workflow(self, request):
        """Delete a workflow"""
        try:
            workflow_id = request.match_info['workflow_id']
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            success = await self.orchestrator.delete_workflow(workflow_id)
            
            if not success:
                return web.json_response({'error': 'Workflow not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to delete workflow {request.match_info.get('workflow_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def execute_workflow(self, request):
        """Execute a workflow"""
        try:
            workflow_id = request.match_info['workflow_id']
            data = await request.json() if request.content_length else {}
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            execution_id = await self.orchestrator.execute_workflow(
                workflow_id, 
                data.get('parameters', {}),
                data.get('context', {})
            )
            
            return web.json_response({
                'success': True,
                'execution_id': execution_id
            })
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow {request.match_info.get('workflow_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # Workflow Executions
    async def list_executions(self, request):
        """List workflow executions"""
        try:
            # Parse query parameters
            limit = int(request.query.get('limit', 50))
            offset = int(request.query.get('offset', 0))
            status = request.query.get('status')
            workflow_id = request.query.get('workflow_id')
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            executions = self.orchestrator.list_executions(
                limit=limit,
                offset=offset,
                status=status,
                workflow_id=workflow_id
            )
            
            return web.json_response({
                'executions': executions,
                'total': len(executions)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list executions: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_execution(self, request):
        """Get specific execution details"""
        try:
            execution_id = request.match_info['execution_id']
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            execution = self.orchestrator.get_execution(execution_id)
            
            if not execution:
                return web.json_response({'error': 'Execution not found'}, status=404)
            
            return web.json_response(execution)
            
        except Exception as e:
            self.logger.error(f"Failed to get execution {request.match_info.get('execution_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def cancel_execution(self, request):
        """Cancel a running execution"""
        try:
            execution_id = request.match_info['execution_id']
            
            if not self.orchestrator:
                return web.json_response({'error': 'Orchestrator not available'}, status=503)
            
            success = await self.orchestrator.cancel_execution(execution_id)
            
            if not success:
                return web.json_response({'error': 'Execution not found or cannot be cancelled'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to cancel execution {request.match_info.get('execution_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # Scheduler Management
    async def get_scheduler_status(self, request):
        """Get scheduler status"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            scheduler = self.orchestrator.scheduler
            
            return web.json_response({
                'running': scheduler.is_running,
                'jobs_count': len(scheduler.jobs),
                'active_jobs': len([j for j in scheduler.jobs.values() if j.enabled]),
                'next_run': scheduler.get_next_run_time() if hasattr(scheduler, 'get_next_run_time') else None
            })
            
        except Exception as e:
            self.logger.error(f"Failed to get scheduler status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def start_scheduler(self, request):
        """Start the scheduler"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            await self.orchestrator.scheduler.start()
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def stop_scheduler(self, request):
        """Stop the scheduler"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            await self.orchestrator.scheduler.stop()
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def list_jobs(self, request):
        """List scheduled jobs"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            jobs = self.orchestrator.scheduler.list_jobs()
            
            return web.json_response({
                'jobs': jobs,
                'total': len(jobs)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list jobs: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def create_job(self, request):
        """Create a new scheduled job"""
        try:
            data = await request.json()
            
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            job_id = await self.orchestrator.scheduler.create_job(data)
            
            return web.json_response({
                'success': True,
                'job_id': job_id
            }, status=201)
            
        except Exception as e:
            self.logger.error(f"Failed to create job: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_job(self, request):
        """Get specific job details"""
        try:
            job_id = request.match_info['job_id']
            
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            job = self.orchestrator.scheduler.get_job(job_id)
            
            if not job:
                return web.json_response({'error': 'Job not found'}, status=404)
            
            return web.json_response(job)
            
        except Exception as e:
            self.logger.error(f"Failed to get job {request.match_info.get('job_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def update_job(self, request):
        """Update a scheduled job"""
        try:
            job_id = request.match_info['job_id']
            data = await request.json()
            
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            success = await self.orchestrator.scheduler.update_job(job_id, data)
            
            if not success:
                return web.json_response({'error': 'Job not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to update job {request.match_info.get('job_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def delete_job(self, request):
        """Delete a scheduled job"""
        try:
            job_id = request.match_info['job_id']
            
            if not self.orchestrator or not hasattr(self.orchestrator, 'scheduler'):
                return web.json_response({'error': 'Scheduler not available'}, status=503)
            
            success = await self.orchestrator.scheduler.delete_job(job_id)
            
            if not success:
                return web.json_response({'error': 'Job not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to delete job {request.match_info.get('job_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # Trigger Management
    async def list_triggers(self, request):
        """List all triggers"""
        try:
            if not self.trigger_system:
                return web.json_response({'error': 'Trigger system not available'}, status=503)
            
            triggers = self.trigger_system.list_triggers()
            
            return web.json_response({
                'triggers': triggers,
                'total': len(triggers)
            })
            
        except Exception as e:
            self.logger.error(f"Failed to list triggers: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def create_trigger(self, request):
        """Create a new trigger"""
        try:
            data = await request.json()
            
            if not self.trigger_system:
                return web.json_response({'error': 'Trigger system not available'}, status=503)
            
            trigger_id = await self.trigger_system.create_trigger(data)
            
            return web.json_response({
                'success': True,
                'trigger_id': trigger_id
            }, status=201)
            
        except Exception as e:
            self.logger.error(f"Failed to create trigger: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_trigger(self, request):
        """Get specific trigger details"""
        try:
            trigger_id = request.match_info['trigger_id']
            
            if not self.trigger_system:
                return web.json_response({'error': 'Trigger system not available'}, status=503)
            
            trigger = self.trigger_system.get_trigger(trigger_id)
            
            if not trigger:
                return web.json_response({'error': 'Trigger not found'}, status=404)
            
            return web.json_response(trigger)
            
        except Exception as e:
            self.logger.error(f"Failed to get trigger {request.match_info.get('trigger_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def update_trigger(self, request):
        """Update a trigger"""
        try:
            trigger_id = request.match_info['trigger_id']
            data = await request.json()
            
            if not self.trigger_system:
                return web.json_response({'error': 'Trigger system not available'}, status=503)
            
            success = await self.trigger_system.update_trigger(trigger_id, data)
            
            if not success:
                return web.json_response({'error': 'Trigger not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to update trigger {request.match_info.get('trigger_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def delete_trigger(self, request):
        """Delete a trigger"""
        try:
            trigger_id = request.match_info['trigger_id']
            
            if not self.trigger_system:
                return web.json_response({'error': 'Trigger system not available'}, status=503)
            
            success = await self.trigger_system.delete_trigger(trigger_id)
            
            if not success:
                return web.json_response({'error': 'Trigger not found'}, status=404)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            self.logger.error(f"Failed to delete trigger {request.match_info.get('trigger_id')}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    # System Status
    async def get_system_status(self, request):
        """Get overall system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'orchestrator': {
                    'initialized': self.orchestrator is not None,
                    'agents_count': len(self.orchestrator.agents) if self.orchestrator else 0,
                    'workflows_count': len(self.orchestrator.list_workflows()) if self.orchestrator else 0
                },
                'scheduler': {
                    'running': (self.orchestrator and 
                              hasattr(self.orchestrator, 'scheduler') and 
                              self.orchestrator.scheduler.is_running),
                    'jobs_count': (len(self.orchestrator.scheduler.jobs) 
                                 if self.orchestrator and hasattr(self.orchestrator, 'scheduler') 
                                 else 0)
                },
                'trigger_system': {
                    'running': self.trigger_system is not None and self.trigger_system.is_running,
                    'triggers_count': (len(self.trigger_system.triggers) 
                                     if self.trigger_system else 0)
                },
                'agents': {}
            }
            
            # Get agent health
            if self.orchestrator:
                for agent_name, agent in self.orchestrator.agents.items():
                    status['agents'][agent_name] = await self._get_agent_health(agent)
            
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def health_check(self, request):
        """Simple health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    async def get_metrics(self, request):
        """Get system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'uptime': 0,  # Would need to track start time
                'requests_total': 0,  # Would need request counter
                'workflows': {
                    'total': 0,
                    'running': 0,
                    'completed': 0,
                    'failed': 0
                },
                'agents': {
                    'total': len(self.orchestrator.agents) if self.orchestrator else 0,
                    'healthy': 0,
                    'unhealthy': 0
                }
            }
            
            # Calculate workflow metrics
            if self.orchestrator:
                executions = self.orchestrator.list_executions(limit=1000)
                metrics['workflows']['total'] = len(executions)
                
                for execution in executions:
                    status = execution.get('status', 'unknown')
                    if status == 'running':
                        metrics['workflows']['running'] += 1
                    elif status == 'completed':
                        metrics['workflows']['completed'] += 1
                    elif status == 'failed':
                        metrics['workflows']['failed'] += 1
                
                # Calculate agent health metrics
                for agent in self.orchestrator.agents.values():
                    health = await self._get_agent_health(agent)
                    if health.get('healthy', False):
                        metrics['agents']['healthy'] += 1
                    else:
                        metrics['agents']['unhealthy'] += 1
            
            return web.json_response(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _get_agent_health(self, agent) -> Dict[str, Any]:
        """Get agent health status"""
        try:
            # Basic health check - can be extended
            health = {
                'healthy': True,
                'last_check': datetime.now().isoformat(),
                'status': getattr(agent, 'status', 'unknown'),
                'errors': []
            }
            
            # Check if agent has health check method
            if hasattr(agent, 'health_check'):
                try:
                    agent_health = await agent.health_check()
                    health.update(agent_health)
                except Exception as e:
                    health['healthy'] = False
                    health['errors'].append(str(e))
            
            return health
            
        except Exception as e:
            return {
                'healthy': False,
                'last_check': datetime.now().isoformat(),
                'errors': [str(e)]
            }