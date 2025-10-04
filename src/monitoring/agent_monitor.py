"""
Agent Monitor

Provides comprehensive monitoring and metrics collection for test automation agents.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import threading
import psutil
import json
from pathlib import Path


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_name: str
    
    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    
    # Timing metrics
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    
    # Recent execution times (for trend analysis)
    recent_execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    error_types: Dict[str, int] = field(default_factory=dict)
    
    # Resource usage
    cpu_usage_history: deque = field(default_factory=lambda: deque(maxlen=60))  # Last 60 measurements
    memory_usage_history: deque = field(default_factory=lambda: deque(maxlen=60))
    
    # Status tracking
    current_status: str = "idle"
    last_execution_start: Optional[datetime] = None
    last_execution_end: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)
    
    # Health metrics
    health_score: float = 100.0
    is_healthy: bool = True
    health_issues: List[str] = field(default_factory=list)
    
    def update_execution(self, execution_time: float, success: bool, error: Optional[str] = None):
        """Update execution metrics"""
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            if error:
                self.error_count += 1
                self.last_error = error
                self.last_error_time = datetime.now()
                
                # Track error types
                error_type = type(error).__name__ if isinstance(error, Exception) else str(error)
                self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # Update timing metrics
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.total_executions
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        
        # Add to recent times
        self.recent_execution_times.append(execution_time)
        
        # Update health score
        self._calculate_health_score()
    
    def update_resource_usage(self, cpu_percent: float, memory_mb: float):
        """Update resource usage metrics"""
        self.cpu_usage_history.append(cpu_percent)
        self.memory_usage_history.append(memory_mb)
    
    def _calculate_health_score(self):
        """Calculate agent health score based on various metrics"""
        score = 100.0
        issues = []
        
        # Success rate impact (0-40 points)
        if self.total_executions > 0:
            success_rate = self.successful_executions / self.total_executions
            if success_rate < 0.5:
                score -= 40
                issues.append("Low success rate")
            elif success_rate < 0.8:
                score -= 20
                issues.append("Moderate success rate")
            elif success_rate < 0.95:
                score -= 10
        
        # Error rate impact (0-30 points)
        if self.total_executions > 0:
            error_rate = self.error_count / self.total_executions
            if error_rate > 0.2:
                score -= 30
                issues.append("High error rate")
            elif error_rate > 0.1:
                score -= 15
                issues.append("Moderate error rate")
            elif error_rate > 0.05:
                score -= 5
        
        # Performance impact (0-20 points)
        if len(self.recent_execution_times) > 10:
            recent_avg = sum(self.recent_execution_times) / len(self.recent_execution_times)
            if recent_avg > self.average_execution_time * 2:
                score -= 20
                issues.append("Performance degradation")
            elif recent_avg > self.average_execution_time * 1.5:
                score -= 10
                issues.append("Slow performance")
        
        # Resource usage impact (0-10 points)
        if self.cpu_usage_history:
            avg_cpu = sum(self.cpu_usage_history) / len(self.cpu_usage_history)
            if avg_cpu > 90:
                score -= 10
                issues.append("High CPU usage")
            elif avg_cpu > 70:
                score -= 5
        
        self.health_score = max(0, score)
        self.is_healthy = self.health_score >= 70
        self.health_issues = issues
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    def get_error_rate(self) -> float:
        """Get error rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.error_count / self.total_executions) * 100
    
    def get_uptime(self) -> timedelta:
        """Get agent uptime"""
        return datetime.now() - self.uptime_start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'agent_name': self.agent_name,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'cancelled_executions': self.cancelled_executions,
            'success_rate': self.get_success_rate(),
            'error_rate': self.get_error_rate(),
            'total_execution_time': self.total_execution_time,
            'average_execution_time': self.average_execution_time,
            'min_execution_time': self.min_execution_time if self.min_execution_time != float('inf') else 0,
            'max_execution_time': self.max_execution_time,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'error_types': dict(self.error_types),
            'current_status': self.current_status,
            'last_execution_start': self.last_execution_start.isoformat() if self.last_execution_start else None,
            'last_execution_end': self.last_execution_end.isoformat() if self.last_execution_end else None,
            'uptime': str(self.get_uptime()),
            'health_score': self.health_score,
            'is_healthy': self.is_healthy,
            'health_issues': self.health_issues,
            'avg_cpu_usage': sum(self.cpu_usage_history) / len(self.cpu_usage_history) if self.cpu_usage_history else 0,
            'avg_memory_usage': sum(self.memory_usage_history) / len(self.memory_usage_history) if self.memory_usage_history else 0
        }


class AgentMonitor:
    """
    Comprehensive agent monitoring system.
    
    Tracks agent performance, health, and resource usage.
    """
    
    def __init__(self, 
                 metrics_file: str = "agent_metrics.json",
                 monitoring_interval: float = 30.0,
                 enable_resource_monitoring: bool = True):
        
        self.metrics_file = Path(metrics_file)
        self.monitoring_interval = monitoring_interval
        self.enable_resource_monitoring = enable_resource_monitoring
        
        # Metrics storage
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Load existing metrics
        self._load_metrics()
        
        # Start monitoring
        self.start_monitoring()
    
    def register_agent(self, agent_name: str) -> AgentMetrics:
        """Register a new agent for monitoring"""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
            self.logger.info(f"Registered agent for monitoring: {agent_name}")
            
            # Trigger callback
            self._trigger_event('agent_registered', {
                'agent_name': agent_name,
                'timestamp': datetime.now().isoformat()
            })
        
        return self.agent_metrics[agent_name]
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent from monitoring"""
        if agent_name in self.agent_metrics:
            del self.agent_metrics[agent_name]
            self.logger.info(f"Unregistered agent from monitoring: {agent_name}")
            
            # Trigger callback
            self._trigger_event('agent_unregistered', {
                'agent_name': agent_name,
                'timestamp': datetime.now().isoformat()
            })
    
    def record_execution_start(self, agent_name: str):
        """Record the start of an agent execution"""
        metrics = self.register_agent(agent_name)
        metrics.current_status = "running"
        metrics.last_execution_start = datetime.now()
        
        self.logger.debug(f"Agent {agent_name} execution started")
        
        # Trigger callback
        self._trigger_event('execution_started', {
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_execution_end(self, agent_name: str, success: bool, 
                           execution_time: Optional[float] = None,
                           error: Optional[str] = None):
        """Record the end of an agent execution"""
        metrics = self.register_agent(agent_name)
        
        end_time = datetime.now()
        metrics.last_execution_end = end_time
        metrics.current_status = "idle"
        
        # Calculate execution time if not provided
        if execution_time is None and metrics.last_execution_start:
            execution_time = (end_time - metrics.last_execution_start).total_seconds()
        
        if execution_time is not None:
            metrics.update_execution(execution_time, success, error)
        
        self.logger.debug(f"Agent {agent_name} execution ended: success={success}, time={execution_time}")
        
        # Trigger callback
        self._trigger_event('execution_ended', {
            'agent_name': agent_name,
            'success': success,
            'execution_time': execution_time,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check for health issues
        if not metrics.is_healthy:
            self._trigger_event('agent_unhealthy', {
                'agent_name': agent_name,
                'health_score': metrics.health_score,
                'health_issues': metrics.health_issues,
                'timestamp': datetime.now().isoformat()
            })
    
    def record_error(self, agent_name: str, error: str):
        """Record an error for an agent"""
        metrics = self.register_agent(agent_name)
        metrics.error_count += 1
        metrics.last_error = error
        metrics.last_error_time = datetime.now()
        
        # Track error type
        error_type = type(error).__name__ if isinstance(error, Exception) else "Unknown"
        metrics.error_types[error_type] = metrics.error_types.get(error_type, 0) + 1
        
        self.logger.warning(f"Agent {agent_name} error recorded: {error}")
        
        # Trigger callback
        self._trigger_event('agent_error', {
            'agent_name': agent_name,
            'error': error,
            'error_type': error_type,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_agent_status(self, agent_name: str, status: str):
        """Update agent status"""
        metrics = self.register_agent(agent_name)
        old_status = metrics.current_status
        metrics.current_status = status
        
        if old_status != status:
            self.logger.debug(f"Agent {agent_name} status changed: {old_status} -> {status}")
            
            # Trigger callback
            self._trigger_event('status_changed', {
                'agent_name': agent_name,
                'old_status': old_status,
                'new_status': status,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_agent_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent"""
        return self.agent_metrics.get(agent_name)
    
    def get_all_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents"""
        return self.agent_metrics.copy()
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system-wide monitoring summary"""
        total_agents = len(self.agent_metrics)
        healthy_agents = sum(1 for m in self.agent_metrics.values() if m.is_healthy)
        total_executions = sum(m.total_executions for m in self.agent_metrics.values())
        total_errors = sum(m.error_count for m in self.agent_metrics.values())
        
        avg_health_score = (sum(m.health_score for m in self.agent_metrics.values()) / 
                           total_agents if total_agents > 0 else 0)
        
        return {
            'total_agents': total_agents,
            'healthy_agents': healthy_agents,
            'unhealthy_agents': total_agents - healthy_agents,
            'total_executions': total_executions,
            'total_errors': total_errors,
            'average_health_score': avg_health_score,
            'system_health': 'healthy' if healthy_agents == total_agents else 'degraded',
            'monitoring_active': self.is_monitoring,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_top_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents"""
        agents = [(name, metrics) for name, metrics in self.agent_metrics.items()]
        agents.sort(key=lambda x: x[1].health_score, reverse=True)
        
        return [
            {
                'agent_name': name,
                'health_score': metrics.health_score,
                'success_rate': metrics.get_success_rate(),
                'total_executions': metrics.total_executions
            }
            for name, metrics in agents[:limit]
        ]
    
    def get_problematic_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get agents with issues"""
        agents = [(name, metrics) for name, metrics in self.agent_metrics.items() 
                 if not metrics.is_healthy]
        agents.sort(key=lambda x: x[1].health_score)
        
        return [
            {
                'agent_name': name,
                'health_score': metrics.health_score,
                'health_issues': metrics.health_issues,
                'error_rate': metrics.get_error_rate(),
                'last_error': metrics.last_error
            }
            for name, metrics in agents[:limit]
        ]
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Agent monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            self.logger.info("Agent monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update resource usage for all agents
                if self.enable_resource_monitoring:
                    self._update_resource_usage()
                
                # Save metrics periodically
                self._save_metrics()
                
                # Sleep until next monitoring cycle
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short sleep on error
    
    def _update_resource_usage(self):
        """Update resource usage for all agents"""
        try:
            # Get system-wide metrics (simplified approach)
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            # Update all agents (in real implementation, you'd track per-agent usage)
            for metrics in self.agent_metrics.values():
                if metrics.current_status == "running":
                    # Simulate per-agent resource usage
                    agent_cpu = cpu_percent / len(self.agent_metrics)
                    agent_memory = memory_mb / len(self.agent_metrics)
                    metrics.update_resource_usage(agent_cpu, agent_memory)
                
        except Exception as e:
            self.logger.error(f"Error updating resource usage: {e}")
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'agents': {name: metrics.to_dict() for name, metrics in self.agent_metrics.items()}
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                
                # Restore agent metrics (simplified - would need full restoration)
                for agent_name, agent_data in data.get('agents', {}).items():
                    metrics = AgentMetrics(agent_name=agent_name)
                    
                    # Restore basic metrics
                    metrics.total_executions = agent_data.get('total_executions', 0)
                    metrics.successful_executions = agent_data.get('successful_executions', 0)
                    metrics.failed_executions = agent_data.get('failed_executions', 0)
                    metrics.error_count = agent_data.get('error_count', 0)
                    metrics.total_execution_time = agent_data.get('total_execution_time', 0.0)
                    metrics.average_execution_time = agent_data.get('average_execution_time', 0.0)
                    
                    self.agent_metrics[agent_name] = metrics
                
                self.logger.info(f"Loaded metrics for {len(self.agent_metrics)} agents")
                
        except Exception as e:
            self.logger.error(f"Error loading metrics: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def _trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger event callbacks"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(event_type, event_data)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event_type}: {e}")
    
    def reset_metrics(self, agent_name: Optional[str] = None):
        """Reset metrics for specific agent or all agents"""
        if agent_name:
            if agent_name in self.agent_metrics:
                self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
                self.logger.info(f"Reset metrics for agent: {agent_name}")
        else:
            for name in self.agent_metrics:
                self.agent_metrics[name] = AgentMetrics(agent_name=name)
            self.logger.info("Reset metrics for all agents")
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if format.lower() == 'json':
            return json.dumps({
                'export_timestamp': datetime.now().isoformat(),
                'system_summary': self.get_system_summary(),
                'agents': {name: metrics.to_dict() for name, metrics in self.agent_metrics.items()}
            }, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup(self):
        """Cleanup monitoring resources"""
        self.stop_monitoring()
        self._save_metrics()
        self.logger.info("Agent monitoring cleanup completed")