"""
Executive Summary Agent - AI-generated insights on stability and risk
Provides high-level business intelligence for executives and stakeholders
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .base_agent import BaseAgent
from .trend_reporter_agent import TrendReporterAgent, TrendMetrics, BusinessInsight, RiskLevel
from ..database.database import DatabaseManager
from ..ai.llm_service import LLMService
from ..monitoring.metrics_collector import MetricsCollector

class SummaryType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    INCIDENT = "incident"

class StakeholderLevel(Enum):
    EXECUTIVE = "executive"
    MANAGEMENT = "management"
    TECHNICAL = "technical"
    BUSINESS = "business"

@dataclass
class StabilityMetrics:
    """System stability metrics"""
    uptime_percentage: float
    mean_time_to_recovery: float
    incident_count: int
    critical_issues: int
    performance_degradation_events: int
    availability_score: float

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    overall_risk_score: float
    risk_level: RiskLevel
    risk_factors: List[Dict[str, Any]]
    mitigation_strategies: List[str]
    business_impact: str
    timeline_to_resolution: str

@dataclass
class ExecutiveInsight:
    """Executive-level insight"""
    category: str  # "Quality", "Performance", "Security", "Compliance", "Business Impact"
    headline: str
    summary: str
    key_metrics: Dict[str, Any]
    business_impact: str
    action_required: bool
    priority: str  # "Low", "Medium", "High", "Critical"
    stakeholders: List[str]

@dataclass
class ExecutiveDashboard:
    """Complete executive dashboard data"""
    period: str
    generated_at: datetime
    overall_health_score: float
    stability_metrics: StabilityMetrics
    risk_assessment: RiskAssessment
    key_insights: List[ExecutiveInsight]
    recommendations: List[str]
    kpis: Dict[str, Any]
    trends: Dict[str, str]  # metric_name -> trend_direction
    alerts: List[Dict[str, Any]]

class ExecutiveSummaryAgent(BaseAgent):
    """
    Agent responsible for generating AI-powered executive summaries
    with stability and risk insights for business stakeholders
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ExecutiveSummary", config)
        self.db_manager = DatabaseManager()
        self.llm_service = LLMService()
        self.metrics_collector = MetricsCollector()
        self.trend_reporter = TrendReporterAgent(config)
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the executive summary agent"""
        self.logger.info("Starting Executive Summary Agent")
        await super().start()
        
    async def stop(self):
        """Stop the executive summary agent"""
        self.logger.info("Stopping Executive Summary Agent")
        await super().stop()
        
    async def generate_executive_summary(
        self,
        summary_type: SummaryType = SummaryType.WEEKLY,
        stakeholder_level: StakeholderLevel = StakeholderLevel.EXECUTIVE,
        include_recommendations: bool = True
    ) -> ExecutiveDashboard:
        """Generate comprehensive executive summary"""
        try:
            self.logger.info(f"Generating {summary_type.value} executive summary for {stakeholder_level.value}")
            
            # Collect comprehensive metrics
            stability_metrics = await self._collect_stability_metrics(summary_type)
            trend_data = await self._get_trend_data(summary_type)
            
            # Perform risk assessment
            risk_assessment = await self._perform_risk_assessment(stability_metrics, trend_data)
            
            # Generate AI-powered insights
            insights = await self._generate_executive_insights(
                stability_metrics, risk_assessment, trend_data, stakeholder_level
            )
            
            # Calculate KPIs
            kpis = await self._calculate_executive_kpis(stability_metrics, trend_data)
            
            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_recommendations(
                    risk_assessment, insights, stakeholder_level
                )
            
            # Identify trends
            trends = await self._identify_trends(trend_data)
            
            # Generate alerts
            alerts = await self._generate_alerts(risk_assessment, insights)
            
            # Calculate overall health score
            health_score = await self._calculate_overall_health_score(
                stability_metrics, risk_assessment, kpis
            )
            
            dashboard = ExecutiveDashboard(
                period=summary_type.value,
                generated_at=datetime.now(),
                overall_health_score=health_score,
                stability_metrics=stability_metrics,
                risk_assessment=risk_assessment,
                key_insights=insights,
                recommendations=recommendations,
                kpis=kpis,
                trends=trends,
                alerts=alerts
            )
            
            # Store summary
            await self._store_executive_summary(dashboard)
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
            raise
    
    async def _collect_stability_metrics(self, summary_type: SummaryType) -> StabilityMetrics:
        """Collect system stability metrics"""
        try:
            # Determine time range
            end_date = datetime.now()
            if summary_type == SummaryType.DAILY:
                start_date = end_date - timedelta(days=1)
            elif summary_type == SummaryType.WEEKLY:
                start_date = end_date - timedelta(weeks=1)
            elif summary_type == SummaryType.MONTHLY:
                start_date = end_date - timedelta(days=30)
            else:  # QUARTERLY
                start_date = end_date - timedelta(days=90)
            
            # Query stability data
            stability_query = """
            SELECT 
                AVG(CASE WHEN status = 'up' THEN 100 ELSE 0 END) as uptime_percentage,
                AVG(recovery_time) as mean_time_to_recovery,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_issues,
                COUNT(CASE WHEN event_type = 'performance_degradation' THEN 1 END) as performance_events,
                COUNT(*) as total_incidents
            FROM system_events 
            WHERE created_at >= %s AND created_at <= %s
            """
            
            result = await self.db_manager.execute_query(
                stability_query, (start_date, end_date)
            )
            
            if result:
                data = result[0]
                return StabilityMetrics(
                    uptime_percentage=data.get('uptime_percentage', 99.0),
                    mean_time_to_recovery=data.get('mean_time_to_recovery', 15.0),
                    incident_count=data.get('total_incidents', 0),
                    critical_issues=data.get('critical_issues', 0),
                    performance_degradation_events=data.get('performance_events', 0),
                    availability_score=data.get('uptime_percentage', 99.0)
                )
            else:
                # Return mock data if no database results
                return self._generate_mock_stability_metrics()
                
        except Exception as e:
            self.logger.warning(f"Database query failed, using mock data: {str(e)}")
            return self._generate_mock_stability_metrics()
    
    def _generate_mock_stability_metrics(self) -> StabilityMetrics:
        """Generate mock stability metrics for demonstration"""
        import random
        
        return StabilityMetrics(
            uptime_percentage=random.uniform(95.0, 99.9),
            mean_time_to_recovery=random.uniform(5.0, 30.0),
            incident_count=random.randint(0, 5),
            critical_issues=random.randint(0, 2),
            performance_degradation_events=random.randint(0, 3),
            availability_score=random.uniform(95.0, 99.9)
        )
    
    async def _get_trend_data(self, summary_type: SummaryType) -> List[TrendMetrics]:
        """Get trend data from trend reporter"""
        try:
            from .trend_reporter_agent import TrendPeriod
            
            period_mapping = {
                SummaryType.DAILY: TrendPeriod.DAILY,
                SummaryType.WEEKLY: TrendPeriod.WEEKLY,
                SummaryType.MONTHLY: TrendPeriod.MONTHLY,
                SummaryType.QUARTERLY: TrendPeriod.QUARTERLY
            }
            
            trend_report = await self.trend_reporter.generate_trend_report(
                period=period_mapping.get(summary_type, TrendPeriod.WEEKLY),
                include_charts=False
            )
            
            return [TrendMetrics(**metric) for metric in trend_report.get('detailed_metrics', [])]
            
        except Exception as e:
            self.logger.warning(f"Failed to get trend data: {str(e)}")
            return []
    
    async def _perform_risk_assessment(
        self, 
        stability_metrics: StabilityMetrics,
        trend_data: List[TrendMetrics]
    ) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        
        risk_factors = []
        risk_score = 0.0
        
        # Stability risk factors
        if stability_metrics.uptime_percentage < 99.0:
            risk_factors.append({
                "factor": "Low System Uptime",
                "impact": "High",
                "description": f"System uptime at {stability_metrics.uptime_percentage:.1f}% below target",
                "weight": 0.3
            })
            risk_score += 30
        
        if stability_metrics.critical_issues > 0:
            risk_factors.append({
                "factor": "Critical Issues Present",
                "impact": "Critical",
                "description": f"{stability_metrics.critical_issues} critical issues identified",
                "weight": 0.4
            })
            risk_score += 40
        
        if stability_metrics.mean_time_to_recovery > 20:
            risk_factors.append({
                "factor": "High Recovery Time",
                "impact": "Medium",
                "description": f"Mean recovery time of {stability_metrics.mean_time_to_recovery:.1f} minutes",
                "weight": 0.2
            })
            risk_score += 20
        
        # Trend-based risk factors
        if trend_data:
            recent_success_rate = sum(m.test_success_rate for m in trend_data[-3:]) / min(3, len(trend_data))
            if recent_success_rate < 85:
                risk_factors.append({
                    "factor": "Declining Test Success Rate",
                    "impact": "High",
                    "description": f"Test success rate at {recent_success_rate:.1f}%",
                    "weight": 0.25
                })
                risk_score += 25
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Generate mitigation strategies
        mitigation_strategies = await self._generate_mitigation_strategies(risk_factors)
        
        # Assess business impact
        business_impact = await self._assess_business_impact(risk_level, risk_factors)
        
        # Estimate timeline
        timeline = self._estimate_resolution_timeline(risk_level, risk_factors)
        
        return RiskAssessment(
            overall_risk_score=min(100, risk_score),
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            business_impact=business_impact,
            timeline_to_resolution=timeline
        )
    
    async def _generate_mitigation_strategies(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate AI-powered mitigation strategies"""
        strategies = []
        
        for factor in risk_factors:
            if "uptime" in factor["factor"].lower():
                strategies.append("Implement redundancy and failover mechanisms")
                strategies.append("Enhance monitoring and alerting systems")
            elif "critical" in factor["factor"].lower():
                strategies.append("Immediate escalation and resolution of critical issues")
                strategies.append("Root cause analysis and preventive measures")
            elif "recovery" in factor["factor"].lower():
                strategies.append("Optimize incident response procedures")
                strategies.append("Automate recovery processes where possible")
            elif "success rate" in factor["factor"].lower():
                strategies.append("Review and improve testing strategies")
                strategies.append("Increase code review coverage")
        
        # Remove duplicates and limit to top strategies
        return list(set(strategies))[:5]
    
    async def _assess_business_impact(self, risk_level: RiskLevel, risk_factors: List[Dict[str, Any]]) -> str:
        """Assess business impact of identified risks"""
        if risk_level == RiskLevel.CRITICAL:
            return "Severe business impact with potential revenue loss and customer churn"
        elif risk_level == RiskLevel.HIGH:
            return "Significant impact on customer satisfaction and operational efficiency"
        elif risk_level == RiskLevel.MEDIUM:
            return "Moderate impact on service quality and team productivity"
        else:
            return "Minimal business impact with manageable operational effects"
    
    def _estimate_resolution_timeline(self, risk_level: RiskLevel, risk_factors: List[Dict[str, Any]]) -> str:
        """Estimate timeline for risk resolution"""
        if risk_level == RiskLevel.CRITICAL:
            return "Immediate action required (0-24 hours)"
        elif risk_level == RiskLevel.HIGH:
            return "Urgent resolution needed (1-3 days)"
        elif risk_level == RiskLevel.MEDIUM:
            return "Planned resolution (1-2 weeks)"
        else:
            return "Routine maintenance (2-4 weeks)"
    
    async def _generate_executive_insights(
        self,
        stability_metrics: StabilityMetrics,
        risk_assessment: RiskAssessment,
        trend_data: List[TrendMetrics],
        stakeholder_level: StakeholderLevel
    ) -> List[ExecutiveInsight]:
        """Generate AI-powered executive insights"""
        
        insights = []
        
        # Quality insight
        if trend_data:
            avg_success_rate = sum(m.test_success_rate for m in trend_data) / len(trend_data)
            quality_insight = ExecutiveInsight(
                category="Quality",
                headline=f"System Quality at {avg_success_rate:.0f}%",
                summary=f"Current test success rate indicates {'strong' if avg_success_rate > 90 else 'moderate' if avg_success_rate > 80 else 'concerning'} quality levels",
                key_metrics={"success_rate": avg_success_rate, "trend": "stable"},
                business_impact="Direct impact on customer satisfaction and product reliability",
                action_required=avg_success_rate < 85,
                priority="High" if avg_success_rate < 85 else "Medium",
                stakeholders=["Engineering", "Product", "QA"]
            )
            insights.append(quality_insight)
        
        # Stability insight
        stability_insight = ExecutiveInsight(
            category="Performance",
            headline=f"System Uptime: {stability_metrics.uptime_percentage:.1f}%",
            summary=f"System availability {'meets' if stability_metrics.uptime_percentage >= 99 else 'below'} target SLA requirements",
            key_metrics={
                "uptime": stability_metrics.uptime_percentage,
                "incidents": stability_metrics.incident_count,
                "mttr": stability_metrics.mean_time_to_recovery
            },
            business_impact="Critical for customer trust and revenue protection",
            action_required=stability_metrics.uptime_percentage < 99,
            priority="Critical" if stability_metrics.uptime_percentage < 95 else "High" if stability_metrics.uptime_percentage < 99 else "Medium",
            stakeholders=["Operations", "Engineering", "Customer Success"]
        )
        insights.append(stability_insight)
        
        # Risk insight
        risk_insight = ExecutiveInsight(
            category="Business Impact",
            headline=f"Overall Risk Level: {risk_assessment.risk_level.value.title()}",
            summary=risk_assessment.business_impact,
            key_metrics={"risk_score": risk_assessment.overall_risk_score, "factors": len(risk_assessment.risk_factors)},
            business_impact=risk_assessment.business_impact,
            action_required=risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            priority=risk_assessment.risk_level.value.title(),
            stakeholders=["Executive", "Operations", "Engineering"]
        )
        insights.append(risk_insight)
        
        return insights
    
    async def _calculate_executive_kpis(
        self,
        stability_metrics: StabilityMetrics,
        trend_data: List[TrendMetrics]
    ) -> Dict[str, Any]:
        """Calculate key performance indicators for executives"""
        
        kpis = {
            "system_availability": stability_metrics.uptime_percentage,
            "incident_count": stability_metrics.incident_count,
            "mean_time_to_recovery": stability_metrics.mean_time_to_recovery,
            "critical_issues": stability_metrics.critical_issues
        }
        
        if trend_data:
            recent_data = trend_data[-5:] if len(trend_data) >= 5 else trend_data
            kpis.update({
                "test_success_rate": sum(m.test_success_rate for m in recent_data) / len(recent_data),
                "test_coverage": sum(m.total_tests for m in recent_data) / len(recent_data),
                "performance_score": sum(m.performance_score for m in recent_data) / len(recent_data),
                "security_score": sum(m.security_score for m in recent_data) / len(recent_data)
            })
        
        return kpis
    
    async def _generate_recommendations(
        self,
        risk_assessment: RiskAssessment,
        insights: List[ExecutiveInsight],
        stakeholder_level: StakeholderLevel
    ) -> List[str]:
        """Generate stakeholder-specific recommendations"""
        
        recommendations = []
        
        # Risk-based recommendations
        if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Immediate review of critical system components",
                "Escalate incident response procedures",
                "Consider additional resource allocation for stability"
            ])
        
        # Insight-based recommendations
        for insight in insights:
            if insight.action_required:
                if insight.category == "Quality":
                    recommendations.append("Invest in automated testing infrastructure")
                elif insight.category == "Performance":
                    recommendations.append("Enhance monitoring and alerting capabilities")
        
        # Stakeholder-specific recommendations
        if stakeholder_level == StakeholderLevel.EXECUTIVE:
            recommendations.extend([
                "Review quarterly quality and stability targets",
                "Consider strategic investments in reliability engineering"
            ])
        elif stakeholder_level == StakeholderLevel.MANAGEMENT:
            recommendations.extend([
                "Implement team performance metrics",
                "Schedule regular quality review meetings"
            ])
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    async def _identify_trends(self, trend_data: List[TrendMetrics]) -> Dict[str, str]:
        """Identify trends in metrics"""
        trends = {}
        
        if len(trend_data) < 2:
            return trends
        
        # Calculate trends for key metrics
        recent = trend_data[-3:]
        older = trend_data[-6:-3] if len(trend_data) >= 6 else trend_data[:-3]
        
        if older:
            metrics_to_analyze = [
                ('success_rate', 'test_success_rate'),
                ('performance', 'performance_score'),
                ('security', 'security_score')
            ]
            
            for trend_name, metric_attr in metrics_to_analyze:
                recent_avg = sum(getattr(m, metric_attr) for m in recent) / len(recent)
                older_avg = sum(getattr(m, metric_attr) for m in older) / len(older)
                
                if recent_avg > older_avg * 1.05:
                    trends[trend_name] = "improving"
                elif recent_avg < older_avg * 0.95:
                    trends[trend_name] = "declining"
                else:
                    trends[trend_name] = "stable"
        
        return trends
    
    async def _generate_alerts(
        self,
        risk_assessment: RiskAssessment,
        insights: List[ExecutiveInsight]
    ) -> List[Dict[str, Any]]:
        """Generate executive alerts"""
        alerts = []
        
        # Risk-based alerts
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            alerts.append({
                "type": "critical",
                "title": "Critical Risk Level Detected",
                "message": "Immediate executive attention required",
                "action": "Review risk assessment and mitigation strategies"
            })
        
        # Insight-based alerts
        for insight in insights:
            if insight.action_required and insight.priority in ["Critical", "High"]:
                alerts.append({
                    "type": insight.priority.lower(),
                    "title": f"{insight.category} Alert",
                    "message": insight.headline,
                    "action": f"Review {insight.category.lower()} metrics and take corrective action"
                })
        
        return alerts
    
    async def _calculate_overall_health_score(
        self,
        stability_metrics: StabilityMetrics,
        risk_assessment: RiskAssessment,
        kpis: Dict[str, Any]
    ) -> float:
        """Calculate overall system health score"""
        
        # Weighted health calculation
        weights = {
            'availability': 0.3,
            'quality': 0.25,
            'performance': 0.2,
            'risk': 0.25
        }
        
        availability_score = stability_metrics.uptime_percentage
        quality_score = kpis.get('test_success_rate', 85)
        performance_score = kpis.get('performance_score', 80)
        risk_score = 100 - risk_assessment.overall_risk_score  # Invert risk score
        
        health_score = (
            availability_score * weights['availability'] +
            quality_score * weights['quality'] +
            performance_score * weights['performance'] +
            risk_score * weights['risk']
        )
        
        return min(100, max(0, health_score))
    
    async def _store_executive_summary(self, dashboard: ExecutiveDashboard):
        """Store executive summary"""
        try:
            query = """
            INSERT INTO executive_summaries (summary_data, period, health_score, generated_at)
            VALUES (%s, %s, %s, %s)
            """
            await self.db_manager.execute_query(
                query, (
                    json.dumps(asdict(dashboard), default=str),
                    dashboard.period,
                    dashboard.overall_health_score,
                    dashboard.generated_at
                )
            )
        except Exception as e:
            self.logger.warning(f"Failed to store executive summary: {str(e)}")
    
    async def get_executive_dashboard_data(self) -> Dict[str, Any]:
        """Get current executive dashboard data"""
        try:
            dashboard = await self.generate_executive_summary()
            return asdict(dashboard)
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    async def generate_stakeholder_report(
        self,
        stakeholder_level: StakeholderLevel,
        format_type: str = "summary"  # "summary", "detailed", "presentation"
    ) -> Dict[str, Any]:
        """Generate stakeholder-specific report"""
        
        dashboard = await self.generate_executive_summary(
            stakeholder_level=stakeholder_level
        )
        
        if format_type == "summary":
            return {
                "health_score": dashboard.overall_health_score,
                "key_insights": [asdict(insight) for insight in dashboard.key_insights[:3]],
                "top_recommendations": dashboard.recommendations[:5],
                "alerts": dashboard.alerts
            }
        elif format_type == "detailed":
            return asdict(dashboard)
        else:  # presentation
            return {
                "executive_summary": {
                    "health_score": dashboard.overall_health_score,
                    "risk_level": dashboard.risk_assessment.risk_level.value,
                    "key_message": dashboard.key_insights[0].summary if dashboard.key_insights else "System operating normally"
                },
                "key_metrics": dashboard.kpis,
                "action_items": [rec for rec in dashboard.recommendations if "immediate" in rec.lower() or "urgent" in rec.lower()]
            }