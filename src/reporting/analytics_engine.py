"""
Analytics Engine Module

This module provides advanced analytics and insights generation for
functional testing, security scanning, and compliance assessment results.
It includes trend analysis, predictive insights, and cross-domain correlations.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import math


class AnalyticsType(Enum):
    """Types of analytics"""
    TREND_ANALYSIS = "trend_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    QUALITY_METRICS = "quality_metrics"
    CORRELATION_ANALYSIS = "correlation_analysis"
    PREDICTIVE_INSIGHTS = "predictive_insights"


class TrendDirection(Enum):
    """Trend directions"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class RiskLevel(Enum):
    """Risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_name: str
    direction: TrendDirection
    change_percentage: float
    confidence_score: float
    data_points: List[float] = field(default_factory=list)
    time_period: str = ""
    prediction: Optional[float] = None
    insights: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance analysis metrics"""
    average_execution_time: float
    median_execution_time: float
    p95_execution_time: float
    throughput: float
    error_rate: float
    success_rate: float
    performance_score: float
    bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Risk assessment results"""
    overall_risk_level: RiskLevel
    risk_score: float
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """Quality metrics analysis"""
    quality_score: float
    test_coverage: float
    code_quality: float
    security_posture: float
    compliance_level: float
    defect_density: float
    technical_debt: float
    maintainability_index: float
    quality_trends: List[TrendAnalysis] = field(default_factory=list)


@dataclass
class CorrelationAnalysis:
    """Correlation analysis between different metrics"""
    correlation_pairs: List[Tuple[str, str, float]] = field(default_factory=list)
    significant_correlations: List[Dict[str, Any]] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


@dataclass
class PredictiveInsights:
    """Predictive insights and forecasting"""
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    confidence_intervals: List[Dict[str, Any]] = field(default_factory=list)
    risk_forecasts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AnalyticsResult:
    """Comprehensive analytics result"""
    analysis_type: AnalyticsType
    generated_at: datetime
    trend_analysis: Optional[List[TrendAnalysis]] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    risk_assessment: Optional[RiskAssessment] = None
    quality_metrics: Optional[QualityMetrics] = None
    correlation_analysis: Optional[CorrelationAnalysis] = None
    predictive_insights: Optional[PredictiveInsights] = None
    summary: str = ""
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsEngine:
    """
    Advanced analytics engine for test results analysis
    """
    
    def __init__(self):
        """Initialize the analytics engine"""
        self.historical_data: Dict[str, List[Any]] = {}
        self.baseline_metrics: Dict[str, float] = {}
    
    def analyze_trends(
        self,
        historical_data: List[Dict[str, Any]],
        metrics: List[str],
        time_window_days: int = 30
    ) -> List[TrendAnalysis]:
        """
        Analyze trends in historical test data
        """
        trends = []
        
        for metric in metrics:
            try:
                # Extract metric values over time
                values = []
                timestamps = []
                
                for data_point in historical_data:
                    if metric in data_point and 'timestamp' in data_point:
                        values.append(float(data_point[metric]))
                        timestamps.append(data_point['timestamp'])
                
                if len(values) < 2:
                    continue
                
                # Calculate trend direction and change
                direction, change_pct = self._calculate_trend_direction(values)
                confidence = self._calculate_trend_confidence(values)
                
                # Generate insights
                insights = self._generate_trend_insights(metric, direction, change_pct, values)
                
                # Make prediction
                prediction = self._predict_next_value(values) if len(values) >= 3 else None
                
                trend = TrendAnalysis(
                    metric_name=metric,
                    direction=direction,
                    change_percentage=change_pct,
                    confidence_score=confidence,
                    data_points=values,
                    time_period=f"{time_window_days} days",
                    prediction=prediction,
                    insights=insights
                )
                
                trends.append(trend)
                
            except Exception as e:
                # Skip metrics that can't be analyzed
                continue
        
        return trends
    
    def analyze_performance(
        self,
        test_results: List[Dict[str, Any]]
    ) -> PerformanceMetrics:
        """
        Analyze performance metrics from test results
        """
        execution_times = []
        success_count = 0
        total_count = len(test_results)
        
        for result in test_results:
            if 'execution_time' in result:
                execution_times.append(float(result['execution_time']))
            
            if result.get('status') == 'passed':
                success_count += 1
        
        if not execution_times:
            execution_times = [0.0]
        
        # Calculate performance metrics
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        p95_time = self._calculate_percentile(execution_times, 95)
        
        success_rate = success_count / total_count if total_count > 0 else 0
        error_rate = 1 - success_rate
        
        # Calculate throughput (tests per second)
        total_time = sum(execution_times)
        throughput = total_count / total_time if total_time > 0 else 0
        
        # Calculate performance score (0-100)
        performance_score = self._calculate_performance_score(
            success_rate, avg_time, error_rate
        )
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(test_results, execution_times)
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(
            success_rate, avg_time, error_rate, bottlenecks
        )
        
        return PerformanceMetrics(
            average_execution_time=avg_time,
            median_execution_time=median_time,
            p95_execution_time=p95_time,
            throughput=throughput,
            error_rate=error_rate,
            success_rate=success_rate,
            performance_score=performance_score,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
    
    def assess_risk(
        self,
        functional_results: Optional[Any] = None,
        security_results: Optional[Any] = None,
        compliance_results: Optional[Any] = None
    ) -> RiskAssessment:
        """
        Assess overall risk based on all test results
        """
        risk_factors = []
        risk_score = 0.0
        
        # Analyze functional testing risks
        if functional_results:
            func_risk = self._assess_functional_risk(functional_results)
            risk_factors.extend(func_risk['factors'])
            risk_score += func_risk['score'] * 0.3  # 30% weight
        
        # Analyze security risks
        if security_results:
            sec_risk = self._assess_security_risk(security_results)
            risk_factors.extend(sec_risk['factors'])
            risk_score += sec_risk['score'] * 0.5  # 50% weight
        
        # Analyze compliance risks
        if compliance_results:
            comp_risk = self._assess_compliance_risk(compliance_results)
            risk_factors.extend(comp_risk['factors'])
            risk_score += comp_risk['score'] * 0.2  # 20% weight
        
        # Determine overall risk level
        overall_risk = self._determine_risk_level(risk_score)
        
        # Generate mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(risk_factors)
        
        # Generate priority actions
        priority_actions = self._generate_priority_actions(risk_factors, overall_risk)
        
        return RiskAssessment(
            overall_risk_level=overall_risk,
            risk_score=risk_score,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            priority_actions=priority_actions
        )
    
    def analyze_quality_metrics(
        self,
        functional_results: Optional[Any] = None,
        security_results: Optional[Any] = None,
        compliance_results: Optional[Any] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> QualityMetrics:
        """
        Analyze overall quality metrics
        """
        # Calculate individual quality scores
        test_coverage = self._calculate_test_coverage(functional_results)
        code_quality = self._calculate_code_quality(functional_results)
        security_posture = self._calculate_security_posture(security_results)
        compliance_level = self._calculate_compliance_level(compliance_results)
        
        # Calculate derived metrics
        defect_density = self._calculate_defect_density(functional_results)
        technical_debt = self._calculate_technical_debt(functional_results, security_results)
        maintainability_index = self._calculate_maintainability_index(
            code_quality, technical_debt, test_coverage
        )
        
        # Calculate overall quality score
        quality_score = self._calculate_overall_quality_score(
            test_coverage, code_quality, security_posture, compliance_level
        )
        
        # Analyze quality trends if historical data is available
        quality_trends = []
        if historical_data:
            quality_trends = self.analyze_trends(
                historical_data,
                ['quality_score', 'test_coverage', 'security_posture', 'compliance_level']
            )
        
        return QualityMetrics(
            quality_score=quality_score,
            test_coverage=test_coverage,
            code_quality=code_quality,
            security_posture=security_posture,
            compliance_level=compliance_level,
            defect_density=defect_density,
            technical_debt=technical_debt,
            maintainability_index=maintainability_index,
            quality_trends=quality_trends
        )
    
    def analyze_correlations(
        self,
        metrics_data: Dict[str, List[float]]
    ) -> CorrelationAnalysis:
        """
        Analyze correlations between different metrics
        """
        correlation_pairs = []
        significant_correlations = []
        
        metric_names = list(metrics_data.keys())
        
        # Calculate pairwise correlations
        for i, metric1 in enumerate(metric_names):
            for j, metric2 in enumerate(metric_names[i+1:], i+1):
                correlation = self._calculate_correlation(
                    metrics_data[metric1], metrics_data[metric2]
                )
                
                correlation_pairs.append((metric1, metric2, correlation))
                
                # Identify significant correlations (|r| > 0.5)
                if abs(correlation) > 0.5:
                    significant_correlations.append({
                        'metric1': metric1,
                        'metric2': metric2,
                        'correlation': correlation,
                        'strength': self._interpret_correlation_strength(correlation),
                        'direction': 'positive' if correlation > 0 else 'negative'
                    })
        
        # Generate insights
        insights = self._generate_correlation_insights(significant_correlations)
        
        return CorrelationAnalysis(
            correlation_pairs=correlation_pairs,
            significant_correlations=significant_correlations,
            insights=insights
        )
    
    def generate_predictive_insights(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int = 30
    ) -> PredictiveInsights:
        """
        Generate predictive insights and forecasts
        """
        predictions = []
        confidence_intervals = []
        risk_forecasts = []
        
        # Key metrics to predict
        key_metrics = ['test_pass_rate', 'security_score', 'compliance_score', 'performance_score']
        
        for metric in key_metrics:
            try:
                # Extract historical values
                values = [data.get(metric, 0) for data in historical_data if metric in data]
                
                if len(values) < 3:
                    continue
                
                # Generate prediction
                prediction = self._forecast_metric(values, forecast_days)
                predictions.append({
                    'metric': metric,
                    'current_value': values[-1] if values else 0,
                    'predicted_value': prediction,
                    'forecast_period': f"{forecast_days} days"
                })
                
                # Calculate confidence interval
                confidence_interval = self._calculate_confidence_interval(values, prediction)
                confidence_intervals.append({
                    'metric': metric,
                    'lower_bound': confidence_interval[0],
                    'upper_bound': confidence_interval[1],
                    'confidence_level': 0.95
                })
                
                # Generate risk forecast
                risk_forecast = self._forecast_risk(metric, values, prediction)
                if risk_forecast:
                    risk_forecasts.append(risk_forecast)
                    
            except Exception:
                continue
        
        # Generate recommendations based on predictions
        recommendations = self._generate_predictive_recommendations(
            predictions, risk_forecasts
        )
        
        return PredictiveInsights(
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            risk_forecasts=risk_forecasts,
            recommendations=recommendations
        )
    
    def generate_comprehensive_analytics(
        self,
        functional_results: Optional[Any] = None,
        security_results: Optional[Any] = None,
        compliance_results: Optional[Any] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> AnalyticsResult:
        """
        Generate comprehensive analytics across all domains
        """
        # Perform all types of analysis
        trend_analysis = None
        if historical_data:
            trend_analysis = self.analyze_trends(
                historical_data,
                ['test_pass_rate', 'security_score', 'compliance_score']
            )
        
        performance_metrics = None
        if functional_results:
            # Convert functional results to expected format
            test_results = self._extract_test_results(functional_results)
            performance_metrics = self.analyze_performance(test_results)
        
        risk_assessment = self.assess_risk(
            functional_results, security_results, compliance_results
        )
        
        quality_metrics = self.analyze_quality_metrics(
            functional_results, security_results, compliance_results, historical_data
        )
        
        correlation_analysis = None
        predictive_insights = None
        
        if historical_data and len(historical_data) > 5:
            # Extract metrics for correlation analysis
            metrics_data = self._extract_metrics_for_correlation(historical_data)
            if metrics_data:
                correlation_analysis = self.analyze_correlations(metrics_data)
            
            predictive_insights = self.generate_predictive_insights(historical_data)
        
        # Generate summary
        summary = self._generate_analytics_summary(
            trend_analysis, performance_metrics, risk_assessment,
            quality_metrics, correlation_analysis, predictive_insights
        )
        
        # Calculate overall confidence score
        confidence_score = self._calculate_overall_confidence(
            trend_analysis, performance_metrics, risk_assessment, quality_metrics
        )
        
        return AnalyticsResult(
            analysis_type=AnalyticsType.PREDICTIVE_INSIGHTS,
            generated_at=datetime.now(),
            trend_analysis=trend_analysis,
            performance_metrics=performance_metrics,
            risk_assessment=risk_assessment,
            quality_metrics=quality_metrics,
            correlation_analysis=correlation_analysis,
            predictive_insights=predictive_insights,
            summary=summary,
            confidence_score=confidence_score
        )
    
    # Helper methods
    
    def _calculate_trend_direction(self, values: List[float]) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and change percentage"""
        if len(values) < 2:
            return TrendDirection.STABLE, 0.0
        
        # Calculate linear regression slope
        n = len(values)
        x = list(range(n))
        
        # Simple linear regression
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return TrendDirection.STABLE, 0.0
        
        slope = numerator / denominator
        
        # Calculate change percentage
        first_value = values[0]
        last_value = values[-1]
        change_pct = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Determine direction
        if abs(slope) < 0.01:  # Very small slope
            return TrendDirection.STABLE, change_pct
        elif slope > 0:
            return TrendDirection.IMPROVING, change_pct
        else:
            return TrendDirection.DECLINING, change_pct
    
    def _calculate_trend_confidence(self, values: List[float]) -> float:
        """Calculate confidence in trend analysis"""
        if len(values) < 3:
            return 0.5
        
        # Calculate R-squared for linear regression
        n = len(values)
        x = list(range(n))
        
        # Linear regression
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.5
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        predicted = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((values[i] - predicted[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r_squared))
    
    def _generate_trend_insights(
        self,
        metric: str,
        direction: TrendDirection,
        change_pct: float,
        values: List[float]
    ) -> List[str]:
        """Generate insights for trend analysis"""
        insights = []
        
        if direction == TrendDirection.IMPROVING:
            insights.append(f"{metric} shows positive improvement trend (+{change_pct:.1f}%)")
        elif direction == TrendDirection.DECLINING:
            insights.append(f"{metric} shows concerning decline ({change_pct:.1f}%)")
        elif direction == TrendDirection.STABLE:
            insights.append(f"{metric} remains stable with minimal variation")
        
        # Add volatility insight
        if len(values) > 2:
            volatility = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0
            if volatility > 0.2:
                insights.append(f"{metric} shows high volatility (CV: {volatility:.2f})")
        
        return insights
    
    def _predict_next_value(self, values: List[float]) -> float:
        """Predict next value using simple linear regression"""
        if len(values) < 2:
            return values[0] if values else 0.0
        
        n = len(values)
        x = list(range(n))
        
        # Linear regression
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return values[-1]
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Predict next value
        return slope * n + intercept
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_values[int(k)]
        
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1
    
    def _calculate_performance_score(
        self,
        success_rate: float,
        avg_time: float,
        error_rate: float
    ) -> float:
        """Calculate overall performance score (0-100)"""
        # Weight factors
        success_weight = 0.5
        speed_weight = 0.3
        reliability_weight = 0.2
        
        # Success rate component (0-50 points)
        success_component = success_rate * 50
        
        # Speed component (0-30 points) - inverse relationship with time
        # Assume 1 second is baseline, score decreases as time increases
        speed_component = max(0, 30 - (avg_time - 1) * 10) if avg_time > 1 else 30
        
        # Reliability component (0-20 points) - inverse of error rate
        reliability_component = (1 - error_rate) * 20
        
        return min(100, success_component + speed_component + reliability_component)
    
    def _identify_bottlenecks(
        self,
        test_results: List[Dict[str, Any]],
        execution_times: List[float]
    ) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if not execution_times:
            return bottlenecks
        
        avg_time = statistics.mean(execution_times)
        threshold = avg_time * 2  # Tests taking more than 2x average
        
        slow_tests = [
            result for i, result in enumerate(test_results)
            if i < len(execution_times) and execution_times[i] > threshold
        ]
        
        if slow_tests:
            bottlenecks.append(f"{len(slow_tests)} tests exceed 2x average execution time")
        
        # Check for high error rates in specific domains
        domain_errors = {}
        for result in test_results:
            domain = result.get('domain', 'unknown')
            if result.get('status') != 'passed':
                domain_errors[domain] = domain_errors.get(domain, 0) + 1
        
        for domain, error_count in domain_errors.items():
            if error_count > len(test_results) * 0.1:  # More than 10% errors
                bottlenecks.append(f"High error rate in {domain} domain ({error_count} failures)")
        
        return bottlenecks
    
    def _generate_performance_recommendations(
        self,
        success_rate: float,
        avg_time: float,
        error_rate: float,
        bottlenecks: List[str]
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if success_rate < 0.9:
            recommendations.append("Investigate and fix failing tests to improve success rate")
        
        if avg_time > 5.0:
            recommendations.append("Optimize slow tests to reduce average execution time")
        
        if error_rate > 0.1:
            recommendations.append("Address high error rate through better error handling")
        
        if bottlenecks:
            recommendations.append("Focus on identified bottlenecks for maximum impact")
        
        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges")
        
        return recommendations
    
    def _assess_functional_risk(self, functional_results: Any) -> Dict[str, Any]:
        """Assess risk from functional testing results"""
        # This is a simplified implementation
        # In practice, you would analyze actual functional test results
        
        risk_factors = []
        risk_score = 0.0
        
        # Placeholder implementation
        if hasattr(functional_results, 'failed_tests'):
            failed_count = len(getattr(functional_results, 'failed_tests', []))
            if failed_count > 0:
                risk_factors.append({
                    'type': 'functional_failures',
                    'severity': 'medium',
                    'description': f"{failed_count} functional tests failed",
                    'impact': 'User experience degradation'
                })
                risk_score += failed_count * 0.1
        
        return {'factors': risk_factors, 'score': min(risk_score, 1.0)}
    
    def _assess_security_risk(self, security_results: Any) -> Dict[str, Any]:
        """Assess risk from security scan results"""
        risk_factors = []
        risk_score = 0.0
        
        # Placeholder implementation
        if hasattr(security_results, 'vulnerabilities'):
            vulnerabilities = getattr(security_results, 'vulnerabilities', [])
            critical_count = sum(1 for v in vulnerabilities if getattr(v, 'severity', '') == 'critical')
            high_count = sum(1 for v in vulnerabilities if getattr(v, 'severity', '') == 'high')
            
            if critical_count > 0:
                risk_factors.append({
                    'type': 'critical_vulnerabilities',
                    'severity': 'critical',
                    'description': f"{critical_count} critical security vulnerabilities",
                    'impact': 'Potential system compromise'
                })
                risk_score += critical_count * 0.3
            
            if high_count > 0:
                risk_factors.append({
                    'type': 'high_vulnerabilities',
                    'severity': 'high',
                    'description': f"{high_count} high-severity vulnerabilities",
                    'impact': 'Security breach risk'
                })
                risk_score += high_count * 0.2
        
        return {'factors': risk_factors, 'score': min(risk_score, 1.0)}
    
    def _assess_compliance_risk(self, compliance_results: Any) -> Dict[str, Any]:
        """Assess risk from compliance assessment results"""
        risk_factors = []
        risk_score = 0.0
        
        # Placeholder implementation
        if hasattr(compliance_results, 'failed_checks'):
            failed_checks = getattr(compliance_results, 'failed_checks', [])
            if failed_checks:
                risk_factors.append({
                    'type': 'compliance_violations',
                    'severity': 'high',
                    'description': f"{len(failed_checks)} compliance violations",
                    'impact': 'Regulatory penalties and legal issues'
                })
                risk_score += len(failed_checks) * 0.15
        
        return {'factors': risk_factors, 'score': min(risk_score, 1.0)}
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine overall risk level from score"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _generate_mitigation_strategies(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate mitigation strategies for identified risks"""
        strategies = []
        
        for factor in risk_factors:
            factor_type = factor.get('type', '')
            
            if 'vulnerabilities' in factor_type:
                strategies.append("Implement security patches and updates immediately")
                strategies.append("Conduct regular security assessments")
            elif 'compliance' in factor_type:
                strategies.append("Develop compliance remediation plan")
                strategies.append("Implement compliance monitoring controls")
            elif 'functional' in factor_type:
                strategies.append("Prioritize fixing critical functional issues")
                strategies.append("Improve test coverage and quality")
        
        # Remove duplicates
        return list(set(strategies))
    
    def _generate_priority_actions(
        self,
        risk_factors: List[Dict[str, Any]],
        overall_risk: RiskLevel
    ) -> List[str]:
        """Generate priority actions based on risk assessment"""
        actions = []
        
        if overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            actions.append("Immediate executive review and action required")
            actions.append("Halt deployment until critical issues are resolved")
        
        # Sort risk factors by severity
        critical_factors = [f for f in risk_factors if f.get('severity') == 'critical']
        high_factors = [f for f in risk_factors if f.get('severity') == 'high']
        
        if critical_factors:
            actions.append(f"Address {len(critical_factors)} critical risk factors immediately")
        
        if high_factors:
            actions.append(f"Plan remediation for {len(high_factors)} high-risk factors")
        
        return actions
    
    def _calculate_test_coverage(self, functional_results: Any) -> float:
        """Calculate test coverage percentage"""
        # Placeholder implementation
        if hasattr(functional_results, 'coverage'):
            return getattr(functional_results, 'coverage', 0.0)
        return 0.75  # Default assumption
    
    def _calculate_code_quality(self, functional_results: Any) -> float:
        """Calculate code quality score"""
        # Placeholder implementation
        return 0.8  # Default assumption
    
    def _calculate_security_posture(self, security_results: Any) -> float:
        """Calculate security posture score"""
        if not security_results:
            return 0.5
        
        # Simplified calculation based on vulnerabilities
        if hasattr(security_results, 'vulnerabilities'):
            vulnerabilities = getattr(security_results, 'vulnerabilities', [])
            if not vulnerabilities:
                return 1.0
            
            # Deduct points based on vulnerability severity
            score = 1.0
            for vuln in vulnerabilities:
                severity = getattr(vuln, 'severity', 'low')
                if severity == 'critical':
                    score -= 0.2
                elif severity == 'high':
                    score -= 0.1
                elif severity == 'medium':
                    score -= 0.05
            
            return max(0.0, score)
        
        return 0.7  # Default assumption
    
    def _calculate_compliance_level(self, compliance_results: Any) -> float:
        """Calculate compliance level score"""
        if not compliance_results:
            return 0.5
        
        # Simplified calculation
        if hasattr(compliance_results, 'passed_checks') and hasattr(compliance_results, 'total_checks'):
            passed = getattr(compliance_results, 'passed_checks', 0)
            total = getattr(compliance_results, 'total_checks', 1)
            return passed / total if total > 0 else 0.0
        
        return 0.8  # Default assumption
    
    def _calculate_defect_density(self, functional_results: Any) -> float:
        """Calculate defect density (defects per KLOC)"""
        # Placeholder implementation
        return 2.5  # Default assumption: 2.5 defects per 1000 lines of code
    
    def _calculate_technical_debt(self, functional_results: Any, security_results: Any) -> float:
        """Calculate technical debt score"""
        # Simplified calculation combining various factors
        debt_score = 0.0
        
        # Add debt from failed tests
        if hasattr(functional_results, 'failed_tests'):
            failed_count = len(getattr(functional_results, 'failed_tests', []))
            debt_score += failed_count * 0.1
        
        # Add debt from security vulnerabilities
        if hasattr(security_results, 'vulnerabilities'):
            vuln_count = len(getattr(security_results, 'vulnerabilities', []))
            debt_score += vuln_count * 0.05
        
        return min(debt_score, 1.0)
    
    def _calculate_maintainability_index(
        self,
        code_quality: float,
        technical_debt: float,
        test_coverage: float
    ) -> float:
        """Calculate maintainability index"""
        # Simplified calculation
        # Higher code quality and test coverage increase maintainability
        # Higher technical debt decreases maintainability
        
        maintainability = (code_quality * 0.4 + test_coverage * 0.4 + (1 - technical_debt) * 0.2)
        return max(0.0, min(1.0, maintainability))
    
    def _calculate_overall_quality_score(
        self,
        test_coverage: float,
        code_quality: float,
        security_posture: float,
        compliance_level: float
    ) -> float:
        """Calculate overall quality score"""
        # Weighted average of all quality metrics
        weights = {
            'test_coverage': 0.25,
            'code_quality': 0.25,
            'security_posture': 0.3,
            'compliance_level': 0.2
        }
        
        quality_score = (
            test_coverage * weights['test_coverage'] +
            code_quality * weights['code_quality'] +
            security_posture * weights['security_posture'] +
            compliance_level * weights['compliance_level']
        )
        
        return quality_score
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.9:
            return "very strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very weak"
    
    def _generate_correlation_insights(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from correlation analysis"""
        insights = []
        
        for corr in correlations:
            metric1 = corr['metric1']
            metric2 = corr['metric2']
            strength = corr['strength']
            direction = corr['direction']
            
            insights.append(
                f"{strength.title()} {direction} correlation between {metric1} and {metric2}"
            )
        
        if not insights:
            insights.append("No significant correlations found between metrics")
        
        return insights
    
    def _forecast_metric(self, values: List[float], forecast_days: int) -> float:
        """Forecast metric value using simple trend analysis"""
        if len(values) < 2:
            return values[0] if values else 0.0
        
        # Simple linear extrapolation
        recent_values = values[-min(5, len(values)):]  # Use last 5 values
        trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
        
        # Project trend forward
        forecast = values[-1] + trend * (forecast_days / 7)  # Assuming weekly data points
        
        return forecast
    
    def _calculate_confidence_interval(
        self,
        values: List[float],
        prediction: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""
        if len(values) < 3:
            margin = abs(prediction) * 0.2  # 20% margin
            return (prediction - margin, prediction + margin)
        
        # Calculate standard error
        std_dev = statistics.stdev(values)
        margin = 1.96 * std_dev  # 95% confidence interval
        
        return (prediction - margin, prediction + margin)
    
    def _forecast_risk(self, metric: str, values: List[float], prediction: float) -> Optional[Dict[str, Any]]:
        """Forecast risk based on metric prediction"""
        if not values:
            return None
        
        current_value = values[-1]
        change = prediction - current_value
        
        # Determine if this represents a risk
        risk_threshold = 0.1  # 10% change threshold
        
        if abs(change / current_value) > risk_threshold:
            return {
                'metric': metric,
                'risk_type': 'degradation' if change < 0 else 'improvement',
                'magnitude': abs(change / current_value),
                'description': f"{metric} predicted to {'decrease' if change < 0 else 'increase'} by {abs(change/current_value)*100:.1f}%"
            }
        
        return None
    
    def _generate_predictive_recommendations(
        self,
        predictions: List[Dict[str, Any]],
        risk_forecasts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on predictions"""
        recommendations = []
        
        # Analyze predictions for concerning trends
        for prediction in predictions:
            metric = prediction['metric']
            current = prediction['current_value']
            predicted = prediction['predicted_value']
            
            if predicted < current * 0.9:  # More than 10% decline
                recommendations.append(f"Take proactive action to prevent {metric} degradation")
        
        # Analyze risk forecasts
        high_risk_forecasts = [rf for rf in risk_forecasts if rf.get('magnitude', 0) > 0.2]
        
        if high_risk_forecasts:
            recommendations.append("Address high-risk forecast areas immediately")
        
        if not recommendations:
            recommendations.append("Continue current practices - trends are stable")
        
        return recommendations
    
    def _extract_test_results(self, functional_results: Any) -> List[Dict[str, Any]]:
        """Extract test results in expected format"""
        # This is a placeholder implementation
        # In practice, you would extract actual test result data
        
        if hasattr(functional_results, 'test_results'):
            return getattr(functional_results, 'test_results', [])
        
        # Return mock data for demonstration
        return [
            {'execution_time': 1.5, 'status': 'passed', 'domain': 'web'},
            {'execution_time': 2.1, 'status': 'failed', 'domain': 'api'},
            {'execution_time': 0.8, 'status': 'passed', 'domain': 'mobile'}
        ]
    
    def _extract_metrics_for_correlation(self, historical_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract metrics data for correlation analysis"""
        metrics_data = {}
        
        # Common metrics to analyze
        metric_names = ['test_pass_rate', 'security_score', 'compliance_score', 'performance_score']
        
        for metric in metric_names:
            values = []
            for data_point in historical_data:
                if metric in data_point:
                    try:
                        values.append(float(data_point[metric]))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) >= 3:  # Need at least 3 points for correlation
                metrics_data[metric] = values
        
        return metrics_data
    
    def _generate_analytics_summary(
        self,
        trend_analysis: Optional[List[TrendAnalysis]],
        performance_metrics: Optional[PerformanceMetrics],
        risk_assessment: Optional[RiskAssessment],
        quality_metrics: Optional[QualityMetrics],
        correlation_analysis: Optional[CorrelationAnalysis],
        predictive_insights: Optional[PredictiveInsights]
    ) -> str:
        """Generate comprehensive analytics summary"""
        
        summary_parts = []
        
        # Overall quality assessment
        if quality_metrics:
            quality_score = quality_metrics.quality_score
            if quality_score >= 0.8:
                summary_parts.append("Overall quality is excellent")
            elif quality_score >= 0.6:
                summary_parts.append("Overall quality is good with room for improvement")
            else:
                summary_parts.append("Overall quality needs significant improvement")
        
        # Risk assessment summary
        if risk_assessment:
            risk_level = risk_assessment.overall_risk_level
            summary_parts.append(f"Overall risk level is {risk_level.value}")
        
        # Performance summary
        if performance_metrics:
            perf_score = performance_metrics.performance_score
            if perf_score >= 80:
                summary_parts.append("Performance metrics are strong")
            elif perf_score >= 60:
                summary_parts.append("Performance is acceptable but could be optimized")
            else:
                summary_parts.append("Performance issues require immediate attention")
        
        # Trend summary
        if trend_analysis:
            improving_trends = [t for t in trend_analysis if t.direction == TrendDirection.IMPROVING]
            declining_trends = [t for t in trend_analysis if t.direction == TrendDirection.DECLINING]
            
            if improving_trends:
                summary_parts.append(f"{len(improving_trends)} metrics show positive trends")
            if declining_trends:
                summary_parts.append(f"{len(declining_trends)} metrics show concerning declines")
        
        # Predictive insights summary
        if predictive_insights and predictive_insights.risk_forecasts:
            high_risk_forecasts = [rf for rf in predictive_insights.risk_forecasts if rf.get('magnitude', 0) > 0.2]
            if high_risk_forecasts:
                summary_parts.append(f"{len(high_risk_forecasts)} metrics forecast high risk")
        
        return ". ".join(summary_parts) + "." if summary_parts else "Analytics completed successfully."
    
    def _calculate_overall_confidence(
        self,
        trend_analysis: Optional[List[TrendAnalysis]],
        performance_metrics: Optional[PerformanceMetrics],
        risk_assessment: Optional[RiskAssessment],
        quality_metrics: Optional[QualityMetrics]
    ) -> float:
        """Calculate overall confidence in analytics results"""
        
        confidence_scores = []
        
        # Trend analysis confidence
        if trend_analysis:
            trend_confidences = [t.confidence_score for t in trend_analysis]
            if trend_confidences:
                confidence_scores.append(statistics.mean(trend_confidences))
        
        # Performance metrics confidence (based on data availability)
        if performance_metrics:
            confidence_scores.append(0.8)  # High confidence in performance calculations
        
        # Risk assessment confidence (based on data completeness)
        if risk_assessment:
            confidence_scores.append(0.7)  # Moderate confidence in risk assessment
        
        # Quality metrics confidence
        if quality_metrics:
            confidence_scores.append(0.75)  # Good confidence in quality calculations
        
        return statistics.mean(confidence_scores) if confidence_scores else 0.5


# Utility functions for analytics

def analyze_test_trends(
    historical_data: List[Dict[str, Any]],
    metrics: Optional[List[str]] = None
) -> List[TrendAnalysis]:
    """Analyze trends in test metrics"""
    
    engine = AnalyticsEngine()
    default_metrics = ['test_pass_rate', 'execution_time', 'coverage']
    
    return engine.analyze_trends(
        historical_data=historical_data,
        metrics=metrics or default_metrics
    )


def assess_overall_risk(
    functional_results: Optional[Any] = None,
    security_results: Optional[Any] = None,
    compliance_results: Optional[Any] = None
) -> RiskAssessment:
    """Assess overall risk across all domains"""
    
    engine = AnalyticsEngine()
    return engine.assess_risk(
        functional_results=functional_results,
        security_results=security_results,
        compliance_results=compliance_results
    )


def generate_quality_report(
    functional_results: Optional[Any] = None,
    security_results: Optional[Any] = None,
    compliance_results: Optional[Any] = None,
    historical_data: Optional[List[Dict[str, Any]]] = None
) -> QualityMetrics:
    """Generate comprehensive quality metrics report"""
    
    engine = AnalyticsEngine()
    return engine.analyze_quality_metrics(
        functional_results=functional_results,
        security_results=security_results,
        compliance_results=compliance_results,
        historical_data=historical_data
    )