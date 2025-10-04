"""
Security Reporter

Specialized reporting for security assessment results, vulnerability analysis,
threat assessment, and security recommendations.
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


class SecurityReportType(Enum):
    """Security report types"""
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    PENETRATION_TEST = "penetration_test"
    SECURITY_AUDIT = "security_audit"
    THREAT_ANALYSIS = "threat_analysis"
    COMPLIANCE_SECURITY = "compliance_security"
    INCIDENT_ANALYSIS = "incident_analysis"


class VulnerabilityCategory(Enum):
    """Vulnerability categories"""
    INJECTION = "injection"
    BROKEN_AUTHENTICATION = "broken_authentication"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    XML_EXTERNAL_ENTITIES = "xml_external_entities"
    BROKEN_ACCESS_CONTROL = "broken_access_control"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    CROSS_SITE_SCRIPTING = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    KNOWN_VULNERABILITIES = "known_vulnerabilities"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SERVER_SIDE_REQUEST_FORGERY = "server_side_request_forgery"
    CRYPTOGRAPHIC_FAILURES = "cryptographic_failures"


class ThreatLevel(Enum):
    """Threat levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class SecurityMetrics:
    """Security-specific metrics"""
    
    # Overall security metrics
    security_score: float = 0.0
    risk_rating: str = "UNKNOWN"
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    
    # Vulnerability metrics
    total_vulnerabilities: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0
    informational_vulnerabilities: int = 0
    
    # Vulnerability by category
    vulnerability_categories: Dict[str, int] = field(default_factory=dict)
    
    # Scanner metrics
    scanners_used: List[str] = field(default_factory=list)
    scan_coverage: float = 0.0
    scan_duration: float = 0.0
    
    # Remediation metrics
    vulnerabilities_fixed: int = 0
    vulnerabilities_mitigated: int = 0
    vulnerabilities_accepted: int = 0
    vulnerabilities_pending: int = 0
    
    # Trend data
    security_trend: List[float] = field(default_factory=list)
    vulnerability_trend: List[int] = field(default_factory=list)
    
    # OWASP Top 10 mapping
    owasp_top10_coverage: Dict[str, int] = field(default_factory=dict)
    
    # False positive metrics
    false_positives: int = 0
    false_positive_rate: float = 0.0


@dataclass
class VulnerabilityDetail:
    """Detailed vulnerability information"""
    
    vulnerability_id: str
    title: str
    description: str
    severity: str
    category: VulnerabilityCategory
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    owasp_category: Optional[str] = None
    
    # Location information
    url: Optional[str] = None
    parameter: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    
    # Technical details
    attack_vector: Optional[str] = None
    payload: Optional[str] = None
    evidence: Optional[str] = None
    
    # Risk assessment
    exploitability: str = "UNKNOWN"
    impact: str = "UNKNOWN"
    likelihood: str = "UNKNOWN"
    
    # Remediation
    remediation: Optional[str] = None
    remediation_effort: str = "UNKNOWN"
    remediation_priority: str = "MEDIUM"
    
    # Scanner information
    scanner: str = ""
    scan_timestamp: Optional[datetime] = None
    
    # Status tracking
    status: str = "OPEN"  # OPEN, FIXED, MITIGATED, ACCEPTED, FALSE_POSITIVE
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "vulnerability_id": self.vulnerability_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category.value if isinstance(self.category, VulnerabilityCategory) else self.category,
            "cwe_id": self.cwe_id,
            "cve_id": self.cve_id,
            "owasp_category": self.owasp_category,
            "url": self.url,
            "parameter": self.parameter,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "attack_vector": self.attack_vector,
            "payload": self.payload,
            "evidence": self.evidence,
            "exploitability": self.exploitability,
            "impact": self.impact,
            "likelihood": self.likelihood,
            "remediation": self.remediation,
            "remediation_effort": self.remediation_effort,
            "remediation_priority": self.remediation_priority,
            "scanner": self.scanner,
            "scan_timestamp": self.scan_timestamp.isoformat() if self.scan_timestamp else None,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None
        }


@dataclass
class SecurityRecommendation:
    """Security recommendation"""
    
    recommendation_id: str
    title: str
    description: str
    priority: str
    category: str
    
    # Implementation details
    implementation_steps: List[str] = field(default_factory=list)
    estimated_effort: str = "UNKNOWN"
    timeline: str = "UNKNOWN"
    cost_estimate: Optional[str] = None
    
    # Risk mitigation
    risk_reduction: str = "UNKNOWN"
    vulnerabilities_addressed: List[str] = field(default_factory=list)
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Compliance
    compliance_standards: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "implementation_steps": self.implementation_steps,
            "estimated_effort": self.estimated_effort,
            "timeline": self.timeline,
            "cost_estimate": self.cost_estimate,
            "risk_reduction": self.risk_reduction,
            "vulnerabilities_addressed": self.vulnerabilities_addressed,
            "prerequisites": self.prerequisites,
            "dependencies": self.dependencies,
            "compliance_standards": self.compliance_standards
        }


@dataclass
class SecurityReport:
    """Comprehensive security report"""
    
    report_id: str
    title: str
    report_type: SecurityReportType
    generated_at: datetime
    
    # Report metadata
    target_system: str = ""
    environment: str = ""
    scan_scope: str = ""
    methodology: str = ""
    
    # Executive summary
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    
    # Metrics and analysis
    metrics: Optional[SecurityMetrics] = None
    vulnerabilities: List[VulnerabilityDetail] = field(default_factory=list)
    recommendations: List[SecurityRecommendation] = field(default_factory=list)
    
    # Risk assessment
    overall_risk_rating: str = "UNKNOWN"
    business_impact: str = ""
    technical_impact: str = ""
    
    # Compliance mapping
    compliance_gaps: List[Dict[str, Any]] = field(default_factory=list)
    regulatory_implications: List[str] = field(default_factory=list)
    
    # Appendices
    scan_details: Dict[str, Any] = field(default_factory=dict)
    tool_configurations: Dict[str, Any] = field(default_factory=dict)
    raw_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "target_system": self.target_system,
            "environment": self.environment,
            "scan_scope": self.scan_scope,
            "methodology": self.methodology,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "metrics": self._metrics_to_dict() if self.metrics else None,
            "vulnerabilities": [vuln.to_dict() for vuln in self.vulnerabilities],
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "overall_risk_rating": self.overall_risk_rating,
            "business_impact": self.business_impact,
            "technical_impact": self.technical_impact,
            "compliance_gaps": self.compliance_gaps,
            "regulatory_implications": self.regulatory_implications,
            "scan_details": self.scan_details,
            "tool_configurations": self.tool_configurations,
            "raw_results": self.raw_results
        }
    
    def _metrics_to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        if not self.metrics:
            return {}
        
        return {
            "security_score": self.metrics.security_score,
            "risk_rating": self.metrics.risk_rating,
            "threat_level": self.metrics.threat_level.value,
            "vulnerabilities": {
                "total": self.metrics.total_vulnerabilities,
                "critical": self.metrics.critical_vulnerabilities,
                "high": self.metrics.high_vulnerabilities,
                "medium": self.metrics.medium_vulnerabilities,
                "low": self.metrics.low_vulnerabilities,
                "informational": self.metrics.informational_vulnerabilities
            },
            "vulnerability_categories": self.metrics.vulnerability_categories,
            "scanners_used": self.metrics.scanners_used,
            "scan_coverage": self.metrics.scan_coverage,
            "scan_duration": self.metrics.scan_duration,
            "remediation": {
                "fixed": self.metrics.vulnerabilities_fixed,
                "mitigated": self.metrics.vulnerabilities_mitigated,
                "accepted": self.metrics.vulnerabilities_accepted,
                "pending": self.metrics.vulnerabilities_pending
            },
            "trends": {
                "security": self.metrics.security_trend,
                "vulnerabilities": self.metrics.vulnerability_trend
            },
            "owasp_top10_coverage": self.metrics.owasp_top10_coverage,
            "false_positives": {
                "count": self.metrics.false_positives,
                "rate": self.metrics.false_positive_rate
            }
        }


class SecurityReporter:
    """Security-focused reporter"""
    
    def __init__(self):
        self.name = "Security Reporter"
        self.version = "1.0.0"
        
        # Report storage
        self.reports: Dict[str, SecurityReport] = {}
        self.report_history: List[str] = []
        
        # Configuration
        self.output_directory = Path("reports/security")
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # OWASP Top 10 mapping
        self.owasp_top10_2021 = {
            "A01": "Broken Access Control",
            "A02": "Cryptographic Failures",
            "A03": "Injection",
            "A04": "Insecure Design",
            "A05": "Security Misconfiguration",
            "A06": "Vulnerable and Outdated Components",
            "A07": "Identification and Authentication Failures",
            "A08": "Software and Data Integrity Failures",
            "A09": "Security Logging and Monitoring Failures",
            "A10": "Server-Side Request Forgery"
        }
    
    def generate_security_report(
        self,
        security_results: Any,
        report_type: SecurityReportType = SecurityReportType.VULNERABILITY_ASSESSMENT,
        target_system: str = "",
        environment: str = ""
    ) -> SecurityReport:
        """Generate comprehensive security report"""
        
        # Create report
        report = SecurityReport(
            report_id=str(uuid.uuid4()),
            title=self._generate_report_title(report_type, target_system),
            report_type=report_type,
            generated_at=datetime.now(),
            target_system=target_system,
            environment=environment
        )
        
        # Extract metrics
        report.metrics = self._extract_security_metrics(security_results)
        
        # Extract vulnerabilities
        report.vulnerabilities = self._extract_vulnerabilities(security_results)
        
        # Generate executive summary
        report.executive_summary = self._generate_executive_summary(report.metrics, report.vulnerabilities)
        
        # Extract key findings
        report.key_findings = self._extract_key_findings(report.vulnerabilities, report.metrics)
        
        # Generate recommendations
        report.recommendations = self._generate_security_recommendations(report.vulnerabilities, report.metrics)
        
        # Assess overall risk
        report.overall_risk_rating = self._assess_overall_risk(report.metrics, report.vulnerabilities)
        
        # Generate impact assessments
        report.business_impact = self._assess_business_impact(report.vulnerabilities)
        report.technical_impact = self._assess_technical_impact(report.vulnerabilities)
        
        # Extract scan details
        report.scan_details = self._extract_scan_details(security_results)
        
        # Store report
        self.reports[report.report_id] = report
        self.report_history.append(report.report_id)
        
        return report
    
    def _generate_report_title(self, report_type: SecurityReportType, target_system: str) -> str:
        """Generate report title"""
        
        type_titles = {
            SecurityReportType.VULNERABILITY_ASSESSMENT: "Vulnerability Assessment Report",
            SecurityReportType.PENETRATION_TEST: "Penetration Testing Report",
            SecurityReportType.SECURITY_AUDIT: "Security Audit Report",
            SecurityReportType.THREAT_ANALYSIS: "Threat Analysis Report",
            SecurityReportType.COMPLIANCE_SECURITY: "Security Compliance Report",
            SecurityReportType.INCIDENT_ANALYSIS: "Security Incident Analysis"
        }
        
        base_title = type_titles.get(report_type, "Security Report")
        
        if target_system:
            base_title += f" - {target_system}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{base_title} ({timestamp})"
    
    def _extract_security_metrics(self, security_results: Any) -> SecurityMetrics:
        """Extract security metrics from results"""
        
        metrics = SecurityMetrics()
        
        # Basic metrics
        metrics.security_score = getattr(security_results, 'security_score', 0.0)
        metrics.risk_rating = getattr(security_results, 'risk_level', 'UNKNOWN')
        
        # Extract vulnerabilities
        vulnerabilities = getattr(security_results, 'vulnerabilities', [])
        metrics.total_vulnerabilities = len(vulnerabilities)
        
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        category_counts = {}
        
        for vuln in vulnerabilities:
            # Count by severity
            severity = self._normalize_severity(vuln.get('severity', 'unknown'))
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            # Count by category
            category = vuln.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        metrics.critical_vulnerabilities = severity_counts['critical']
        metrics.high_vulnerabilities = severity_counts['high']
        metrics.medium_vulnerabilities = severity_counts['medium']
        metrics.low_vulnerabilities = severity_counts['low']
        metrics.informational_vulnerabilities = severity_counts['informational']
        
        metrics.vulnerability_categories = category_counts
        
        # Scanner information
        scanners = getattr(security_results, 'scanners_used', [])
        metrics.scanners_used = scanners if isinstance(scanners, list) else [str(scanners)]
        
        metrics.scan_coverage = getattr(security_results, 'scan_coverage', 0.0)
        metrics.scan_duration = getattr(security_results, 'scan_duration', 0.0)
        
        # OWASP Top 10 mapping
        metrics.owasp_top10_coverage = self._map_owasp_top10(vulnerabilities)
        
        # Determine threat level
        if metrics.critical_vulnerabilities > 0:
            metrics.threat_level = ThreatLevel.CRITICAL
        elif metrics.high_vulnerabilities > 0:
            metrics.threat_level = ThreatLevel.HIGH
        elif metrics.medium_vulnerabilities > 0:
            metrics.threat_level = ThreatLevel.MEDIUM
        elif metrics.low_vulnerabilities > 0:
            metrics.threat_level = ThreatLevel.LOW
        else:
            metrics.threat_level = ThreatLevel.INFORMATIONAL
        
        return metrics
    
    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels"""
        
        severity = str(severity).lower()
        
        if severity in ['critical', 'crit']:
            return 'critical'
        elif severity in ['high', 'h']:
            return 'high'
        elif severity in ['medium', 'med', 'm']:
            return 'medium'
        elif severity in ['low', 'l']:
            return 'low'
        elif severity in ['informational', 'info', 'i']:
            return 'informational'
        else:
            return 'unknown'
    
    def _extract_vulnerabilities(self, security_results: Any) -> List[VulnerabilityDetail]:
        """Extract detailed vulnerability information"""
        
        vulnerabilities = []
        raw_vulns = getattr(security_results, 'vulnerabilities', [])
        
        for i, vuln in enumerate(raw_vulns):
            vuln_detail = VulnerabilityDetail(
                vulnerability_id=vuln.get('id', f"VULN-{i+1:04d}"),
                title=vuln.get('title', vuln.get('name', 'Unknown Vulnerability')),
                description=vuln.get('description', 'No description available'),
                severity=self._normalize_severity(vuln.get('severity', 'unknown')),
                category=self._map_vulnerability_category(vuln.get('category', 'unknown')),
                cwe_id=vuln.get('cwe_id'),
                cve_id=vuln.get('cve_id'),
                owasp_category=vuln.get('owasp_category'),
                url=vuln.get('url'),
                parameter=vuln.get('parameter'),
                file_path=vuln.get('file_path'),
                line_number=vuln.get('line_number'),
                attack_vector=vuln.get('attack_vector'),
                payload=vuln.get('payload'),
                evidence=vuln.get('evidence'),
                exploitability=vuln.get('exploitability', 'UNKNOWN'),
                impact=vuln.get('impact', 'UNKNOWN'),
                likelihood=vuln.get('likelihood', 'UNKNOWN'),
                remediation=vuln.get('remediation'),
                remediation_effort=vuln.get('remediation_effort', 'UNKNOWN'),
                remediation_priority=self._calculate_remediation_priority(vuln),
                scanner=vuln.get('scanner', 'Unknown'),
                scan_timestamp=vuln.get('scan_timestamp'),
                status=vuln.get('status', 'OPEN')
            )
            
            vulnerabilities.append(vuln_detail)
        
        return vulnerabilities
    
    def _map_vulnerability_category(self, category: str) -> VulnerabilityCategory:
        """Map vulnerability category to enum"""
        
        category_mapping = {
            'injection': VulnerabilityCategory.INJECTION,
            'sql_injection': VulnerabilityCategory.INJECTION,
            'xss': VulnerabilityCategory.CROSS_SITE_SCRIPTING,
            'cross_site_scripting': VulnerabilityCategory.CROSS_SITE_SCRIPTING,
            'authentication': VulnerabilityCategory.BROKEN_AUTHENTICATION,
            'broken_authentication': VulnerabilityCategory.BROKEN_AUTHENTICATION,
            'access_control': VulnerabilityCategory.BROKEN_ACCESS_CONTROL,
            'broken_access_control': VulnerabilityCategory.BROKEN_ACCESS_CONTROL,
            'misconfiguration': VulnerabilityCategory.SECURITY_MISCONFIGURATION,
            'security_misconfiguration': VulnerabilityCategory.SECURITY_MISCONFIGURATION,
            'sensitive_data': VulnerabilityCategory.SENSITIVE_DATA_EXPOSURE,
            'data_exposure': VulnerabilityCategory.SENSITIVE_DATA_EXPOSURE,
            'cryptographic': VulnerabilityCategory.CRYPTOGRAPHIC_FAILURES,
            'crypto': VulnerabilityCategory.CRYPTOGRAPHIC_FAILURES,
            'ssrf': VulnerabilityCategory.SERVER_SIDE_REQUEST_FORGERY,
            'server_side_request_forgery': VulnerabilityCategory.SERVER_SIDE_REQUEST_FORGERY
        }
        
        return category_mapping.get(category.lower(), VulnerabilityCategory.KNOWN_VULNERABILITIES)
    
    def _calculate_remediation_priority(self, vuln: Dict[str, Any]) -> str:
        """Calculate remediation priority based on vulnerability characteristics"""
        
        severity = self._normalize_severity(vuln.get('severity', 'unknown'))
        exploitability = vuln.get('exploitability', 'unknown').lower()
        impact = vuln.get('impact', 'unknown').lower()
        
        # Critical severity always gets critical priority
        if severity == 'critical':
            return 'CRITICAL'
        
        # High severity with high exploitability
        if severity == 'high' and exploitability in ['high', 'easy']:
            return 'CRITICAL'
        
        # High severity or high impact
        if severity == 'high' or impact == 'high':
            return 'HIGH'
        
        # Medium severity
        if severity == 'medium':
            return 'MEDIUM'
        
        # Low severity
        if severity == 'low':
            return 'LOW'
        
        return 'MEDIUM'  # Default
    
    def _map_owasp_top10(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Map vulnerabilities to OWASP Top 10 categories"""
        
        owasp_mapping = {}
        
        for vuln in vulnerabilities:
            category = vuln.get('category', '').lower()
            owasp_category = None
            
            # Map to OWASP Top 10 2021
            if 'access_control' in category or 'authorization' in category:
                owasp_category = 'A01'
            elif 'crypto' in category or 'encryption' in category:
                owasp_category = 'A02'
            elif 'injection' in category or 'sql' in category or 'xss' in category:
                owasp_category = 'A03'
            elif 'design' in category:
                owasp_category = 'A04'
            elif 'misconfiguration' in category or 'config' in category:
                owasp_category = 'A05'
            elif 'component' in category or 'dependency' in category:
                owasp_category = 'A06'
            elif 'authentication' in category or 'session' in category:
                owasp_category = 'A07'
            elif 'integrity' in category or 'deserialization' in category:
                owasp_category = 'A08'
            elif 'logging' in category or 'monitoring' in category:
                owasp_category = 'A09'
            elif 'ssrf' in category:
                owasp_category = 'A10'
            
            if owasp_category:
                owasp_mapping[owasp_category] = owasp_mapping.get(owasp_category, 0) + 1
        
        return owasp_mapping
    
    def _generate_executive_summary(
        self,
        metrics: SecurityMetrics,
        vulnerabilities: List[VulnerabilityDetail]
    ) -> str:
        """Generate executive summary"""
        
        summary_parts = []
        
        # Overall assessment
        summary_parts.append(f"Security Assessment Summary:")
        summary_parts.append(f"- Security Score: {metrics.security_score:.1%}")
        summary_parts.append(f"- Risk Rating: {metrics.risk_rating}")
        summary_parts.append(f"- Threat Level: {metrics.threat_level.value.upper()}")
        
        # Vulnerability summary
        summary_parts.append(f"\nVulnerability Summary:")
        summary_parts.append(f"- Total Vulnerabilities: {metrics.total_vulnerabilities}")
        summary_parts.append(f"- Critical: {metrics.critical_vulnerabilities}")
        summary_parts.append(f"- High: {metrics.high_vulnerabilities}")
        summary_parts.append(f"- Medium: {metrics.medium_vulnerabilities}")
        summary_parts.append(f"- Low: {metrics.low_vulnerabilities}")
        
        # Key concerns
        if metrics.critical_vulnerabilities > 0:
            summary_parts.append(f"\n⚠️  CRITICAL: {metrics.critical_vulnerabilities} critical vulnerabilities require immediate attention")
        
        if metrics.high_vulnerabilities > 0:
            summary_parts.append(f"\n⚠️  HIGH PRIORITY: {metrics.high_vulnerabilities} high-severity vulnerabilities identified")
        
        # Top vulnerability categories
        if metrics.vulnerability_categories:
            top_categories = sorted(metrics.vulnerability_categories.items(), key=lambda x: x[1], reverse=True)[:3]
            summary_parts.append(f"\nTop Vulnerability Categories:")
            for category, count in top_categories:
                summary_parts.append(f"- {category}: {count} vulnerabilities")
        
        # Scanning coverage
        summary_parts.append(f"\nScan Coverage: {metrics.scan_coverage:.1%}")
        summary_parts.append(f"Scanners Used: {', '.join(metrics.scanners_used)}")
        
        return "\n".join(summary_parts)
    
    def _extract_key_findings(
        self,
        vulnerabilities: List[VulnerabilityDetail],
        metrics: SecurityMetrics
    ) -> List[str]:
        """Extract key security findings"""
        
        findings = []
        
        # Critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            findings.append(f"{len(critical_vulns)} critical vulnerabilities pose immediate security risks")
            
            # Highlight specific critical issues
            for vuln in critical_vulns[:3]:  # Top 3
                findings.append(f"Critical: {vuln.title} - {vuln.description[:100]}...")
        
        # High-impact vulnerabilities
        high_impact_vulns = [v for v in vulnerabilities if v.impact == 'HIGH']
        if high_impact_vulns:
            findings.append(f"{len(high_impact_vulns)} vulnerabilities have high business impact")
        
        # OWASP Top 10 coverage
        if metrics.owasp_top10_coverage:
            owasp_count = len(metrics.owasp_top10_coverage)
            findings.append(f"Vulnerabilities span {owasp_count} OWASP Top 10 categories")
        
        # Authentication issues
        auth_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.BROKEN_AUTHENTICATION]
        if auth_vulns:
            findings.append(f"{len(auth_vulns)} authentication vulnerabilities compromise access controls")
        
        # Injection vulnerabilities
        injection_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.INJECTION]
        if injection_vulns:
            findings.append(f"{len(injection_vulns)} injection vulnerabilities enable data compromise")
        
        # Configuration issues
        config_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.SECURITY_MISCONFIGURATION]
        if config_vulns:
            findings.append(f"{len(config_vulns)} security misconfigurations increase attack surface")
        
        return findings
    
    def _generate_security_recommendations(
        self,
        vulnerabilities: List[VulnerabilityDetail],
        metrics: SecurityMetrics
    ) -> List[SecurityRecommendation]:
        """Generate security recommendations"""
        
        recommendations = []
        
        # Critical vulnerability remediation
        critical_vulns = [v for v in vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            rec = SecurityRecommendation(
                recommendation_id="SEC-REC-001",
                title="Address Critical Security Vulnerabilities",
                description=f"Immediately remediate {len(critical_vulns)} critical vulnerabilities",
                priority="CRITICAL",
                category="vulnerability_remediation",
                implementation_steps=[
                    "Review all critical vulnerabilities",
                    "Prioritize based on exploitability and impact",
                    "Implement patches or workarounds",
                    "Verify fixes through re-testing",
                    "Update security controls"
                ],
                estimated_effort="HIGH",
                timeline="1-2 weeks",
                risk_reduction="HIGH",
                vulnerabilities_addressed=[v.vulnerability_id for v in critical_vulns]
            )
            recommendations.append(rec)
        
        # Authentication improvements
        auth_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.BROKEN_AUTHENTICATION]
        if auth_vulns:
            rec = SecurityRecommendation(
                recommendation_id="SEC-REC-002",
                title="Strengthen Authentication Controls",
                description="Implement robust authentication mechanisms",
                priority="HIGH",
                category="authentication",
                implementation_steps=[
                    "Implement multi-factor authentication",
                    "Enforce strong password policies",
                    "Implement account lockout mechanisms",
                    "Use secure session management",
                    "Implement proper logout functionality"
                ],
                estimated_effort="MEDIUM",
                timeline="2-4 weeks",
                risk_reduction="HIGH"
            )
            recommendations.append(rec)
        
        # Input validation
        injection_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.INJECTION]
        if injection_vulns:
            rec = SecurityRecommendation(
                recommendation_id="SEC-REC-003",
                title="Implement Input Validation and Sanitization",
                description="Prevent injection attacks through proper input handling",
                priority="HIGH",
                category="input_validation",
                implementation_steps=[
                    "Implement parameterized queries",
                    "Use input validation libraries",
                    "Sanitize all user inputs",
                    "Implement output encoding",
                    "Use prepared statements"
                ],
                estimated_effort="MEDIUM",
                timeline="3-4 weeks",
                risk_reduction="HIGH"
            )
            recommendations.append(rec)
        
        # Security configuration
        config_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.SECURITY_MISCONFIGURATION]
        if config_vulns:
            rec = SecurityRecommendation(
                recommendation_id="SEC-REC-004",
                title="Harden Security Configuration",
                description="Address security misconfigurations",
                priority="MEDIUM",
                category="configuration",
                implementation_steps=[
                    "Review and harden server configurations",
                    "Disable unnecessary services and features",
                    "Implement security headers",
                    "Configure proper error handling",
                    "Update default credentials"
                ],
                estimated_effort="MEDIUM",
                timeline="2-3 weeks",
                risk_reduction="MEDIUM"
            )
            recommendations.append(rec)
        
        # Security monitoring
        if metrics.total_vulnerabilities > 10:
            rec = SecurityRecommendation(
                recommendation_id="SEC-REC-005",
                title="Implement Security Monitoring",
                description="Establish continuous security monitoring",
                priority="MEDIUM",
                category="monitoring",
                implementation_steps=[
                    "Implement security information and event management (SIEM)",
                    "Set up vulnerability scanning automation",
                    "Implement intrusion detection systems",
                    "Establish security incident response procedures",
                    "Create security dashboards and alerting"
                ],
                estimated_effort="HIGH",
                timeline="4-6 weeks",
                risk_reduction="MEDIUM"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _assess_overall_risk(
        self,
        metrics: SecurityMetrics,
        vulnerabilities: List[VulnerabilityDetail]
    ) -> str:
        """Assess overall security risk"""
        
        # Risk scoring based on vulnerabilities
        risk_score = 0
        
        # Weight by severity
        risk_score += metrics.critical_vulnerabilities * 10
        risk_score += metrics.high_vulnerabilities * 5
        risk_score += metrics.medium_vulnerabilities * 2
        risk_score += metrics.low_vulnerabilities * 1
        
        # Adjust for exploitability
        high_exploitability = len([v for v in vulnerabilities if v.exploitability == 'HIGH'])
        risk_score += high_exploitability * 3
        
        # Determine risk level
        if risk_score >= 50:
            return "CRITICAL"
        elif risk_score >= 25:
            return "HIGH"
        elif risk_score >= 10:
            return "MEDIUM"
        elif risk_score > 0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _assess_business_impact(self, vulnerabilities: List[VulnerabilityDetail]) -> str:
        """Assess business impact of vulnerabilities"""
        
        impact_factors = []
        
        # Data exposure risks
        data_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.SENSITIVE_DATA_EXPOSURE]
        if data_vulns:
            impact_factors.append(f"Risk of sensitive data exposure ({len(data_vulns)} vulnerabilities)")
        
        # Authentication bypass
        auth_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.BROKEN_AUTHENTICATION]
        if auth_vulns:
            impact_factors.append(f"Risk of unauthorized access ({len(auth_vulns)} vulnerabilities)")
        
        # Service disruption
        critical_vulns = [v for v in vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            impact_factors.append(f"Risk of service disruption ({len(critical_vulns)} critical vulnerabilities)")
        
        # Compliance implications
        compliance_vulns = [v for v in vulnerabilities if v.compliance_standards]
        if compliance_vulns:
            impact_factors.append(f"Compliance violations possible ({len(compliance_vulns)} compliance-related vulnerabilities)")
        
        if not impact_factors:
            return "Minimal business impact expected from identified vulnerabilities."
        
        return "Potential business impacts include: " + "; ".join(impact_factors) + "."
    
    def _assess_technical_impact(self, vulnerabilities: List[VulnerabilityDetail]) -> str:
        """Assess technical impact of vulnerabilities"""
        
        impact_factors = []
        
        # System compromise
        critical_vulns = [v for v in vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            impact_factors.append(f"System compromise possible ({len(critical_vulns)} critical vulnerabilities)")
        
        # Data integrity
        injection_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.INJECTION]
        if injection_vulns:
            impact_factors.append(f"Data integrity at risk ({len(injection_vulns)} injection vulnerabilities)")
        
        # Access control bypass
        access_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.BROKEN_ACCESS_CONTROL]
        if access_vulns:
            impact_factors.append(f"Access control bypass possible ({len(access_vulns)} vulnerabilities)")
        
        # Configuration weaknesses
        config_vulns = [v for v in vulnerabilities if v.category == VulnerabilityCategory.SECURITY_MISCONFIGURATION]
        if config_vulns:
            impact_factors.append(f"System hardening required ({len(config_vulns)} misconfigurations)")
        
        if not impact_factors:
            return "Limited technical impact from identified vulnerabilities."
        
        return "Technical impacts include: " + "; ".join(impact_factors) + "."
    
    def _extract_scan_details(self, security_results: Any) -> Dict[str, Any]:
        """Extract scan execution details"""
        
        return {
            "scan_start_time": getattr(security_results, 'scan_start_time', None),
            "scan_end_time": getattr(security_results, 'scan_end_time', None),
            "scan_duration": getattr(security_results, 'scan_duration', 0.0),
            "scanners_used": getattr(security_results, 'scanners_used', []),
            "scan_scope": getattr(security_results, 'scan_scope', ''),
            "scan_configuration": getattr(security_results, 'scan_configuration', {}),
            "scan_coverage": getattr(security_results, 'scan_coverage', 0.0),
            "scan_errors": getattr(security_results, 'scan_errors', []),
            "scan_warnings": getattr(security_results, 'scan_warnings', [])
        }
    
    def export_security_report(
        self,
        report: SecurityReport,
        format: str = "html",
        output_path: Optional[Path] = None
    ) -> Path:
        """Export security report"""
        
        output_path = output_path or self.output_directory
        
        # Generate filename
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"security_report_{timestamp}.{format}"
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
        
        logger.info(f"Security report exported to: {full_path}")
        return full_path
    
    def _export_json(self, report: SecurityReport, path: Path):
        """Export as JSON"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _export_html(self, report: SecurityReport, path: Path):
        """Export as HTML"""
        
        html_content = self._generate_html_security_report(report)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_pdf(self, report: SecurityReport, path: Path):
        """Export as PDF (placeholder - would require PDF library)"""
        
        # This would require a PDF generation library like reportlab
        # For now, export as HTML
        html_path = path.with_suffix('.html')
        self._export_html(report, html_path)
        logger.warning(f"PDF export not implemented, exported as HTML: {html_path}")
    
    def _generate_html_security_report(self, report: SecurityReport) -> str:
        """Generate HTML security report"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }}
                .vulnerability {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffebee; border-left: 3px solid #d32f2f; }}
                .high {{ background-color: #fff3e0; border-left: 3px solid #f57c00; }}
                .medium {{ background-color: #fffde7; border-left: 3px solid #fbc02d; }}
                .low {{ background-color: #f1f8e9; border-left: 3px solid #388e3c; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .recommendation {{ margin: 10px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Target System:</strong> {report.target_system}</p>
                <p><strong>Environment:</strong> {report.environment}</p>
                <p><strong>Overall Risk Rating:</strong> <span class="{report.overall_risk_rating.lower()}">{report.overall_risk_rating}</span></p>
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
                <h2>Security Metrics</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>Security Score</h3>
                        <p>{report.metrics.security_score:.1%}</p>
                    </div>
                    <div class="metric">
                        <h3>Total Vulnerabilities</h3>
                        <p>{report.metrics.total_vulnerabilities}</p>
                    </div>
                    <div class="metric">
                        <h3>Critical</h3>
                        <p class="critical">{report.metrics.critical_vulnerabilities}</p>
                    </div>
                    <div class="metric">
                        <h3>High</h3>
                        <p class="high">{report.metrics.high_vulnerabilities}</p>
                    </div>
                    <div class="metric">
                        <h3>Medium</h3>
                        <p class="medium">{report.metrics.medium_vulnerabilities}</p>
                    </div>
                    <div class="metric">
                        <h3>Low</h3>
                        <p class="low">{report.metrics.low_vulnerabilities}</p>
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
        
        # Add vulnerabilities
        if report.vulnerabilities:
            html += """
            <div class="section">
                <h2>Vulnerabilities</h2>
            """
            
            for vuln in report.vulnerabilities:
                severity_class = vuln.severity.lower()
                html += f"""
                <div class="vulnerability {severity_class}">
                    <h3>{vuln.title} <span class="{severity_class}">({vuln.severity.upper()})</span></h3>
                    <p><strong>ID:</strong> {vuln.vulnerability_id}</p>
                    <p><strong>Description:</strong> {vuln.description}</p>
                    <p><strong>Category:</strong> {vuln.category.value if hasattr(vuln.category, 'value') else vuln.category}</p>
                    {f'<p><strong>URL:</strong> {vuln.url}</p>' if vuln.url else ''}
                    {f'<p><strong>CWE:</strong> {vuln.cwe_id}</p>' if vuln.cwe_id else ''}
                    {f'<p><strong>CVE:</strong> {vuln.cve_id}</p>' if vuln.cve_id else ''}
                    {f'<p><strong>Remediation:</strong> {vuln.remediation}</p>' if vuln.remediation else ''}
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
                    <p><strong>Estimated Effort:</strong> {rec.estimated_effort}</p>
                    <p><strong>Timeline:</strong> {rec.timeline}</p>
                    {f'<p><strong>Risk Reduction:</strong> {rec.risk_reduction}</p>' if rec.risk_reduction != 'UNKNOWN' else ''}
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
    
    def get_vulnerability_statistics(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get vulnerability statistics for a report"""
        
        if report_id not in self.reports:
            return None
        
        report = self.reports[report_id]
        
        if not report.metrics:
            return None
        
        return {
            "total_vulnerabilities": report.metrics.total_vulnerabilities,
            "by_severity": {
                "critical": report.metrics.critical_vulnerabilities,
                "high": report.metrics.high_vulnerabilities,
                "medium": report.metrics.medium_vulnerabilities,
                "low": report.metrics.low_vulnerabilities,
                "informational": report.metrics.informational_vulnerabilities
            },
            "by_category": report.metrics.vulnerability_categories,
            "owasp_top10_coverage": report.metrics.owasp_top10_coverage,
            "security_score": report.metrics.security_score,
            "risk_rating": report.metrics.risk_rating,
            "threat_level": report.metrics.threat_level.value
        }


# Utility functions
def generate_vulnerability_report(security_results: Any, target_system: str = "") -> SecurityReport:
    """Generate vulnerability assessment report"""
    
    reporter = SecurityReporter()
    
    return reporter.generate_security_report(
        security_results=security_results,
        report_type=SecurityReportType.VULNERABILITY_ASSESSMENT,
        target_system=target_system
    )


def generate_penetration_test_report(security_results: Any, target_system: str = "") -> SecurityReport:
    """Generate penetration testing report"""
    
    reporter = SecurityReporter()
    
    return reporter.generate_security_report(
        security_results=security_results,
        report_type=SecurityReportType.PENETRATION_TEST,
        target_system=target_system
    )