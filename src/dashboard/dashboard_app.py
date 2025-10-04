"""
Orchestration Dashboard Application

Web-based dashboard for managing and monitoring the test automation system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import aiohttp_jinja2
import jinja2
from aiohttp import web, WSMsgType
import aiofiles

from .api_routes import APIRoutes
from .websocket_handler import WebSocketHandler


class DashboardApp:
    """
    Main dashboard application that provides a web interface for:
    - Monitoring agent status and health
    - Managing workflows and schedules
    - Viewing test results and reports
    - Configuring triggers and notifications
    - Real-time system monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, orchestrator=None, trigger_system=None):
        # Handle string config path for compatibility
        if isinstance(config, str):
            config_path = Path(config)
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                except Exception:
                    config = {"dashboard": {"port": 8082}}
            else:
                config = {"dashboard": {"port": 8082}}
        
        self.config = config or {"dashboard": {"port": 8082}}
        self.orchestrator = orchestrator
        self.trigger_system = trigger_system
        self.logger = logging.getLogger(__name__)
        
        # Web application
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Components
        self.api_routes: Optional[APIRoutes] = None
        self.websocket_handler: Optional[WebSocketHandler] = None
        
        # State
        self.is_running = False
        
        # Paths
        self.static_dir = Path(__file__).parent / 'static'
        self.templates_dir = Path(__file__).parent / 'templates'
        
        # Ensure directories exist
        self.static_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize dashboard (alias for compatibility)"""
        await self.start()
    
    async def start_server(self):
        """Start server (alias for compatibility)"""
        await self.start()
    
    async def stop_server(self):
        """Stop server (alias for compatibility)"""
        await self.stop()
    
    async def shutdown(self):
        """Shutdown dashboard (alias for compatibility)"""
        await self.stop()
    
    async def start(self):
        """Start the dashboard application"""
        if self.is_running:
            self.logger.warning("Dashboard already running")
            return
        
        self.logger.info("Starting dashboard application...")
        
        try:
            # Create web application
            self.app = web.Application()
            
            # Setup Jinja2 templates
            aiohttp_jinja2.setup(
                self.app,
                loader=jinja2.FileSystemLoader(str(self.templates_dir))
            )
            
            # Initialize components
            self.api_routes = APIRoutes(self.orchestrator, self.trigger_system)
            self.websocket_handler = WebSocketHandler(self.orchestrator, self.trigger_system)
            
            # Setup routes
            await self._setup_routes()
            
            # Setup middleware
            self._setup_middleware()
            
            # Create static files if they don't exist
            await self._create_static_files()
            await self._create_templates()
            
            # Start web server
            await self._start_web_server()
            
            # Setup event handlers for real-time updates
            self._setup_event_handlers()
            
            self.is_running = True
            self.logger.info("Dashboard application started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            raise
    
    async def stop(self):
        """Stop the dashboard application"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping dashboard application...")
        
        # Close WebSocket connections
        if self.websocket_handler:
            await self.websocket_handler.close_all_connections()
        
        # Stop web server
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        self.is_running = False
        self.logger.info("Dashboard application stopped")
    
    async def _setup_routes(self):
        """Setup web routes"""
        # Static files
        self.app.router.add_static('/static/', path=self.static_dir, name='static')
        
        # Main dashboard pages
        self.app.router.add_get('/', self._dashboard_home)
        self.app.router.add_get('/agents', self._agents_page)
        self.app.router.add_get('/workflows', self._workflows_page)
        self.app.router.add_get('/schedules', self._schedules_page)
        self.app.router.add_get('/triggers', self._triggers_page)
        self.app.router.add_get('/reports', self._reports_page)
        self.app.router.add_get('/logs', self._logs_page)
        self.app.router.add_get('/settings', self._settings_page)
        
        # WebSocket endpoint
        self.app.router.add_get('/ws', self.websocket_handler.handle_websocket)
        
        # API routes
        api_prefix = '/api/v1'
        
        # Agent management
        self.app.router.add_get(f'{api_prefix}/agents', self.api_routes.list_agents)
        self.app.router.add_get(f'{api_prefix}/agents/{{agent_id}}', self.api_routes.get_agent)
        self.app.router.add_post(f'{api_prefix}/agents/{{agent_id}}/restart', self.api_routes.restart_agent)
        
        # Workflow management
        self.app.router.add_get(f'{api_prefix}/workflows', self.api_routes.list_workflows)
        self.app.router.add_post(f'{api_prefix}/workflows', self.api_routes.create_workflow)
        self.app.router.add_get(f'{api_prefix}/workflows/{{workflow_id}}', self.api_routes.get_workflow)
        self.app.router.add_put(f'{api_prefix}/workflows/{{workflow_id}}', self.api_routes.update_workflow)
        self.app.router.add_delete(f'{api_prefix}/workflows/{{workflow_id}}', self.api_routes.delete_workflow)
        self.app.router.add_post(f'{api_prefix}/workflows/{{workflow_id}}/execute', self.api_routes.execute_workflow)
        
        # Workflow executions
        self.app.router.add_get(f'{api_prefix}/executions', self.api_routes.list_executions)
        self.app.router.add_get(f'{api_prefix}/executions/{{execution_id}}', self.api_routes.get_execution)
        self.app.router.add_post(f'{api_prefix}/executions/{{execution_id}}/cancel', self.api_routes.cancel_execution)
        
        # Scheduler management
        self.app.router.add_get(f'{api_prefix}/scheduler/status', self.api_routes.get_scheduler_status)
        self.app.router.add_post(f'{api_prefix}/scheduler/start', self.api_routes.start_scheduler)
        self.app.router.add_post(f'{api_prefix}/scheduler/stop', self.api_routes.stop_scheduler)
        self.app.router.add_get(f'{api_prefix}/scheduler/jobs', self.api_routes.list_jobs)
        self.app.router.add_post(f'{api_prefix}/scheduler/jobs', self.api_routes.create_job)
        self.app.router.add_get(f'{api_prefix}/scheduler/jobs/{{job_id}}', self.api_routes.get_job)
        self.app.router.add_put(f'{api_prefix}/scheduler/jobs/{{job_id}}', self.api_routes.update_job)
        self.app.router.add_delete(f'{api_prefix}/scheduler/jobs/{{job_id}}', self.api_routes.delete_job)
        
        # Trigger management
        self.app.router.add_get(f'{api_prefix}/triggers', self.api_routes.list_triggers)
        self.app.router.add_post(f'{api_prefix}/triggers', self.api_routes.create_trigger)
        self.app.router.add_get(f'{api_prefix}/triggers/{{trigger_id}}', self.api_routes.get_trigger)
        self.app.router.add_put(f'{api_prefix}/triggers/{{trigger_id}}', self.api_routes.update_trigger)
        self.app.router.add_delete(f'{api_prefix}/triggers/{{trigger_id}}', self.api_routes.delete_trigger)
        
        # System status
        self.app.router.add_get(f'{api_prefix}/status', self.api_routes.get_system_status)
        self.app.router.add_get(f'{api_prefix}/health', self.api_routes.health_check)
        self.app.router.add_get(f'{api_prefix}/metrics', self.api_routes.get_metrics)
    
    def _setup_middleware(self):
        """Setup middleware"""
        # CORS middleware
        async def cors_middleware(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        # Error handling middleware
        async def error_middleware(request, handler):
            try:
                return await handler(request)
            except web.HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Unhandled error in {request.path}: {e}")
                return web.json_response(
                    {'error': 'Internal server error'},
                    status=500
                )
        
        self.app.middlewares.append(cors_middleware)
        self.app.middlewares.append(error_middleware)
    
    async def _start_web_server(self):
        """Start the web server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        host = self.config.get('host', '0.0.0.0')
        port = self.config.get('port', 8081)
        
        self.site = web.TCPSite(self.runner, host, port)
        await self.site.start()
        
        self.logger.info(f"Dashboard web server started on {host}:{port}")
    
    def _setup_event_handlers(self):
        """Setup event handlers for real-time updates"""
        if self.orchestrator:
            # Listen to orchestrator events
            self.orchestrator.add_event_handler('workflow_started', self._on_workflow_event)
            self.orchestrator.add_event_handler('workflow_completed', self._on_workflow_event)
            self.orchestrator.add_event_handler('workflow_failed', self._on_workflow_event)
            self.orchestrator.add_event_handler('health_check', self._on_health_check)
        
        if self.trigger_system:
            # Listen to trigger events
            self.trigger_system.add_event_handler('trigger_processed', self._on_trigger_event)
    
    async def _on_workflow_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle workflow events for real-time updates"""
        if self.websocket_handler:
            await self.websocket_handler.broadcast({
                'type': 'workflow_event',
                'event_type': event_type,
                'data': event_data,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _on_health_check(self, event_type: str, event_data: Dict[str, Any]):
        """Handle health check events"""
        if self.websocket_handler:
            await self.websocket_handler.broadcast({
                'type': 'health_update',
                'data': event_data,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _on_trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle trigger events"""
        if self.websocket_handler:
            await self.websocket_handler.broadcast({
                'type': 'trigger_event',
                'event_type': event_type,
                'data': event_data,
                'timestamp': datetime.now().isoformat()
            })
    
    # Page handlers
    @aiohttp_jinja2.template('dashboard.html')
    async def _dashboard_home(self, request):
        """Dashboard home page"""
        return {
            'title': 'Test Automation Dashboard',
            'page': 'dashboard'
        }
    
    @aiohttp_jinja2.template('agents.html')
    async def _agents_page(self, request):
        """Agents management page"""
        return {
            'title': 'Agents',
            'page': 'agents'
        }
    
    @aiohttp_jinja2.template('workflows.html')
    async def _workflows_page(self, request):
        """Workflows management page"""
        return {
            'title': 'Workflows',
            'page': 'workflows'
        }
    
    @aiohttp_jinja2.template('schedules.html')
    async def _schedules_page(self, request):
        """Schedules management page"""
        return {
            'title': 'Schedules',
            'page': 'schedules'
        }
    
    @aiohttp_jinja2.template('triggers.html')
    async def _triggers_page(self, request):
        """Triggers management page"""
        return {
            'title': 'Triggers',
            'page': 'triggers'
        }
    
    @aiohttp_jinja2.template('reports.html')
    async def _reports_page(self, request):
        """Reports page"""
        return {
            'title': 'Reports',
            'page': 'reports'
        }
    
    @aiohttp_jinja2.template('logs.html')
    async def _logs_page(self, request):
        """Logs page"""
        return {
            'title': 'Logs',
            'page': 'logs'
        }
    
    @aiohttp_jinja2.template('settings.html')
    async def _settings_page(self, request):
        """Settings page"""
        return {
            'title': 'Settings',
            'page': 'settings'
        }
    
    async def _create_static_files(self):
        """Create static CSS and JS files"""
        # Create main CSS file
        css_content = """
/* Dashboard Styles */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --background-color: #f8fafc;
    --card-background: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--background-color);
    color: var(--text-primary);
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.header {
    background: var(--card-background);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
}

.nav {
    display: flex;
    gap: 2rem;
}

.nav a {
    text-decoration: none;
    color: var(--text-secondary);
    font-weight: 500;
    transition: color 0.2s;
}

.nav a:hover,
.nav a.active {
    color: var(--primary-color);
}

/* Main Content */
.main {
    padding: 2rem 0;
}

.page-title {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 2rem;
    color: var(--text-primary);
}

/* Cards */
.card {
    background: var(--card-background);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color);
    margin-bottom: 1.5rem;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
}

/* Grid */
.grid {
    display: grid;
    gap: 1.5rem;
}

.grid-2 {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.grid-3 {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.grid-4 {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

/* Status indicators */
.status {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status-success {
    background-color: #dcfce7;
    color: #166534;
}

.status-warning {
    background-color: #fef3c7;
    color: #92400e;
}

.status-error {
    background-color: #fee2e2;
    color: #991b1b;
}

.status-info {
    background-color: #dbeafe;
    color: #1e40af;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: currentColor;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background-color: #1d4ed8;
}

.btn-secondary {
    background-color: var(--secondary-color);
    color: white;
}

.btn-secondary:hover {
    background-color: #475569;
}

.btn-success {
    background-color: var(--success-color);
    color: white;
}

.btn-success:hover {
    background-color: #059669;
}

.btn-warning {
    background-color: var(--warning-color);
    color: white;
}

.btn-warning:hover {
    background-color: #d97706;
}

.btn-error {
    background-color: var(--error-color);
    color: white;
}

.btn-error:hover {
    background-color: #dc2626;
}

/* Tables */
.table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.table th,
.table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.table th {
    font-weight: 600;
    color: var(--text-primary);
    background-color: #f8fafc;
}

.table tbody tr:hover {
    background-color: #f8fafc;
}

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-input,
.form-select,
.form-textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.875rem;
    transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Loading */
.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top: 3px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }
    
    .header-content {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav {
        gap: 1rem;
    }
    
    .grid-2,
    .grid-3,
    .grid-4 {
        grid-template-columns: 1fr;
    }
}
"""
        
        css_file = self.static_dir / 'dashboard.css'
        async with aiofiles.open(css_file, 'w') as f:
            await f.write(css_content)
        
        # Create main JavaScript file
        js_content = """
// Dashboard JavaScript
class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = connected ? 'status status-success' : 'status status-error';
            statusElement.innerHTML = connected ? 
                '<span class="status-dot"></span>Connected' : 
                '<span class="status-dot"></span>Disconnected';
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'workflow_event':
                this.handleWorkflowEvent(data);
                break;
            case 'health_update':
                this.handleHealthUpdate(data);
                break;
            case 'trigger_event':
                this.handleTriggerEvent(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handleWorkflowEvent(data) {
        // Update workflow status in UI
        this.updateWorkflowStatus(data.data.workflow_id, data.event_type, data.data);
        
        // Show notification
        this.showNotification(`Workflow ${data.event_type.replace('workflow_', '')}`, 
                            data.data.workflow_name || data.data.workflow_id);
    }
    
    handleHealthUpdate(data) {
        // Update agent health indicators
        this.updateAgentHealth(data.data);
    }
    
    handleTriggerEvent(data) {
        // Update trigger status
        this.updateTriggerStatus(data.data.trigger_id, data.event_type, data.data);
    }
    
    setupEventListeners() {
        // Refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('refresh-btn')) {
                this.refreshData(e.target.dataset.type);
            }
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('ajax-form')) {
                e.preventDefault();
                this.handleFormSubmit(e.target);
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Load system status
            await this.loadSystemStatus();
            
            // Load page-specific data based on current page
            const page = document.body.dataset.page;
            switch (page) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'agents':
                    await this.loadAgentsData();
                    break;
                case 'workflows':
                    await this.loadWorkflowsData();
                    break;
                case 'schedules':
                    await this.loadSchedulesData();
                    break;
                case 'triggers':
                    await this.loadTriggersData();
                    break;
                case 'reports':
                    await this.loadReportsData();
                    break;
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load data');
        }
    }
    
    async apiCall(endpoint, options = {}) {
        const response = await fetch(`/api/v1${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async loadSystemStatus() {
        try {
            const status = await this.apiCall('/status');
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }
    
    async loadDashboardData() {
        // Load dashboard overview data
        const [agents, workflows, executions] = await Promise.all([
            this.apiCall('/agents'),
            this.apiCall('/workflows'),
            this.apiCall('/executions?limit=10')
        ]);
        
        this.updateDashboardOverview({ agents, workflows, executions });
    }
    
    async loadAgentsData() {
        const agents = await this.apiCall('/agents');
        this.updateAgentsTable(agents);
    }
    
    async loadWorkflowsData() {
        const workflows = await this.apiCall('/workflows');
        this.updateWorkflowsTable(workflows);
    }
    
    async loadSchedulesData() {
        const jobs = await this.apiCall('/scheduler/jobs');
        this.updateSchedulesTable(jobs);
    }
    
    async loadTriggersData() {
        const triggers = await this.apiCall('/triggers');
        this.updateTriggersTable(triggers);
    }
    
    async loadReportsData() {
        // Load recent reports and executions
        const executions = await this.apiCall('/executions?limit=50');
        this.updateReportsTable(executions);
    }
    
    updateSystemStatus(status) {
        // Update system status indicators
        const elements = {
            'orchestrator-status': status.orchestrator?.initialized ? 'success' : 'error',
            'scheduler-status': status.scheduler?.running ? 'success' : 'warning',
            'agents-status': Object.values(status.agents || {}).every(Boolean) ? 'success' : 'warning'
        };
        
        Object.entries(elements).forEach(([id, statusClass]) => {
            const element = document.getElementById(id);
            if (element) {
                element.className = `status status-${statusClass}`;
            }
        });
    }
    
    updateWorkflowStatus(workflowId, eventType, data) {
        const row = document.querySelector(`[data-workflow-id="${workflowId}"]`);
        if (row) {
            const statusCell = row.querySelector('.workflow-status');
            if (statusCell) {
                let statusClass = 'info';
                let statusText = eventType.replace('workflow_', '');
                
                if (eventType === 'workflow_completed') {
                    statusClass = 'success';
                    statusText = 'completed';
                } else if (eventType === 'workflow_failed') {
                    statusClass = 'error';
                    statusText = 'failed';
                } else if (eventType === 'workflow_started') {
                    statusClass = 'info';
                    statusText = 'running';
                }
                
                statusCell.innerHTML = `<span class="status status-${statusClass}"><span class="status-dot"></span>${statusText}</span>`;
            }
        }
    }
    
    updateAgentHealth(healthData) {
        Object.entries(healthData).forEach(([agentName, health]) => {
            const element = document.getElementById(`agent-${agentName}-status`);
            if (element) {
                const statusClass = health.healthy ? 'success' : 'error';
                const statusText = health.healthy ? 'healthy' : 'unhealthy';
                element.innerHTML = `<span class="status status-${statusClass}"><span class="status-dot"></span>${statusText}</span>`;
            }
        });
    }
    
    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to notifications container
        let container = document.getElementById('notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications';
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }
    
    showError(message) {
        this.showNotification('Error', message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification('Success', message, 'success');
    }
    
    async refreshData(type) {
        try {
            switch (type) {
                case 'agents':
                    await this.loadAgentsData();
                    break;
                case 'workflows':
                    await this.loadWorkflowsData();
                    break;
                case 'schedules':
                    await this.loadSchedulesData();
                    break;
                case 'triggers':
                    await this.loadTriggersData();
                    break;
                case 'reports':
                    await this.loadReportsData();
                    break;
                default:
                    await this.loadInitialData();
            }
            
            this.showSuccess('Data refreshed successfully');
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showError('Failed to refresh data');
        }
    }
    
    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const method = form.dataset.method || 'POST';
            const endpoint = form.action.replace(window.location.origin + '/api/v1', '');
            
            await this.apiCall(endpoint, {
                method: method,
                body: JSON.stringify(data)
            });
            
            this.showSuccess('Operation completed successfully');
            
            // Refresh relevant data
            const refreshType = form.dataset.refresh;
            if (refreshType) {
                await this.refreshData(refreshType);
            }
            
            // Close modal if exists
            const modal = form.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Form submission failed:', error);
            this.showError('Operation failed');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
"""
        
        js_file = self.static_dir / 'dashboard.js'
        async with aiofiles.open(js_file, 'w') as f:
            await f.write(js_content)
    
    async def _create_templates(self):
        """Create HTML templates"""
        # Base template
        base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Test Automation Dashboard</title>
    <link rel="stylesheet" href="/static/dashboard.css">
</head>
<body data-page="{{ page }}">
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">Test Automation Dashboard</div>
                <nav class="nav">
                    <a href="/" class="{% if page == 'dashboard' %}active{% endif %}">Dashboard</a>
                    <a href="/agents" class="{% if page == 'agents' %}active{% endif %}">Agents</a>
                    <a href="/workflows" class="{% if page == 'workflows' %}active{% endif %}">Workflows</a>
                    <a href="/schedules" class="{% if page == 'schedules' %}active{% endif %}">Schedules</a>
                    <a href="/triggers" class="{% if page == 'triggers' %}active{% endif %}">Triggers</a>
                    <a href="/reports" class="{% if page == 'reports' %}active{% endif %}">Reports</a>
                    <a href="/logs" class="{% if page == 'logs' %}active{% endif %}">Logs</a>
                    <a href="/settings" class="{% if page == 'settings' %}active{% endif %}">Settings</a>
                </nav>
                <div id="connection-status" class="status status-info">
                    <span class="status-dot"></span>Connecting...
                </div>
            </div>
        </div>
    </header>
    
    <main class="main">
        <div class="container">
            {% block content %}{% endblock %}
        </div>
    </main>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>
"""
        
        base_file = self.templates_dir / 'base.html'
        async with aiofiles.open(base_file, 'w') as f:
            await f.write(base_template)
        
        # Dashboard template
        dashboard_template = """
{% extends "base.html" %}

{% block content %}
<h1 class="page-title">Dashboard</h1>

<div class="grid grid-4">
    <div class="card">
        <div class="card-header">
            <div class="card-title">System Status</div>
        </div>
        <div class="grid">
            <div>
                <div>Orchestrator</div>
                <div id="orchestrator-status" class="status status-info">
                    <span class="status-dot"></span>Loading...
                </div>
            </div>
            <div>
                <div>Scheduler</div>
                <div id="scheduler-status" class="status status-info">
                    <span class="status-dot"></span>Loading...
                </div>
            </div>
            <div>
                <div>Agents</div>
                <div id="agents-status" class="status status-info">
                    <span class="status-dot"></span>Loading...
                </div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <div class="card-title">Workflows</div>
        </div>
        <div id="workflows-summary">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <div class="card-title">Recent Executions</div>
        </div>
        <div id="executions-summary">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <div class="card-title">Agents Health</div>
        </div>
        <div id="agents-health">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
</div>

<div class="grid grid-2">
    <div class="card">
        <div class="card-header">
            <div class="card-title">Recent Activity</div>
            <button class="btn btn-secondary refresh-btn" data-type="activity">Refresh</button>
        </div>
        <div id="recent-activity">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <div class="card-title">System Metrics</div>
            <button class="btn btn-secondary refresh-btn" data-type="metrics">Refresh</button>
        </div>
        <div id="system-metrics">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
        
        dashboard_file = self.templates_dir / 'dashboard.html'
        async with aiofiles.open(dashboard_file, 'w') as f:
            await f.write(dashboard_template)
        
        # Create other page templates (simplified versions)
        pages = ['agents', 'workflows', 'schedules', 'triggers', 'reports', 'logs', 'settings']
        
        for page in pages:
            template_content = f"""
{{% extends "base.html" %}}

{{% block content %}}
<h1 class="page-title">{page.title()}</h1>

<div class="card">
    <div class="card-header">
        <div class="card-title">{page.title()} Management</div>
        <button class="btn btn-primary">Add New</button>
    </div>
    <div id="{page}-content">
        <div class="loading">
            <div class="spinner"></div>
        </div>
    </div>
</div>
{{% endblock %}}
"""
            
            page_file = self.templates_dir / f'{page}.html'
            async with aiofiles.open(page_file, 'w') as f:
                await f.write(template_content)
    
    def get_status(self) -> Dict[str, Any]:
        """Get dashboard status"""
        return {
            'running': self.is_running,
            'web_server': self.site is not None,
            'websocket_connections': len(self.websocket_handler.connections) if self.websocket_handler else 0,
            'components': {
                'api_routes': self.api_routes is not None,
                'websocket_handler': self.websocket_handler is not None
            }
        }