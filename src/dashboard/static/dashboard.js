
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
