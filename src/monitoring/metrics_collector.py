"""
Metrics Collector

Comprehensive metrics collection and storage system for the test automation framework.
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
import statistics


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"           # Monotonically increasing value
    GAUGE = "gauge"              # Current value that can go up or down
    HISTOGRAM = "histogram"       # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Rate of events per time unit


@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricPoint':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            value=data['value'],
            metric_type=MetricType(data['type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            tags=data.get('tags', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class MetricSeries:
    """Time series of metric points"""
    name: str
    metric_type: MetricType
    points: List[MetricPoint] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=7))
    
    def add_point(self, value: Union[int, float], timestamp: Optional[datetime] = None, 
                  tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a new data point"""
        point = MetricPoint(
            name=self.name,
            value=value,
            metric_type=self.metric_type,
            timestamp=timestamp or datetime.now(),
            tags={**self.tags, **(tags or {})},
            metadata=metadata or {}
        )
        self.points.append(point)
        self._cleanup_old_points()
    
    def _cleanup_old_points(self):
        """Remove points older than retention period"""
        cutoff = datetime.now() - self.retention_period
        self.points = [p for p in self.points if p.timestamp > cutoff]
    
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the latest point"""
        return self.points[-1] if self.points else None
    
    def get_range(self, start: datetime, end: datetime) -> List[MetricPoint]:
        """Get points within time range"""
        return [p for p in self.points if start <= p.timestamp <= end]
    
    def get_statistics(self, window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get statistical summary of the series"""
        if not self.points:
            return {}
        
        # Filter by time window if specified
        if window:
            cutoff = datetime.now() - window
            values = [p.value for p in self.points if p.timestamp > cutoff]
        else:
            values = [p.value for p in self.points]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'sum': sum(values),
            'latest': values[-1]
        }
    
    def get_rate(self, window: timedelta = timedelta(minutes=1)) -> float:
        """Calculate rate of change over time window"""
        cutoff = datetime.now() - window
        recent_points = [p for p in self.points if p.timestamp > cutoff]
        
        if len(recent_points) < 2:
            return 0.0
        
        # For counters, calculate rate as difference over time
        if self.metric_type == MetricType.COUNTER:
            first_point = recent_points[0]
            last_point = recent_points[-1]
            time_diff = (last_point.timestamp - first_point.timestamp).total_seconds()
            
            if time_diff > 0:
                return (last_point.value - first_point.value) / time_diff
        
        # For other types, calculate average rate
        elif self.metric_type in [MetricType.GAUGE, MetricType.TIMER]:
            return len(recent_points) / window.total_seconds()
        
        return 0.0


class MetricsCollector:
    """
    Comprehensive metrics collection and storage system.
    
    Collects metrics from agents, system monitoring, and custom sources.
    """
    
    def __init__(self, 
                 storage_path: str = "metrics.db",
                 retention_days: int = 30,
                 collection_interval: float = 5.0,
                 enable_persistence: bool = True,
                 max_memory_points: int = 10000):
        
        self.storage_path = Path(storage_path)
        self.retention_days = retention_days
        self.collection_interval = collection_interval
        self.enable_persistence = enable_persistence
        self.max_memory_points = max_memory_points
        
        # In-memory storage
        self.series: Dict[str, MetricSeries] = {}
        self.series_lock = threading.RLock()
        
        # Collection state
        self.is_collecting = False
        self.collection_thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Collection sources
        self.collection_sources: Dict[str, Callable] = {}
        
        # Aggregation rules
        self.aggregation_rules: Dict[str, Dict[str, Any]] = {}
        
        # Alert rules
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.collection_stats = {
            'points_collected': 0,
            'points_persisted': 0,
            'collection_errors': 0,
            'last_collection_time': None,
            'collection_duration_avg': 0.0
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize database if persistence is enabled
        if self.enable_persistence:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metric persistence"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        tags TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp 
                    ON metrics(name, timestamp)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                    ON metrics(timestamp)
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS metric_aggregates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        period TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        count INTEGER,
                        min_value REAL,
                        max_value REAL,
                        avg_value REAL,
                        sum_value REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_aggregates_name_period 
                    ON metric_aggregates(name, period, start_time)
                ''')
                
                self.logger.info("Metrics database initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing metrics database: {e}")
    
    def start_collection(self):
        """Start metrics collection"""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            self.logger.info("Metrics collection started")
            
            # Trigger callback
            self._trigger_event('collection_started', {
                'timestamp': datetime.now().isoformat(),
                'interval': self.collection_interval
            })
    
    def stop_collection(self):
        """Stop metrics collection"""
        if self.is_collecting:
            self.is_collecting = False
            if self.collection_thread:
                self.collection_thread.join(timeout=10)
            
            # Persist remaining metrics
            if self.enable_persistence:
                self._persist_all_metrics()
            
            self.logger.info("Metrics collection stopped")
            
            # Trigger callback
            self._trigger_event('collection_stopped', {
                'timestamp': datetime.now().isoformat()
            })
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                start_time = time.time()
                
                # Collect from all registered sources
                self._collect_from_sources()
                
                # Process aggregation rules
                self._process_aggregations()
                
                # Check alert rules
                self._check_alerts()
                
                # Persist metrics periodically
                if self.enable_persistence and self.collection_stats['points_collected'] % 100 == 0:
                    self._persist_all_metrics()
                
                # Update collection stats
                collection_duration = time.time() - start_time
                self.collection_stats['last_collection_time'] = datetime.now()
                
                # Update average duration
                if self.collection_stats['collection_duration_avg'] == 0:
                    self.collection_stats['collection_duration_avg'] = collection_duration
                else:
                    self.collection_stats['collection_duration_avg'] = (
                        self.collection_stats['collection_duration_avg'] * 0.9 + 
                        collection_duration * 0.1
                    )
                
                # Sleep until next collection
                time.sleep(max(0, self.collection_interval - collection_duration))
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                self.collection_stats['collection_errors'] += 1
                time.sleep(5)  # Short sleep on error
    
    def _collect_from_sources(self):
        """Collect metrics from all registered sources"""
        for source_name, source_func in self.collection_sources.items():
            try:
                metrics = source_func()
                if isinstance(metrics, dict):
                    for name, value in metrics.items():
                        self.record_gauge(f"{source_name}.{name}", value)
                elif isinstance(metrics, list):
                    for metric in metrics:
                        if isinstance(metric, MetricPoint):
                            self.record_metric_point(metric)
                        elif isinstance(metric, dict):
                            self.record_metric(**metric)
                            
            except Exception as e:
                self.logger.error(f"Error collecting from source {source_name}: {e}")
    
    def record_metric(self, name: str, value: Union[int, float], metric_type: MetricType,
                     tags: Optional[Dict[str, str]] = None, 
                     metadata: Optional[Dict[str, Any]] = None,
                     timestamp: Optional[datetime] = None):
        """Record a metric point"""
        with self.series_lock:
            # Get or create series
            if name not in self.series:
                self.series[name] = MetricSeries(
                    name=name,
                    metric_type=metric_type,
                    retention_period=timedelta(days=self.retention_days)
                )
            
            # Add point to series
            self.series[name].add_point(
                value=value,
                timestamp=timestamp,
                tags=tags,
                metadata=metadata
            )
            
            # Update stats
            self.collection_stats['points_collected'] += 1
            
            # Trigger callback
            self._trigger_event('metric_recorded', {
                'name': name,
                'value': value,
                'type': metric_type.value,
                'timestamp': (timestamp or datetime.now()).isoformat()
            })
    
    def record_metric_point(self, point: MetricPoint):
        """Record a metric point object"""
        self.record_metric(
            name=point.name,
            value=point.value,
            metric_type=point.metric_type,
            tags=point.tags,
            metadata=point.metadata,
            timestamp=point.timestamp
        )
    
    def record_counter(self, name: str, value: Union[int, float] = 1, 
                      tags: Optional[Dict[str, str]] = None):
        """Record a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def record_gauge(self, name: str, value: Union[int, float], 
                    tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_timer(self, name: str, duration: float, 
                    tags: Optional[Dict[str, str]] = None):
        """Record a timer metric (duration in seconds)"""
        self.record_metric(name, duration, MetricType.TIMER, tags)
    
    def record_histogram(self, name: str, value: Union[int, float], 
                        tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def increment_counter(self, name: str, increment: Union[int, float] = 1,
                         tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self.series_lock:
            if name in self.series and self.series[name].metric_type == MetricType.COUNTER:
                latest = self.series[name].get_latest()
                if latest:
                    new_value = latest.value + increment
                else:
                    new_value = increment
            else:
                new_value = increment
            
            self.record_counter(name, new_value, tags)
    
    def get_series(self, name: str) -> Optional[MetricSeries]:
        """Get metric series by name"""
        with self.series_lock:
            return self.series.get(name)
    
    def get_latest_value(self, name: str) -> Optional[Union[int, float]]:
        """Get latest value for a metric"""
        series = self.get_series(name)
        if series:
            latest = series.get_latest()
            return latest.value if latest else None
        return None
    
    def get_statistics(self, name: str, window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get statistics for a metric series"""
        series = self.get_series(name)
        return series.get_statistics(window) if series else {}
    
    def get_rate(self, name: str, window: timedelta = timedelta(minutes=1)) -> float:
        """Get rate for a metric series"""
        series = self.get_series(name)
        return series.get_rate(window) if series else 0.0
    
    def list_metrics(self, pattern: Optional[str] = None) -> List[str]:
        """List all metric names, optionally filtered by pattern"""
        with self.series_lock:
            names = list(self.series.keys())
            
            if pattern:
                import re
                regex = re.compile(pattern)
                names = [name for name in names if regex.search(name)]
            
            return sorted(names)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self.series_lock:
            summary = {}
            
            for name, series in self.series.items():
                latest = series.get_latest()
                stats = series.get_statistics(timedelta(hours=1))  # Last hour
                
                summary[name] = {
                    'type': series.metric_type.value,
                    'latest_value': latest.value if latest else None,
                    'latest_timestamp': latest.timestamp.isoformat() if latest else None,
                    'point_count': len(series.points),
                    'statistics': stats,
                    'tags': series.tags
                }
            
            return summary
    
    def add_collection_source(self, name: str, source_func: Callable):
        """Add a metrics collection source"""
        self.collection_sources[name] = source_func
        self.logger.info(f"Added collection source: {name}")
    
    def remove_collection_source(self, name: str):
        """Remove a metrics collection source"""
        if name in self.collection_sources:
            del self.collection_sources[name]
            self.logger.info(f"Removed collection source: {name}")
    
    def add_aggregation_rule(self, name: str, source_pattern: str, 
                           aggregation_type: str, window: timedelta):
        """Add metric aggregation rule"""
        self.aggregation_rules[name] = {
            'source_pattern': source_pattern,
            'aggregation_type': aggregation_type,  # sum, avg, min, max, count
            'window': window,
            'last_processed': datetime.now()
        }
        self.logger.info(f"Added aggregation rule: {name}")
    
    def _process_aggregations(self):
        """Process aggregation rules"""
        for rule_name, rule in self.aggregation_rules.items():
            try:
                # Find matching metrics
                import re
                pattern = re.compile(rule['source_pattern'])
                matching_series = [name for name in self.series.keys() if pattern.search(name)]
                
                if not matching_series:
                    continue
                
                # Calculate aggregation
                window_start = datetime.now() - rule['window']
                values = []
                
                for series_name in matching_series:
                    series = self.series[series_name]
                    recent_points = [p for p in series.points if p.timestamp > window_start]
                    values.extend([p.value for p in recent_points])
                
                if not values:
                    continue
                
                # Apply aggregation function
                agg_type = rule['aggregation_type']
                if agg_type == 'sum':
                    result = sum(values)
                elif agg_type == 'avg':
                    result = sum(values) / len(values)
                elif agg_type == 'min':
                    result = min(values)
                elif agg_type == 'max':
                    result = max(values)
                elif agg_type == 'count':
                    result = len(values)
                else:
                    continue
                
                # Record aggregated metric
                self.record_gauge(f"aggregated.{rule_name}", result, 
                                tags={'aggregation_type': agg_type})
                
                rule['last_processed'] = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Error processing aggregation rule {rule_name}: {e}")
    
    def add_alert_rule(self, name: str, metric_pattern: str, 
                      condition: str, threshold: float, 
                      callback: Optional[Callable] = None):
        """Add metric alert rule"""
        self.alert_rules[name] = {
            'metric_pattern': metric_pattern,
            'condition': condition,  # gt, lt, eq, gte, lte
            'threshold': threshold,
            'callback': callback,
            'last_triggered': None,
            'trigger_count': 0
        }
        self.logger.info(f"Added alert rule: {name}")
    
    def _check_alerts(self):
        """Check alert rules"""
        for rule_name, rule in self.alert_rules.items():
            try:
                # Find matching metrics
                import re
                pattern = re.compile(rule['metric_pattern'])
                matching_series = [name for name in self.series.keys() if pattern.search(name)]
                
                for series_name in matching_series:
                    latest_value = self.get_latest_value(series_name)
                    if latest_value is None:
                        continue
                    
                    # Check condition
                    condition = rule['condition']
                    threshold = rule['threshold']
                    triggered = False
                    
                    if condition == 'gt' and latest_value > threshold:
                        triggered = True
                    elif condition == 'lt' and latest_value < threshold:
                        triggered = True
                    elif condition == 'eq' and latest_value == threshold:
                        triggered = True
                    elif condition == 'gte' and latest_value >= threshold:
                        triggered = True
                    elif condition == 'lte' and latest_value <= threshold:
                        triggered = True
                    
                    if triggered:
                        alert_data = {
                            'rule_name': rule_name,
                            'metric_name': series_name,
                            'value': latest_value,
                            'threshold': threshold,
                            'condition': condition,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Update rule stats
                        rule['last_triggered'] = datetime.now()
                        rule['trigger_count'] += 1
                        
                        # Call callback if provided
                        if rule['callback']:
                            try:
                                rule['callback'](alert_data)
                            except Exception as e:
                                self.logger.error(f"Error in alert callback: {e}")
                        
                        # Trigger event
                        self._trigger_event('alert_triggered', alert_data)
                        
                        self.logger.warning(f"Alert triggered: {rule_name} - {series_name} = {latest_value}")
                        
            except Exception as e:
                self.logger.error(f"Error checking alert rule {rule_name}: {e}")
    
    def _persist_all_metrics(self):
        """Persist all metrics to database"""
        if not self.enable_persistence:
            return
        
        try:
            with sqlite3.connect(self.storage_path) as conn:
                points_to_persist = []
                
                with self.series_lock:
                    for series in self.series.values():
                        for point in series.points:
                            points_to_persist.append((
                                point.name,
                                point.value,
                                point.metric_type.value,
                                point.timestamp.isoformat(),
                                json.dumps(point.tags),
                                json.dumps(point.metadata)
                            ))
                
                if points_to_persist:
                    conn.executemany('''
                        INSERT OR REPLACE INTO metrics 
                        (name, value, type, timestamp, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', points_to_persist)
                    
                    self.collection_stats['points_persisted'] += len(points_to_persist)
                    
                    # Clean up old data
                    cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
                    conn.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff,))
                    
                    self.logger.debug(f"Persisted {len(points_to_persist)} metric points")
                    
        except Exception as e:
            self.logger.error(f"Error persisting metrics: {e}")
    
    def query_metrics(self, name_pattern: str, start_time: datetime, 
                     end_time: datetime, limit: int = 1000) -> List[MetricPoint]:
        """Query metrics from database"""
        if not self.enable_persistence:
            return []
        
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute('''
                    SELECT name, value, type, timestamp, tags, metadata
                    FROM metrics
                    WHERE name LIKE ? AND timestamp BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (name_pattern, start_time.isoformat(), end_time.isoformat(), limit))
                
                points = []
                for row in cursor.fetchall():
                    point = MetricPoint(
                        name=row[0],
                        value=row[1],
                        metric_type=MetricType(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        tags=json.loads(row[4]) if row[4] else {},
                        metadata=json.loads(row[5]) if row[5] else {}
                    )
                    points.append(point)
                
                return points
                
        except Exception as e:
            self.logger.error(f"Error querying metrics: {e}")
            return []
    
    def export_metrics(self, format: str = 'json', 
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> str:
        """Export metrics in specified format"""
        if format.lower() == 'json':
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'collection_stats': self.collection_stats,
                'metrics_summary': self.get_metrics_summary()
            }
            
            if start_time and end_time:
                # Export historical data
                all_metrics = {}
                for name in self.list_metrics():
                    points = self.query_metrics(name, start_time, end_time)
                    all_metrics[name] = [point.to_dict() for point in points]
                export_data['historical_data'] = all_metrics
            
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            **self.collection_stats,
            'is_collecting': self.is_collecting,
            'collection_interval': self.collection_interval,
            'series_count': len(self.series),
            'collection_sources': list(self.collection_sources.keys()),
            'aggregation_rules': len(self.aggregation_rules),
            'alert_rules': len(self.alert_rules),
            'retention_days': self.retention_days
        }
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        try:
            self.event_callbacks[event_type].remove(callback)
        except ValueError:
            pass
    
    def _trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger event callbacks"""
        for callback in self.event_callbacks[event_type]:
            try:
                callback(event_type, event_data)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event_type}: {e}")
    
    def cleanup(self):
        """Cleanup collector resources"""
        self.stop_collection()
        
        # Final persistence
        if self.enable_persistence:
            self._persist_all_metrics()
        
        self.logger.info("Metrics collector cleanup completed")


# Context manager for timing operations
class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, 
                 tags: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.metric_name, duration, self.tags)


# Decorator for timing functions
def timed_metric(collector: MetricsCollector, metric_name: Optional[str] = None,
                tags: Optional[Dict[str, str]] = None):
    """Decorator to time function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = metric_name or f"function.{func.__name__}.duration"
            with TimerContext(collector, name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator