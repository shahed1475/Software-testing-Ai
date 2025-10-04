"""
Unified Reporter

Consolidates functional testing, security scanning, and compliance assessment results
into comprehensive, actionable reports with integrated analytics and visualizations.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Report output formats"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"
    EXCEL = "excel"
    CSV = "csv"
    MARKDOWN = "markdown"


class ReportScope(Enum):
    """Report scope levels"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    COMPLIANCE_FOCUSED = "compliance_focused"
    SECURITY_FOCUSED = "security_focused"
    FUNCTIONAL_FOCUSED = "functional_focused"
    COMPREHENSIVE = "comprehensive"


class ReportTemplate(Enum):
    """Pre-defined report templates"""
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    TECHNICAL_REPORT = "technical_report"
    SECURITY_ASSESSMENT = "security_assessment"
    COMPLIANCE_AUDIT = "compliance_audit"
    QUALITY_GATE = "quality_gate"
    TREND_ANALYSIS = "trend_analysis"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class ReportMetrics:
    """Consolidated metrics across all testing domains"""
    
    # Overall metrics
    overall_quality_score: float = 0.0
    risk_level: str = "UNKNOWN"
    total_tests_executed: int = 0
    execution_duration: float = 0.0
    
    # Functional metrics
    functional_pass_rate: float = 0.0
    functional_tests_total: int = 0
    functional_tests_passed: int = 0
    functional_tests_failed: int = 0
    functional_coverage: float = 0.0
    
    # Security metrics
    security_score: float = 0.0
    vulnerabilities_total: int = 0
    vulnerabilities_critical: int = 0
    vulnerabilities_high: int = 0
    vulnerabilities_medium: int = 0
    vulnerabilities_low: int = 0
    security_scans_executed: int = 0
    
    # Compliance metrics
    compliance_score: float = 0.0
    compliance_checks_total: int = 0
    compliance_checks_passed: int = 0
    compliance_checks_failed: int = 0
    compliance_gaps: int = 0
    standards_assessed: List[str] = field(default_factory=list)
    
    # Domain coverage
    web_coverage: float = 0.0
    api_coverage: float = 0.0
    mobile_coverage: float = 0.0
    
    # Trend data
    quality_trend: List[float] = field(default_factory=list)
    security_trend: List[float] = field(default_factory=list)
    compliance_trend: List[float] = field(default_factory=list)


@dataclass
class ReportVisualization:
    """Report visualization configuration"""
    
    chart_id: str
    chart_type: str  # bar, line, pie, scatter, heatmap, etc.
    title: str
    data: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)
    interactive: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["png", "svg", "pdf"])


@dataclass
class ReportSection:
    """Individual report section"""
    
    section_id: str
    title: str
    content: str
    subsections: List['ReportSection'] = field(default_factory=list)
    visualizations: List[ReportVisualization] = field(default_factory=list)
    data_tables: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical
    tags: List[str] = field(default_factory=list)


@dataclass
class UnifiedReport:
    """Comprehensive unified report"""
    
    report_id: str
    title: str
    generated_at: datetime
    scope: ReportScope
    template: ReportTemplate
    format: ReportFormat
    
    # Report metadata
    execution_id: str = ""
    test_plan_name: str = ""
    target_system: str = ""
    environment: str = ""
    version: str = "1.0.0"
    
    # Report content
    executive_summary: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    metrics: Optional[ReportMetrics] = None
    
    # Analysis results
    key_findings: List[Dict[str, Any]] = field(default_factory=list)
    critical_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Attachments and references
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    
    # Report configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "scope": self.scope.value,
            "template": self.template.value,
            "format": self.format.value,
            "execution_id": self.execution_id,
            "test_plan_name": self.test_plan_name,
            "target_system": self.target_system,
            "environment": self.environment,
            "version": self.version,
            "executive_summary": self.executive_summary,
            "sections": [self._section_to_dict(section) for section in self.sections],
            "metrics": self._metrics_to_dict() if self.metrics else None,
            "key_findings": self.key_findings,
            "critical_issues": self.critical_issues,
            "recommendations": self.recommendations,
            "attachments": self.attachments,
            "references": self.references,
            "config": self.config
        }
    
    def _section_to_dict(self, section: ReportSection) -> Dict[str, Any]:
        """Convert section to dictionary"""
        return {
            "section_id": section.section_id,
            "title": section.title,
            "content": section.content,
            "subsections": [self._section_to_dict(sub) for sub in section.subsections],
            "visualizations": [self._viz_to_dict(viz) for viz in section.visualizations],
            "data_tables": section.data_tables,
            "recommendations": section.recommendations,
            "priority": section.priority,
            "tags": section.tags
        }
    
    def _viz_to_dict(self, viz: ReportVisualization) -> Dict[str, Any]:
        """Convert visualization to dictionary"""
        return {
            "chart_id": viz.chart_id,
            "chart_type": viz.chart_type,
            "title": viz.title,
            "data": viz.data,
            "config": viz.config,
            "interactive": viz.interactive,
            "export_formats": viz.export_formats
        }
    
    def _metrics_to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        if not self.metrics:
            return {}
        
        return {
            "overall_quality_score": self.metrics.overall_quality_score,
            "risk_level": self.metrics.risk_level,
            "total_tests_executed": self.metrics.total_tests_executed,
            "execution_duration": self.metrics.execution_duration,
            "functional": {
                "pass_rate": self.metrics.functional_pass_rate,
                "total": self.metrics.functional_tests_total,
                "passed": self.metrics.functional_tests_passed,
                "failed": self.metrics.functional_tests_failed,
                "coverage": self.metrics.functional_coverage
            },
            "security": {
                "score": self.metrics.security_score,
                "vulnerabilities": {
                    "total": self.metrics.vulnerabilities_total,
                    "critical": self.metrics.vulnerabilities_critical,
                    "high": self.metrics.vulnerabilities_high,
                    "medium": self.metrics.vulnerabilities_medium,
                    "low": self.metrics.vulnerabilities_low
                },
                "scans_executed": self.metrics.security_scans_executed
            },
            "compliance": {
                "score": self.metrics.compliance_score,
                "checks": {
                    "total": self.metrics.compliance_checks_total,
                    "passed": self.metrics.compliance_checks_passed,
                    "failed": self.metrics.compliance_checks_failed
                },
                "gaps": self.metrics.compliance_gaps,
                "standards": self.metrics.standards_assessed
            },
            "domain_coverage": {
                "web": self.metrics.web_coverage,
                "api": self.metrics.api_coverage,
                "mobile": self.metrics.mobile_coverage
            },
            "trends": {
                "quality": self.metrics.quality_trend,
                "security": self.metrics.security_trend,
                "compliance": self.metrics.compliance_trend
            }
        }


class UnifiedReporter:
    """Main unified reporting engine"""
    
    def __init__(self):
        self.name = "Unified Reporter"
        self.version = "1.0.0"
        
        # Report storage
        self.reports: Dict[str, UnifiedReport] = {}
        self.report_history: List[str] = []
        
        # Configuration
        self.default_format = ReportFormat.HTML
        self.default_scope = ReportScope.COMPREHENSIVE
        self.default_template = ReportTemplate.TECHNICAL_REPORT
        
        # Output configuration
        self.output_directory = Path("reports")
        self.output_directory.mkdir(exist_ok=True)
        
        # Template configurations
        self.template_configs = self._initialize_template_configs()
    
    def _initialize_template_configs(self) -> Dict[ReportTemplate, Dict[str, Any]]:
        """Initialize template configurations"""
        
        return {
            ReportTemplate.EXECUTIVE_DASHBOARD: {
                "sections": ["executive_summary", "key_metrics", "risk_assessment", "recommendations"],
                "visualizations": ["quality_scorecard", "risk_matrix", "trend_charts"],
                "detail_level": "high_level",
                "target_audience": "executives"
            },
            ReportTemplate.TECHNICAL_REPORT: {
                "sections": ["overview", "functional_results", "security_results", "compliance_results", "analysis", "recommendations"],
                "visualizations": ["test_results_charts", "vulnerability_analysis", "compliance_gaps"],
                "detail_level": "detailed",
                "target_audience": "technical_teams"
            },
            ReportTemplate.SECURITY_ASSESSMENT: {
                "sections": ["security_overview", "vulnerability_analysis", "threat_assessment", "remediation_plan"],
                "visualizations": ["vulnerability_distribution", "risk_heatmap", "security_trends"],
                "detail_level": "security_focused",
                "target_audience": "security_teams"
            },
            ReportTemplate.COMPLIANCE_AUDIT: {
                "sections": ["compliance_overview", "standards_assessment", "gap_analysis", "remediation_roadmap"],
                "visualizations": ["compliance_scorecard", "gap_analysis_charts", "compliance_trends"],
                "detail_level": "compliance_focused",
                "target_audience": "compliance_teams"
            },
            ReportTemplate.QUALITY_GATE: {
                "sections": ["quality_summary", "gate_criteria", "pass_fail_analysis", "next_steps"],
                "visualizations": ["quality_gate_status", "criteria_breakdown", "trend_analysis"],
                "detail_level": "gate_focused",
                "target_audience": "development_teams"
            }
        }
    
    def generate_unified_report(
        self,
        unified_result: Any,  # UnifiedTestResult from unified_orchestrator
        template: ReportTemplate = None,
        scope: ReportScope = None,
        format: ReportFormat = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedReport:
        """Generate unified report from test results"""
        
        # Use defaults if not specified
        template = template or self.default_template
        scope = scope or self.default_scope
        format = format or self.default_format
        
        # Create report
        report = UnifiedReport(
            report_id=str(uuid.uuid4()),
            title=self._generate_report_title(unified_result, template),
            generated_at=datetime.now(),
            scope=scope,
            template=template,
            format=format,
            execution_id=getattr(unified_result, 'execution_id', ''),
            test_plan_name=getattr(unified_result.plan, 'name', '') if hasattr(unified_result, 'plan') else '',
            target_system=self._extract_target_system(unified_result),
            environment=self._extract_environment(unified_result)
        )
        
        # Apply custom configuration
        if custom_config:
            report.config.update(custom_config)
        
        # Extract and consolidate metrics
        report.metrics = self._extract_unified_metrics(unified_result)
        
        # Generate executive summary
        report.executive_summary = self._generate_executive_summary(unified_result, report.metrics)
        
        # Generate sections based on template
        report.sections = self._generate_report_sections(unified_result, template, scope)
        
        # Extract key findings
        report.key_findings = self._extract_key_findings(unified_result)
        
        # Extract critical issues
        report.critical_issues = self._extract_critical_issues(unified_result)
        
        # Generate recommendations
        report.recommendations = self._generate_unified_recommendations(unified_result, report.metrics)
        
        # Store report
        self.reports[report.report_id] = report
        self.report_history.append(report.report_id)
        
        return report
    
    def _generate_report_title(self, unified_result: Any, template: ReportTemplate) -> str:
        """Generate report title"""
        
        base_title = "Unified Testing Report"
        
        if template == ReportTemplate.EXECUTIVE_DASHBOARD:
            base_title = "Executive Testing Dashboard"
        elif template == ReportTemplate.SECURITY_ASSESSMENT:
            base_title = "Security Assessment Report"
        elif template == ReportTemplate.COMPLIANCE_AUDIT:
            base_title = "Compliance Audit Report"
        elif template == ReportTemplate.QUALITY_GATE:
            base_title = "Quality Gate Report"
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"{base_title} - {timestamp}"
    
    def _extract_target_system(self, unified_result: Any) -> str:
        """Extract target system information"""
        
        if hasattr(unified_result, 'plan') and hasattr(unified_result.plan, 'name'):
            return unified_result.plan.name
        
        return "Unknown System"
    
    def _extract_environment(self, unified_result: Any) -> str:
        """Extract environment information"""
        
        # This would typically come from the execution context
        return "Test Environment"
    
    def _extract_unified_metrics(self, unified_result: Any) -> ReportMetrics:
        """Extract and consolidate metrics from unified results"""
        
        metrics = ReportMetrics()
        
        # Overall metrics
        metrics.overall_quality_score = getattr(unified_result, 'overall_quality_score', 0.0)
        metrics.risk_level = getattr(unified_result, 'risk_level', 'UNKNOWN')
        metrics.total_tests_executed = getattr(unified_result, 'total_tests_executed', 0)
        metrics.execution_duration = getattr(unified_result, 'duration', 0.0)
        
        # Functional metrics
        functional_results = getattr(unified_result, 'functional_results', [])
        metrics.functional_tests_total = len(functional_results)
        metrics.functional_tests_passed = len([r for r in functional_results if getattr(r, 'passed', False)])
        metrics.functional_tests_failed = metrics.functional_tests_total - metrics.functional_tests_passed
        metrics.functional_pass_rate = getattr(unified_result, 'functional_pass_rate', 0.0)
        
        # Security metrics
        security_results = getattr(unified_result, 'security_results', None)
        if security_results:
            metrics.security_score = getattr(unified_result, 'security_score', 0.0)
            vulnerabilities = getattr(security_results, 'vulnerabilities', [])
            metrics.vulnerabilities_total = len(vulnerabilities)
            
            # Count by severity
            for vuln in vulnerabilities:
                severity = getattr(vuln, 'severity', 'unknown')
                if hasattr(severity, 'value'):
                    severity = severity.value
                
                if severity.lower() == 'critical':
                    metrics.vulnerabilities_critical += 1
                elif severity.lower() == 'high':
                    metrics.vulnerabilities_high += 1
                elif severity.lower() == 'medium':
                    metrics.vulnerabilities_medium += 1
                elif severity.lower() == 'low':
                    metrics.vulnerabilities_low += 1
        
        # Compliance metrics
        compliance_results = getattr(unified_result, 'compliance_results', None)
        if compliance_results:
            metrics.compliance_score = getattr(unified_result, 'compliance_score', 0.0)
            metrics.compliance_checks_total = getattr(compliance_results, 'total_checks', 0)
            metrics.compliance_checks_passed = getattr(compliance_results, 'passed_checks', 0)
            metrics.compliance_checks_failed = metrics.compliance_checks_total - metrics.compliance_checks_passed
            metrics.compliance_gaps = len(getattr(unified_result, 'compliance_gaps', []))
        
        # Domain coverage
        domain_coverage = getattr(unified_result, 'domain_coverage', {})
        metrics.web_coverage = domain_coverage.get('web', 0.0)
        metrics.api_coverage = domain_coverage.get('api', 0.0)
        metrics.mobile_coverage = domain_coverage.get('mobile', 0.0)
        
        return metrics
    
    def _generate_executive_summary(self, unified_result: Any, metrics: ReportMetrics) -> str:
        """Generate executive summary"""
        
        summary_parts = []
        
        # Overall assessment
        quality_assessment = self._get_quality_assessment(metrics.overall_quality_score)
        summary_parts.append(f"Overall Quality Assessment: {quality_assessment}")
        
        # Key metrics
        summary_parts.append(f"Total Tests Executed: {metrics.total_tests_executed}")
        summary_parts.append(f"Functional Pass Rate: {metrics.functional_pass_rate:.1%}")
        summary_parts.append(f"Security Score: {metrics.security_score:.1%}")
        summary_parts.append(f"Compliance Score: {metrics.compliance_score:.1%}")
        
        # Risk level
        summary_parts.append(f"Risk Level: {metrics.risk_level}")
        
        # Critical issues
        critical_issues = getattr(unified_result, 'critical_issues', [])
        if critical_issues:
            summary_parts.append(f"Critical Issues Identified: {len(critical_issues)}")
        
        # Recommendations count
        recommendations = getattr(unified_result, 'recommendations', [])
        if recommendations:
            summary_parts.append(f"Recommendations Provided: {len(recommendations)}")
        
        return "\n".join(summary_parts)
    
    def _get_quality_assessment(self, score: float) -> str:
        """Get quality assessment based on score"""
        
        if score >= 0.9:
            return "EXCELLENT"
        elif score >= 0.8:
            return "GOOD"
        elif score >= 0.7:
            return "ACCEPTABLE"
        elif score >= 0.5:
            return "NEEDS IMPROVEMENT"
        else:
            return "CRITICAL"
    
    def _generate_report_sections(
        self,
        unified_result: Any,
        template: ReportTemplate,
        scope: ReportScope
    ) -> List[ReportSection]:
        """Generate report sections based on template and scope"""
        
        sections = []
        template_config = self.template_configs.get(template, {})
        section_names = template_config.get("sections", [])
        
        for section_name in section_names:
            section = self._create_section(section_name, unified_result, scope)
            if section:
                sections.append(section)
        
        return sections
    
    def _create_section(
        self,
        section_name: str,
        unified_result: Any,
        scope: ReportScope
    ) -> Optional[ReportSection]:
        """Create individual report section"""
        
        section_creators = {
            "overview": self._create_overview_section,
            "executive_summary": self._create_executive_summary_section,
            "key_metrics": self._create_key_metrics_section,
            "functional_results": self._create_functional_results_section,
            "security_results": self._create_security_results_section,
            "compliance_results": self._create_compliance_results_section,
            "analysis": self._create_analysis_section,
            "recommendations": self._create_recommendations_section,
            "risk_assessment": self._create_risk_assessment_section
        }
        
        creator = section_creators.get(section_name)
        if creator:
            return creator(unified_result, scope)
        
        return None
    
    def _create_overview_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create overview section"""
        
        content = "This report provides a comprehensive analysis of the unified testing execution, "
        content += "covering functional testing, security scanning, and compliance assessment results."
        
        return ReportSection(
            section_id="overview",
            title="Overview",
            content=content,
            priority="high"
        )
    
    def _create_executive_summary_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create executive summary section"""
        
        metrics = self._extract_unified_metrics(unified_result)
        content = self._generate_executive_summary(unified_result, metrics)
        
        # Add quality scorecard visualization
        scorecard_viz = ReportVisualization(
            chart_id="quality_scorecard",
            chart_type="scorecard",
            title="Quality Scorecard",
            data={
                "overall_quality": metrics.overall_quality_score,
                "functional_quality": metrics.functional_pass_rate,
                "security_quality": metrics.security_score,
                "compliance_quality": metrics.compliance_score
            }
        )
        
        return ReportSection(
            section_id="executive_summary",
            title="Executive Summary",
            content=content,
            visualizations=[scorecard_viz],
            priority="critical"
        )
    
    def _create_key_metrics_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create key metrics section"""
        
        metrics = self._extract_unified_metrics(unified_result)
        
        content = f"""
        Key Performance Indicators:
        
        Overall Quality Score: {metrics.overall_quality_score:.2f}
        Risk Level: {metrics.risk_level}
        Total Tests Executed: {metrics.total_tests_executed}
        Execution Duration: {metrics.execution_duration:.2f} seconds
        
        Functional Testing:
        - Pass Rate: {metrics.functional_pass_rate:.1%}
        - Tests Passed: {metrics.functional_tests_passed}
        - Tests Failed: {metrics.functional_tests_failed}
        
        Security Assessment:
        - Security Score: {metrics.security_score:.1%}
        - Total Vulnerabilities: {metrics.vulnerabilities_total}
        - Critical Vulnerabilities: {metrics.vulnerabilities_critical}
        
        Compliance Assessment:
        - Compliance Score: {metrics.compliance_score:.1%}
        - Total Checks: {metrics.compliance_checks_total}
        - Compliance Gaps: {metrics.compliance_gaps}
        """
        
        # Add metrics visualization
        metrics_viz = ReportVisualization(
            chart_id="key_metrics_chart",
            chart_type="bar",
            title="Key Metrics Overview",
            data={
                "categories": ["Functional", "Security", "Compliance"],
                "scores": [metrics.functional_pass_rate, metrics.security_score, metrics.compliance_score]
            }
        )
        
        return ReportSection(
            section_id="key_metrics",
            title="Key Metrics",
            content=content.strip(),
            visualizations=[metrics_viz],
            priority="high"
        )
    
    def _create_functional_results_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create functional results section"""
        
        functional_results = getattr(unified_result, 'functional_results', [])
        
        content = f"""
        Functional Testing Results:
        
        Total Tests: {len(functional_results)}
        Passed: {len([r for r in functional_results if getattr(r, 'passed', False)])}
        Failed: {len([r for r in functional_results if not getattr(r, 'passed', True)])}
        Pass Rate: {getattr(unified_result, 'functional_pass_rate', 0.0):.1%}
        """
        
        # Add domain coverage data
        domain_coverage = getattr(unified_result, 'domain_coverage', {})
        if domain_coverage:
            content += "\n\nDomain Coverage:\n"
            for domain, coverage in domain_coverage.items():
                content += f"- {domain.upper()}: {coverage:.1%}\n"
        
        return ReportSection(
            section_id="functional_results",
            title="Functional Testing Results",
            content=content.strip(),
            priority="high"
        )
    
    def _create_security_results_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create security results section"""
        
        security_results = getattr(unified_result, 'security_results', None)
        security_vulnerabilities = getattr(unified_result, 'security_vulnerabilities', [])
        
        content = f"""
        Security Assessment Results:
        
        Security Score: {getattr(unified_result, 'security_score', 0.0):.1%}
        Total Vulnerabilities: {len(security_vulnerabilities)}
        """
        
        # Count vulnerabilities by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in security_vulnerabilities:
            severity = vuln.get("severity", "unknown").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        content += "\n\nVulnerabilities by Severity:\n"
        for severity, count in severity_counts.items():
            content += f"- {severity.upper()}: {count}\n"
        
        return ReportSection(
            section_id="security_results",
            title="Security Assessment Results",
            content=content.strip(),
            priority="high"
        )
    
    def _create_compliance_results_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create compliance results section"""
        
        compliance_results = getattr(unified_result, 'compliance_results', None)
        compliance_gaps = getattr(unified_result, 'compliance_gaps', [])
        
        content = f"""
        Compliance Assessment Results:
        
        Compliance Score: {getattr(unified_result, 'compliance_score', 0.0):.1%}
        Total Compliance Gaps: {len(compliance_gaps)}
        """
        
        if compliance_results:
            total_checks = getattr(compliance_results, 'total_checks', 0)
            passed_checks = getattr(compliance_results, 'passed_checks', 0)
            content += f"\nTotal Checks: {total_checks}\n"
            content += f"Passed Checks: {passed_checks}\n"
            content += f"Failed Checks: {total_checks - passed_checks}\n"
        
        return ReportSection(
            section_id="compliance_results",
            title="Compliance Assessment Results",
            content=content.strip(),
            priority="high"
        )
    
    def _create_analysis_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create analysis section"""
        
        content = "Cross-Domain Analysis:\n\n"
        
        # Integration issues
        integration_issues = getattr(unified_result, 'integration_issues', [])
        if integration_issues:
            content += f"Integration Issues Identified: {len(integration_issues)}\n"
            for issue in integration_issues[:5]:  # Show top 5
                content += f"- {issue.get('test_id', 'Unknown')}: {issue.get('error', 'No details')}\n"
        
        # Risk analysis
        risk_level = getattr(unified_result, 'risk_level', 'UNKNOWN')
        content += f"\nOverall Risk Level: {risk_level}\n"
        
        return ReportSection(
            section_id="analysis",
            title="Cross-Domain Analysis",
            content=content.strip(),
            priority="medium"
        )
    
    def _create_recommendations_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create recommendations section"""
        
        recommendations = getattr(unified_result, 'recommendations', [])
        
        content = "Recommendations for Improvement:\n\n"
        
        for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
            priority = rec.get('priority', 'medium')
            title = rec.get('title', 'No title')
            description = rec.get('description', 'No description')
            
            content += f"{i}. [{priority.upper()}] {title}\n"
            content += f"   {description}\n\n"
        
        return ReportSection(
            section_id="recommendations",
            title="Recommendations",
            content=content.strip(),
            recommendations=recommendations,
            priority="high"
        )
    
    def _create_risk_assessment_section(self, unified_result: Any, scope: ReportScope) -> ReportSection:
        """Create risk assessment section"""
        
        risk_level = getattr(unified_result, 'risk_level', 'UNKNOWN')
        critical_issues = getattr(unified_result, 'critical_issues', [])
        
        content = f"""
        Risk Assessment:
        
        Overall Risk Level: {risk_level}
        Critical Issues: {len(critical_issues)}
        
        Risk Factors:
        """
        
        # Add risk factors based on results
        metrics = self._extract_unified_metrics(unified_result)
        
        if metrics.functional_pass_rate < 0.8:
            content += "\n- Functional test failures indicate potential quality issues"
        
        if metrics.vulnerabilities_critical > 0:
            content += f"\n- {metrics.vulnerabilities_critical} critical security vulnerabilities identified"
        
        if metrics.compliance_gaps > 0:
            content += f"\n- {metrics.compliance_gaps} compliance gaps may lead to regulatory issues"
        
        return ReportSection(
            section_id="risk_assessment",
            title="Risk Assessment",
            content=content.strip(),
            priority="critical"
        )
    
    def _extract_key_findings(self, unified_result: Any) -> List[Dict[str, Any]]:
        """Extract key findings from results"""
        
        findings = []
        
        # Quality score finding
        quality_score = getattr(unified_result, 'overall_quality_score', 0.0)
        findings.append({
            "type": "quality_assessment",
            "title": "Overall Quality Score",
            "value": quality_score,
            "assessment": self._get_quality_assessment(quality_score),
            "impact": "high" if quality_score < 0.7 else "medium"
        })
        
        # Security findings
        security_vulnerabilities = getattr(unified_result, 'security_vulnerabilities', [])
        critical_vulns = [v for v in security_vulnerabilities if v.get("severity") == "critical"]
        if critical_vulns:
            findings.append({
                "type": "security_critical",
                "title": "Critical Security Vulnerabilities",
                "value": len(critical_vulns),
                "assessment": "CRITICAL",
                "impact": "critical"
            })
        
        # Compliance findings
        compliance_gaps = getattr(unified_result, 'compliance_gaps', [])
        if compliance_gaps:
            findings.append({
                "type": "compliance_gaps",
                "title": "Compliance Gaps",
                "value": len(compliance_gaps),
                "assessment": "NEEDS ATTENTION",
                "impact": "high"
            })
        
        return findings
    
    def _extract_critical_issues(self, unified_result: Any) -> List[Dict[str, Any]]:
        """Extract critical issues from results"""
        
        return getattr(unified_result, 'critical_issues', [])
    
    def _generate_unified_recommendations(
        self,
        unified_result: Any,
        metrics: ReportMetrics
    ) -> List[Dict[str, Any]]:
        """Generate unified recommendations"""
        
        recommendations = []
        
        # Quality improvement recommendations
        if metrics.overall_quality_score < 0.8:
            recommendations.append({
                "priority": "high",
                "category": "quality_improvement",
                "title": "Improve Overall Quality Score",
                "description": f"Current score: {metrics.overall_quality_score:.2f}",
                "actions": [
                    "Address failing functional tests",
                    "Resolve security vulnerabilities",
                    "Fix compliance gaps",
                    "Implement quality gates"
                ],
                "estimated_effort": "medium",
                "timeline": "2-4 weeks"
            })
        
        # Security recommendations
        if metrics.vulnerabilities_critical > 0:
            recommendations.append({
                "priority": "critical",
                "category": "security",
                "title": "Address Critical Security Vulnerabilities",
                "description": f"{metrics.vulnerabilities_critical} critical vulnerabilities found",
                "actions": [
                    "Patch critical vulnerabilities immediately",
                    "Implement security controls",
                    "Conduct security code review",
                    "Enhance security monitoring"
                ],
                "estimated_effort": "high",
                "timeline": "1-2 weeks"
            })
        
        # Compliance recommendations
        if metrics.compliance_gaps > 0:
            recommendations.append({
                "priority": "high",
                "category": "compliance",
                "title": "Address Compliance Gaps",
                "description": f"{metrics.compliance_gaps} compliance gaps identified",
                "actions": [
                    "Review compliance requirements",
                    "Update policies and procedures",
                    "Implement compliance controls",
                    "Conduct compliance training"
                ],
                "estimated_effort": "medium",
                "timeline": "3-6 weeks"
            })
        
        # Add existing recommendations from unified result
        existing_recommendations = getattr(unified_result, 'recommendations', [])
        recommendations.extend(existing_recommendations)
        
        return recommendations
    
    def export_report(
        self,
        report: UnifiedReport,
        output_path: Optional[Path] = None,
        format: Optional[ReportFormat] = None
    ) -> Path:
        """Export report to specified format"""
        
        format = format or report.format
        output_path = output_path or self.output_directory
        
        # Generate filename
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"unified_report_{timestamp}.{format.value}"
        full_path = output_path / filename
        
        # Export based on format
        if format == ReportFormat.JSON:
            self._export_json(report, full_path)
        elif format == ReportFormat.HTML:
            self._export_html(report, full_path)
        elif format == ReportFormat.MARKDOWN:
            self._export_markdown(report, full_path)
        else:
            # Default to JSON
            self._export_json(report, full_path)
        
        logger.info(f"Report exported to: {full_path}")
        return full_path
    
    def _export_json(self, report: UnifiedReport, path: Path):
        """Export report as JSON"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _export_html(self, report: UnifiedReport, path: Path):
        """Export report as HTML"""
        
        html_content = self._generate_html_report(report)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_markdown(self, report: UnifiedReport, path: Path):
        """Export report as Markdown"""
        
        markdown_content = self._generate_markdown_report(report)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def _generate_html_report(self, report: UnifiedReport) -> str:
        """Generate HTML report content"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .critical {{ color: #d32f2f; }}
                .high {{ color: #f57c00; }}
                .medium {{ color: #fbc02d; }}
                .low {{ color: #388e3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Execution ID: {report.execution_id}</p>
                <p>Target System: {report.target_system}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <pre>{report.executive_summary}</pre>
            </div>
        """
        
        # Add metrics if available
        if report.metrics:
            html += f"""
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>Overall Quality</h3>
                        <p>{report.metrics.overall_quality_score:.2f}</p>
                    </div>
                    <div class="metric">
                        <h3>Functional Pass Rate</h3>
                        <p>{report.metrics.functional_pass_rate:.1%}</p>
                    </div>
                    <div class="metric">
                        <h3>Security Score</h3>
                        <p>{report.metrics.security_score:.1%}</p>
                    </div>
                    <div class="metric">
                        <h3>Compliance Score</h3>
                        <p>{report.metrics.compliance_score:.1%}</p>
                    </div>
                </div>
            </div>
            """
        
        # Add sections
        for section in report.sections:
            html += f"""
            <div class="section">
                <h2>{section.title}</h2>
                <pre>{section.content}</pre>
            </div>
            """
        
        # Add recommendations
        if report.recommendations:
            html += """
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
            """
            
            for rec in report.recommendations:
                priority_class = rec.get('priority', 'medium').lower()
                html += f"""
                <li class="{priority_class}">
                    <strong>[{rec.get('priority', 'MEDIUM').upper()}]</strong> 
                    {rec.get('title', 'No title')} - {rec.get('description', 'No description')}
                </li>
                """
            
            html += """
                </ul>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_report(self, report: UnifiedReport) -> str:
        """Generate Markdown report content"""
        
        markdown = f"""# {report.title}

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Execution ID:** {report.execution_id}  
**Target System:** {report.target_system}  
**Environment:** {report.environment}

## Executive Summary

{report.executive_summary}

"""
        
        # Add metrics
        if report.metrics:
            markdown += f"""## Key Metrics

| Metric | Value |
|--------|-------|
| Overall Quality Score | {report.metrics.overall_quality_score:.2f} |
| Risk Level | {report.metrics.risk_level} |
| Functional Pass Rate | {report.metrics.functional_pass_rate:.1%} |
| Security Score | {report.metrics.security_score:.1%} |
| Compliance Score | {report.metrics.compliance_score:.1%} |
| Total Tests Executed | {report.metrics.total_tests_executed} |

"""
        
        # Add sections
        for section in report.sections:
            markdown += f"""## {section.title}

{section.content}

"""
        
        # Add recommendations
        if report.recommendations:
            markdown += """## Recommendations

"""
            for i, rec in enumerate(report.recommendations, 1):
                priority = rec.get('priority', 'medium').upper()
                title = rec.get('title', 'No title')
                description = rec.get('description', 'No description')
                
                markdown += f"{i}. **[{priority}]** {title}  \n   {description}\n\n"
        
        return markdown
    
    def get_report_summary(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report summary"""
        
        if report_id not in self.reports:
            return None
        
        report = self.reports[report_id]
        
        return {
            "report_id": report.report_id,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "scope": report.scope.value,
            "template": report.template.value,
            "format": report.format.value,
            "execution_id": report.execution_id,
            "overall_quality_score": report.metrics.overall_quality_score if report.metrics else 0.0,
            "risk_level": report.metrics.risk_level if report.metrics else "UNKNOWN",
            "total_sections": len(report.sections),
            "total_recommendations": len(report.recommendations),
            "critical_issues": len(report.critical_issues)
        }
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports"""
        
        return [self.get_report_summary(report_id) for report_id in self.report_history]


# Utility functions
def generate_comprehensive_report(unified_result: Any) -> UnifiedReport:
    """Generate comprehensive unified report"""
    
    reporter = UnifiedReporter()
    
    return reporter.generate_unified_report(
        unified_result=unified_result,
        template=ReportTemplate.TECHNICAL_REPORT,
        scope=ReportScope.COMPREHENSIVE,
        format=ReportFormat.HTML
    )


def generate_executive_dashboard(unified_result: Any) -> UnifiedReport:
    """Generate executive dashboard report"""
    
    reporter = UnifiedReporter()
    
    return reporter.generate_unified_report(
        unified_result=unified_result,
        template=ReportTemplate.EXECUTIVE_DASHBOARD,
        scope=ReportScope.EXECUTIVE_SUMMARY,
        format=ReportFormat.HTML
    )