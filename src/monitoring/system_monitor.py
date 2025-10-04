"""
System Monitor

Provides comprehensive system-level monitoring for the test automation framework.
"""

import asyncio
import logging
import platform
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import json
import psutil
import socket


@dataclass
class SystemMetrics:
    """System-level metrics"""
    
    # System information
    hostname: str = field(default_factory=lambda: socket.gethostname())
    platform: str = field(default_factory=lambda: platform.platform())
    python_version: str = field(default_factory=lambda: platform.python_version())
    
    # CPU metrics
    cpu_count: int = field(default_factory=psutil.cpu_count)
    cpu_usage_percent: float = 0.0
    cpu_usage_history: deque = field(default_factory=lambda: deque(maxlen=300))  # 5 minutes at 1s intervals
    cpu_load_average: List[float] = field(default_factory=list)
    
    # Memory metrics
    total_memory_gb: float = 0.0
    available_memory_gb: float = 0.0
    used_memory_gb: float = 0.0
    memory_usage_percent: float = 0.0
    memory_usage_history: deque = field(default_factory=lambda: deque(maxlen=300))
    
    # Disk metrics
    disk_usage: Dict[str, Dict[str, float]] = field(default_factory=dict)
    disk_io_counters: Dict[str, Any] = field(default_factory=dict)
    
    # Network metrics
    network_io_counters: Dict[str, Any] = field(default_factory=dict)
    network_connections: int = 0
    
    # Process metrics
    total_processes: int = 0
    running_processes: int = 0
    framework_processes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    boot_time: datetime = field(default_factory=lambda: datetime.fromtimestamp(psutil.boot_time()))
    uptime: timedelta = field(default_factory=timedelta)
    
    # Health indicators
    health_score: float = 100.0
    health_status: str = "healthy"
    health_issues: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_cpu_metrics(self):
        """Update CPU-related metrics"""
        try:
            self.cpu_usage_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_history.append(self.cpu_usage_percent)
            
            # Get load average (Unix-like systems)
            try:
                self.cpu_load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                self.cpu_load_average = [self.cpu_usage_percent / 100.0] * 3
                
        except Exception as e:
            logging.error(f"Error updating CPU metrics: {e}")
    
    def update_memory_metrics(self):
        """Update memory-related metrics"""
        try:
            memory = psutil.virtual_memory()
            
            self.total_memory_gb = memory.total / (1024**3)
            self.available_memory_gb = memory.available / (1024**3)
            self.used_memory_gb = memory.used / (1024**3)
            self.memory_usage_percent = memory.percent
            
            self.memory_usage_history.append(self.memory_usage_percent)
            
        except Exception as e:
            logging.error(f"Error updating memory metrics: {e}")
    
    def update_disk_metrics(self):
        """Update disk-related metrics"""
        try:
            self.disk_usage.clear()
            
            # Get disk usage for all mounted disks
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.disk_usage[partition.device] = {
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'usage_percent': (usage.used / usage.total) * 100,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype
                    }
                except (PermissionError, OSError):
                    # Skip inaccessible partitions
                    continue
            
            # Get disk I/O counters
            try:
                self.disk_io_counters = psutil.disk_io_counters(perdisk=True)
            except Exception:
                self.disk_io_counters = {}
                
        except Exception as e:
            logging.error(f"Error updating disk metrics: {e}")
    
    def update_network_metrics(self):
        """Update network-related metrics"""
        try:
            # Network I/O counters
            self.network_io_counters = psutil.net_io_counters(pernic=True)
            
            # Network connections
            self.network_connections = len(psutil.net_connections())
            
        except Exception as e:
            logging.error(f"Error updating network metrics: {e}")
    
    def update_process_metrics(self):
        """Update process-related metrics"""
        try:
            processes = list(psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']))
            
            self.total_processes = len(processes)
            self.running_processes = sum(1 for p in processes if p.info['status'] == 'running')
            
            # Find framework-related processes
            self.framework_processes.clear()
            framework_keywords = ['python', 'pytest', 'selenium', 'docker', 'test']
            
            for process in processes:
                try:
                    name = process.info['name'].lower()
                    if any(keyword in name for keyword in framework_keywords):
                        self.framework_processes.append({
                            'pid': process.info['pid'],
                            'name': process.info['name'],
                            'status': process.info['status'],
                            'cpu_percent': process.info['cpu_percent'],
                            'memory_percent': process.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logging.error(f"Error updating process metrics: {e}")
    
    def update_health_metrics(self):
        """Update system health indicators"""
        try:
            score = 100.0
            issues = []
            alerts = []
            
            # CPU health check
            if self.cpu_usage_percent > 90:
                score -= 30
                issues.append("High CPU usage")
                alerts.append({
                    'type': 'cpu_high',
                    'message': f'CPU usage is {self.cpu_usage_percent:.1f}%',
                    'severity': 'critical',
                    'timestamp': datetime.now().isoformat()
                })
            elif self.cpu_usage_percent > 70:
                score -= 15
                issues.append("Moderate CPU usage")
                alerts.append({
                    'type': 'cpu_moderate',
                    'message': f'CPU usage is {self.cpu_usage_percent:.1f}%',
                    'severity': 'warning',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory health check
            if self.memory_usage_percent > 90:
                score -= 25
                issues.append("High memory usage")
                alerts.append({
                    'type': 'memory_high',
                    'message': f'Memory usage is {self.memory_usage_percent:.1f}%',
                    'severity': 'critical',
                    'timestamp': datetime.now().isoformat()
                })
            elif self.memory_usage_percent > 75:
                score -= 10
                issues.append("Moderate memory usage")
                alerts.append({
                    'type': 'memory_moderate',
                    'message': f'Memory usage is {self.memory_usage_percent:.1f}%',
                    'severity': 'warning',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk health check
            for device, usage in self.disk_usage.items():
                if usage['usage_percent'] > 95:
                    score -= 20
                    issues.append(f"Disk {device} almost full")
                    alerts.append({
                        'type': 'disk_full',
                        'message': f'Disk {device} is {usage["usage_percent"]:.1f}% full',
                        'severity': 'critical',
                        'timestamp': datetime.now().isoformat()
                    })
                elif usage['usage_percent'] > 85:
                    score -= 5
                    issues.append(f"Disk {device} running low")
                    alerts.append({
                        'type': 'disk_low',
                        'message': f'Disk {device} is {usage["usage_percent"]:.1f}% full',
                        'severity': 'warning',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Update health status
            self.health_score = max(0, score)
            self.health_issues = issues
            self.alerts = alerts
            
            if self.health_score >= 80:
                self.health_status = "healthy"
            elif self.health_score >= 60:
                self.health_status = "degraded"
            else:
                self.health_status = "critical"
                
        except Exception as e:
            logging.error(f"Error updating health metrics: {e}")
    
    def update_all_metrics(self):
        """Update all system metrics"""
        self.update_cpu_metrics()
        self.update_memory_metrics()
        self.update_disk_metrics()
        self.update_network_metrics()
        self.update_process_metrics()
        self.update_health_metrics()
        
        # Update uptime
        self.uptime = datetime.now() - self.boot_time
        self.last_updated = datetime.now()
    
    def get_cpu_trend(self, minutes: int = 5) -> Dict[str, float]:
        """Get CPU usage trend over specified minutes"""
        if not self.cpu_usage_history:
            return {'trend': 0.0, 'average': 0.0, 'min': 0.0, 'max': 0.0}
        
        # Get recent data (assuming 1-second intervals)
        recent_data = list(self.cpu_usage_history)[-minutes * 60:]
        
        if len(recent_data) < 2:
            return {'trend': 0.0, 'average': recent_data[0] if recent_data else 0.0, 'min': 0.0, 'max': 0.0}
        
        # Calculate trend (simple linear regression slope)
        n = len(recent_data)
        x_sum = sum(range(n))
        y_sum = sum(recent_data)
        xy_sum = sum(i * y for i, y in enumerate(recent_data))
        x2_sum = sum(i * i for i in range(n))
        
        trend = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0
        
        return {
            'trend': trend,
            'average': sum(recent_data) / len(recent_data),
            'min': min(recent_data),
            'max': max(recent_data)
        }
    
    def get_memory_trend(self, minutes: int = 5) -> Dict[str, float]:
        """Get memory usage trend over specified minutes"""
        if not self.memory_usage_history:
            return {'trend': 0.0, 'average': 0.0, 'min': 0.0, 'max': 0.0}
        
        recent_data = list(self.memory_usage_history)[-minutes * 60:]
        
        if len(recent_data) < 2:
            return {'trend': 0.0, 'average': recent_data[0] if recent_data else 0.0, 'min': 0.0, 'max': 0.0}
        
        # Calculate trend
        n = len(recent_data)
        x_sum = sum(range(n))
        y_sum = sum(recent_data)
        xy_sum = sum(i * y for i, y in enumerate(recent_data))
        x2_sum = sum(i * i for i in range(n))
        
        trend = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0
        
        return {
            'trend': trend,
            'average': sum(recent_data) / len(recent_data),
            'min': min(recent_data),
            'max': max(recent_data)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'hostname': self.hostname,
            'platform': self.platform,
            'python_version': self.python_version,
            'cpu_count': self.cpu_count,
            'cpu_usage_percent': self.cpu_usage_percent,
            'cpu_load_average': self.cpu_load_average,
            'total_memory_gb': self.total_memory_gb,
            'available_memory_gb': self.available_memory_gb,
            'used_memory_gb': self.used_memory_gb,
            'memory_usage_percent': self.memory_usage_percent,
            'disk_usage': self.disk_usage,
            'network_connections': self.network_connections,
            'total_processes': self.total_processes,
            'running_processes': self.running_processes,
            'framework_processes_count': len(self.framework_processes),
            'boot_time': self.boot_time.isoformat(),
            'uptime_seconds': self.uptime.total_seconds(),
            'health_score': self.health_score,
            'health_status': self.health_status,
            'health_issues': self.health_issues,
            'alerts_count': len(self.alerts),
            'last_updated': self.last_updated.isoformat(),
            'cpu_trend': self.get_cpu_trend(),
            'memory_trend': self.get_memory_trend()
        }


class SystemMonitor:
    """
    Comprehensive system monitoring for the test automation framework.
    
    Monitors system resources, health, and performance.
    """
    
    def __init__(self, 
                 monitoring_interval: float = 5.0,
                 metrics_file: str = "system_metrics.json",
                 enable_alerts: bool = True,
                 alert_thresholds: Optional[Dict[str, float]] = None):
        
        self.monitoring_interval = monitoring_interval
        self.metrics_file = Path(metrics_file)
        self.enable_alerts = enable_alerts
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0
        }
        
        # System metrics
        self.metrics = SystemMetrics()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Alert history
        self.alert_history: deque = deque(maxlen=1000)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.monitoring_stats = {
            'updates_count': 0,
            'errors_count': 0,
            'last_update_duration': 0.0,
            'average_update_duration': 0.0
        }
    
    def start_monitoring(self):
        """Start system monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("System monitoring started")
            
            # Trigger callback
            self._trigger_event('monitoring_started', {
                'timestamp': datetime.now().isoformat(),
                'interval': self.monitoring_interval
            })
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=10)
            self.logger.info("System monitoring stopped")
            
            # Save final metrics
            self._save_metrics()
            
            # Trigger callback
            self._trigger_event('monitoring_stopped', {
                'timestamp': datetime.now().isoformat()
            })
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # Update all metrics
                self.metrics.update_all_metrics()
                
                # Check for alerts
                if self.enable_alerts:
                    self._check_alerts()
                
                # Save metrics periodically
                if self.monitoring_stats['updates_count'] % 12 == 0:  # Every minute at 5s intervals
                    self._save_metrics()
                
                # Update monitoring stats
                update_duration = time.time() - start_time
                self.monitoring_stats['updates_count'] += 1
                self.monitoring_stats['last_update_duration'] = update_duration
                
                # Calculate average duration
                total_duration = (self.monitoring_stats['average_update_duration'] * 
                                (self.monitoring_stats['updates_count'] - 1) + update_duration)
                self.monitoring_stats['average_update_duration'] = total_duration / self.monitoring_stats['updates_count']
                
                # Trigger update event
                self._trigger_event('metrics_updated', {
                    'timestamp': datetime.now().isoformat(),
                    'health_score': self.metrics.health_score,
                    'health_status': self.metrics.health_status
                })
                
                # Sleep until next update
                time.sleep(max(0, self.monitoring_interval - update_duration))
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                self.monitoring_stats['errors_count'] += 1
                time.sleep(5)  # Short sleep on error
    
    def _check_alerts(self):
        """Check for system alerts"""
        try:
            current_alerts = []
            
            # CPU alerts
            if self.metrics.cpu_usage_percent >= self.alert_thresholds['cpu_critical']:
                alert = self._create_alert('cpu_critical', 
                                         f'Critical CPU usage: {self.metrics.cpu_usage_percent:.1f}%')
                current_alerts.append(alert)
            elif self.metrics.cpu_usage_percent >= self.alert_thresholds['cpu_warning']:
                alert = self._create_alert('cpu_warning', 
                                         f'High CPU usage: {self.metrics.cpu_usage_percent:.1f}%')
                current_alerts.append(alert)
            
            # Memory alerts
            if self.metrics.memory_usage_percent >= self.alert_thresholds['memory_critical']:
                alert = self._create_alert('memory_critical', 
                                         f'Critical memory usage: {self.metrics.memory_usage_percent:.1f}%')
                current_alerts.append(alert)
            elif self.metrics.memory_usage_percent >= self.alert_thresholds['memory_warning']:
                alert = self._create_alert('memory_warning', 
                                         f'High memory usage: {self.metrics.memory_usage_percent:.1f}%')
                current_alerts.append(alert)
            
            # Disk alerts
            for device, usage in self.metrics.disk_usage.items():
                if usage['usage_percent'] >= self.alert_thresholds['disk_critical']:
                    alert = self._create_alert('disk_critical', 
                                             f'Critical disk usage on {device}: {usage["usage_percent"]:.1f}%')
                    current_alerts.append(alert)
                elif usage['usage_percent'] >= self.alert_thresholds['disk_warning']:
                    alert = self._create_alert('disk_warning', 
                                             f'High disk usage on {device}: {usage["usage_percent"]:.1f}%')
                    current_alerts.append(alert)
            
            # Process new alerts
            for alert in current_alerts:
                self._process_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, alert_type: str, message: str) -> Dict[str, Any]:
        """Create alert dictionary"""
        severity = 'critical' if 'critical' in alert_type else 'warning'
        
        return {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'hostname': self.metrics.hostname
        }
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process and store alert"""
        # Add to history
        self.alert_history.append(alert)
        
        # Log alert
        if alert['severity'] == 'critical':
            self.logger.critical(f"System Alert: {alert['message']}")
        else:
            self.logger.warning(f"System Alert: {alert['message']}")
        
        # Trigger callback
        self._trigger_event('alert_triggered', alert)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return self.metrics
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get current metrics as dictionary"""
        return self.metrics.to_dict()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        return {
            'health_score': self.metrics.health_score,
            'health_status': self.metrics.health_status,
            'health_issues': self.metrics.health_issues,
            'active_alerts': len(self.metrics.alerts),
            'cpu_usage': self.metrics.cpu_usage_percent,
            'memory_usage': self.metrics.memory_usage_percent,
            'disk_usage_max': max((usage['usage_percent'] for usage in self.metrics.disk_usage.values()), default=0),
            'uptime_hours': self.metrics.uptime.total_seconds() / 3600,
            'last_updated': self.metrics.last_updated.isoformat()
        }
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        return {
            'cpu': {
                'usage_percent': self.metrics.cpu_usage_percent,
                'count': self.metrics.cpu_count,
                'load_average': self.metrics.cpu_load_average,
                'trend': self.metrics.get_cpu_trend()
            },
            'memory': {
                'total_gb': self.metrics.total_memory_gb,
                'used_gb': self.metrics.used_memory_gb,
                'available_gb': self.metrics.available_memory_gb,
                'usage_percent': self.metrics.memory_usage_percent,
                'trend': self.metrics.get_memory_trend()
            },
            'disk': self.metrics.disk_usage,
            'network': {
                'connections': self.metrics.network_connections,
                'interfaces': len(self.metrics.network_io_counters)
            },
            'processes': {
                'total': self.metrics.total_processes,
                'running': self.metrics.running_processes,
                'framework_related': len(self.metrics.framework_processes)
            }
        }
    
    def get_alerts(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        alerts = list(self.alert_history)
        
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]
        
        return alerts[-limit:] if limit else alerts
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'is_monitoring': self.is_monitoring,
            'monitoring_interval': self.monitoring_interval,
            'updates_count': self.monitoring_stats['updates_count'],
            'errors_count': self.monitoring_stats['errors_count'],
            'last_update_duration': self.monitoring_stats['last_update_duration'],
            'average_update_duration': self.monitoring_stats['average_update_duration'],
            'alert_thresholds': self.alert_thresholds,
            'total_alerts': len(self.alert_history)
        }
    
    def update_alert_thresholds(self, thresholds: Dict[str, float]):
        """Update alert thresholds"""
        self.alert_thresholds.update(thresholds)
        self.logger.info(f"Updated alert thresholds: {thresholds}")
        
        # Trigger callback
        self._trigger_event('thresholds_updated', {
            'thresholds': self.alert_thresholds,
            'timestamp': datetime.now().isoformat()
        })
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': self.metrics.to_dict(),
                'monitoring_stats': self.get_monitoring_stats(),
                'recent_alerts': list(self.alert_history)[-100:]  # Last 100 alerts
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving system metrics: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
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
    
    def force_update(self):
        """Force immediate metrics update"""
        try:
            self.metrics.update_all_metrics()
            self.logger.debug("Forced system metrics update")
            
            # Trigger callback
            self._trigger_event('metrics_updated', {
                'timestamp': datetime.now().isoformat(),
                'forced': True
            })
            
        except Exception as e:
            self.logger.error(f"Error in forced update: {e}")
    
    def reset_alerts(self):
        """Clear alert history"""
        self.alert_history.clear()
        self.logger.info("Alert history cleared")
        
        # Trigger callback
        self._trigger_event('alerts_cleared', {
            'timestamp': datetime.now().isoformat()
        })
    
    def export_metrics(self, format: str = 'json', include_history: bool = False) -> str:
        """Export system metrics"""
        if format.lower() == 'json':
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_info': {
                    'hostname': self.metrics.hostname,
                    'platform': self.metrics.platform,
                    'python_version': self.metrics.python_version
                },
                'current_metrics': self.metrics.to_dict(),
                'health_summary': self.get_health_summary(),
                'resource_summary': self.get_resource_summary(),
                'monitoring_stats': self.get_monitoring_stats()
            }
            
            if include_history:
                data['cpu_history'] = list(self.metrics.cpu_usage_history)
                data['memory_history'] = list(self.metrics.memory_usage_history)
                data['alert_history'] = list(self.alert_history)
            
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup(self):
        """Cleanup monitoring resources"""
        self.stop_monitoring()
        self.logger.info("System monitoring cleanup completed")