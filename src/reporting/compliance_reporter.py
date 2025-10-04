"""
Compliance Reporter

Specialized reporting for compliance assessment results, regulatory analysis,
gap identification, and compliance recommendations.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


class ComplianceReportType(Enum):
    """Compliance report types"""
    GDPR_ASSESSMENT = "gdpr_assessment"
    PCI_DSS_ASSESSMENT = "pci_dss_assessment"
    HIPAA_ASSESSMENT = "hipaa_assessment"
    SOX_ASSESSMENT = "sox_assessment"
    ISO27001_ASSESSMENT = "iso27001_assessment"
    MULTI_STANDARD_ASSESSMENT = "multi_standard_assessment"
    GAP_ANALYSIS = "gap_analysis"
    REMEDIATION_PLAN = "remediation_plan"


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    REQUIRES_REVIEW = "requires_review"
    IN_PROGRESS = "in_progress"


class ComplianceRiskLevel(Enum):
    """Compliance risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class ComplianceMetrics:
    """Compliance-specific metrics"""
    
    # Overall compliance metrics
    overall_compliance_score: float = 0.0
    compliance_percentage: float = 0.0
    risk_score: float = 0.0
    
    # Requirement metrics
    total_requirements: int = 0
    compliant_requirements: int = 0
    non_compliant_requirements: int = 0
    partially_compliant_requirements: int = 0
    not_applicable_requirements: int = 0
    
    # Gap analysis
    critical_gaps: int = 0
    high_risk_gaps: int = 0
    medium_risk_gaps: int = 0
    low_risk_gaps: int = 0
    
    # Standard-specific metrics
    standards_assessed: List[str] = field(default_factory=list)
    standard_scores: Dict[str, float] = field(default_factory=dict)
    
    # Control metrics
    total_controls: int = 0
    implemented_controls: int = 0
    missing_controls: int = 0
    ineffective_controls: int = 0
    
    # Assessment metrics
    assessment_coverage: float = 0.0
    assessment_duration: float = 0.0
    automated_checks: int = 0
    manual_checks: int = 0
    
    # Remediation metrics
    remediation_items: int = 0
    high_priority_items: int = 0
    estimated_remediation_effort: str = "UNKNOWN"
    
    # Trend data
    compliance_trend: List[float] = field(default_factory=list)
    gap_trend: List[int] = field(default_factory=list)


@dataclass
class ComplianceGap:
    """Detailed compliance gap information"""
    
    gap_id: str
    requirement_id: str
    requirement_title: str
    standard: str
    
    # Gap details
    gap_description: str
    current_state: str
    required_state: str
    gap_type: str  # MISSING, INADEQUATE, INEFFECTIVE, OUTDATED
    
    # Risk assessment
    risk_level: ComplianceRiskLevel
    business_impact: str
    regulatory_impact: str
    financial_impact: Optional[str] = None
    
    # Evidence
    evidence_required: List[str] = field(default_factory=list)
    evidence_found: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    
    # Remediation
    remediation_actions: List[str] = field(default_factory=list)
    remediation_priority: str = "MEDIUM"
    estimated_effort: str = "UNKNOWN"
    estimated_timeline: str = "UNKNOWN"
    estimated_cost: Optional[str] = None
    
    # Ownership
    responsible_party: Optional[str] = None
    stakeholders: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # Status tracking
    status: str = "OPEN"  # OPEN, IN_PROGRESS, RESOLVED, ACCEPTED
    identified_date: Optional[datetime] = None
    target_resolution_date: Optional[datetime] = None
    actual_resolution_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "gap_id": self.gap_id,
            "requirement_id": self.requirement_id,
            "requirement_title": self.requirement_title,
            "standard": self.standard,
            "gap_description": self.gap_description,
            "current_state": self.current_state,
            "required_state": self.required_state,
            "gap_type": self.gap_type,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, ComplianceRiskLevel) else self.risk_level,
            "business_impact": self.business_impact,
            "regulatory_impact": self.regulatory_impact,
            "financial_impact": self.financial_impact,
            "evidence_required": self.evidence_required,
            "evidence_found": self.evidence_found,
            "evidence_gaps": self.evidence_gaps,
            "remediation_actions": self.remediation_actions,
            "remediation_priority": self.remediation_priority,
            "estimated_effort": self.estimated_effort,
            "estimated_timeline": self.estimated_timeline,
            "estimated_cost": self.estimated_cost,
            "responsible_party": self.responsible_party,
            "stakeholders": self.stakeholders,
            "dependencies": self.dependencies,
            "prerequisites": self.prerequisites,
            "status": self.status,
            "identified_date": self.identified_date.isoformat() if self.identified_date else None,
            "target_resolution_date": self.target_resolution_date.isoformat() if self.target_resolution_date else None,
            "actual_resolution_date": self.actual_resolution_date.isoformat() if self.actual_resolution_date else None
        }


@dataclass
class ComplianceRecommendation:
    """Compliance recommendation"""
    
    recommendation_id: str
    title: str
    description: str
    priority: str
    category: str
    standard: str
    
    # Implementation details
    implementation_steps: List[str] = field(default_factory=list)
    estimated_effort: str = "UNKNOWN"
    timeline: str = "UNKNOWN"
    cost_estimate: Optional[str] = None
    
    # Compliance improvement
    compliance_improvement: str = "UNKNOWN"
    gaps_addressed: List[str] = field(default_factory=list)
    requirements_satisfied: List[str] = field(default_factory=list)
    
    # Risk mitigation
    risk_reduction: str = "UNKNOWN"
    regulatory_benefits: List[str] = field(default_factory=list)
    business_benefits: List[str] = field(default_factory=list)
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Resources
    required_resources: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "standard": self.standard,
            "implementation_steps": self.implementation_steps,
            "estimated_effort": self.estimated_effort,
            "timeline": self.timeline,
            "cost_estimate": self.cost_estimate,
            "compliance_improvement": self.compliance_improvement,
            "gaps_addressed": self.gaps_addressed,
            "requirements_satisfied": self.requirements_satisfied,
            "risk_reduction": self.risk_reduction,
            "regulatory_benefits": self.regulatory_benefits,
            "business_benefits": self.business_benefits,
            "prerequisites": self.prerequisites,
            "dependencies": self.dependencies,
            "required_resources": self.required_resources,
            "required_skills": self.required_skills
        }


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    
    report_id: str
    title: str
    report_type: ComplianceReportType
    generated_at: datetime
    
    # Report metadata
    target_organization: str = ""
    assessment_scope: str = ""
    standards_assessed: List[str] = field(default_factory=list)
    assessment_period: str = ""
    
    # Executive summary
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    
    # Metrics and analysis
    metrics: Optional[ComplianceMetrics] = None
    gaps: List[ComplianceGap] = field(default_factory=list)
    recommendations: List[ComplianceRecommendation] = field(default_factory=list)
    
    # Compliance status
    overall_compliance_status: ComplianceStatus = ComplianceStatus.REQUIRES_REVIEW
    standard_compliance_status: Dict[str, ComplianceStatus] = field(default_factory=dict)
    
    # Risk assessment
    overall_risk_level: ComplianceRiskLevel = ComplianceRiskLevel.MEDIUM
    regulatory_risks: List[str] = field(default_factory=list)
    business_risks: List[str] = field(default_factory=list)
    
    # Remediation planning
    remediation_roadmap: List[Dict[str, Any]] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    
    # Evidence and documentation
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    documentation_gaps: List[str] = field(default_factory=list)
    
    # Appendices
    assessment_details: Dict[str, Any] = field(default_factory=dict)
    control_matrix: Dict[str, Any] = field(default_factory=dict)
    raw_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "target_organization": self.target_organization,
            "assessment_scope": self.assessment_scope,
            "standards_assessed": self.standards_assessed,
            "assessment_period": self.assessment_period,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "metrics": self._metrics_to_dict() if self.metrics else None,
            "gaps": [gap.to_dict() for gap in self.gaps],
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "overall_compliance_status": self.overall_compliance_status.value,
            "standard_compliance_status": {k: v.value for k, v in self.standard_compliance_status.items()},
            "overall_risk_level": self.overall_risk_level.value,
            "regulatory_risks": self.regulatory_risks,
            "business_risks": self.business_risks,
            "remediation_roadmap": self.remediation_roadmap,
            "priority_actions": self.priority_actions,
            "evidence_summary": self.evidence_summary,
            "documentation_gaps": self.documentation_gaps,
            "assessment_details": self.assessment_details,
            "control_matrix": self.control_matrix,
            "raw_results": self.raw_results
        }
    
    def _metrics_to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        if not self.metrics:
            return {}
        
        return {
            "overall_compliance_score": self.metrics.overall_compliance_score,
            "compliance_percentage": self.metrics.compliance_percentage,
            "risk_score": self.metrics.risk_score,
            "requirements": {
                "total": self.metrics.total_requirements,
                "compliant": self.metrics.compliant_requirements,
                "non_compliant": self.metrics.non_compliant_requirements,
                "partially_compliant": self.metrics.partially_compliant_requirements,
                "not_applicable": self.metrics.not_applicable_requirements
            },
            "gaps": {
                "critical": self.metrics.critical_gaps,
                "high": self.metrics.high_risk_gaps,
                "medium": self.metrics.medium_risk_gaps,
                "low": self.metrics.low_risk_gaps
            },
            "standards_assessed": self.metrics.standards_assessed,
            "standard_scores": self.metrics.standard_scores,
            "controls": {
                "total": self.metrics.total_controls,
                "implemented": self.metrics.implemented_controls,
                "missing": self.metrics.missing_controls,
                "ineffective": self.metrics.ineffective_controls
            },
            "assessment": {
                "coverage": self.metrics.assessment_coverage,
                "duration": self.metrics.assessment_duration,
                "automated_checks": self.metrics.automated_checks,
                "manual_checks": self.metrics.manual_checks
            },
            "remediation": {
                "items": self.metrics.remediation_items,
                "high_priority": self.metrics.high_priority_items,
                "estimated_effort": self.metrics.estimated_remediation_effort
            },
            "trends": {
                "compliance": self.metrics.compliance_trend,
                "gaps": self.metrics.gap_trend
            }
        }


class ComplianceReporter:
    """Compliance-focused reporter"""
    
    def __init__(self):
        self.name = "Compliance Reporter"
        self.version = "1.0.0"
        
        # Report storage
        self.reports: Dict[str, ComplianceReport] = {}
        self.report_history: List[str] = []
        
        # Configuration
        self.output_directory = Path("reports/compliance")
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Standard mappings
        self.standard_names = {
            "gdpr": "General Data Protection Regulation (GDPR)",
            "pci_dss": "Payment Card Industry Data Security Standard (PCI DSS)",
            "hipaa": "Health Insurance Portability and Accountability Act (HIPAA)",
            "sox": "Sarbanes-Oxley Act (SOX)",
            "iso27001": "ISO/IEC 27001:2013"
        }
        
        # Risk level mappings
        self.risk_level_weights = {
            ComplianceRiskLevel.CRITICAL: 10,
            ComplianceRiskLevel.HIGH: 5,
            ComplianceRiskLevel.MEDIUM: 2,
            ComplianceRiskLevel.LOW: 1,
            ComplianceRiskLevel.MINIMAL: 0
        }
    
    def generate_compliance_report(
        self,
        compliance_results: Any,
        report_type: ComplianceReportType = ComplianceReportType.MULTI_STANDARD_ASSESSMENT,
        target_organization: str = "",
        assessment_scope: str = ""
    ) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        
        # Create report
        report = ComplianceReport(
            report_id=str(uuid.uuid4()),
            title=self._generate_report_title(report_type, target_organization),
            report_type=report_type,
            generated_at=datetime.now(),
            target_organization=target_organization,
            assessment_scope=assessment_scope
        )
        
        # Extract standards assessed
        report.standards_assessed = self._extract_standards_assessed(compliance_results)
        
        # Extract metrics
        report.metrics = self._extract_compliance_metrics(compliance_results)
        
        # Extract gaps
        report.gaps = self._extract_compliance_gaps(compliance_results)
        
        # Generate executive summary
        report.executive_summary = self._generate_executive_summary(report.metrics, report.gaps)
        
        # Extract key findings
        report.key_findings = self._extract_key_findings(report.gaps, report.metrics)
        
        # Generate recommendations
        report.recommendations = self._generate_compliance_recommendations(report.gaps, report.metrics)
        
        # Assess compliance status
        report.overall_compliance_status = self._assess_overall_compliance_status(report.metrics, report.gaps)
        report.standard_compliance_status = self._assess_standard_compliance_status(compliance_results)
        
        # Assess risk levels
        report.overall_risk_level = self._assess_overall_risk_level(report.gaps)
        
        # Extract risks
        report.regulatory_risks = self._extract_regulatory_risks(report.gaps)
        report.business_risks = self._extract_business_risks(report.gaps)
        
        # Generate remediation roadmap
        report.remediation_roadmap = self._generate_remediation_roadmap(report.gaps, report.recommendations)
        report.priority_actions = self._extract_priority_actions(report.gaps, report.recommendations)
        
        # Extract evidence summary
        report.evidence_summary = self._extract_evidence_summary(compliance_results)
        report.documentation_gaps = self._extract_documentation_gaps(report.gaps)
        
        # Extract assessment details
        report.assessment_details = self._extract_assessment_details(compliance_results)
        
        # Store report
        self.reports[report.report_id] = report
        self.report_history.append(report.report_id)
        
        return report
    
    def _generate_report_title(self, report_type: ComplianceReportType, target_organization: str) -> str:
        """Generate report title"""
        
        type_titles = {
            ComplianceReportType.GDPR_ASSESSMENT: "GDPR Compliance Assessment",
            ComplianceReportType.PCI_DSS_ASSESSMENT: "PCI DSS Compliance Assessment",
            ComplianceReportType.HIPAA_ASSESSMENT: "HIPAA Compliance Assessment",
            ComplianceReportType.SOX_ASSESSMENT: "SOX Compliance Assessment",
            ComplianceReportType.ISO27001_ASSESSMENT: "ISO 27001 Compliance Assessment",
            ComplianceReportType.MULTI_STANDARD_ASSESSMENT: "Multi-Standard Compliance Assessment",
            ComplianceReportType.GAP_ANALYSIS: "Compliance Gap Analysis",
            ComplianceReportType.REMEDIATION_PLAN: "Compliance Remediation Plan"
        }
        
        base_title = type_titles.get(report_type, "Compliance Report")
        
        if target_organization:
            base_title += f" - {target_organization}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{base_title} ({timestamp})"
    
    def _extract_standards_assessed(self, compliance_results: Any) -> List[str]:
        """Extract standards that were assessed"""
        
        standards = []
        
        # Check for standard-specific results
        if hasattr(compliance_results, 'gdpr_results') and compliance_results.gdpr_results:
            standards.append("GDPR")
        
        if hasattr(compliance_results, 'pci_dss_results') and compliance_results.pci_dss_results:
            standards.append("PCI DSS")
        
        if hasattr(compliance_results, 'hipaa_results') and compliance_results.hipaa_results:
            standards.append("HIPAA")
        
        # Check for general standards list
        if hasattr(compliance_results, 'standards_assessed'):
            standards.extend(compliance_results.standards_assessed)
        
        # Remove duplicates and return
        return list(set(standards))
    
    def _extract_compliance_metrics(self, compliance_results: Any) -> ComplianceMetrics:
        """Extract compliance metrics from results"""
        
        metrics = ComplianceMetrics()
        
        # Basic metrics
        metrics.overall_compliance_score = getattr(compliance_results, 'overall_compliance_score', 0.0)
        metrics.compliance_percentage = getattr(compliance_results, 'compliance_percentage', 0.0)
        metrics.risk_score = getattr(compliance_results, 'risk_score', 0.0)
        
        # Extract requirements
        all_results = getattr(compliance_results, 'all_results', [])
        
        metrics.total_requirements = len(all_results)
        
        # Count by status
        status_counts = {
            "compliant": 0,
            "non_compliant": 0,
            "partially_compliant": 0,
            "not_applicable": 0
        }
        
        for result in all_results:
            status = self._normalize_compliance_status(result.get('status', 'unknown'))
            if status in status_counts:
                status_counts[status] += 1
        
        metrics.compliant_requirements = status_counts['compliant']
        metrics.non_compliant_requirements = status_counts['non_compliant']
        metrics.partially_compliant_requirements = status_counts['partially_compliant']
        metrics.not_applicable_requirements = status_counts['not_applicable']
        
        # Standards assessed
        metrics.standards_assessed = self._extract_standards_assessed(compliance_results)
        
        # Standard-specific scores
        if hasattr(compliance_results, 'standard_scores'):
            metrics.standard_scores = compliance_results.standard_scores
        
        # Assessment metrics
        metrics.assessment_coverage = getattr(compliance_results, 'assessment_coverage', 0.0)
        metrics.assessment_duration = getattr(compliance_results, 'assessment_duration', 0.0)
        
        # Check types
        automated_checks = len([r for r in all_results if r.get('check_type') == 'automated'])
        manual_checks = len([r for r in all_results if r.get('check_type') == 'manual'])
        
        metrics.automated_checks = automated_checks
        metrics.manual_checks = manual_checks
        
        return metrics
    
    def _normalize_compliance_status(self, status: str) -> str:
        """Normalize compliance status"""
        
        status = str(status).lower()
        
        if status in ['compliant', 'pass', 'passed', 'satisfied']:
            return 'compliant'
        elif status in ['non_compliant', 'non-compliant', 'fail', 'failed', 'not_satisfied']:
            return 'non_compliant'
        elif status in ['partially_compliant', 'partially-compliant', 'partial', 'warning']:
            return 'partially_compliant'
        elif status in ['not_applicable', 'not-applicable', 'n/a', 'na']:
            return 'not_applicable'
        else:
            return 'unknown'
    
    def _extract_compliance_gaps(self, compliance_results: Any) -> List[ComplianceGap]:
        """Extract detailed compliance gaps"""
        
        gaps = []
        all_results = getattr(compliance_results, 'all_results', [])
        
        gap_counter = 1
        
        for result in all_results:
            status = self._normalize_compliance_status(result.get('status', 'unknown'))
            
            # Only create gaps for non-compliant and partially compliant items
            if status in ['non_compliant', 'partially_compliant']:
                gap = ComplianceGap(
                    gap_id=f"GAP-{gap_counter:04d}",
                    requirement_id=result.get('requirement_id', f"REQ-{gap_counter}"),
                    requirement_title=result.get('requirement_title', result.get('title', 'Unknown Requirement')),
                    standard=result.get('standard', 'Unknown'),
                    gap_description=result.get('gap_description', result.get('description', 'Compliance gap identified')),
                    current_state=result.get('current_state', 'Not documented'),
                    required_state=result.get('required_state', 'Compliant state required'),
                    gap_type=self._determine_gap_type(result),
                    risk_level=self._assess_gap_risk_level(result),
                    business_impact=result.get('business_impact', 'Impact assessment required'),
                    regulatory_impact=result.get('regulatory_impact', 'Regulatory review required'),
                    evidence_required=result.get('evidence_required', []),
                    evidence_found=result.get('evidence_found', []),
                    evidence_gaps=result.get('evidence_gaps', []),
                    remediation_actions=result.get('remediation_actions', []),
                    remediation_priority=self._calculate_remediation_priority(result),
                    estimated_effort=result.get('estimated_effort', 'UNKNOWN'),
                    estimated_timeline=result.get('estimated_timeline', 'UNKNOWN'),
                    responsible_party=result.get('responsible_party'),
                    status='OPEN',
                    identified_date=datetime.now()
                )
                
                gaps.append(gap)
                gap_counter += 1
        
        return gaps
    
    def _determine_gap_type(self, result: Dict[str, Any]) -> str:
        """Determine the type of compliance gap"""
        
        gap_type = result.get('gap_type', '').upper()
        
        if gap_type in ['MISSING', 'INADEQUATE', 'INEFFECTIVE', 'OUTDATED']:
            return gap_type
        
        # Infer from other fields
        if not result.get('evidence_found'):
            return 'MISSING'
        elif result.get('status') == 'partially_compliant':
            return 'INADEQUATE'
        else:
            return 'INEFFECTIVE'
    
    def _assess_gap_risk_level(self, result: Dict[str, Any]) -> ComplianceRiskLevel:
        """Assess risk level for a compliance gap"""
        
        # Check explicit risk level
        risk_level = result.get('risk_level', '').lower()
        
        if risk_level == 'critical':
            return ComplianceRiskLevel.CRITICAL
        elif risk_level == 'high':
            return ComplianceRiskLevel.HIGH
        elif risk_level == 'medium':
            return ComplianceRiskLevel.MEDIUM
        elif risk_level == 'low':
            return ComplianceRiskLevel.LOW
        
        # Infer from other factors
        severity = result.get('severity', '').lower()
        impact = result.get('impact', '').lower()
        
        if severity == 'critical' or impact == 'high':
            return ComplianceRiskLevel.CRITICAL
        elif severity == 'high' or impact == 'medium':
            return ComplianceRiskLevel.HIGH
        elif severity == 'medium':
            return ComplianceRiskLevel.MEDIUM
        else:
            return ComplianceRiskLevel.LOW
    
    def _calculate_remediation_priority(self, result: Dict[str, Any]) -> str:
        """Calculate remediation priority"""
        
        risk_level = self._assess_gap_risk_level(result)
        
        if risk_level == ComplianceRiskLevel.CRITICAL:
            return 'CRITICAL'
        elif risk_level == ComplianceRiskLevel.HIGH:
            return 'HIGH'
        elif risk_level == ComplianceRiskLevel.MEDIUM:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_executive_summary(
        self,
        metrics: ComplianceMetrics,
        gaps: List[ComplianceGap]
    ) -> str:
        """Generate executive summary"""
        
        summary_parts = []
        
        # Overall assessment
        summary_parts.append(f"Compliance Assessment Summary:")
        summary_parts.append(f"- Overall Compliance Score: {metrics.overall_compliance_score:.1%}")
        summary_parts.append(f"- Compliance Percentage: {metrics.compliance_percentage:.1%}")
        summary_parts.append(f"- Standards Assessed: {', '.join(metrics.standards_assessed)}")
        
        # Requirements summary
        summary_parts.append(f"\nRequirements Assessment:")
        summary_parts.append(f"- Total Requirements: {metrics.total_requirements}")
        summary_parts.append(f"- Compliant: {metrics.compliant_requirements}")
        summary_parts.append(f"- Non-Compliant: {metrics.non_compliant_requirements}")
        summary_parts.append(f"- Partially Compliant: {metrics.partially_compliant_requirements}")
        
        # Gap summary
        summary_parts.append(f"\nCompliance Gaps:")
        summary_parts.append(f"- Total Gaps: {len(gaps)}")
        
        gap_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for gap in gaps:
            risk_level = gap.risk_level.value if isinstance(gap.risk_level, ComplianceRiskLevel) else gap.risk_level
            if risk_level in gap_counts:
                gap_counts[risk_level] += 1
        
        summary_parts.append(f"- Critical Risk: {gap_counts['critical']}")
        summary_parts.append(f"- High Risk: {gap_counts['high']}")
        summary_parts.append(f"- Medium Risk: {gap_counts['medium']}")
        summary_parts.append(f"- Low Risk: {gap_counts['low']}")
        
        # Key concerns
        if gap_counts['critical'] > 0:
            summary_parts.append(f"\n⚠️  CRITICAL: {gap_counts['critical']} critical compliance gaps require immediate attention")
        
        if gap_counts['high'] > 0:
            summary_parts.append(f"\n⚠️  HIGH PRIORITY: {gap_counts['high']} high-risk compliance gaps identified")
        
        # Assessment coverage
        summary_parts.append(f"\nAssessment Coverage: {metrics.assessment_coverage:.1%}")
        summary_parts.append(f"Automated Checks: {metrics.automated_checks}")
        summary_parts.append(f"Manual Checks: {metrics.manual_checks}")
        
        return "\n".join(summary_parts)
    
    def _extract_key_findings(
        self,
        gaps: List[ComplianceGap],
        metrics: ComplianceMetrics
    ) -> List[str]:
        """Extract key compliance findings"""
        
        findings = []
        
        # Critical gaps
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        if critical_gaps:
            findings.append(f"{len(critical_gaps)} critical compliance gaps pose significant regulatory risk")
            
            # Highlight specific critical gaps
            for gap in critical_gaps[:3]:  # Top 3
                findings.append(f"Critical Gap: {gap.requirement_title} - {gap.gap_description[:100]}...")
        
        # Standard-specific findings
        standard_gaps = {}
        for gap in gaps:
            standard = gap.standard
            if standard not in standard_gaps:
                standard_gaps[standard] = []
            standard_gaps[standard].append(gap)
        
        for standard, std_gaps in standard_gaps.items():
            if len(std_gaps) > 0:
                findings.append(f"{standard}: {len(std_gaps)} compliance gaps identified")
        
        # High-risk gaps
        high_risk_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.HIGH]
        if high_risk_gaps:
            findings.append(f"{len(high_risk_gaps)} high-risk gaps require priority attention")
        
        # Evidence gaps
        evidence_gaps = [g for g in gaps if g.evidence_gaps]
        if evidence_gaps:
            findings.append(f"{len(evidence_gaps)} requirements lack sufficient evidence documentation")
        
        # Control gaps
        missing_controls = [g for g in gaps if g.gap_type == 'MISSING']
        if missing_controls:
            findings.append(f"{len(missing_controls)} required controls are missing")
        
        # Ineffective controls
        ineffective_controls = [g for g in gaps if g.gap_type == 'INEFFECTIVE']
        if ineffective_controls:
            findings.append(f"{len(ineffective_controls)} controls are ineffective")
        
        return findings
    
    def _generate_compliance_recommendations(
        self,
        gaps: List[ComplianceGap],
        metrics: ComplianceMetrics
    ) -> List[ComplianceRecommendation]:
        """Generate compliance recommendations"""
        
        recommendations = []
        
        # Critical gap remediation
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        if critical_gaps:
            rec = ComplianceRecommendation(
                recommendation_id="COMP-REC-001",
                title="Address Critical Compliance Gaps",
                description=f"Immediately remediate {len(critical_gaps)} critical compliance gaps",
                priority="CRITICAL",
                category="gap_remediation",
                standard="Multi-Standard",
                implementation_steps=[
                    "Review all critical compliance gaps",
                    "Prioritize based on regulatory impact",
                    "Implement required controls and processes",
                    "Document evidence and procedures",
                    "Validate compliance through testing"
                ],
                estimated_effort="HIGH",
                timeline="1-3 months",
                compliance_improvement="HIGH",
                gaps_addressed=[g.gap_id for g in critical_gaps],
                risk_reduction="HIGH"
            )
            recommendations.append(rec)
        
        # Documentation improvements
        evidence_gaps = [g for g in gaps if g.evidence_gaps]
        if evidence_gaps:
            rec = ComplianceRecommendation(
                recommendation_id="COMP-REC-002",
                title="Improve Documentation and Evidence Management",
                description="Establish comprehensive documentation practices",
                priority="HIGH",
                category="documentation",
                standard="Multi-Standard",
                implementation_steps=[
                    "Implement document management system",
                    "Create evidence collection procedures",
                    "Establish document retention policies",
                    "Train staff on documentation requirements",
                    "Implement regular documentation reviews"
                ],
                estimated_effort="MEDIUM",
                timeline="2-4 months",
                compliance_improvement="MEDIUM"
            )
            recommendations.append(rec)
        
        # Control implementation
        missing_controls = [g for g in gaps if g.gap_type == 'MISSING']
        if missing_controls:
            rec = ComplianceRecommendation(
                recommendation_id="COMP-REC-003",
                title="Implement Missing Controls",
                description="Deploy required security and compliance controls",
                priority="HIGH",
                category="control_implementation",
                standard="Multi-Standard",
                implementation_steps=[
                    "Conduct control gap analysis",
                    "Design control implementation plan",
                    "Deploy technical and administrative controls",
                    "Establish control monitoring procedures",
                    "Validate control effectiveness"
                ],
                estimated_effort="HIGH",
                timeline="3-6 months",
                compliance_improvement="HIGH"
            )
            recommendations.append(rec)
        
        # Process improvements
        ineffective_controls = [g for g in gaps if g.gap_type == 'INEFFECTIVE']
        if ineffective_controls:
            rec = ComplianceRecommendation(
                recommendation_id="COMP-REC-004",
                title="Enhance Control Effectiveness",
                description="Improve existing but ineffective controls",
                priority="MEDIUM",
                category="process_improvement",
                standard="Multi-Standard",
                implementation_steps=[
                    "Assess current control effectiveness",
                    "Identify improvement opportunities",
                    "Redesign control procedures",
                    "Implement enhanced monitoring",
                    "Conduct effectiveness testing"
                ],
                estimated_effort="MEDIUM",
                timeline="2-4 months",
                compliance_improvement="MEDIUM"
            )
            recommendations.append(rec)
        
        # Compliance monitoring
        if len(gaps) > 10:
            rec = ComplianceRecommendation(
                recommendation_id="COMP-REC-005",
                title="Establish Continuous Compliance Monitoring",
                description="Implement ongoing compliance assessment and monitoring",
                priority="MEDIUM",
                category="monitoring",
                standard="Multi-Standard",
                implementation_steps=[
                    "Implement compliance monitoring tools",
                    "Establish regular assessment schedules",
                    "Create compliance dashboards",
                    "Implement automated compliance checks",
                    "Establish compliance reporting procedures"
                ],
                estimated_effort="HIGH",
                timeline="4-6 months",
                compliance_improvement="MEDIUM"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _assess_overall_compliance_status(
        self,
        metrics: ComplianceMetrics,
        gaps: List[ComplianceGap]
    ) -> ComplianceStatus:
        """Assess overall compliance status"""
        
        if metrics.compliance_percentage >= 95:
            return ComplianceStatus.COMPLIANT
        elif metrics.compliance_percentage >= 80:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        elif metrics.compliance_percentage >= 50:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.NON_COMPLIANT
    
    def _assess_standard_compliance_status(self, compliance_results: Any) -> Dict[str, ComplianceStatus]:
        """Assess compliance status for each standard"""
        
        status_map = {}
        
        # Check for standard-specific results
        if hasattr(compliance_results, 'standard_scores'):
            for standard, score in compliance_results.standard_scores.items():
                if score >= 0.95:
                    status_map[standard] = ComplianceStatus.COMPLIANT
                elif score >= 0.80:
                    status_map[standard] = ComplianceStatus.PARTIALLY_COMPLIANT
                else:
                    status_map[standard] = ComplianceStatus.NON_COMPLIANT
        
        return status_map
    
    def _assess_overall_risk_level(self, gaps: List[ComplianceGap]) -> ComplianceRiskLevel:
        """Assess overall compliance risk level"""
        
        if not gaps:
            return ComplianceRiskLevel.MINIMAL
        
        # Count gaps by risk level
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for gap in gaps:
            risk_level = gap.risk_level.value if isinstance(gap.risk_level, ComplianceRiskLevel) else gap.risk_level
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
        
        # Determine overall risk
        if risk_counts['critical'] > 0:
            return ComplianceRiskLevel.CRITICAL
        elif risk_counts['high'] > 3:
            return ComplianceRiskLevel.CRITICAL
        elif risk_counts['high'] > 0:
            return ComplianceRiskLevel.HIGH
        elif risk_counts['medium'] > 5:
            return ComplianceRiskLevel.HIGH
        elif risk_counts['medium'] > 0:
            return ComplianceRiskLevel.MEDIUM
        else:
            return ComplianceRiskLevel.LOW
    
    def _extract_regulatory_risks(self, gaps: List[ComplianceGap]) -> List[str]:
        """Extract regulatory risks from gaps"""
        
        risks = []
        
        # Critical regulatory risks
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        if critical_gaps:
            risks.append(f"Potential regulatory sanctions due to {len(critical_gaps)} critical compliance gaps")
        
        # Standard-specific risks
        standard_risks = {}
        for gap in gaps:
            standard = gap.standard
            if standard not in standard_risks:
                standard_risks[standard] = []
            standard_risks[standard].append(gap)
        
        for standard, std_gaps in standard_risks.items():
            high_risk_gaps = [g for g in std_gaps if g.risk_level in [ComplianceRiskLevel.CRITICAL, ComplianceRiskLevel.HIGH]]
            if high_risk_gaps:
                risks.append(f"{standard}: Risk of non-compliance findings ({len(high_risk_gaps)} high-risk gaps)")
        
        # Evidence risks
        evidence_gaps = [g for g in gaps if g.evidence_gaps]
        if evidence_gaps:
            risks.append(f"Audit findings likely due to insufficient evidence ({len(evidence_gaps)} gaps)")
        
        return risks
    
    def _extract_business_risks(self, gaps: List[ComplianceGap]) -> List[str]:
        """Extract business risks from gaps"""
        
        risks = []
        
        # Financial risks
        high_risk_gaps = [g for g in gaps if g.risk_level in [ComplianceRiskLevel.CRITICAL, ComplianceRiskLevel.HIGH]]
        if high_risk_gaps:
            risks.append(f"Potential financial penalties and legal costs ({len(high_risk_gaps)} high-risk gaps)")
        
        # Operational risks
        missing_controls = [g for g in gaps if g.gap_type == 'MISSING']
        if missing_controls:
            risks.append(f"Operational disruption risk due to missing controls ({len(missing_controls)} gaps)")
        
        # Reputational risks
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        if critical_gaps:
            risks.append(f"Reputational damage from compliance failures ({len(critical_gaps)} critical gaps)")
        
        # Business continuity risks
        ineffective_controls = [g for g in gaps if g.gap_type == 'INEFFECTIVE']
        if ineffective_controls:
            risks.append(f"Business process inefficiencies ({len(ineffective_controls)} ineffective controls)")
        
        return risks
    
    def _generate_remediation_roadmap(
        self,
        gaps: List[ComplianceGap],
        recommendations: List[ComplianceRecommendation]
    ) -> List[Dict[str, Any]]:
        """Generate remediation roadmap"""
        
        roadmap = []
        
        # Phase 1: Critical gaps (0-3 months)
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        if critical_gaps:
            roadmap.append({
                "phase": "Phase 1: Critical Remediation",
                "timeline": "0-3 months",
                "priority": "CRITICAL",
                "gaps_addressed": len(critical_gaps),
                "key_activities": [
                    "Address all critical compliance gaps",
                    "Implement emergency controls",
                    "Document immediate remediation actions",
                    "Conduct validation testing"
                ],
                "success_criteria": [
                    "All critical gaps resolved",
                    "Emergency controls operational",
                    "Regulatory risk mitigated"
                ]
            })
        
        # Phase 2: High-risk gaps (3-6 months)
        high_risk_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.HIGH]
        if high_risk_gaps:
            roadmap.append({
                "phase": "Phase 2: High-Priority Remediation",
                "timeline": "3-6 months",
                "priority": "HIGH",
                "gaps_addressed": len(high_risk_gaps),
                "key_activities": [
                    "Implement missing controls",
                    "Enhance documentation processes",
                    "Establish monitoring procedures",
                    "Conduct staff training"
                ],
                "success_criteria": [
                    "High-risk gaps resolved",
                    "Control framework established",
                    "Documentation complete"
                ]
            })
        
        # Phase 3: Medium-risk gaps (6-12 months)
        medium_risk_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.MEDIUM]
        if medium_risk_gaps:
            roadmap.append({
                "phase": "Phase 3: Process Optimization",
                "timeline": "6-12 months",
                "priority": "MEDIUM",
                "gaps_addressed": len(medium_risk_gaps),
                "key_activities": [
                    "Optimize existing processes",
                    "Implement automation",
                    "Enhance monitoring capabilities",
                    "Conduct regular assessments"
                ],
                "success_criteria": [
                    "Process efficiency improved",
                    "Automation implemented",
                    "Continuous monitoring active"
                ]
            })
        
        # Phase 4: Continuous improvement (12+ months)
        roadmap.append({
            "phase": "Phase 4: Continuous Improvement",
            "timeline": "12+ months",
            "priority": "LOW",
            "gaps_addressed": "Ongoing",
            "key_activities": [
                "Maintain compliance posture",
                "Regular compliance assessments",
                "Process improvements",
                "Technology updates"
            ],
            "success_criteria": [
                "Sustained compliance",
                "Proactive risk management",
                "Continuous improvement culture"
            ]
        })
        
        return roadmap
    
    def _extract_priority_actions(
        self,
        gaps: List[ComplianceGap],
        recommendations: List[ComplianceRecommendation]
    ) -> List[str]:
        """Extract priority actions"""
        
        actions = []
        
        # Critical gap actions
        critical_gaps = [g for g in gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]
        for gap in critical_gaps[:5]:  # Top 5 critical gaps
            actions.append(f"CRITICAL: {gap.requirement_title} - {gap.remediation_actions[0] if gap.remediation_actions else 'Immediate remediation required'}")
        
        # High-priority recommendations
        high_priority_recs = [r for r in recommendations if r.priority == 'CRITICAL']
        for rec in high_priority_recs[:3]:  # Top 3 recommendations
            actions.append(f"IMPLEMENT: {rec.title}")
        
        # Evidence collection
        evidence_gaps = [g for g in gaps if g.evidence_gaps]
        if evidence_gaps:
            actions.append(f"DOCUMENT: Collect evidence for {len(evidence_gaps)} requirements")
        
        return actions
    
    def _extract_evidence_summary(self, compliance_results: Any) -> Dict[str, Any]:
        """Extract evidence summary"""
        
        return {
            "total_evidence_items": getattr(compliance_results, 'total_evidence_items', 0),
            "evidence_collected": getattr(compliance_results, 'evidence_collected', 0),
            "evidence_gaps": getattr(compliance_results, 'evidence_gaps', 0),
            "evidence_quality": getattr(compliance_results, 'evidence_quality', 'UNKNOWN'),
            "documentation_completeness": getattr(compliance_results, 'documentation_completeness', 0.0)
        }
    
    def _extract_documentation_gaps(self, gaps: List[ComplianceGap]) -> List[str]:
        """Extract documentation gaps"""
        
        doc_gaps = []
        
        for gap in gaps:
            if gap.evidence_gaps:
                for evidence_gap in gap.evidence_gaps:
                    doc_gaps.append(f"{gap.requirement_title}: {evidence_gap}")
        
        return doc_gaps
    
    def _extract_assessment_details(self, compliance_results: Any) -> Dict[str, Any]:
        """Extract assessment execution details"""
        
        return {
            "assessment_start_time": getattr(compliance_results, 'assessment_start_time', None),
            "assessment_end_time": getattr(compliance_results, 'assessment_end_time', None),
            "assessment_duration": getattr(compliance_results, 'assessment_duration', 0.0),
            "standards_assessed": getattr(compliance_results, 'standards_assessed', []),
            "assessment_scope": getattr(compliance_results, 'assessment_scope', ''),
            "assessment_methodology": getattr(compliance_results, 'assessment_methodology', ''),
            "assessors": getattr(compliance_results, 'assessors', []),
            "assessment_tools": getattr(compliance_results, 'assessment_tools', [])
        }
    
    def export_compliance_report(
        self,
        report: ComplianceReport,
        format: str = "html",
        output_path: Optional[Path] = None
    ) -> Path:
        """Export compliance report"""
        
        output_path = output_path or self.output_directory
        
        # Generate filename
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.{format}"
        full_path = output_path / filename
        
        # Export based on format
        if format.lower() == "json":
            self._export_json(report, full_path)
        elif format.lower() == "html":
            self._export_html(report, full_path)
        elif format.lower() == "pdf":
            self._export_pdf(report, full_path)
        else:
            # Default to JSON
            self._export_json(report, full_path)
        
        logger.info(f"Compliance report exported to: {full_path}")
        return full_path
    
    def _export_json(self, report: ComplianceReport, path: Path):
        """Export as JSON"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _export_html(self, report: ComplianceReport, path: Path):
        """Export as HTML"""
        
        html_content = self._generate_html_compliance_report(report)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_pdf(self, report: ComplianceReport, path: Path):
        """Export as PDF (placeholder - would require PDF library)"""
        
        # This would require a PDF generation library like reportlab
        # For now, export as HTML
        html_path = path.with_suffix('.html')
        self._export_html(report, html_path)
        logger.warning(f"PDF export not implemented, exported as HTML: {html_path}")
    
    def _generate_html_compliance_report(self, report: ComplianceReport) -> str:
        """Generate HTML compliance report"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }}
                .gap {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffebee; border-left: 3px solid #d32f2f; }}
                .high {{ background-color: #fff3e0; border-left: 3px solid #f57c00; }}
                .medium {{ background-color: #fffde7; border-left: 3px solid #fbc02d; }}
                .low {{ background-color: #f1f8e9; border-left: 3px solid #388e3c; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .recommendation {{ margin: 10px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }}
                .roadmap {{ margin: 10px 0; padding: 10px; background-color: #f3e5f5; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Target Organization:</strong> {report.target_organization}</p>
                <p><strong>Assessment Scope:</strong> {report.assessment_scope}</p>
                <p><strong>Standards Assessed:</strong> {', '.join(report.standards_assessed)}</p>
                <p><strong>Overall Compliance Status:</strong> <span class="{report.overall_compliance_status.value}">{report.overall_compliance_status.value.upper()}</span></p>
                <p><strong>Overall Risk Level:</strong> <span class="{report.overall_risk_level.value}">{report.overall_risk_level.value.upper()}</span></p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <pre>{report.executive_summary}</pre>
            </div>
        """
        
        # Add metrics
        if report.metrics:
            html += f"""
            <div class="section">
                <h2>Compliance Metrics</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>Compliance Score</h3>
                        <p>{report.metrics.overall_compliance_score:.1%}</p>
                    </div>
                    <div class="metric">
                        <h3>Compliance %</h3>
                        <p>{report.metrics.compliance_percentage:.1%}</p>
                    </div>
                    <div class="metric">
                        <h3>Total Requirements</h3>
                        <p>{report.metrics.total_requirements}</p>
                    </div>
                    <div class="metric">
                        <h3>Compliant</h3>
                        <p class="low">{report.metrics.compliant_requirements}</p>
                    </div>
                    <div class="metric">
                        <h3>Non-Compliant</h3>
                        <p class="critical">{report.metrics.non_compliant_requirements}</p>
                    </div>
                    <div class="metric">
                        <h3>Partial</h3>
                        <p class="medium">{report.metrics.partially_compliant_requirements}</p>
                    </div>
                </div>
            </div>
            """
        
        # Add key findings
        if report.key_findings:
            html += """
            <div class="section">
                <h2>Key Findings</h2>
                <ul>
            """
            for finding in report.key_findings:
                html += f"<li>{finding}</li>"
            html += """
                </ul>
            </div>
            """
        
        # Add compliance gaps
        if report.gaps:
            html += """
            <div class="section">
                <h2>Compliance Gaps</h2>
            """
            
            for gap in report.gaps:
                risk_class = gap.risk_level.value if hasattr(gap.risk_level, 'value') else gap.risk_level
                html += f"""
                <div class="gap {risk_class}">
                    <h3>{gap.requirement_title} <span class="{risk_class}">({gap.risk_level.value.upper() if hasattr(gap.risk_level, 'value') else gap.risk_level.upper()})</span></h3>
                    <p><strong>Gap ID:</strong> {gap.gap_id}</p>
                    <p><strong>Standard:</strong> {gap.standard}</p>
                    <p><strong>Description:</strong> {gap.gap_description}</p>
                    <p><strong>Gap Type:</strong> {gap.gap_type}</p>
                    <p><strong>Current State:</strong> {gap.current_state}</p>
                    <p><strong>Required State:</strong> {gap.required_state}</p>
                    <p><strong>Business Impact:</strong> {gap.business_impact}</p>
                    <p><strong>Remediation Priority:</strong> {gap.remediation_priority}</p>
                </div>
                """
            
            html += """
            </div>
            """
        
        # Add recommendations
        if report.recommendations:
            html += """
            <div class="section">
                <h2>Recommendations</h2>
            """
            
            for rec in report.recommendations:
                html += f"""
                <div class="recommendation">
                    <h3>[{rec.priority}] {rec.title}</h3>
                    <p>{rec.description}</p>
                    <p><strong>Standard:</strong> {rec.standard}</p>
                    <p><strong>Estimated Effort:</strong> {rec.estimated_effort}</p>
                    <p><strong>Timeline:</strong> {rec.timeline}</p>
                    {f'<p><strong>Compliance Improvement:</strong> {rec.compliance_improvement}</p>' if rec.compliance_improvement != 'UNKNOWN' else ''}
                </div>
                """
            
            html += """
            </div>
            """
        
        # Add remediation roadmap
        if report.remediation_roadmap:
            html += """
            <div class="section">
                <h2>Remediation Roadmap</h2>
            """
            
            for phase in report.remediation_roadmap:
                html += f"""
                <div class="roadmap">
                    <h3>{phase['phase']}</h3>
                    <p><strong>Timeline:</strong> {phase['timeline']}</p>
                    <p><strong>Priority:</strong> {phase['priority']}</p>
                    <p><strong>Gaps Addressed:</strong> {phase['gaps_addressed']}</p>
                    <p><strong>Key Activities:</strong></p>
                    <ul>
                """
                for activity in phase['key_activities']:
                    html += f"<li>{activity}</li>"
                html += """
                    </ul>
                </div>
                """
            
            html += """
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def get_compliance_statistics(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get compliance statistics for a report"""
        
        if report_id not in self.reports:
            return None
        
        report = self.reports[report_id]
        
        if not report.metrics:
            return None
        
        return {
            "overall_compliance_score": report.metrics.overall_compliance_score,
            "compliance_percentage": report.metrics.compliance_percentage,
            "risk_score": report.metrics.risk_score,
            "requirements": {
                "total": report.metrics.total_requirements,
                "compliant": report.metrics.compliant_requirements,
                "non_compliant": report.metrics.non_compliant_requirements,
                "partially_compliant": report.metrics.partially_compliant_requirements,
                "not_applicable": report.metrics.not_applicable_requirements
            },
            "gaps": {
                "total": len(report.gaps),
                "critical": len([g for g in report.gaps if g.risk_level == ComplianceRiskLevel.CRITICAL]),
                "high": len([g for g in report.gaps if g.risk_level == ComplianceRiskLevel.HIGH]),
                "medium": len([g for g in report.gaps if g.risk_level == ComplianceRiskLevel.MEDIUM]),
                "low": len([g for g in report.gaps if g.risk_level == ComplianceRiskLevel.LOW])
            },
            "standards_assessed": report.metrics.standards_assessed,
            "standard_scores": report.metrics.standard_scores,
            "overall_compliance_status": report.overall_compliance_status.value,
            "overall_risk_level": report.overall_risk_level.value
        }


# Utility functions
def generate_gdpr_compliance_report(compliance_results: Any, target_organization: str = "") -> ComplianceReport:
    """Generate GDPR compliance report"""
    
    reporter = ComplianceReporter()
    
    return reporter.generate_compliance_report(
        compliance_results=compliance_results,
        report_type=ComplianceReportType.GDPR_ASSESSMENT,
        target_organization=target_organization
    )


def generate_multi_standard_compliance_report(compliance_results: Any, target_organization: str = "") -> ComplianceReport:
    """Generate multi-standard compliance report"""
    
    reporter = ComplianceReporter()
    
    return reporter.generate_compliance_report(
        compliance_results=compliance_results,
        report_type=ComplianceReportType.MULTI_STANDARD_ASSESSMENT,
        target_organization=target_organization
    )