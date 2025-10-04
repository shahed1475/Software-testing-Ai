"""
Business Dashboard - Interactive visualizations for stakeholders
Provides business-friendly QA insights with charts, KPIs, and trends
"""

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
import plotly.io as pio

from ..agents.executive_summary_agent import ExecutiveSummaryAgent, StakeholderLevel
from ..agents.trend_reporter_agent import TrendReporterAgent
from ..analytics.historical_analyzer import HistoricalAnalyzer
from ..database.database import DatabaseManager

class DashboardType(Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"

class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"

class TimeRange(Enum):
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    LAST_YEAR = "1y"

@dataclass
class KPIWidget:
    """KPI widget configuration"""
    title: str
    value: float
    unit: str
    trend: float  # Percentage change
    target: Optional[float]
    color: str
    icon: str
    description: str

@dataclass
class ChartWidget:
    """Chart widget configuration"""
    title: str
    chart_type: ChartType
    data: Dict[str, Any]
    config: Dict[str, Any]
    height: int
    width: int

@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    dashboard_type: DashboardType
    title: str
    description: str
    kpis: List[KPIWidget]
    charts: List[ChartWidget]
    filters: Dict[str, Any]
    refresh_interval: int  # seconds
    stakeholder_level: StakeholderLevel

class BusinessDashboard:
    """
    Business-friendly dashboard generator
    Creates interactive visualizations for different stakeholder levels
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        
        # Initialize agents
        self.executive_agent = ExecutiveSummaryAgent({})
        self.trend_reporter = TrendReporterAgent({})
        self.historical_analyzer = HistoricalAnalyzer({})
        
        # Chart themes
        self.themes = {
            "executive": {
                "primary_color": "#1f77b4",
                "secondary_color": "#ff7f0e",
                "background": "#ffffff",
                "text_color": "#2c3e50",
                "font_family": "Arial, sans-serif"
            },
            "operational": {
                "primary_color": "#2ca02c",
                "secondary_color": "#d62728",
                "background": "#f8f9fa",
                "text_color": "#495057",
                "font_family": "Arial, sans-serif"
            },
            "technical": {
                "primary_color": "#9467bd",
                "secondary_color": "#8c564b",
                "background": "#ffffff",
                "text_color": "#212529",
                "font_family": "Consolas, monospace"
            }
        }
    
    async def generate_dashboard(
        self,
        dashboard_type: DashboardType,
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange = TimeRange.LAST_7D,
        filters: Optional[Dict[str, Any]] = None
    ) -> DashboardLayout:
        """Generate complete dashboard layout"""
        
        try:
            self.logger.info(f"Generating {dashboard_type.value} dashboard for {stakeholder_level.value}")
            
            # Get base data
            dashboard_data = await self._collect_dashboard_data(time_range, filters)
            
            # Generate dashboard based on type
            if dashboard_type == DashboardType.EXECUTIVE:
                return await self._generate_executive_dashboard(dashboard_data, stakeholder_level, time_range)
            elif dashboard_type == DashboardType.OPERATIONAL:
                return await self._generate_operational_dashboard(dashboard_data, stakeholder_level, time_range)
            elif dashboard_type == DashboardType.TECHNICAL:
                return await self._generate_technical_dashboard(dashboard_data, stakeholder_level, time_range)
            elif dashboard_type == DashboardType.COMPLIANCE:
                return await self._generate_compliance_dashboard(dashboard_data, stakeholder_level, time_range)
            elif dashboard_type == DashboardType.PERFORMANCE:
                return await self._generate_performance_dashboard(dashboard_data, stakeholder_level, time_range)
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard: {str(e)}")
            return self._create_error_dashboard(dashboard_type, str(e))
    
    async def _collect_dashboard_data(
        self,
        time_range: TimeRange,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Collect all data needed for dashboard"""
        
        # Get executive summary
        executive_summary = await self.executive_agent.generate_executive_summary()
        
        # Get trend data
        from ..agents.trend_reporter_agent import TrendPeriod
        period_mapping = {
            TimeRange.LAST_24H: TrendPeriod.DAILY,
            TimeRange.LAST_7D: TrendPeriod.WEEKLY,
            TimeRange.LAST_30D: TrendPeriod.MONTHLY,
            TimeRange.LAST_90D: TrendPeriod.MONTHLY,
            TimeRange.LAST_YEAR: TrendPeriod.MONTHLY
        }
        
        trend_data = await self.trend_reporter.generate_trend_report(
            period=period_mapping.get(time_range, TrendPeriod.WEEKLY)
        )
        
        # Get historical analysis
        historical_data = await self.historical_analyzer.analyze_historical_trends()
        
        # Generate mock time series data
        time_series_data = self._generate_time_series_data(time_range)
        
        return {
            "executive_summary": executive_summary,
            "trend_data": trend_data,
            "historical_data": historical_data,
            "time_series": time_series_data,
            "filters": filters or {},
            "generated_at": datetime.now()
        }
    
    def _generate_time_series_data(self, time_range: TimeRange) -> Dict[str, pd.DataFrame]:
        """Generate mock time series data for charts"""
        
        # Calculate date range
        end_date = datetime.now()
        days_mapping = {
            TimeRange.LAST_24H: 1,
            TimeRange.LAST_7D: 7,
            TimeRange.LAST_30D: 30,
            TimeRange.LAST_90D: 90,
            TimeRange.LAST_YEAR: 365
        }
        
        days = days_mapping.get(time_range, 7)
        start_date = end_date - timedelta(days=days)
        
        # Generate date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='H' if days <= 7 else 'D')
        
        # Generate mock data
        import numpy as np
        np.random.seed(42)  # For reproducible results
        
        data = {
            "test_success_rate": pd.DataFrame({
                "timestamp": date_range,
                "value": 85 + np.random.normal(0, 5, len(date_range)).cumsum() * 0.1
            }),
            "performance_score": pd.DataFrame({
                "timestamp": date_range,
                "value": 75 + np.random.normal(0, 3, len(date_range)).cumsum() * 0.05
            }),
            "defect_count": pd.DataFrame({
                "timestamp": date_range,
                "value": np.maximum(0, 10 + np.random.normal(0, 2, len(date_range)).cumsum() * 0.1)
            }),
            "coverage": pd.DataFrame({
                "timestamp": date_range,
                "value": np.clip(80 + np.random.normal(0, 2, len(date_range)).cumsum() * 0.05, 0, 100)
            })
        }
        
        return data
    
    async def _generate_executive_dashboard(
        self,
        data: Dict[str, Any],
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange
    ) -> DashboardLayout:
        """Generate executive dashboard"""
        
        executive_summary = data["executive_summary"]
        
        # KPIs for executives
        kpis = [
            KPIWidget(
                title="System Health",
                value=executive_summary.overall_health_score,
                unit="%",
                trend=2.5,
                target=95.0,
                color="#28a745" if executive_summary.overall_health_score > 90 else "#ffc107",
                icon="🏥",
                description="Overall system health and stability"
            ),
            KPIWidget(
                title="Risk Level",
                value=self._risk_to_numeric(executive_summary.risk_assessment.risk_level),
                unit="",
                trend=-0.5,
                target=1.0,
                color="#28a745" if self._risk_to_numeric(executive_summary.risk_assessment.risk_level) <= 2 else "#dc3545",
                icon="⚠️",
                description="Current system risk assessment"
            ),
            KPIWidget(
                title="Uptime",
                value=executive_summary.stability_metrics.uptime_percentage,
                unit="%",
                trend=0.1,
                target=99.9,
                color="#28a745",
                icon="⏱️",
                description="System availability and uptime"
            ),
            KPIWidget(
                title="Active Issues",
                value=len(executive_summary.alerts),
                unit="",
                trend=-2.0,
                target=0.0,
                color="#dc3545" if len(executive_summary.alerts) > 5 else "#28a745",
                icon="🚨",
                description="Number of active alerts and issues"
            )
        ]
        
        # Charts for executives
        charts = [
            await self._create_health_trend_chart(data["time_series"]),
            await self._create_risk_assessment_chart(executive_summary),
            await self._create_business_impact_chart(data["trend_data"]),
            await self._create_executive_summary_chart(executive_summary)
        ]
        
        return DashboardLayout(
            dashboard_type=DashboardType.EXECUTIVE,
            title="Executive QA Dashboard",
            description="High-level quality assurance insights for executive decision making",
            kpis=kpis,
            charts=charts,
            filters={"time_range": time_range.value, "stakeholder": stakeholder_level.value},
            refresh_interval=300,  # 5 minutes
            stakeholder_level=stakeholder_level
        )
    
    async def _generate_operational_dashboard(
        self,
        data: Dict[str, Any],
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange
    ) -> DashboardLayout:
        """Generate operational dashboard"""
        
        executive_summary = data["executive_summary"]
        
        # KPIs for operations
        kpis = [
            KPIWidget(
                title="Test Success Rate",
                value=92.5,
                unit="%",
                trend=1.2,
                target=95.0,
                color="#28a745",
                icon="✅",
                description="Percentage of tests passing"
            ),
            KPIWidget(
                title="MTTR",
                value=executive_summary.stability_metrics.mean_time_to_recovery,
                unit="min",
                trend=-5.0,
                target=30.0,
                color="#ffc107",
                icon="🔧",
                description="Mean time to recovery for incidents"
            ),
            KPIWidget(
                title="Deployment Frequency",
                value=12.0,
                unit="/week",
                trend=8.3,
                target=10.0,
                color="#28a745",
                icon="🚀",
                description="Number of deployments per week"
            ),
            KPIWidget(
                title="Test Coverage",
                value=87.3,
                unit="%",
                trend=2.1,
                target=90.0,
                color="#ffc107",
                icon="📊",
                description="Code coverage by automated tests"
            )
        ]
        
        # Charts for operations
        charts = [
            await self._create_test_results_chart(data["time_series"]),
            await self._create_deployment_pipeline_chart(data),
            await self._create_incident_timeline_chart(data),
            await self._create_performance_metrics_chart(data["time_series"])
        ]
        
        return DashboardLayout(
            dashboard_type=DashboardType.OPERATIONAL,
            title="Operational QA Dashboard",
            description="Operational metrics and monitoring for QA teams",
            kpis=kpis,
            charts=charts,
            filters={"time_range": time_range.value, "environment": "all"},
            refresh_interval=60,  # 1 minute
            stakeholder_level=stakeholder_level
        )
    
    async def _generate_technical_dashboard(
        self,
        data: Dict[str, Any],
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange
    ) -> DashboardLayout:
        """Generate technical dashboard"""
        
        # KPIs for technical teams
        kpis = [
            KPIWidget(
                title="Code Quality Score",
                value=8.7,
                unit="/10",
                trend=0.3,
                target=9.0,
                color="#28a745",
                icon="💻",
                description="Overall code quality assessment"
            ),
            KPIWidget(
                title="Technical Debt",
                value=23.5,
                unit="hours",
                trend=-2.1,
                target=20.0,
                color="#ffc107",
                icon="⚡",
                description="Estimated technical debt in hours"
            ),
            KPIWidget(
                title="Security Vulnerabilities",
                value=3.0,
                unit="",
                trend=-1.0,
                target=0.0,
                color="#dc3545",
                icon="🔒",
                description="Number of security vulnerabilities"
            ),
            KPIWidget(
                title="Performance Score",
                value=78.2,
                unit="%",
                trend=1.8,
                target=85.0,
                color="#ffc107",
                icon="⚡",
                description="Application performance score"
            )
        ]
        
        # Charts for technical teams
        charts = [
            await self._create_code_quality_chart(data),
            await self._create_security_scan_chart(data),
            await self._create_performance_analysis_chart(data["time_series"]),
            await self._create_test_automation_chart(data)
        ]
        
        return DashboardLayout(
            dashboard_type=DashboardType.TECHNICAL,
            title="Technical QA Dashboard",
            description="Detailed technical metrics for development teams",
            kpis=kpis,
            charts=charts,
            filters={"time_range": time_range.value, "component": "all", "environment": "all"},
            refresh_interval=30,  # 30 seconds
            stakeholder_level=stakeholder_level
        )
    
    async def _generate_compliance_dashboard(
        self,
        data: Dict[str, Any],
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange
    ) -> DashboardLayout:
        """Generate compliance dashboard"""
        
        # KPIs for compliance
        kpis = [
            KPIWidget(
                title="Compliance Score",
                value=94.2,
                unit="%",
                trend=1.5,
                target=95.0,
                color="#28a745",
                icon="📋",
                description="Overall compliance score"
            ),
            KPIWidget(
                title="Policy Violations",
                value=2.0,
                unit="",
                trend=-1.0,
                target=0.0,
                color="#ffc107",
                icon="⚖️",
                description="Number of policy violations"
            ),
            KPIWidget(
                title="Audit Readiness",
                value=87.5,
                unit="%",
                trend=3.2,
                target=90.0,
                color="#ffc107",
                icon="🔍",
                description="Readiness for compliance audits"
            ),
            KPIWidget(
                title="Data Privacy Score",
                value=96.8,
                unit="%",
                trend=0.5,
                target=95.0,
                color="#28a745",
                icon="🔐",
                description="Data privacy compliance score"
            )
        ]
        
        # Charts for compliance
        charts = [
            await self._create_compliance_overview_chart(data),
            await self._create_policy_violations_chart(data),
            await self._create_audit_trail_chart(data),
            await self._create_risk_heatmap_chart(data)
        ]
        
        return DashboardLayout(
            dashboard_type=DashboardType.COMPLIANCE,
            title="Compliance Dashboard",
            description="Regulatory compliance and policy adherence metrics",
            kpis=kpis,
            charts=charts,
            filters={"time_range": time_range.value, "regulation": "all"},
            refresh_interval=3600,  # 1 hour
            stakeholder_level=stakeholder_level
        )
    
    async def _generate_performance_dashboard(
        self,
        data: Dict[str, Any],
        stakeholder_level: StakeholderLevel,
        time_range: TimeRange
    ) -> DashboardLayout:
        """Generate performance dashboard"""
        
        # KPIs for performance
        kpis = [
            KPIWidget(
                title="Response Time",
                value=245.0,
                unit="ms",
                trend=-8.2,
                target=200.0,
                color="#ffc107",
                icon="⏱️",
                description="Average API response time"
            ),
            KPIWidget(
                title="Throughput",
                value=1250.0,
                unit="req/s",
                trend=12.5,
                target=1000.0,
                color="#28a745",
                icon="📈",
                description="Requests processed per second"
            ),
            KPIWidget(
                title="Error Rate",
                value=0.8,
                unit="%",
                trend=-0.3,
                target=1.0,
                color="#28a745",
                icon="❌",
                description="Percentage of failed requests"
            ),
            KPIWidget(
                title="Resource Usage",
                value=67.3,
                unit="%",
                trend=2.1,
                target=80.0,
                color="#28a745",
                icon="💾",
                description="Average system resource utilization"
            )
        ]
        
        # Charts for performance
        charts = [
            await self._create_response_time_chart(data["time_series"]),
            await self._create_throughput_chart(data["time_series"]),
            await self._create_error_rate_chart(data["time_series"]),
            await self._create_resource_usage_chart(data)
        ]
        
        return DashboardLayout(
            dashboard_type=DashboardType.PERFORMANCE,
            title="Performance Dashboard",
            description="Application and system performance metrics",
            kpis=kpis,
            charts=charts,
            filters={"time_range": time_range.value, "service": "all"},
            refresh_interval=30,  # 30 seconds
            stakeholder_level=stakeholder_level
        )
    
    # Chart creation methods
    async def _create_health_trend_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create health trend chart"""
        
        success_rate_data = time_series["test_success_rate"]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=success_rate_data["timestamp"],
            y=success_rate_data["value"],
            mode='lines+markers',
            name='Health Score',
            line=dict(color='#28a745', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_hline(y=95, line_dash="dash", line_color="red", 
                     annotation_text="Target: 95%")
        
        fig.update_layout(
            title="System Health Trend",
            xaxis_title="Time",
            yaxis_title="Health Score (%)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="System Health Trend",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=12
        )
    
    async def _create_risk_assessment_chart(self, executive_summary) -> ChartWidget:
        """Create risk assessment chart"""
        
        risk_categories = ["Security", "Performance", "Compliance", "Operational", "Technical"]
        risk_scores = [75, 85, 92, 88, 80]  # Mock data
        
        fig = go.Figure(data=go.Bar(
            x=risk_categories,
            y=risk_scores,
            marker_color=['#dc3545' if score < 80 else '#ffc107' if score < 90 else '#28a745' 
                         for score in risk_scores]
        ))
        
        fig.update_layout(
            title="Risk Assessment by Category",
            xaxis_title="Risk Category",
            yaxis_title="Risk Score (%)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Risk Assessment",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_business_impact_chart(self, trend_data: Dict[str, Any]) -> ChartWidget:
        """Create business impact chart"""
        
        categories = ["Revenue Impact", "Customer Satisfaction", "Operational Efficiency", "Brand Reputation"]
        values = [85, 92, 78, 88]  # Mock data
        
        fig = go.Figure(data=go.Pie(
            labels=categories,
            values=values,
            hole=0.4,
            marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        ))
        
        fig.update_layout(
            title="Business Impact Assessment",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Business Impact",
            chart_type=ChartType.PIE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_executive_summary_chart(self, executive_summary) -> ChartWidget:
        """Create executive summary gauge chart"""
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=executive_summary.overall_health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Health Score"},
            delta={'reference': 95},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Health Score Gauge",
            chart_type=ChartType.GAUGE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": False},
            height=400,
            width=6
        )
    
    async def _create_test_results_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create test results chart"""
        
        success_data = time_series["test_success_rate"]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Test Success Rate', 'Test Coverage'),
            vertical_spacing=0.1
        )
        
        # Success rate
        fig.add_trace(
            go.Scatter(
                x=success_data["timestamp"],
                y=success_data["value"],
                mode='lines+markers',
                name='Success Rate',
                line=dict(color='#28a745')
            ),
            row=1, col=1
        )
        
        # Coverage (mock data)
        coverage_data = time_series["coverage"]
        fig.add_trace(
            go.Scatter(
                x=coverage_data["timestamp"],
                y=coverage_data["value"],
                mode='lines+markers',
                name='Coverage',
                line=dict(color='#1f77b4')
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Test Results Overview",
            template="plotly_white",
            height=500
        )
        
        return ChartWidget(
            title="Test Results",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=500,
            width=12
        )
    
    async def _create_deployment_pipeline_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create deployment pipeline chart"""
        
        stages = ["Build", "Test", "Security Scan", "Deploy to Staging", "Deploy to Prod"]
        success_rates = [98, 95, 92, 97, 99]
        
        fig = go.Figure(data=go.Funnel(
            y=stages,
            x=success_rates,
            textinfo="value+percent initial",
            marker_color=['#28a745' if rate > 95 else '#ffc107' if rate > 90 else '#dc3545' 
                         for rate in success_rates]
        ))
        
        fig.update_layout(
            title="Deployment Pipeline Success Rates",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Deployment Pipeline",
            chart_type=ChartType.FUNNEL,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=8
        )
    
    async def _create_incident_timeline_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create incident timeline chart"""
        
        # Mock incident data
        incidents = [
            {"date": "2024-01-15", "severity": "High", "duration": 45},
            {"date": "2024-01-18", "severity": "Medium", "duration": 20},
            {"date": "2024-01-22", "severity": "Low", "duration": 10},
            {"date": "2024-01-25", "severity": "Critical", "duration": 120},
        ]
        
        df = pd.DataFrame(incidents)
        df["date"] = pd.to_datetime(df["date"])
        
        color_map = {"Critical": "#dc3545", "High": "#fd7e14", "Medium": "#ffc107", "Low": "#28a745"}
        
        fig = go.Figure()
        
        for severity in df["severity"].unique():
            severity_data = df[df["severity"] == severity]
            fig.add_trace(go.Scatter(
                x=severity_data["date"],
                y=severity_data["duration"],
                mode='markers',
                name=severity,
                marker=dict(
                    size=15,
                    color=color_map[severity]
                )
            ))
        
        fig.update_layout(
            title="Incident Timeline",
            xaxis_title="Date",
            yaxis_title="Duration (minutes)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Incident Timeline",
            chart_type=ChartType.SCATTER,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=8
        )
    
    async def _create_performance_metrics_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create performance metrics chart"""
        
        performance_data = time_series["performance_score"]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance_data["timestamp"],
            y=performance_data["value"],
            fill='tonexty',
            mode='lines',
            name='Performance Score',
            line=dict(color='#1f77b4')
        ))
        
        fig.update_layout(
            title="Performance Score Trend",
            xaxis_title="Time",
            yaxis_title="Performance Score",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Performance Metrics",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    # Additional chart methods for technical dashboard
    async def _create_code_quality_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create code quality chart"""
        
        metrics = ["Maintainability", "Reliability", "Security", "Coverage", "Duplication"]
        scores = [8.5, 9.2, 7.8, 8.7, 9.0]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=scores,
            theta=metrics,
            fill='toself',
            name='Code Quality'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            title="Code Quality Radar",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Code Quality",
            chart_type=ChartType.SCATTER,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_security_scan_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create security scan results chart"""
        
        severity_levels = ["Critical", "High", "Medium", "Low"]
        counts = [2, 5, 12, 8]
        
        fig = go.Figure(data=go.Bar(
            x=severity_levels,
            y=counts,
            marker_color=['#dc3545', '#fd7e14', '#ffc107', '#28a745']
        ))
        
        fig.update_layout(
            title="Security Vulnerabilities by Severity",
            xaxis_title="Severity Level",
            yaxis_title="Count",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Security Scan Results",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_performance_analysis_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create detailed performance analysis chart"""
        
        performance_data = time_series["performance_score"]
        
        # Create histogram of performance scores
        fig = go.Figure(data=go.Histogram(
            x=performance_data["value"],
            nbinsx=20,
            marker_color='#1f77b4',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Performance Score Distribution",
            xaxis_title="Performance Score",
            yaxis_title="Frequency",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Performance Analysis",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_test_automation_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create test automation metrics chart"""
        
        categories = ["Unit Tests", "Integration Tests", "E2E Tests", "Performance Tests"]
        automated = [95, 78, 65, 45]
        manual = [5, 22, 35, 55]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Automated', x=categories, y=automated, marker_color='#28a745'))
        fig.add_trace(go.Bar(name='Manual', x=categories, y=manual, marker_color='#ffc107'))
        
        fig.update_layout(
            title="Test Automation Coverage",
            xaxis_title="Test Category",
            yaxis_title="Percentage",
            barmode='stack',
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Test Automation",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    # Additional chart methods for compliance dashboard
    async def _create_compliance_overview_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create compliance overview chart"""
        
        standards = ["GDPR", "PCI DSS", "HIPAA", "SOX", "ISO 27001"]
        compliance_scores = [96, 94, 92, 89, 95]
        
        fig = go.Figure(data=go.Bar(
            x=standards,
            y=compliance_scores,
            marker_color=['#28a745' if score >= 95 else '#ffc107' if score >= 90 else '#dc3545' 
                         for score in compliance_scores]
        ))
        
        fig.add_hline(y=95, line_dash="dash", line_color="red", 
                     annotation_text="Target: 95%")
        
        fig.update_layout(
            title="Compliance Scores by Standard",
            xaxis_title="Compliance Standard",
            yaxis_title="Compliance Score (%)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Compliance Overview",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=8
        )
    
    async def _create_policy_violations_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create policy violations chart"""
        
        # Mock violation data over time
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        violations = [max(0, 5 + int(np.random.normal(0, 2))) for _ in dates]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=violations,
            mode='lines+markers',
            name='Policy Violations',
            line=dict(color='#dc3545')
        ))
        
        fig.update_layout(
            title="Policy Violations Over Time",
            xaxis_title="Date",
            yaxis_title="Number of Violations",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Policy Violations",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=8
        )
    
    async def _create_audit_trail_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create audit trail chart"""
        
        activities = ["Data Access", "Config Changes", "User Actions", "System Events"]
        counts = [245, 67, 123, 89]
        
        fig = go.Figure(data=go.Pie(
            labels=activities,
            values=counts,
            hole=0.3
        ))
        
        fig.update_layout(
            title="Audit Trail Activity Distribution",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Audit Trail",
            chart_type=ChartType.PIE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_risk_heatmap_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create risk heatmap chart"""
        
        # Mock risk matrix data
        risk_areas = ["Data Security", "Access Control", "Audit Logging", "Encryption", "Backup"]
        risk_levels = ["Low", "Medium", "High", "Critical"]
        
        # Create risk matrix
        import numpy as np
        risk_matrix = np.random.randint(1, 5, size=(len(risk_areas), len(risk_levels)))
        
        fig = go.Figure(data=go.Heatmap(
            z=risk_matrix,
            x=risk_levels,
            y=risk_areas,
            colorscale='RdYlGn_r',
            showscale=True
        ))
        
        fig.update_layout(
            title="Risk Assessment Heatmap",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Risk Heatmap",
            chart_type=ChartType.HEATMAP,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    # Performance dashboard charts
    async def _create_response_time_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create response time chart"""
        
        # Mock response time data
        timestamps = time_series["test_success_rate"]["timestamp"]
        response_times = 200 + np.random.normal(0, 50, len(timestamps))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=response_times,
            mode='lines',
            name='Response Time',
            line=dict(color='#1f77b4')
        ))
        
        fig.add_hline(y=500, line_dash="dash", line_color="red", 
                     annotation_text="SLA: 500ms")
        
        fig.update_layout(
            title="API Response Time",
            xaxis_title="Time",
            yaxis_title="Response Time (ms)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Response Time",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_throughput_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create throughput chart"""
        
        timestamps = time_series["test_success_rate"]["timestamp"]
        throughput = 1000 + np.random.normal(0, 200, len(timestamps))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=throughput,
            fill='tozeroy',
            mode='lines',
            name='Throughput',
            line=dict(color='#28a745')
        ))
        
        fig.update_layout(
            title="System Throughput",
            xaxis_title="Time",
            yaxis_title="Requests per Second",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Throughput",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_error_rate_chart(self, time_series: Dict[str, pd.DataFrame]) -> ChartWidget:
        """Create error rate chart"""
        
        timestamps = time_series["test_success_rate"]["timestamp"]
        error_rates = np.maximum(0, 1 + np.random.normal(0, 0.5, len(timestamps)))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=error_rates,
            mode='lines+markers',
            name='Error Rate',
            line=dict(color='#dc3545'),
            marker=dict(size=4)
        ))
        
        fig.add_hline(y=5, line_dash="dash", line_color="orange", 
                     annotation_text="Warning: 5%")
        
        fig.update_layout(
            title="Error Rate",
            xaxis_title="Time",
            yaxis_title="Error Rate (%)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Error Rate",
            chart_type=ChartType.LINE,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    async def _create_resource_usage_chart(self, data: Dict[str, Any]) -> ChartWidget:
        """Create resource usage chart"""
        
        resources = ["CPU", "Memory", "Disk I/O", "Network"]
        usage = [65, 72, 45, 38]
        
        fig = go.Figure()
        
        for i, (resource, value) in enumerate(zip(resources, usage)):
            color = '#28a745' if value < 70 else '#ffc107' if value < 85 else '#dc3545'
            fig.add_trace(go.Bar(
                x=[resource],
                y=[value],
                name=resource,
                marker_color=color,
                showlegend=False
            ))
        
        fig.add_hline(y=80, line_dash="dash", line_color="red", 
                     annotation_text="Critical: 80%")
        
        fig.update_layout(
            title="Resource Utilization",
            xaxis_title="Resource Type",
            yaxis_title="Usage (%)",
            template="plotly_white",
            height=400
        )
        
        return ChartWidget(
            title="Resource Usage",
            chart_type=ChartType.BAR,
            data={"figure": fig.to_json()},
            config={"displayModeBar": True},
            height=400,
            width=6
        )
    
    def _risk_to_numeric(self, risk_level) -> float:
        """Convert risk level to numeric value"""
        risk_mapping = {
            "LOW": 1.0,
            "MEDIUM": 2.0,
            "HIGH": 3.0,
            "CRITICAL": 4.0
        }
        return risk_mapping.get(str(risk_level).upper(), 2.0)
    
    def _create_error_dashboard(self, dashboard_type: DashboardType, error_message: str) -> DashboardLayout:
        """Create error dashboard when generation fails"""
        
        error_kpi = KPIWidget(
            title="Dashboard Status",
            value=0.0,
            unit="",
            trend=0.0,
            target=1.0,
            color="#dc3545",
            icon="❌",
            description=f"Error: {error_message}"
        )
        
        return DashboardLayout(
            dashboard_type=dashboard_type,
            title=f"Error - {dashboard_type.value.title()} Dashboard",
            description=f"Failed to generate dashboard: {error_message}",
            kpis=[error_kpi],
            charts=[],
            filters={},
            refresh_interval=300,
            stakeholder_level=StakeholderLevel.TECHNICAL
        )
    
    async def export_dashboard(
        self,
        dashboard: DashboardLayout,
        format_type: str = "html"
    ) -> str:
        """Export dashboard to various formats"""
        
        if format_type == "html":
            return await self._export_to_html(dashboard)
        elif format_type == "pdf":
            return await self._export_to_pdf(dashboard)
        elif format_type == "json":
            return json.dumps(asdict(dashboard), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_to_html(self, dashboard: DashboardLayout) -> str:
        """Export dashboard to HTML"""
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{dashboard.title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .dashboard-header {{ text-align: center; margin-bottom: 30px; }}
        .kpi-container {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
        .kpi-widget {{ text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .chart-container {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>{dashboard.title}</h1>
        <p>{dashboard.description}</p>
    </div>
    
    <div class="kpi-container">
        {"".join([f'''
        <div class="kpi-widget">
            <h3>{kpi.icon} {kpi.title}</h3>
            <h2 style="color: {kpi.color}">{kpi.value}{kpi.unit}</h2>
            <p>Trend: {kpi.trend:+.1f}%</p>
        </div>
        ''' for kpi in dashboard.kpis])}
    </div>
    
    <div class="charts">
        {"".join([f'''
        <div class="chart-container">
            <div id="chart-{i}"></div>
            <script>
                Plotly.newPlot('chart-{i}', {chart.data.get("figure", "{}")});
            </script>
        </div>
        ''' for i, chart in enumerate(dashboard.charts)])}
    </div>
</body>
</html>
"""
        
        return html_template
    
    async def _export_to_pdf(self, dashboard: DashboardLayout) -> str:
        """Export dashboard to PDF (mock implementation)"""
        
        # In a real implementation, this would use libraries like:
        # - weasyprint
        # - reportlab
        # - matplotlib for static charts
        
        return f"PDF export not implemented. Dashboard: {dashboard.title}"


# Utility functions for dashboard generation
import numpy as np

def generate_mock_data():
    """Generate mock data for demonstration"""
    return {
        "health_scores": np.random.normal(85, 10, 100),
        "response_times": np.random.exponential(200, 100),
        "error_rates": np.random.exponential(1, 100),
        "throughput": np.random.normal(1000, 200, 100)
    }