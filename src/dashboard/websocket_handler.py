"""
WebSocket Handler for Dashboard

Handles real-time communication between the dashboard and clients.
"""

import asyncio
import json
import logging
import weakref
from datetime import datetime
from typing import Any, Dict, List, Set
from aiohttp import web, WSMsgType


class WebSocketHandler:
    """
    WebSocket handler for real-time dashboard updates.
    
    Manages WebSocket connections and broadcasts events to connected clients.
    """
    
    def __init__(self, orchestrator=None, trigger_system=None):
        self.orchestrator = orchestrator
        self.trigger_system = trigger_system
        self.logger = logging.getLogger(__name__)
        
        # Use WeakSet to automatically clean up closed connections
        self.connections: Set[web.WebSocketResponse] = weakref.WeakSet()
        
        # Event handlers
        self.event_handlers = {}
        
        # Statistics
        self.stats = {
            'connections_total': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'broadcasts_sent': 0
        }
    
    async def handle_websocket(self, request):
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to connections
        self.connections.add(ws)
        self.stats['connections_total'] += 1
        
        client_info = {
            'remote': request.remote,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'connected_at': datetime.now().isoformat()
        }
        
        self.logger.info(f"WebSocket client connected: {client_info['remote']}")
        
        try:
            # Send welcome message
            await self._send_message(ws, {
                'type': 'welcome',
                'message': 'Connected to Test Automation Dashboard',
                'timestamp': datetime.now().isoformat(),
                'client_info': client_info
            })
            
            # Send initial system status
            await self._send_system_status(ws)
            
            # Handle incoming messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(ws, data)
                        self.stats['messages_received'] += 1
                    except json.JSONDecodeError:
                        await self._send_error(ws, 'Invalid JSON message')
                    except Exception as e:
                        self.logger.error(f"Error handling WebSocket message: {e}")
                        await self._send_error(ws, f'Message handling error: {str(e)}')
                
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f'WebSocket error: {ws.exception()}')
                    break
                
                elif msg.type == WSMsgType.CLOSE:
                    self.logger.info(f"WebSocket client disconnected: {client_info['remote']}")
                    break
        
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
        
        finally:
            # Connection will be automatically removed from WeakSet
            pass
        
        return ws
    
    async def _handle_message(self, ws: web.WebSocketResponse, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = data.get('type')
        
        if message_type == 'ping':
            await self._send_message(ws, {
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
        
        elif message_type == 'subscribe':
            # Subscribe to specific events
            events = data.get('events', [])
            await self._handle_subscription(ws, events)
        
        elif message_type == 'unsubscribe':
            # Unsubscribe from events
            events = data.get('events', [])
            await self._handle_unsubscription(ws, events)
        
        elif message_type == 'get_status':
            # Send current system status
            await self._send_system_status(ws)
        
        elif message_type == 'get_agents':
            # Send current agents status
            await self._send_agents_status(ws)
        
        elif message_type == 'get_workflows':
            # Send current workflows
            await self._send_workflows_status(ws)
        
        elif message_type == 'get_executions':
            # Send recent executions
            limit = data.get('limit', 10)
            await self._send_executions_status(ws, limit)
        
        else:
            await self._send_error(ws, f'Unknown message type: {message_type}')
    
    async def _handle_subscription(self, ws: web.WebSocketResponse, events: List[str]):
        """Handle event subscription"""
        # Store subscription info in WebSocket (if needed for filtering)
        if not hasattr(ws, '_subscriptions'):
            ws._subscriptions = set()
        
        ws._subscriptions.update(events)
        
        await self._send_message(ws, {
            'type': 'subscription_confirmed',
            'events': events,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_unsubscription(self, ws: web.WebSocketResponse, events: List[str]):
        """Handle event unsubscription"""
        if hasattr(ws, '_subscriptions'):
            ws._subscriptions.difference_update(events)
        
        await self._send_message(ws, {
            'type': 'unsubscription_confirmed',
            'events': events,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _send_message(self, ws: web.WebSocketResponse, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            if ws.closed:
                return False
            
            await ws.send_str(json.dumps(message))
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    async def _send_error(self, ws: web.WebSocketResponse, error_message: str):
        """Send error message to WebSocket connection"""
        await self._send_message(ws, {
            'type': 'error',
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _send_system_status(self, ws: web.WebSocketResponse):
        """Send current system status"""
        try:
            status = {
                'orchestrator': {
                    'initialized': self.orchestrator is not None,
                    'agents_count': len(self.orchestrator.agents) if self.orchestrator else 0
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
                }
            }
            
            await self._send_message(ws, {
                'type': 'system_status',
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send system status: {e}")
            await self._send_error(ws, 'Failed to get system status')
    
    async def _send_agents_status(self, ws: web.WebSocketResponse):
        """Send current agents status"""
        try:
            if not self.orchestrator:
                await self._send_error(ws, 'Orchestrator not available')
                return
            
            agents_status = {}
            for agent_name, agent in self.orchestrator.agents.items():
                agents_status[agent_name] = {
                    'name': agent_name,
                    'status': agent.status.value if hasattr(agent, 'status') else 'unknown',
                    'last_execution': getattr(agent, 'last_execution', None)
                }
            
            await self._send_message(ws, {
                'type': 'agents_status',
                'data': agents_status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send agents status: {e}")
            await self._send_error(ws, 'Failed to get agents status')
    
    async def _send_workflows_status(self, ws: web.WebSocketResponse):
        """Send current workflows"""
        try:
            if not self.orchestrator:
                await self._send_error(ws, 'Orchestrator not available')
                return
            
            workflows = self.orchestrator.list_workflows()
            
            await self._send_message(ws, {
                'type': 'workflows_status',
                'data': workflows,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send workflows status: {e}")
            await self._send_error(ws, 'Failed to get workflows status')
    
    async def _send_executions_status(self, ws: web.WebSocketResponse, limit: int = 10):
        """Send recent executions"""
        try:
            if not self.orchestrator:
                await self._send_error(ws, 'Orchestrator not available')
                return
            
            executions = self.orchestrator.list_executions(limit=limit)
            
            await self._send_message(ws, {
                'type': 'executions_status',
                'data': executions,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send executions status: {e}")
            await self._send_error(ws, 'Failed to get executions status')
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        # Create list of connections to avoid modification during iteration
        connections_list = list(self.connections)
        
        # Send to all connections concurrently
        tasks = []
        for ws in connections_list:
            if not ws.closed:
                # Check if client is subscribed to this event type
                if self._should_send_to_client(ws, message):
                    tasks.append(self._send_message(ws, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful sends
            successful_sends = sum(1 for result in results if result is True)
            self.stats['broadcasts_sent'] += successful_sends
            
            self.logger.debug(f"Broadcast sent to {successful_sends}/{len(tasks)} clients")
    
    def _should_send_to_client(self, ws: web.WebSocketResponse, message: Dict[str, Any]) -> bool:
        """Check if message should be sent to specific client based on subscriptions"""
        # If client has no subscriptions, send all messages
        if not hasattr(ws, '_subscriptions') or not ws._subscriptions:
            return True
        
        message_type = message.get('type', '')
        event_type = message.get('event_type', '')
        
        # Check if client is subscribed to this message type or event type
        return (message_type in ws._subscriptions or 
                event_type in ws._subscriptions or 
                'all' in ws._subscriptions)
    
    async def broadcast_workflow_event(self, event_type: str, workflow_data: Dict[str, Any]):
        """Broadcast workflow-related event"""
        await self.broadcast({
            'type': 'workflow_event',
            'event_type': event_type,
            'data': workflow_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_agent_event(self, event_type: str, agent_data: Dict[str, Any]):
        """Broadcast agent-related event"""
        await self.broadcast({
            'type': 'agent_event',
            'event_type': event_type,
            'data': agent_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_system_event(self, event_type: str, system_data: Dict[str, Any]):
        """Broadcast system-related event"""
        await self.broadcast({
            'type': 'system_event',
            'event_type': event_type,
            'data': system_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_health_update(self, health_data: Dict[str, Any]):
        """Broadcast health status update"""
        await self.broadcast({
            'type': 'health_update',
            'data': health_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_trigger_event(self, event_type: str, trigger_data: Dict[str, Any]):
        """Broadcast trigger-related event"""
        await self.broadcast({
            'type': 'trigger_event',
            'event_type': event_type,
            'data': trigger_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def close_all_connections(self):
        """Close all WebSocket connections"""
        if not self.connections:
            return
        
        connections_list = list(self.connections)
        
        for ws in connections_list:
            try:
                if not ws.closed:
                    await ws.close()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket connection: {e}")
        
        self.logger.info(f"Closed {len(connections_list)} WebSocket connections")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket handler statistics"""
        return {
            'active_connections': len(self.connections),
            'total_connections': self.stats['connections_total'],
            'messages_sent': self.stats['messages_sent'],
            'messages_received': self.stats['messages_received'],
            'broadcasts_sent': self.stats['broadcasts_sent']
        }
    
    def add_event_handler(self, event_type: str, handler):
        """Add event handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler):
        """Remove event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, event_data)
                    else:
                        handler(event_type, event_data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Also broadcast to WebSocket clients
        await self.broadcast({
            'type': 'event',
            'event_type': event_type,
            'data': event_data,
            'timestamp': datetime.now().isoformat()
        })