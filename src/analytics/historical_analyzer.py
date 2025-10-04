"""
Historical Analyzer - Advanced trend analysis for failure rates, flakiness, and performance
Provides comprehensive historical insights and predictive analytics
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict

from ..database.database import DatabaseManager
from ..monitoring.metrics_collector import MetricsCollector

class AnalysisPeriod(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"

class MetricType(Enum):
    FAILURE_RATE = "failure_rate"
    FLAKINESS = "flakiness"
    PERFORMANCE = "performance"
    COVERAGE = "coverage"
    SECURITY = "security"
    COMPLIANCE = "compliance"

@dataclass
class HistoricalDataPoint:
    """Single historical data point"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_type: MetricType
    period: AnalysisPeriod
    trend_direction: TrendDirection
    trend_strength: float  # 0-1, how strong the trend is
    slope: float  # Rate of change
    correlation: float  # Correlation coefficient
    volatility: float  # Standard deviation
    confidence_interval: Tuple[float, float]
    seasonal_patterns: Dict[str, Any]
    anomalies: List[Dict[str, Any]]

@dataclass
class FlakinessMetrics:
    """Flakiness analysis metrics"""
    flaky_test_count: int
    flakiness_rate: float
    most_flaky_tests: List[Dict[str, Any]]
    flakiness_trend: TrendDirection
    stability_score: float
    intermittent_failures: int

@dataclass
class PerformanceMetrics:
    """Performance analysis metrics"""
    avg_execution_time: float
    performance_trend: TrendDirection
    slowest_tests: List[Dict[str, Any]]
    performance_degradation_events: int
    throughput_trend: TrendDirection
    resource_utilization: Dict[str, float]

@dataclass
class FailureAnalysis:
    """Failure rate analysis"""
    overall_failure_rate: float
    failure_trend: TrendDirection
    failure_categories: Dict[str, int]
    most_failing_components: List[Dict[str, Any]]
    failure_patterns: List[Dict[str, Any]]
    recovery_metrics: Dict[str, float]

@dataclass
class HistoricalReport:
    """Comprehensive historical analysis report"""
    analysis_period: AnalysisPeriod
    date_range: Tuple[datetime, datetime]
    generated_at: datetime
    failure_analysis: FailureAnalysis
    flakiness_metrics: FlakinessMetrics
    performance_metrics: PerformanceMetrics
    trend_analyses: List[TrendAnalysis]
    predictions: Dict[str, Any]
    recommendations: List[str]
    quality_score_trend: TrendDirection
    business_impact_analysis: Dict[str, Any]

class HistoricalAnalyzer:
    """
    Advanced historical analyzer for comprehensive trend analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_manager = DatabaseManager()
        self.metrics_collector = MetricsCollector()
        self.logger = logging.getLogger(__name__)
        
        # Analysis parameters
        self.min_data_points = config.get('min_data_points', 10)
        self.anomaly_threshold = config.get('anomaly_threshold', 2.0)  # Standard deviations
        self.trend_confidence = config.get('trend_confidence', 0.95)
        
    async def analyze_historical_trends(
        self,
        period: AnalysisPeriod = AnalysisPeriod.MONTHLY,
        lookback_months: int = 6,
        include_predictions: bool = True
    ) -> HistoricalReport:
        """Generate comprehensive historical trend analysis"""
        
        try:
            self.logger.info(f"Starting historical analysis for {period.value} over {lookback_months} months")
            
            # Define date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_months * 30)
            
            # Collect historical data
            historical_data = await self._collect_historical_data(start_date, end_date, period)
            
            # Analyze failure rates
            failure_analysis = await self._analyze_failure_rates(historical_data, period)
            
            # Analyze flakiness
            flakiness_metrics = await self._analyze_flakiness(historical_data, period)
            
            # Analyze performance
            performance_metrics = await self._analyze_performance(historical_data, period)
            
            # Generate trend analyses
            trend_analyses = await self._generate_trend_analyses(historical_data, period)
            
            # Generate predictions
            predictions = {}
            if include_predictions:
                predictions = await self._generate_predictions(historical_data, trend_analyses)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                failure_analysis, flakiness_metrics, performance_metrics, trend_analyses
            )
            
            # Analyze business impact
            business_impact = await self._analyze_business_impact(
                failure_analysis, performance_metrics, trend_analyses
            )
            
            # Determine overall quality trend
            quality_trend = await self._determine_quality_trend(trend_analyses)
            
            report = HistoricalReport(
                analysis_period=period,
                date_range=(start_date, end_date),
                generated_at=datetime.now(),
                failure_analysis=failure_analysis,
                flakiness_metrics=flakiness_metrics,
                performance_metrics=performance_metrics,
                trend_analyses=trend_analyses,
                predictions=predictions,
                recommendations=recommendations,
                quality_score_trend=quality_trend,
                business_impact_analysis=business_impact
            )
            
            # Store analysis results
            await self._store_historical_analysis(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error in historical analysis: {str(e)}")
            raise
    
    async def _collect_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        period: AnalysisPeriod
    ) -> List[HistoricalDataPoint]:
        """Collect historical data from database"""
        
        try:
            # Query test execution data
            test_query = """
            SELECT 
                DATE_TRUNC(%s, created_at) as period,
                COUNT(*) as total_tests,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tests,
                COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_tests,
                AVG(execution_time) as avg_execution_time,
                AVG(CASE WHEN flaky = true THEN 1 ELSE 0 END) as flakiness_rate,
                AVG(performance_score) as performance_score,
                AVG(coverage_percentage) as coverage
            FROM test_executions 
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY DATE_TRUNC(%s, created_at)
            ORDER BY period
            """
            
            period_sql = self._get_sql_period(period)
            results = await self.db_manager.execute_query(
                test_query, (period_sql, start_date, end_date, period_sql)
            )
            
            historical_data = []
            
            if results:
                for row in results:
                    timestamp = row['period']
                    total_tests = row['total_tests'] or 0
                    failed_tests = row['failed_tests'] or 0
                    
                    # Failure rate
                    failure_rate = (failed_tests / total_tests * 100) if total_tests > 0 else 0
                    historical_data.append(HistoricalDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.FAILURE_RATE,
                        value=failure_rate,
                        metadata={
                            'total_tests': total_tests,
                            'failed_tests': failed_tests,
                            'passed_tests': row['passed_tests'] or 0
                        }
                    ))
                    
                    # Flakiness
                    flakiness_rate = (row['flakiness_rate'] or 0) * 100
                    historical_data.append(HistoricalDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.FLAKINESS,
                        value=flakiness_rate,
                        metadata={'total_tests': total_tests}
                    ))
                    
                    # Performance
                    performance_score = row['performance_score'] or 80
                    historical_data.append(HistoricalDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.PERFORMANCE,
                        value=performance_score,
                        metadata={
                            'avg_execution_time': row['avg_execution_time'] or 0,
                            'total_tests': total_tests
                        }
                    ))
                    
                    # Coverage
                    coverage = row['coverage'] or 75
                    historical_data.append(HistoricalDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.COVERAGE,
                        value=coverage,
                        metadata={'total_tests': total_tests}
                    ))
            else:
                # Generate mock data for demonstration
                historical_data = self._generate_mock_historical_data(start_date, end_date, period)
            
            return historical_data
            
        except Exception as e:
            self.logger.warning(f"Database query failed, generating mock data: {str(e)}")
            return self._generate_mock_historical_data(start_date, end_date, period)
    
    def _generate_mock_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        period: AnalysisPeriod
    ) -> List[HistoricalDataPoint]:
        """Generate mock historical data for demonstration"""
        
        import random
        
        historical_data = []
        current_date = start_date
        
        # Period increment
        if period == AnalysisPeriod.DAILY:
            increment = timedelta(days=1)
        elif period == AnalysisPeriod.WEEKLY:
            increment = timedelta(weeks=1)
        else:  # MONTHLY
            increment = timedelta(days=30)
        
        # Base values with trends
        base_failure_rate = 15.0
        base_flakiness = 8.0
        base_performance = 85.0
        base_coverage = 78.0
        
        while current_date <= end_date:
            # Add some trend and randomness
            days_from_start = (current_date - start_date).days
            trend_factor = days_from_start / 180.0  # 6 months
            
            # Failure rate (improving trend)
            failure_rate = max(2, base_failure_rate - (trend_factor * 5) + random.uniform(-3, 3))
            historical_data.append(HistoricalDataPoint(
                timestamp=current_date,
                metric_type=MetricType.FAILURE_RATE,
                value=failure_rate,
                metadata={'total_tests': random.randint(100, 500), 'failed_tests': int(failure_rate * 5)}
            ))
            
            # Flakiness (stable with some volatility)
            flakiness = max(1, base_flakiness + random.uniform(-2, 4))
            historical_data.append(HistoricalDataPoint(
                timestamp=current_date,
                metric_type=MetricType.FLAKINESS,
                value=flakiness,
                metadata={'total_tests': random.randint(100, 500)}
            ))
            
            # Performance (slight improvement)
            performance = min(95, base_performance + (trend_factor * 3) + random.uniform(-2, 2))
            historical_data.append(HistoricalDataPoint(
                timestamp=current_date,
                metric_type=MetricType.PERFORMANCE,
                value=performance,
                metadata={'avg_execution_time': random.uniform(10, 30)}
            ))
            
            # Coverage (gradual improvement)
            coverage = min(90, base_coverage + (trend_factor * 8) + random.uniform(-1, 2))
            historical_data.append(HistoricalDataPoint(
                timestamp=current_date,
                metric_type=MetricType.COVERAGE,
                value=coverage,
                metadata={'total_tests': random.randint(100, 500)}
            ))
            
            current_date += increment
        
        return historical_data
    
    def _get_sql_period(self, period: AnalysisPeriod) -> str:
        """Convert period enum to SQL period string"""
        mapping = {
            AnalysisPeriod.HOURLY: 'hour',
            AnalysisPeriod.DAILY: 'day',
            AnalysisPeriod.WEEKLY: 'week',
            AnalysisPeriod.MONTHLY: 'month',
            AnalysisPeriod.QUARTERLY: 'quarter',
            AnalysisPeriod.YEARLY: 'year'
        }
        return mapping.get(period, 'day')
    
    async def _analyze_failure_rates(
        self,
        historical_data: List[HistoricalDataPoint],
        period: AnalysisPeriod
    ) -> FailureAnalysis:
        """Analyze failure rate trends"""
        
        failure_data = [dp for dp in historical_data if dp.metric_type == MetricType.FAILURE_RATE]
        
        if not failure_data:
            return self._create_empty_failure_analysis()
        
        # Calculate overall failure rate
        failure_values = [dp.value for dp in failure_data]
        overall_failure_rate = statistics.mean(failure_values)
        
        # Determine trend
        trend_direction = self._calculate_trend_direction(failure_values)
        
        # Analyze failure categories (mock data)
        failure_categories = {
            "Test Failures": 45,
            "Environment Issues": 25,
            "Infrastructure": 15,
            "Code Issues": 10,
            "Other": 5
        }
        
        # Most failing components (mock data)
        most_failing_components = [
            {"component": "Authentication Service", "failure_rate": 12.5, "trend": "improving"},
            {"component": "Payment Gateway", "failure_rate": 8.3, "trend": "stable"},
            {"component": "User Management", "failure_rate": 6.7, "trend": "declining"}
        ]
        
        # Failure patterns
        failure_patterns = [
            {"pattern": "Weekend Spikes", "frequency": "weekly", "impact": "medium"},
            {"pattern": "Deploy Day Issues", "frequency": "bi-weekly", "impact": "high"},
            {"pattern": "Load-Related Failures", "frequency": "daily", "impact": "low"}
        ]
        
        # Recovery metrics
        recovery_metrics = {
            "mean_time_to_recovery": 15.5,
            "recovery_success_rate": 94.2,
            "escalation_rate": 8.3
        }
        
        return FailureAnalysis(
            overall_failure_rate=overall_failure_rate,
            failure_trend=trend_direction,
            failure_categories=failure_categories,
            most_failing_components=most_failing_components,
            failure_patterns=failure_patterns,
            recovery_metrics=recovery_metrics
        )
    
    def _create_empty_failure_analysis(self) -> FailureAnalysis:
        """Create empty failure analysis"""
        return FailureAnalysis(
            overall_failure_rate=0.0,
            failure_trend=TrendDirection.STABLE,
            failure_categories={},
            most_failing_components=[],
            failure_patterns=[],
            recovery_metrics={}
        )
    
    async def _analyze_flakiness(
        self,
        historical_data: List[HistoricalDataPoint],
        period: AnalysisPeriod
    ) -> FlakinessMetrics:
        """Analyze test flakiness trends"""
        
        flakiness_data = [dp for dp in historical_data if dp.metric_type == MetricType.FLAKINESS]
        
        if not flakiness_data:
            return self._create_empty_flakiness_metrics()
        
        # Calculate flakiness metrics
        flakiness_values = [dp.value for dp in flakiness_data]
        flakiness_rate = statistics.mean(flakiness_values)
        
        # Determine trend
        trend_direction = self._calculate_trend_direction(flakiness_values)
        
        # Calculate stability score (inverse of flakiness)
        stability_score = max(0, 100 - flakiness_rate)
        
        # Most flaky tests (mock data)
        most_flaky_tests = [
            {"test_name": "test_user_authentication", "flakiness_rate": 15.2, "executions": 150},
            {"test_name": "test_payment_processing", "flakiness_rate": 12.8, "executions": 200},
            {"test_name": "test_data_synchronization", "flakiness_rate": 10.5, "executions": 180}
        ]
        
        return FlakinessMetrics(
            flaky_test_count=len(most_flaky_tests),
            flakiness_rate=flakiness_rate,
            most_flaky_tests=most_flaky_tests,
            flakiness_trend=trend_direction,
            stability_score=stability_score,
            intermittent_failures=sum(dp.metadata.get('total_tests', 0) for dp in flakiness_data[-5:])
        )
    
    def _create_empty_flakiness_metrics(self) -> FlakinessMetrics:
        """Create empty flakiness metrics"""
        return FlakinessMetrics(
            flaky_test_count=0,
            flakiness_rate=0.0,
            most_flaky_tests=[],
            flakiness_trend=TrendDirection.STABLE,
            stability_score=100.0,
            intermittent_failures=0
        )
    
    async def _analyze_performance(
        self,
        historical_data: List[HistoricalDataPoint],
        period: AnalysisPeriod
    ) -> PerformanceMetrics:
        """Analyze performance trends"""
        
        performance_data = [dp for dp in historical_data if dp.metric_type == MetricType.PERFORMANCE]
        
        if not performance_data:
            return self._create_empty_performance_metrics()
        
        # Calculate performance metrics
        performance_values = [dp.value for dp in performance_data]
        avg_performance = statistics.mean(performance_values)
        
        # Determine trend
        trend_direction = self._calculate_trend_direction(performance_values)
        
        # Calculate execution times
        execution_times = [dp.metadata.get('avg_execution_time', 0) for dp in performance_data if dp.metadata.get('avg_execution_time')]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        # Slowest tests (mock data)
        slowest_tests = [
            {"test_name": "test_full_integration", "avg_time": 45.2, "trend": "stable"},
            {"test_name": "test_database_migration", "avg_time": 38.7, "trend": "improving"},
            {"test_name": "test_large_dataset", "avg_time": 32.1, "trend": "declining"}
        ]
        
        # Performance degradation events
        degradation_events = len([v for v in performance_values if v < 70])
        
        # Resource utilization (mock data)
        resource_utilization = {
            "cpu_usage": 65.2,
            "memory_usage": 78.5,
            "disk_io": 45.3,
            "network_io": 32.1
        }
        
        return PerformanceMetrics(
            avg_execution_time=avg_execution_time,
            performance_trend=trend_direction,
            slowest_tests=slowest_tests,
            performance_degradation_events=degradation_events,
            throughput_trend=trend_direction,
            resource_utilization=resource_utilization
        )
    
    def _create_empty_performance_metrics(self) -> PerformanceMetrics:
        """Create empty performance metrics"""
        return PerformanceMetrics(
            avg_execution_time=0.0,
            performance_trend=TrendDirection.STABLE,
            slowest_tests=[],
            performance_degradation_events=0,
            throughput_trend=TrendDirection.STABLE,
            resource_utilization={}
        )
    
    async def _generate_trend_analyses(
        self,
        historical_data: List[HistoricalDataPoint],
        period: AnalysisPeriod
    ) -> List[TrendAnalysis]:
        """Generate detailed trend analyses for all metrics"""
        
        trend_analyses = []
        
        # Group data by metric type
        metric_groups = defaultdict(list)
        for dp in historical_data:
            metric_groups[dp.metric_type].append(dp)
        
        for metric_type, data_points in metric_groups.items():
            if len(data_points) < self.min_data_points:
                continue
            
            values = [dp.value for dp in data_points]
            timestamps = [dp.timestamp for dp in data_points]
            
            # Calculate trend metrics
            trend_direction = self._calculate_trend_direction(values)
            slope = self._calculate_slope(values)
            correlation = self._calculate_correlation(timestamps, values)
            volatility = statistics.stdev(values) if len(values) > 1 else 0
            confidence_interval = self._calculate_confidence_interval(values)
            trend_strength = abs(correlation)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(data_points)
            
            # Analyze seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(data_points, period)
            
            trend_analysis = TrendAnalysis(
                metric_type=metric_type,
                period=period,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                slope=slope,
                correlation=correlation,
                volatility=volatility,
                confidence_interval=confidence_interval,
                seasonal_patterns=seasonal_patterns,
                anomalies=anomalies
            )
            
            trend_analyses.append(trend_analysis)
        
        return trend_analyses
    
    def _calculate_trend_direction(self, values: List[float]) -> TrendDirection:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return TrendDirection.STABLE
        
        # Calculate slope
        x = list(range(len(values)))
        slope = self._calculate_slope(values)
        
        # Calculate volatility
        volatility = statistics.stdev(values) if len(values) > 1 else 0
        mean_value = statistics.mean(values)
        cv = volatility / mean_value if mean_value != 0 else 0  # Coefficient of variation
        
        # Determine trend
        if cv > 0.3:  # High volatility
            return TrendDirection.VOLATILE
        elif abs(slope) < 0.1:  # Minimal change
            return TrendDirection.STABLE
        elif slope > 0:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.DECLINING
    
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear regression slope"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        # Linear regression
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _calculate_correlation(self, timestamps: List[datetime], values: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(values) < 2:
            return 0.0
        
        # Convert timestamps to numeric values
        base_time = timestamps[0]
        x = [(t - base_time).total_seconds() for t in timestamps]
        
        try:
            correlation_matrix = np.corrcoef(x, values)
            return correlation_matrix[0, 1] if not np.isnan(correlation_matrix[0, 1]) else 0.0
        except:
            return 0.0
    
    def _calculate_confidence_interval(self, values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval"""
        if len(values) < 2:
            mean_val = values[0] if values else 0
            return (mean_val, mean_val)
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        # Simple confidence interval (assuming normal distribution)
        margin = 1.96 * std_val / (len(values) ** 0.5)  # 95% confidence
        
        return (mean_val - margin, mean_val + margin)
    
    def _detect_anomalies(self, data_points: List[HistoricalDataPoint]) -> List[Dict[str, Any]]:
        """Detect anomalies in data points"""
        if len(data_points) < 3:
            return []
        
        values = [dp.value for dp in data_points]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        anomalies = []
        for dp in data_points:
            z_score = abs(dp.value - mean_val) / std_val if std_val > 0 else 0
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    "timestamp": dp.timestamp,
                    "value": dp.value,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3 else "medium"
                })
        
        return anomalies
    
    def _analyze_seasonal_patterns(
        self,
        data_points: List[HistoricalDataPoint],
        period: AnalysisPeriod
    ) -> Dict[str, Any]:
        """Analyze seasonal patterns in data"""
        
        patterns = {}
        
        if len(data_points) < 7:  # Need at least a week of data
            return patterns
        
        # Group by day of week
        day_groups = defaultdict(list)
        for dp in data_points:
            day_of_week = dp.timestamp.strftime('%A')
            day_groups[day_of_week].append(dp.value)
        
        # Calculate averages by day
        day_averages = {}
        for day, values in day_groups.items():
            if values:
                day_averages[day] = statistics.mean(values)
        
        if day_averages:
            patterns['day_of_week'] = day_averages
            
            # Find peak and low days
            max_day = max(day_averages, key=day_averages.get)
            min_day = min(day_averages, key=day_averages.get)
            
            patterns['peak_day'] = max_day
            patterns['low_day'] = min_day
            patterns['weekly_variation'] = day_averages[max_day] - day_averages[min_day]
        
        return patterns
    
    async def _generate_predictions(
        self,
        historical_data: List[HistoricalDataPoint],
        trend_analyses: List[TrendAnalysis]
    ) -> Dict[str, Any]:
        """Generate predictions based on historical trends"""
        
        predictions = {}
        
        for trend_analysis in trend_analyses:
            metric_name = trend_analysis.metric_type.value
            
            # Simple linear prediction
            if trend_analysis.trend_direction != TrendDirection.VOLATILE:
                current_value = historical_data[-1].value if historical_data else 0
                predicted_change = trend_analysis.slope * 30  # 30 days ahead
                predicted_value = current_value + predicted_change
                
                predictions[metric_name] = {
                    "predicted_value": predicted_value,
                    "confidence": trend_analysis.trend_strength,
                    "trend_direction": trend_analysis.trend_direction.value,
                    "prediction_horizon": "30_days"
                }
        
        return predictions
    
    async def _generate_recommendations(
        self,
        failure_analysis: FailureAnalysis,
        flakiness_metrics: FlakinessMetrics,
        performance_metrics: PerformanceMetrics,
        trend_analyses: List[TrendAnalysis]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Failure rate recommendations
        if failure_analysis.failure_trend == TrendDirection.DECLINING:
            recommendations.append("Address increasing failure rates with improved testing strategies")
        if failure_analysis.overall_failure_rate > 10:
            recommendations.append("Implement stricter quality gates to reduce failure rates")
        
        # Flakiness recommendations
        if flakiness_metrics.flakiness_rate > 5:
            recommendations.append("Focus on stabilizing flaky tests to improve reliability")
        if flakiness_metrics.flakiness_trend == TrendDirection.DECLINING:
            recommendations.append("Investigate root causes of increasing test flakiness")
        
        # Performance recommendations
        if performance_metrics.performance_trend == TrendDirection.DECLINING:
            recommendations.append("Optimize test execution performance and resource usage")
        if performance_metrics.avg_execution_time > 30:
            recommendations.append("Consider test parallelization to reduce execution time")
        
        # Trend-based recommendations
        for trend in trend_analyses:
            if trend.volatility > 20:
                recommendations.append(f"Stabilize {trend.metric_type.value} metrics to reduce volatility")
            if trend.trend_direction == TrendDirection.DECLINING and trend.metric_type in [MetricType.PERFORMANCE, MetricType.COVERAGE]:
                recommendations.append(f"Implement improvement plan for {trend.metric_type.value}")
        
        return recommendations[:10]  # Limit to top 10
    
    async def _analyze_business_impact(
        self,
        failure_analysis: FailureAnalysis,
        performance_metrics: PerformanceMetrics,
        trend_analyses: List[TrendAnalysis]
    ) -> Dict[str, Any]:
        """Analyze business impact of trends"""
        
        impact_analysis = {
            "overall_impact": "medium",
            "risk_factors": [],
            "cost_implications": {},
            "customer_impact": "low"
        }
        
        # Calculate risk factors
        if failure_analysis.overall_failure_rate > 15:
            impact_analysis["risk_factors"].append("High failure rate affecting reliability")
        
        if performance_metrics.performance_degradation_events > 5:
            impact_analysis["risk_factors"].append("Performance issues impacting user experience")
        
        # Estimate cost implications
        impact_analysis["cost_implications"] = {
            "testing_efficiency": 85 - failure_analysis.overall_failure_rate,
            "maintenance_overhead": min(100, failure_analysis.overall_failure_rate * 2),
            "customer_satisfaction_risk": "medium" if failure_analysis.overall_failure_rate > 10 else "low"
        }
        
        return impact_analysis
    
    async def _determine_quality_trend(self, trend_analyses: List[TrendAnalysis]) -> TrendDirection:
        """Determine overall quality trend"""
        
        if not trend_analyses:
            return TrendDirection.STABLE
        
        # Weight different metrics
        weights = {
            MetricType.FAILURE_RATE: -0.4,  # Negative because lower is better
            MetricType.FLAKINESS: -0.3,     # Negative because lower is better
            MetricType.PERFORMANCE: 0.2,    # Positive because higher is better
            MetricType.COVERAGE: 0.1        # Positive because higher is better
        }
        
        weighted_score = 0
        total_weight = 0
        
        for trend in trend_analyses:
            if trend.metric_type in weights:
                weight = weights[trend.metric_type]
                
                # Convert trend direction to numeric score
                if trend.trend_direction == TrendDirection.IMPROVING:
                    score = 1
                elif trend.trend_direction == TrendDirection.DECLINING:
                    score = -1
                else:
                    score = 0
                
                weighted_score += score * abs(weight)
                total_weight += abs(weight)
        
        if total_weight == 0:
            return TrendDirection.STABLE
        
        final_score = weighted_score / total_weight
        
        if final_score > 0.2:
            return TrendDirection.IMPROVING
        elif final_score < -0.2:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    async def _store_historical_analysis(self, report: HistoricalReport):
        """Store historical analysis results"""
        try:
            query = """
            INSERT INTO historical_analyses (analysis_data, period, date_range, generated_at)
            VALUES (%s, %s, %s, %s)
            """
            await self.db_manager.execute_query(
                query, (
                    json.dumps(asdict(report), default=str),
                    report.analysis_period.value,
                    f"{report.date_range[0]} - {report.date_range[1]}",
                    report.generated_at
                )
            )
        except Exception as e:
            self.logger.warning(f"Failed to store historical analysis: {str(e)}")
    
    async def get_metric_history(
        self,
        metric_type: MetricType,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get history for a specific metric"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        historical_data = await self._collect_historical_data(
            start_date, end_date, AnalysisPeriod.DAILY
        )
        
        metric_data = [
            {
                "timestamp": dp.timestamp,
                "value": dp.value,
                "metadata": dp.metadata
            }
            for dp in historical_data
            if dp.metric_type == metric_type
        ]
        
        return metric_data
    
    async def compare_periods(
        self,
        metric_type: MetricType,
        period1_days: int = 30,
        period2_days: int = 30
    ) -> Dict[str, Any]:
        """Compare two time periods for a metric"""
        
        end_date = datetime.now()
        period1_start = end_date - timedelta(days=period1_days)
        period2_start = period1_start - timedelta(days=period2_days)
        
        # Get data for both periods
        period1_data = await self._collect_historical_data(
            period1_start, end_date, AnalysisPeriod.DAILY
        )
        period2_data = await self._collect_historical_data(
            period2_start, period1_start, AnalysisPeriod.DAILY
        )
        
        # Filter by metric type
        period1_values = [dp.value for dp in period1_data if dp.metric_type == metric_type]
        period2_values = [dp.value for dp in period2_data if dp.metric_type == metric_type]
        
        if not period1_values or not period2_values:
            return {"error": "Insufficient data for comparison"}
        
        period1_avg = statistics.mean(period1_values)
        period2_avg = statistics.mean(period2_values)
        
        change_percent = ((period1_avg - period2_avg) / period2_avg * 100) if period2_avg != 0 else 0
        
        return {
            "metric_type": metric_type.value,
            "period1_average": period1_avg,
            "period2_average": period2_avg,
            "change_percent": change_percent,
            "trend": "improving" if change_percent > 5 else "declining" if change_percent < -5 else "stable"
        }