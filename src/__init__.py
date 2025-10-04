"""
Test Automation Orchestrator Package

A comprehensive test automation system with intelligent orchestration,
scheduling, monitoring, and reporting capabilities.
"""

__version__ = "1.0.0"
__author__ = "Test Automation Team"
__description__ = "Intelligent Test Automation Orchestrator"

# Core components
from .agents.test_orchestrator import TestOrchestrator
from .agents.test_scheduler import TestScheduler
from .agents.trigger_system import TriggerSystem
from .dashboard.dashboard_app import DashboardApp

# Configuration
from .config.settings_manager import get_settings, get_settings_manager
from .config.environment_manager import EnvironmentManager
from .config.config_manager import ConfigManager

# Monitoring
from .monitoring.agent_monitor import AgentMonitor
from .monitoring.system_monitor import SystemMonitor
from .monitoring.metrics_collector import MetricsCollector
from .monitoring.logger_config import setup_logging

__all__ = [
    "TestOrchestrator",
    "TestScheduler", 
    "TriggerSystem",
    "DashboardApp",
    "get_settings",
    "get_settings_manager",
    "EnvironmentManager",
    "ConfigManager",
    "AgentMonitor",
    "SystemMonitor",
    "MetricsCollector",
    "setup_logging"
]