"""
AI-Powered Testing Agents

This package contains intelligent agents for orchestrating and automating testing workflows.
Each agent is responsible for specific aspects of the testing pipeline.
"""

from .base_agent import BaseAgent, AgentStatus, AgentConfig
from .test_runner_agent import TestRunnerAgent
from .notifier_agent import NotifierAgent
from .test_scheduler import TestScheduler

# Phase 5 - Business & Collaboration Features
try:
    from .trend_reporter_agent import TrendReporterAgent, TrendPeriod, TrendMetrics, BusinessInsight
    from .executive_summary_agent import ExecutiveSummaryAgent, SummaryType, StakeholderLevel, ExecutiveInsight
    PHASE5_AVAILABLE = True
except ImportError:
    PHASE5_AVAILABLE = False

__all__ = [
    'BaseAgent',
    'AgentStatus', 
    'AgentConfig',
    'TestRunnerAgent',
    'NotifierAgent',
    'TestScheduler'
]

# Add Phase 5 exports if available
if PHASE5_AVAILABLE:
    __all__.extend([
        'TrendReporterAgent',
        'TrendPeriod',
        'TrendMetrics',
        'BusinessInsight',
        'ExecutiveSummaryAgent',
        'SummaryType',
        'StakeholderLevel',
        'ExecutiveInsight'
    ])