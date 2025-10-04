"""
On-Demand Test Trigger System

Provides various mechanisms for triggering test workflows on-demand,
including webhooks, API endpoints, file watchers, and manual triggers.
"""

import asyncio
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path
import uuid
import aiohttp
from aiohttp import web
import aiofiles
import watchdog.observers
from watchdog.events import FileSystemEventHandler


@dataclass
class TriggerConfig:
    """Configuration for a trigger"""
    id: str
    name: str
    type: str  # webhook, api, file_watcher, schedule, manual
    enabled: bool = True
    workflow_id: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    authentication: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TriggerEvent:
    """Represents a trigger event"""
    id: str
    trigger_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    processed: bool = False
    workflow_execution_id: Optional[str] = None
    error: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for triggers"""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


class FileWatcherHandler(FileSystemEventHandler):
    """File system event handler for file watchers"""
    
    def __init__(self, trigger_system, trigger_config: TriggerConfig):
        self.trigger_system = trigger_system
        self.trigger_config = trigger_config
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self._handle_file_event('modified', event.src_path))
    
    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(self._handle_file_event('created', event.src_path))
    
    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(self._handle_file_event('deleted', event.src_path))
    
    async def _handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event"""
        try:
            # Check if file matches patterns
            conditions = self.trigger_config.conditions
            patterns = conditions.get('file_patterns', [])
            
            if patterns:
                file_name = Path(file_path).name
                if not any(file_name.endswith(pattern.replace('*', '')) for pattern in patterns):
                    return
            
            # Create trigger event
            trigger_event = TriggerEvent(
                id=str(uuid.uuid4()),
                trigger_id=self.trigger_config.id,
                event_type=f'file_{event_type}',
                payload={
                    'file_path': file_path,
                    'file_name': Path(file_path).name,
                    'event_type': event_type
                },
                source='file_watcher'
            )
            
            await self.trigger_system.process_trigger_event(trigger_event)
            
        except Exception as e:
            self.logger.error(f"Error handling file event: {e}")


class TriggerSystem:
    """
    On-demand test trigger system that supports multiple trigger types:
    - Webhooks (GitHub, GitLab, Jenkins, etc.)
    - REST API endpoints
    - File watchers
    - Manual triggers
    - External system integrations
    """
    
    def __init__(self, config: Dict[str, Any], orchestrator=None):
        self.config = config
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        
        # Trigger management
        self.triggers: Dict[str, TriggerConfig] = {}
        self.trigger_events: Dict[str, TriggerEvent] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Rate limiting
        self.rate_limiter = RateLimiter()
        
        # File watchers
        self.file_observers: Dict[str, watchdog.observers.Observer] = {}
        
        # Web server for webhooks and API
        self.web_app: Optional[web.Application] = None
        self.web_runner: Optional[web.AppRunner] = None
        self.web_site: Optional[web.TCPSite] = None
        
        # Storage
        self.triggers_file = Path(config.get('triggers_file', 'data/triggers.json'))
        self.events_file = Path(config.get('trigger_events_file', 'data/trigger_events.json'))
        
        # Ensure data directory exists
        self.triggers_file.parent.mkdir(parents=True, exist_ok=True)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_running = False
        
        # Load existing data
        self._load_triggers()
        self._load_trigger_events()
    
    async def start(self):
        """Start the trigger system"""
        if self.is_running:
            self.logger.warning("Trigger system already running")
            return
        
        self.logger.info("Starting trigger system...")
        
        try:
            # Start web server for webhooks and API
            await self._start_web_server()
            
            # Start file watchers
            await self._start_file_watchers()
            
            self.is_running = True
            self.logger.info("Trigger system started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start trigger system: {e}")
            raise
    
    async def stop(self):
        """Stop the trigger system"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping trigger system...")
        
        # Stop web server
        await self._stop_web_server()
        
        # Stop file watchers
        self._stop_file_watchers()
        
        self.is_running = False
        self.logger.info("Trigger system stopped")
    
    async def _start_web_server(self):
        """Start web server for webhooks and API endpoints"""
        web_config = self.config.get('web_server', {})
        
        if not web_config.get('enabled', True):
            return
        
        self.web_app = web.Application()
        
        # Add routes
        self.web_app.router.add_post('/webhook/{trigger_id}', self._handle_webhook)
        self.web_app.router.add_post('/api/trigger/{trigger_id}', self._handle_api_trigger)
        self.web_app.router.add_get('/api/triggers', self._list_triggers)
        self.web_app.router.add_post('/api/triggers', self._create_trigger_endpoint)
        self.web_app.router.add_get('/api/triggers/{trigger_id}', self._get_trigger)
        self.web_app.router.add_put('/api/triggers/{trigger_id}', self._update_trigger_endpoint)
        self.web_app.router.add_delete('/api/triggers/{trigger_id}', self._delete_trigger_endpoint)
        self.web_app.router.add_get('/api/events', self._list_events)
        self.web_app.router.add_get('/health', self._health_check)
        
        # Add middleware
        self.web_app.middlewares.append(self._auth_middleware)
        self.web_app.middlewares.append(self._rate_limit_middleware)
        
        # Start server
        self.web_runner = web.AppRunner(self.web_app)
        await self.web_runner.setup()
        
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 8080)
        
        self.web_site = web.TCPSite(self.web_runner, host, port)
        await self.web_site.start()
        
        self.logger.info(f"Web server started on {host}:{port}")
    
    async def _stop_web_server(self):
        """Stop web server"""
        if self.web_site:
            await self.web_site.stop()
        
        if self.web_runner:
            await self.web_runner.cleanup()
        
        self.web_app = None
        self.web_runner = None
        self.web_site = None
    
    async def _start_file_watchers(self):
        """Start file watchers for file-based triggers"""
        for trigger in self.triggers.values():
            if trigger.type == 'file_watcher' and trigger.enabled:
                await self._start_file_watcher(trigger)
    
    async def _start_file_watcher(self, trigger_config: TriggerConfig):
        """Start a file watcher for a specific trigger"""
        try:
            conditions = trigger_config.conditions
            watch_path = conditions.get('watch_path', '.')
            recursive = conditions.get('recursive', True)
            
            if not Path(watch_path).exists():
                self.logger.warning(f"Watch path does not exist: {watch_path}")
                return
            
            observer = watchdog.observers.Observer()
            event_handler = FileWatcherHandler(self, trigger_config)
            
            observer.schedule(event_handler, watch_path, recursive=recursive)
            observer.start()
            
            self.file_observers[trigger_config.id] = observer
            self.logger.info(f"Started file watcher for trigger: {trigger_config.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to start file watcher for {trigger_config.name}: {e}")
    
    def _stop_file_watchers(self):
        """Stop all file watchers"""
        for observer in self.file_observers.values():
            observer.stop()
            observer.join()
        
        self.file_observers.clear()
    
    @web.middleware
    async def _auth_middleware(self, request, handler):
        """Authentication middleware"""
        # Skip auth for health check
        if request.path == '/health':
            return await handler(request)
        
        # Check API key
        api_key = request.headers.get('X-API-Key')
        expected_key = self.config.get('api_key')
        
        if expected_key and api_key != expected_key:
            return web.json_response({'error': 'Invalid API key'}, status=401)
        
        return await handler(request)
    
    @web.middleware
    async def _rate_limit_middleware(self, request, handler):
        """Rate limiting middleware"""
        # Get client IP
        client_ip = request.remote
        
        # Check rate limit
        rate_limit_config = self.config.get('rate_limit', {})
        if rate_limit_config.get('enabled', True):
            max_requests = rate_limit_config.get('max_requests', 100)
            window_seconds = rate_limit_config.get('window_seconds', 3600)
            
            if not self.rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                return web.json_response({'error': 'Rate limit exceeded'}, status=429)
        
        return await handler(request)
    
    async def _handle_webhook(self, request):
        """Handle webhook requests"""
        trigger_id = request.match_info['trigger_id']
        
        if trigger_id not in self.triggers:
            return web.json_response({'error': 'Trigger not found'}, status=404)
        
        trigger_config = self.triggers[trigger_id]
        
        if not trigger_config.enabled:
            return web.json_response({'error': 'Trigger disabled'}, status=403)
        
        if trigger_config.type != 'webhook':
            return web.json_response({'error': 'Invalid trigger type'}, status=400)
        
        try:
            # Get request data
            headers = dict(request.headers)
            payload = await request.json() if request.content_type == 'application/json' else {}
            
            # Verify webhook signature if configured
            if not await self._verify_webhook_signature(request, trigger_config, payload):
                return web.json_response({'error': 'Invalid signature'}, status=401)
            
            # Check conditions
            if not self._check_webhook_conditions(trigger_config, headers, payload):
                return web.json_response({'message': 'Conditions not met'}, status=200)
            
            # Create trigger event
            trigger_event = TriggerEvent(
                id=str(uuid.uuid4()),
                trigger_id=trigger_id,
                event_type='webhook',
                payload=payload,
                headers=headers,
                source=headers.get('user-agent', 'unknown')
            )
            
            # Process event
            execution_id = await self.process_trigger_event(trigger_event)
            
            return web.json_response({
                'message': 'Webhook processed successfully',
                'event_id': trigger_event.id,
                'execution_id': execution_id
            })
            
        except Exception as e:
            self.logger.error(f"Error processing webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _verify_webhook_signature(self, request, trigger_config: TriggerConfig, payload: Dict) -> bool:
        """Verify webhook signature"""
        auth_config = trigger_config.authentication
        
        if not auth_config.get('verify_signature', False):
            return True
        
        signature_header = auth_config.get('signature_header', 'X-Hub-Signature-256')
        secret = auth_config.get('secret')
        
        if not secret:
            return True
        
        signature = request.headers.get(signature_header)
        if not signature:
            return False
        
        # Calculate expected signature
        body = await request.read()
        expected_signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _check_webhook_conditions(self, trigger_config: TriggerConfig, 
                                headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
        """Check if webhook conditions are met"""
        conditions = trigger_config.conditions
        
        # Check event types
        event_types = conditions.get('event_types', [])
        if event_types:
            event_type = payload.get('action') or headers.get('X-GitHub-Event') or headers.get('X-GitLab-Event')
            if event_type not in event_types:
                return False
        
        # Check branches
        branches = conditions.get('branches', [])
        if branches:
            branch = None
            if 'ref' in payload:
                branch = payload['ref'].replace('refs/heads/', '')
            elif 'object_attributes' in payload and 'target_branch' in payload['object_attributes']:
                branch = payload['object_attributes']['target_branch']
            
            if branch and branch not in branches:
                return False
        
        # Check repository
        repositories = conditions.get('repositories', [])
        if repositories:
            repo_name = None
            if 'repository' in payload and 'full_name' in payload['repository']:
                repo_name = payload['repository']['full_name']
            elif 'project' in payload and 'path_with_namespace' in payload['project']:
                repo_name = payload['project']['path_with_namespace']
            
            if repo_name and repo_name not in repositories:
                return False
        
        return True
    
    async def _handle_api_trigger(self, request):
        """Handle API trigger requests"""
        trigger_id = request.match_info['trigger_id']
        
        if trigger_id not in self.triggers:
            return web.json_response({'error': 'Trigger not found'}, status=404)
        
        trigger_config = self.triggers[trigger_id]
        
        if not trigger_config.enabled:
            return web.json_response({'error': 'Trigger disabled'}, status=403)
        
        try:
            payload = await request.json() if request.content_type == 'application/json' else {}
            
            # Create trigger event
            trigger_event = TriggerEvent(
                id=str(uuid.uuid4()),
                trigger_id=trigger_id,
                event_type='api',
                payload=payload,
                headers=dict(request.headers),
                source='api'
            )
            
            # Process event
            execution_id = await self.process_trigger_event(trigger_event)
            
            return web.json_response({
                'message': 'Trigger processed successfully',
                'event_id': trigger_event.id,
                'execution_id': execution_id
            })
            
        except Exception as e:
            self.logger.error(f"Error processing API trigger: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _list_triggers(self, request):
        """List all triggers"""
        triggers_data = []
        for trigger in self.triggers.values():
            triggers_data.append({
                'id': trigger.id,
                'name': trigger.name,
                'type': trigger.type,
                'enabled': trigger.enabled,
                'workflow_id': trigger.workflow_id,
                'created_at': trigger.created_at.isoformat(),
                'updated_at': trigger.updated_at.isoformat()
            })
        
        return web.json_response({'triggers': triggers_data})
    
    async def _create_trigger_endpoint(self, request):
        """Create a new trigger via API"""
        try:
            data = await request.json()
            
            trigger_id = self.create_trigger(
                name=data['name'],
                trigger_type=data['type'],
                workflow_id=data.get('workflow_id'),
                conditions=data.get('conditions', {}),
                authentication=data.get('authentication', {}),
                rate_limit=data.get('rate_limit', {}),
                metadata=data.get('metadata', {})
            )
            
            return web.json_response({
                'message': 'Trigger created successfully',
                'trigger_id': trigger_id
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _get_trigger(self, request):
        """Get trigger details"""
        trigger_id = request.match_info['trigger_id']
        
        if trigger_id not in self.triggers:
            return web.json_response({'error': 'Trigger not found'}, status=404)
        
        trigger = self.triggers[trigger_id]
        
        return web.json_response({
            'id': trigger.id,
            'name': trigger.name,
            'type': trigger.type,
            'enabled': trigger.enabled,
            'workflow_id': trigger.workflow_id,
            'conditions': trigger.conditions,
            'authentication': {k: '***' if k == 'secret' else v for k, v in trigger.authentication.items()},
            'rate_limit': trigger.rate_limit,
            'metadata': trigger.metadata,
            'created_at': trigger.created_at.isoformat(),
            'updated_at': trigger.updated_at.isoformat()
        })
    
    async def _update_trigger_endpoint(self, request):
        """Update trigger via API"""
        trigger_id = request.match_info['trigger_id']
        
        if trigger_id not in self.triggers:
            return web.json_response({'error': 'Trigger not found'}, status=404)
        
        try:
            data = await request.json()
            
            self.update_trigger(trigger_id, **data)
            
            return web.json_response({'message': 'Trigger updated successfully'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _delete_trigger_endpoint(self, request):
        """Delete trigger via API"""
        trigger_id = request.match_info['trigger_id']
        
        if trigger_id not in self.triggers:
            return web.json_response({'error': 'Trigger not found'}, status=404)
        
        self.delete_trigger(trigger_id)
        
        return web.json_response({'message': 'Trigger deleted successfully'})
    
    async def _list_events(self, request):
        """List trigger events"""
        limit = int(request.query.get('limit', 100))
        offset = int(request.query.get('offset', 0))
        
        events = list(self.trigger_events.values())
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        events_data = []
        for event in events[offset:offset + limit]:
            events_data.append({
                'id': event.id,
                'trigger_id': event.trigger_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'source': event.source,
                'processed': event.processed,
                'workflow_execution_id': event.workflow_execution_id,
                'error': event.error
            })
        
        return web.json_response({
            'events': events_data,
            'total': len(self.trigger_events),
            'limit': limit,
            'offset': offset
        })
    
    async def _health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'running': self.is_running,
            'triggers_count': len(self.triggers),
            'active_triggers': len([t for t in self.triggers.values() if t.enabled]),
            'events_count': len(self.trigger_events),
            'timestamp': datetime.now().isoformat()
        })
    
    def create_trigger(self, name: str, trigger_type: str, **kwargs) -> str:
        """Create a new trigger"""
        trigger_id = kwargs.get('trigger_id', str(uuid.uuid4()))
        
        trigger = TriggerConfig(
            id=trigger_id,
            name=name,
            type=trigger_type,
            enabled=kwargs.get('enabled', True),
            workflow_id=kwargs.get('workflow_id'),
            conditions=kwargs.get('conditions', {}),
            authentication=kwargs.get('authentication', {}),
            rate_limit=kwargs.get('rate_limit', {}),
            metadata=kwargs.get('metadata', {})
        )
        
        self.triggers[trigger_id] = trigger
        self._save_triggers()
        
        # Start file watcher if needed
        if trigger_type == 'file_watcher' and trigger.enabled and self.is_running:
            asyncio.create_task(self._start_file_watcher(trigger))
        
        self.logger.info(f"Created trigger: {name} ({trigger_id})")
        return trigger_id
    
    def update_trigger(self, trigger_id: str, **kwargs):
        """Update an existing trigger"""
        if trigger_id not in self.triggers:
            raise ValueError(f"Trigger not found: {trigger_id}")
        
        trigger = self.triggers[trigger_id]
        
        # Update fields
        if 'name' in kwargs:
            trigger.name = kwargs['name']
        if 'enabled' in kwargs:
            trigger.enabled = kwargs['enabled']
        if 'workflow_id' in kwargs:
            trigger.workflow_id = kwargs['workflow_id']
        if 'conditions' in kwargs:
            trigger.conditions = kwargs['conditions']
        if 'authentication' in kwargs:
            trigger.authentication = kwargs['authentication']
        if 'rate_limit' in kwargs:
            trigger.rate_limit = kwargs['rate_limit']
        if 'metadata' in kwargs:
            trigger.metadata = kwargs['metadata']
        
        trigger.updated_at = datetime.now()
        
        self._save_triggers()
        
        # Restart file watcher if needed
        if trigger.type == 'file_watcher' and self.is_running:
            if trigger_id in self.file_observers:
                self.file_observers[trigger_id].stop()
                del self.file_observers[trigger_id]
            
            if trigger.enabled:
                asyncio.create_task(self._start_file_watcher(trigger))
        
        self.logger.info(f"Updated trigger: {trigger.name} ({trigger_id})")
    
    def delete_trigger(self, trigger_id: str):
        """Delete a trigger"""
        if trigger_id not in self.triggers:
            raise ValueError(f"Trigger not found: {trigger_id}")
        
        trigger = self.triggers[trigger_id]
        
        # Stop file watcher if running
        if trigger_id in self.file_observers:
            self.file_observers[trigger_id].stop()
            del self.file_observers[trigger_id]
        
        del self.triggers[trigger_id]
        self._save_triggers()
        
        self.logger.info(f"Deleted trigger: {trigger.name} ({trigger_id})")
    
    async def process_trigger_event(self, event: TriggerEvent) -> Optional[str]:
        """Process a trigger event"""
        try:
            self.trigger_events[event.id] = event
            
            # Get trigger config
            if event.trigger_id not in self.triggers:
                event.error = "Trigger not found"
                event.processed = True
                self._save_trigger_events()
                return None
            
            trigger_config = self.triggers[event.trigger_id]
            
            if not trigger_config.enabled:
                event.error = "Trigger disabled"
                event.processed = True
                self._save_trigger_events()
                return None
            
            # Execute workflow if orchestrator is available
            execution_id = None
            if self.orchestrator and trigger_config.workflow_id:
                execution_id = await self.orchestrator.execute_workflow(
                    workflow_id=trigger_config.workflow_id,
                    triggered_by=f"trigger:{event.event_type}",
                    trigger_data={
                        'trigger_id': event.trigger_id,
                        'event_id': event.id,
                        'payload': event.payload,
                        'source': event.source
                    }
                )
                
                event.workflow_execution_id = execution_id
            
            event.processed = True
            self._save_trigger_events()
            
            self.logger.info(f"Processed trigger event: {event.id} -> {execution_id}")
            
            # Emit event
            await self._emit_event('trigger_processed', {
                'event_id': event.id,
                'trigger_id': event.trigger_id,
                'execution_id': execution_id
            })
            
            return execution_id
            
        except Exception as e:
            event.error = str(e)
            event.processed = True
            self._save_trigger_events()
            
            self.logger.error(f"Error processing trigger event {event.id}: {e}")
            return None
    
    async def manual_trigger(self, workflow_id: str, payload: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Manually trigger a workflow"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not available")
        
        # Create manual trigger event
        event = TriggerEvent(
            id=str(uuid.uuid4()),
            trigger_id="manual",
            event_type="manual",
            payload=payload or {},
            source="manual"
        )
        
        # Execute workflow
        execution_id = await self.orchestrator.execute_workflow(
            workflow_id=workflow_id,
            triggered_by="manual",
            trigger_data={
                'event_id': event.id,
                'payload': event.payload
            }
        )
        
        event.workflow_execution_id = execution_id
        event.processed = True
        
        self.trigger_events[event.id] = event
        self._save_trigger_events()
        
        self.logger.info(f"Manual trigger executed: {workflow_id} -> {execution_id}")
        return execution_id
    
    def _load_triggers(self):
        """Load triggers from storage"""
        try:
            if self.triggers_file.exists():
                with open(self.triggers_file, 'r') as f:
                    triggers_data = json.load(f)
                
                for trigger_data in triggers_data:
                    trigger = TriggerConfig(
                        id=trigger_data['id'],
                        name=trigger_data['name'],
                        type=trigger_data['type'],
                        enabled=trigger_data.get('enabled', True),
                        workflow_id=trigger_data.get('workflow_id'),
                        conditions=trigger_data.get('conditions', {}),
                        authentication=trigger_data.get('authentication', {}),
                        rate_limit=trigger_data.get('rate_limit', {}),
                        metadata=trigger_data.get('metadata', {}),
                        created_at=datetime.fromisoformat(trigger_data.get('created_at', datetime.now().isoformat())),
                        updated_at=datetime.fromisoformat(trigger_data.get('updated_at', datetime.now().isoformat()))
                    )
                    self.triggers[trigger.id] = trigger
                
                self.logger.info(f"Loaded {len(self.triggers)} triggers from storage")
        except Exception as e:
            self.logger.error(f"Error loading triggers: {e}")
    
    def _save_triggers(self):
        """Save triggers to storage"""
        try:
            triggers_data = []
            for trigger in self.triggers.values():
                triggers_data.append({
                    'id': trigger.id,
                    'name': trigger.name,
                    'type': trigger.type,
                    'enabled': trigger.enabled,
                    'workflow_id': trigger.workflow_id,
                    'conditions': trigger.conditions,
                    'authentication': trigger.authentication,
                    'rate_limit': trigger.rate_limit,
                    'metadata': trigger.metadata,
                    'created_at': trigger.created_at.isoformat(),
                    'updated_at': trigger.updated_at.isoformat()
                })
            
            with open(self.triggers_file, 'w') as f:
                json.dump(triggers_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving triggers: {e}")
    
    def _load_trigger_events(self):
        """Load trigger events from storage"""
        try:
            if self.events_file.exists():
                with open(self.events_file, 'r') as f:
                    events_data = json.load(f)
                
                for event_data in events_data:
                    event = TriggerEvent(
                        id=event_data['id'],
                        trigger_id=event_data['trigger_id'],
                        event_type=event_data['event_type'],
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        payload=event_data.get('payload', {}),
                        source=event_data.get('source', ''),
                        headers=event_data.get('headers', {}),
                        processed=event_data.get('processed', False),
                        workflow_execution_id=event_data.get('workflow_execution_id'),
                        error=event_data.get('error')
                    )
                    self.trigger_events[event.id] = event
                
                # Keep only recent events (last 1000)
                if len(self.trigger_events) > 1000:
                    sorted_events = sorted(
                        self.trigger_events.values(),
                        key=lambda x: x.timestamp,
                        reverse=True
                    )
                    self.trigger_events = {
                        event.id: event for event in sorted_events[:1000]
                    }
                
                self.logger.info(f"Loaded {len(self.trigger_events)} trigger events from storage")
        except Exception as e:
            self.logger.error(f"Error loading trigger events: {e}")
    
    def _save_trigger_events(self):
        """Save trigger events to storage"""
        try:
            events_data = []
            for event in self.trigger_events.values():
                events_data.append({
                    'id': event.id,
                    'trigger_id': event.trigger_id,
                    'event_type': event.event_type,
                    'timestamp': event.timestamp.isoformat(),
                    'payload': event.payload,
                    'source': event.source,
                    'headers': event.headers,
                    'processed': event.processed,
                    'workflow_execution_id': event.workflow_execution_id,
                    'error': event.error
                })
            
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving trigger events: {e}")
    
    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit an event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, event_data)
                    else:
                        handler(event_type, event_data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def get_status(self) -> Dict[str, Any]:
        """Get trigger system status"""
        return {
            'running': self.is_running,
            'triggers': {
                'total': len(self.triggers),
                'enabled': len([t for t in self.triggers.values() if t.enabled]),
                'by_type': {
                    trigger_type: len([t for t in self.triggers.values() if t.type == trigger_type])
                    for trigger_type in set(t.type for t in self.triggers.values())
                }
            },
            'events': {
                'total': len(self.trigger_events),
                'processed': len([e for e in self.trigger_events.values() if e.processed]),
                'recent': len([
                    e for e in self.trigger_events.values()
                    if e.timestamp > datetime.now() - timedelta(hours=24)
                ])
            },
            'file_watchers': len(self.file_observers),
            'web_server': self.web_site is not None
        }