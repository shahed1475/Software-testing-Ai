"""
Orchestration Dashboard Package

Web-based dashboard for managing and monitoring the test automation system.
Provides interfaces for:
- Agent management and monitoring
- Workflow creation and execution
- Test scheduling and triggers
- Report viewing and analysis
- System health and metrics
"""

from .dashboard_app import DashboardApp
from .api_routes import APIRoutes
from .websocket_handler import WebSocketHandler

__all__ = [
    'DashboardApp',
    'APIRoutes', 
    'WebSocketHandler'
]