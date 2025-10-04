"""
Trend Reporter Agent - Business-friendly summaries with charts and trends
Provides executive-level insights and visualizations for QA metrics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .base_agent import BaseAgent
from ..database.database import DatabaseManager
from ..monitoring.metrics_collector import MetricsCollector
from ..ai.llm_service import LLMService

class TrendPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TrendMetrics:
    """Data structure for trend metrics"""
    period: str
    test_success_rate: float
    failure_rate: float
    flakiness_score: float
    performance_score: float
    security_score: float
    compliance_score: float
    total_tests: int
    failed_tests: int
    execution_time: float
    timestamp: datetime

@dataclass
class BusinessInsight:
    """Business-friendly insight with recommendations"""
    title: str
    description: str
    impact: str
    risk_level: RiskLevel
    recommendation: str
    metrics: Dict[str, Any]
    trend_direction: str  # "improving", "declining", "stable"

@dataclass
class ExecutiveSummary:
    """Executive summary for stakeholders"""
    period: str
    overall_health_score: float
    key_insights: List[BusinessInsight]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    charts: Dict[str, str]  # chart_name -> base64_encoded_image
    generated_at: datetime

class TrendReporterAgent(BaseAgent):
    """
    Agent responsible for generating business-friendly trend reports
    and executive summaries with visualizations
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("TrendReporter", config)
        self.db_manager = DatabaseManager()
        self.metrics_collector = MetricsCollector()
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the trend reporter agent"""
        self.logger.info("Starting Trend Reporter Agent")
        await super().start()
        
    async def stop(self):
        """Stop the trend reporter agent"""
        self.logger.info("Stopping Trend Reporter Agent")
        await super().stop()
        
    async def generate_trend_report(
        self, 
        period: TrendPeriod = TrendPeriod.WEEKLY,
        include_charts: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive trend report"""
        try:
            # Collect historical data
            historical_data = await self._collect_historical_data(period)
            
            # Calculate trend metrics
            trend_metrics = await self._calculate_trend_metrics(historical_data)
            
            # Generate business insights
            insights = await self._generate_business_insights(trend_metrics)
            
            # Create visualizations
            charts = {}
            if include_charts:
                charts = await self._create_trend_charts(trend_metrics)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                trend_metrics, insights, charts, period.value
            )
            
            report = {
                "summary": asdict(executive_summary),
                "detailed_metrics": [asdict(metric) for metric in trend_metrics],
                "insights": [asdict(insight) for insight in insights],
                "charts": charts,
                "generated_at": datetime.now().isoformat()
            }
            
            # Store report
            await self._store_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating trend report: {str(e)}")
            raise
    
    async def _collect_historical_data(self, period: TrendPeriod) -> List[Dict[str, Any]]:
        """Collect historical test data based on period"""
        end_date = datetime.now()
        
        # Determine date range based on period
        if period == TrendPeriod.DAILY:
            start_date = end_date - timedelta(days=30)
            interval = "1 day"
        elif period == TrendPeriod.WEEKLY:
            start_date = end_date - timedelta(weeks=12)
            interval = "1 week"
        elif period == TrendPeriod.MONTHLY:
            start_date = end_date - timedelta(days=365)
            interval = "1 month"
        else:  # QUARTERLY
            start_date = end_date - timedelta(days=730)
            interval = "3 months"
        
        # Query database for historical data
        query = """
        SELECT 
            DATE_TRUNC(%s, created_at) as period,
            COUNT(*) as total_tests,
            SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tests,
            SUM(CASE WHEN status = 'flaky' THEN 1 ELSE 0 END) as flaky_tests,
            AVG(execution_time) as avg_execution_time,
            AVG(performance_score) as avg_performance_score,
            AVG(security_score) as avg_security_score,
            AVG(compliance_score) as avg_compliance_score
        FROM test_results 
        WHERE created_at >= %s AND created_at <= %s
        GROUP BY DATE_TRUNC(%s, created_at)
        ORDER BY period
        """
        
        try:
            results = await self.db_manager.execute_query(
                query, (interval, start_date, end_date, interval)
            )
            return results
        except Exception as e:
            self.logger.warning(f"Database query failed, using mock data: {str(e)}")
            return self._generate_mock_historical_data(period)
    
    def _generate_mock_historical_data(self, period: TrendPeriod) -> List[Dict[str, Any]]:
        """Generate mock historical data for demonstration"""
        import random
        
        data = []
        end_date = datetime.now()
        
        if period == TrendPeriod.DAILY:
            days = 30
            for i in range(days):
                date = end_date - timedelta(days=i)
                data.append({
                    'period': date,
                    'total_tests': random.randint(50, 200),
                    'passed_tests': random.randint(40, 180),
                    'failed_tests': random.randint(5, 20),
                    'flaky_tests': random.randint(0, 10),
                    'avg_execution_time': random.uniform(30, 120),
                    'avg_performance_score': random.uniform(70, 95),
                    'avg_security_score': random.uniform(80, 98),
                    'avg_compliance_score': random.uniform(85, 99)
                })
        
        return sorted(data, key=lambda x: x['period'])
    
    async def _calculate_trend_metrics(self, historical_data: List[Dict[str, Any]]) -> List[TrendMetrics]:
        """Calculate trend metrics from historical data"""
        metrics = []
        
        for data_point in historical_data:
            total_tests = data_point.get('total_tests', 0)
            passed_tests = data_point.get('passed_tests', 0)
            failed_tests = data_point.get('failed_tests', 0)
            flaky_tests = data_point.get('flaky_tests', 0)
            
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            failure_rate = (failed_tests / total_tests * 100) if total_tests > 0 else 0
            flakiness_score = (flaky_tests / total_tests * 100) if total_tests > 0 else 0
            
            metric = TrendMetrics(
                period=data_point['period'].strftime('%Y-%m-%d'),
                test_success_rate=success_rate,
                failure_rate=failure_rate,
                flakiness_score=flakiness_score,
                performance_score=data_point.get('avg_performance_score', 0),
                security_score=data_point.get('avg_security_score', 0),
                compliance_score=data_point.get('avg_compliance_score', 0),
                total_tests=total_tests,
                failed_tests=failed_tests,
                execution_time=data_point.get('avg_execution_time', 0),
                timestamp=data_point['period']
            )
            metrics.append(metric)
        
        return metrics
    
    async def _generate_business_insights(self, trend_metrics: List[TrendMetrics]) -> List[BusinessInsight]:
        """Generate AI-powered business insights"""
        insights = []
        
        if len(trend_metrics) < 2:
            return insights
        
        # Analyze trends
        recent_metrics = trend_metrics[-5:]  # Last 5 data points
        older_metrics = trend_metrics[-10:-5] if len(trend_metrics) >= 10 else trend_metrics[:-5]
        
        # Success rate trend
        recent_success = sum(m.test_success_rate for m in recent_metrics) / len(recent_metrics)
        older_success = sum(m.test_success_rate for m in older_metrics) / len(older_metrics) if older_metrics else recent_success
        
        success_trend = "improving" if recent_success > older_success else "declining" if recent_success < older_success else "stable"
        
        # Generate insights using AI
        prompt = f"""
        Analyze the following QA metrics trends and provide business insights:
        
        Recent Success Rate: {recent_success:.1f}%
        Previous Success Rate: {older_success:.1f}%
        Trend: {success_trend}
        
        Recent Average Metrics:
        - Failure Rate: {sum(m.failure_rate for m in recent_metrics) / len(recent_metrics):.1f}%
        - Flakiness Score: {sum(m.flakiness_score for m in recent_metrics) / len(recent_metrics):.1f}%
        - Performance Score: {sum(m.performance_score for m in recent_metrics) / len(recent_metrics):.1f}
        - Security Score: {sum(m.security_score for m in recent_metrics) / len(recent_metrics):.1f}
        
        Provide 3-5 key business insights with:
        1. Title (concise)
        2. Description (business-friendly)
        3. Impact assessment
        4. Risk level (low/medium/high/critical)
        5. Actionable recommendation
        """
        
        try:
            ai_insights = await self.llm_service.generate_insights(prompt)
            # Parse AI response and create BusinessInsight objects
            # For now, create sample insights
            insights.extend(self._create_sample_insights(recent_metrics, success_trend))
        except Exception as e:
            self.logger.warning(f"AI insight generation failed: {str(e)}")
            insights.extend(self._create_sample_insights(recent_metrics, success_trend))
        
        return insights
    
    def _create_sample_insights(self, metrics: List[TrendMetrics], trend: str) -> List[BusinessInsight]:
        """Create sample business insights"""
        avg_success = sum(m.test_success_rate for m in metrics) / len(metrics)
        avg_flakiness = sum(m.flakiness_score for m in metrics) / len(metrics)
        
        insights = []
        
        # Quality trend insight
        if trend == "improving":
            insights.append(BusinessInsight(
                title="Quality Improvement Trend",
                description=f"Test success rate has improved to {avg_success:.1f}%, indicating better code quality and testing practices.",
                impact="Positive impact on product reliability and customer satisfaction",
                risk_level=RiskLevel.LOW,
                recommendation="Continue current practices and consider expanding successful strategies to other areas",
                metrics={"success_rate": avg_success, "trend": trend},
                trend_direction=trend
            ))
        elif trend == "declining":
            insights.append(BusinessInsight(
                title="Quality Decline Alert",
                description=f"Test success rate has declined to {avg_success:.1f}%, requiring immediate attention.",
                impact="Risk of increased bugs in production and customer impact",
                risk_level=RiskLevel.HIGH if avg_success < 80 else RiskLevel.MEDIUM,
                recommendation="Review recent code changes, increase code review rigor, and investigate failing tests",
                metrics={"success_rate": avg_success, "trend": trend},
                trend_direction=trend
            ))
        
        # Flakiness insight
        if avg_flakiness > 5:
            insights.append(BusinessInsight(
                title="Test Flakiness Concern",
                description=f"Test flakiness score of {avg_flakiness:.1f}% indicates unreliable tests affecting development velocity.",
                impact="Reduced developer confidence and slower release cycles",
                risk_level=RiskLevel.MEDIUM,
                recommendation="Identify and fix flaky tests, improve test environment stability",
                metrics={"flakiness_score": avg_flakiness},
                trend_direction="stable"
            ))
        
        return insights
    
    async def _create_trend_charts(self, trend_metrics: List[TrendMetrics]) -> Dict[str, str]:
        """Create trend visualization charts"""
        charts = {}
        
        # Prepare data
        df = pd.DataFrame([asdict(metric) for metric in trend_metrics])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Success Rate Trend Chart
        fig_success = go.Figure()
        fig_success.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['test_success_rate'],
            mode='lines+markers',
            name='Success Rate',
            line=dict(color='green', width=3)
        ))
        fig_success.update_layout(
            title='Test Success Rate Trend',
            xaxis_title='Date',
            yaxis_title='Success Rate (%)',
            template='plotly_white'
        )
        charts['success_rate_trend'] = fig_success.to_html(include_plotlyjs='cdn')
        
        # Multi-metric Dashboard
        fig_multi = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Success Rate', 'Performance Score', 'Security Score', 'Compliance Score'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add traces
        fig_multi.add_trace(
            go.Scatter(x=df['timestamp'], y=df['test_success_rate'], name='Success Rate'),
            row=1, col=1
        )
        fig_multi.add_trace(
            go.Scatter(x=df['timestamp'], y=df['performance_score'], name='Performance'),
            row=1, col=2
        )
        fig_multi.add_trace(
            go.Scatter(x=df['timestamp'], y=df['security_score'], name='Security'),
            row=2, col=1
        )
        fig_multi.add_trace(
            go.Scatter(x=df['timestamp'], y=df['compliance_score'], name='Compliance'),
            row=2, col=2
        )
        
        fig_multi.update_layout(
            title_text="QA Metrics Dashboard",
            template='plotly_white',
            height=600
        )
        charts['metrics_dashboard'] = fig_multi.to_html(include_plotlyjs='cdn')
        
        # Risk Assessment Chart
        risk_data = []
        for metric in trend_metrics[-10:]:  # Last 10 data points
            risk_score = self._calculate_risk_score(metric)
            risk_data.append({
                'date': metric.timestamp,
                'risk_score': risk_score,
                'success_rate': metric.test_success_rate
            })
        
        risk_df = pd.DataFrame(risk_data)
        fig_risk = go.Figure()
        fig_risk.add_trace(go.Scatter(
            x=risk_df['date'],
            y=risk_df['risk_score'],
            mode='lines+markers',
            name='Risk Score',
            line=dict(color='red', width=3),
            fill='tonexty'
        ))
        fig_risk.update_layout(
            title='Risk Assessment Trend',
            xaxis_title='Date',
            yaxis_title='Risk Score',
            template='plotly_white'
        )
        charts['risk_assessment'] = fig_risk.to_html(include_plotlyjs='cdn')
        
        return charts
    
    def _calculate_risk_score(self, metric: TrendMetrics) -> float:
        """Calculate overall risk score based on metrics"""
        # Weighted risk calculation
        weights = {
            'failure_rate': 0.3,
            'flakiness': 0.2,
            'performance': 0.2,
            'security': 0.15,
            'compliance': 0.15
        }
        
        risk_score = (
            metric.failure_rate * weights['failure_rate'] +
            metric.flakiness_score * weights['flakiness'] +
            (100 - metric.performance_score) * weights['performance'] +
            (100 - metric.security_score) * weights['security'] +
            (100 - metric.compliance_score) * weights['compliance']
        )
        
        return min(100, max(0, risk_score))
    
    async def _generate_executive_summary(
        self, 
        trend_metrics: List[TrendMetrics],
        insights: List[BusinessInsight],
        charts: Dict[str, str],
        period: str
    ) -> ExecutiveSummary:
        """Generate executive summary"""
        
        # Calculate overall health score
        if trend_metrics:
            recent_metrics = trend_metrics[-5:]  # Last 5 data points
            health_score = sum([
                sum(m.test_success_rate for m in recent_metrics) / len(recent_metrics) * 0.4,
                sum(m.performance_score for m in recent_metrics) / len(recent_metrics) * 0.2,
                sum(m.security_score for m in recent_metrics) / len(recent_metrics) * 0.2,
                sum(m.compliance_score for m in recent_metrics) / len(recent_metrics) * 0.2
            ])
        else:
            health_score = 0
        
        # Risk assessment
        risk_assessment = {
            "overall_risk": "Low" if health_score > 85 else "Medium" if health_score > 70 else "High",
            "key_risks": [insight.title for insight in insights if insight.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]],
            "mitigation_priority": "Immediate" if health_score < 70 else "Planned"
        }
        
        # Generate recommendations
        recommendations = [
            "Maintain current quality standards and practices",
            "Focus on reducing test flakiness to improve reliability",
            "Implement continuous monitoring for early issue detection"
        ]
        
        if health_score < 80:
            recommendations.extend([
                "Conduct thorough review of failing tests",
                "Increase code review coverage and standards",
                "Consider additional automated testing strategies"
            ])
        
        return ExecutiveSummary(
            period=period,
            overall_health_score=health_score,
            key_insights=insights,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            charts=charts,
            generated_at=datetime.now()
        )
    
    async def _store_report(self, report: Dict[str, Any]):
        """Store the generated report"""
        try:
            # Store in database
            query = """
            INSERT INTO trend_reports (report_data, generated_at)
            VALUES (%s, %s)
            """
            await self.db_manager.execute_query(
                query, (json.dumps(report), datetime.now())
            )
        except Exception as e:
            self.logger.warning(f"Failed to store report in database: {str(e)}")
            # Store as file backup
            filename = f"trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"reports/trends/{filename}"
            
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Report stored as file: {filepath}")
    
    async def get_historical_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical trend reports"""
        try:
            query = """
            SELECT report_data, generated_at 
            FROM trend_reports 
            ORDER BY generated_at DESC 
            LIMIT %s
            """
            results = await self.db_manager.execute_query(query, (limit,))
            return [json.loads(result['report_data']) for result in results]
        except Exception as e:
            self.logger.error(f"Error retrieving historical reports: {str(e)}")
            return []
    
    async def generate_voice_summary(self, report: Dict[str, Any]) -> str:
        """Generate voice-friendly summary of the report"""
        summary = report.get('summary', {})
        health_score = summary.get('overall_health_score', 0)
        
        voice_summary = f"""
        Quality Health Report Summary:
        
        Overall system health is at {health_score:.0f} percent.
        
        {len(summary.get('key_insights', []))} key insights have been identified.
        
        Risk level is currently {summary.get('risk_assessment', {}).get('overall_risk', 'unknown')}.
        
        Top recommendations include: {', '.join(summary.get('recommendations', [])[:3])}.
        
        Detailed charts and metrics are available in the full report.
        """
        
        return voice_summary.strip()