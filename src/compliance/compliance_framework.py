"""
Compliance Framework

Core framework for implementing compliance checks across various standards
including GDPR, PCI-DSS, HIPAA, and other regulatory requirements.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    GDPR = "gdpr"  # General Data Protection Regulation
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    SOX = "sox"  # Sarbanes-Oxley Act
    ISO_27001 = "iso_27001"  # ISO/IEC 27001
    NIST = "nist"  # NIST Cybersecurity Framework
    OWASP = "owasp"  # OWASP Security Standards
    CUSTOM = "custom"  # Custom compliance requirements


class ComplianceLevel(Enum):
    """Compliance requirement severity levels"""
    CRITICAL = "critical"  # Must be compliant
    HIGH = "high"  # Should be compliant
    MEDIUM = "medium"  # Recommended compliance
    LOW = "low"  # Optional compliance
    INFO = "info"  # Informational only


class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class ComplianceRequirement:
    """Individual compliance requirement definition"""
    
    id: str
    standard: ComplianceStandard
    title: str
    description: str
    level: ComplianceLevel
    
    # Requirement details
    section: Optional[str] = None
    subsection: Optional[str] = None
    control_id: Optional[str] = None
    
    # Implementation guidance
    implementation_guidance: str = ""
    testing_procedures: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    
    # Remediation
    remediation_guidance: str = ""
    remediation_effort: str = "medium"  # low, medium, high
    
    # References
    references: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    applicable_systems: List[str] = field(default_factory=list)


@dataclass
class ComplianceCheck:
    """Individual compliance check implementation"""
    
    check_id: str
    requirement_id: str
    name: str
    description: str
    
    # Check implementation
    check_type: str  # automated, manual, hybrid
    check_method: str  # code_analysis, configuration_check, process_review, etc.
    
    # Automation details
    automated: bool = False
    script_path: Optional[str] = None
    command: Optional[str] = None
    
    # Manual check details
    manual_steps: List[str] = field(default_factory=list)
    reviewer_role: Optional[str] = None
    
    # Validation
    expected_result: str = ""
    pass_criteria: List[str] = field(default_factory=list)
    fail_criteria: List[str] = field(default_factory=list)
    
    # Execution settings
    timeout_minutes: int = 30
    retry_count: int = 1
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ComplianceResult:
    """Result of a compliance check"""
    
    check_id: str
    requirement_id: str
    status: ComplianceStatus
    
    # Execution details
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Results
    passed: bool = False
    score: Optional[float] = None  # 0.0 to 1.0
    confidence: Optional[float] = None  # 0.0 to 1.0
    
    # Evidence and findings
    evidence: Dict[str, Any] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Issues and remediation
    issues_found: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)
    
    # Metadata
    checker_name: str = ""
    checker_version: str = ""
    error_message: Optional[str] = None
    
    # Artifacts
    artifacts: List[str] = field(default_factory=list)  # File paths to evidence
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    
    report_id: str
    standard: ComplianceStandard
    target: str  # System/application being assessed
    
    # Execution details
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Results summary
    total_requirements: int = 0
    total_checks: int = 0
    
    compliant_count: int = 0
    non_compliant_count: int = 0
    partially_compliant_count: int = 0
    not_applicable_count: int = 0
    
    # Compliance score (0.0 to 1.0)
    overall_compliance_score: float = 0.0
    critical_compliance_score: float = 0.0
    high_compliance_score: float = 0.0
    
    # Results by requirement
    requirement_results: Dict[str, List[ComplianceResult]] = field(default_factory=dict)
    
    # Issues and recommendations
    critical_issues: List[str] = field(default_factory=list)
    high_priority_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Remediation plan
    immediate_actions: List[str] = field(default_factory=list)
    short_term_actions: List[str] = field(default_factory=list)
    long_term_actions: List[str] = field(default_factory=list)
    
    # Metadata
    assessor: str = ""
    assessment_scope: str = ""
    limitations: List[str] = field(default_factory=list)
    
    # Artifacts
    report_files: List[str] = field(default_factory=list)
    evidence_files: List[str] = field(default_factory=list)


class ComplianceChecker(ABC):
    """Abstract base class for compliance checkers"""
    
    def __init__(self, name: str, version: str, standard: ComplianceStandard):
        self.name = name
        self.version = version
        self.standard = standard
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Configuration
        self.config: Dict[str, Any] = {}
        self.requirements: Dict[str, ComplianceRequirement] = {}
        self.checks: Dict[str, ComplianceCheck] = {}
    
    @abstractmethod
    def get_supported_requirements(self) -> List[ComplianceRequirement]:
        """Get list of supported compliance requirements"""
        pass
    
    @abstractmethod
    def get_available_checks(self) -> List[ComplianceCheck]:
        """Get list of available compliance checks"""
        pass
    
    @abstractmethod
    async def execute_check(self, check: ComplianceCheck, context: Dict[str, Any]) -> ComplianceResult:
        """Execute a single compliance check"""
        pass
    
    async def execute_requirement(self, requirement_id: str, context: Dict[str, Any]) -> List[ComplianceResult]:
        """Execute all checks for a specific requirement"""
        results = []
        
        # Find checks for this requirement
        relevant_checks = [
            check for check in self.checks.values()
            if check.requirement_id == requirement_id
        ]
        
        if not relevant_checks:
            self.logger.warning(f"No checks found for requirement: {requirement_id}")
            return results
        
        # Execute checks
        for check in relevant_checks:
            try:
                result = await self.execute_check(check, context)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Check {check.check_id} failed: {e}")
                # Create error result
                error_result = ComplianceResult(
                    check_id=check.check_id,
                    requirement_id=requirement_id,
                    status=ComplianceStatus.ERROR,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration=0,
                    passed=False,
                    error_message=str(e),
                    checker_name=self.name,
                    checker_version=self.version
                )
                results.append(error_result)
        
        return results
    
    async def execute_full_assessment(self, context: Dict[str, Any]) -> ComplianceReport:
        """Execute full compliance assessment"""
        report = ComplianceReport(
            report_id=f"{self.standard.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            standard=self.standard,
            target=context.get("target", "Unknown"),
            start_time=datetime.now(),
            assessor=context.get("assessor", "Automated"),
            assessment_scope=context.get("scope", "Full Assessment")
        )
        
        try:
            # Load requirements and checks
            requirements = self.get_supported_requirements()
            checks = self.get_available_checks()
            
            report.total_requirements = len(requirements)
            report.total_checks = len(checks)
            
            # Execute checks for each requirement
            for requirement in requirements:
                self.logger.info(f"Assessing requirement: {requirement.id}")
                
                results = await self.execute_requirement(requirement.id, context)
                report.requirement_results[requirement.id] = results
                
                # Update counters based on results
                self._update_report_counters(report, results)
            
            # Calculate compliance scores
            self._calculate_compliance_scores(report)
            
            # Generate recommendations
            self._generate_recommendations(report)
            
            # Finalize report
            report.end_time = datetime.now()
            report.duration = (report.end_time - report.start_time).total_seconds()
            
            self.logger.info(f"Compliance assessment completed: {report.overall_compliance_score:.2%} compliant")
            
        except Exception as e:
            self.logger.error(f"Compliance assessment failed: {e}")
            report.end_time = datetime.now()
            report.duration = (report.end_time - report.start_time).total_seconds()
            report.critical_issues.append(f"Assessment failed: {e}")
        
        return report
    
    def _update_report_counters(self, report: ComplianceReport, results: List[ComplianceResult]):
        """Update report counters based on check results"""
        for result in results:
            if result.status == ComplianceStatus.COMPLIANT:
                report.compliant_count += 1
            elif result.status == ComplianceStatus.NON_COMPLIANT:
                report.non_compliant_count += 1
            elif result.status == ComplianceStatus.PARTIALLY_COMPLIANT:
                report.partially_compliant_count += 1
            elif result.status == ComplianceStatus.NOT_APPLICABLE:
                report.not_applicable_count += 1
    
    def _calculate_compliance_scores(self, report: ComplianceReport):
        """Calculate compliance scores"""
        total_applicable = (
            report.compliant_count + 
            report.non_compliant_count + 
            report.partially_compliant_count
        )
        
        if total_applicable > 0:
            # Overall compliance score
            compliant_score = report.compliant_count + (report.partially_compliant_count * 0.5)
            report.overall_compliance_score = compliant_score / total_applicable
            
            # Calculate scores by severity (would need requirement severity mapping)
            # This is a simplified calculation
            report.critical_compliance_score = report.overall_compliance_score
            report.high_compliance_score = report.overall_compliance_score
    
    def _generate_recommendations(self, report: ComplianceReport):
        """Generate recommendations based on assessment results"""
        # Analyze non-compliant results
        for requirement_id, results in report.requirement_results.items():
            for result in results:
                if result.status == ComplianceStatus.NON_COMPLIANT:
                    if result.recommendations:
                        report.recommendations.extend(result.recommendations)
                    
                    # Add to appropriate action lists based on severity
                    requirement = self.requirements.get(requirement_id)
                    if requirement:
                        if requirement.level == ComplianceLevel.CRITICAL:
                            report.immediate_actions.extend(result.remediation_steps)
                        elif requirement.level == ComplianceLevel.HIGH:
                            report.short_term_actions.extend(result.remediation_steps)
                        else:
                            report.long_term_actions.extend(result.remediation_steps)
        
        # Remove duplicates
        report.recommendations = list(set(report.recommendations))
        report.immediate_actions = list(set(report.immediate_actions))
        report.short_term_actions = list(set(report.short_term_actions))
        report.long_term_actions = list(set(report.long_term_actions))
    
    def load_configuration(self, config: Dict[str, Any]):
        """Load checker configuration"""
        self.config = config
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate assessment context"""
        required_fields = ["target"]
        
        for field in required_fields:
            if field not in context:
                self.logger.error(f"Missing required context field: {field}")
                return False
        
        return True
    
    async def generate_report_files(self, report: ComplianceReport, output_dir: str):
        """Generate compliance report files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate JSON report
            json_path = output_path / f"{report.report_id}.json"
            
            import json
            report_data = {
                "report_info": {
                    "report_id": report.report_id,
                    "standard": report.standard.value,
                    "target": report.target,
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat() if report.end_time else None,
                    "duration": report.duration,
                    "assessor": report.assessor
                },
                "summary": {
                    "total_requirements": report.total_requirements,
                    "total_checks": report.total_checks,
                    "compliant_count": report.compliant_count,
                    "non_compliant_count": report.non_compliant_count,
                    "partially_compliant_count": report.partially_compliant_count,
                    "not_applicable_count": report.not_applicable_count,
                    "overall_compliance_score": report.overall_compliance_score,
                    "critical_compliance_score": report.critical_compliance_score,
                    "high_compliance_score": report.high_compliance_score
                },
                "results": {
                    requirement_id: [
                        {
                            "check_id": result.check_id,
                            "status": result.status.value,
                            "passed": result.passed,
                            "score": result.score,
                            "findings": result.findings,
                            "recommendations": result.recommendations,
                            "issues_found": result.issues_found
                        }
                        for result in results
                    ]
                    for requirement_id, results in report.requirement_results.items()
                },
                "issues": {
                    "critical_issues": report.critical_issues,
                    "high_priority_issues": report.high_priority_issues
                },
                "recommendations": report.recommendations,
                "action_plan": {
                    "immediate_actions": report.immediate_actions,
                    "short_term_actions": report.short_term_actions,
                    "long_term_actions": report.long_term_actions
                }
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            report.report_files.append(str(json_path))
            
            self.logger.info(f"Compliance report generated: {json_path}")
        
        except Exception as e:
            self.logger.warning(f"Failed to generate report files: {e}")


# Utility functions
def create_compliance_requirement(
    id: str,
    standard: ComplianceStandard,
    title: str,
    description: str,
    level: ComplianceLevel = ComplianceLevel.MEDIUM,
    **kwargs
) -> ComplianceRequirement:
    """Create a compliance requirement with common defaults"""
    return ComplianceRequirement(
        id=id,
        standard=standard,
        title=title,
        description=description,
        level=level,
        **kwargs
    )


def create_compliance_check(
    check_id: str,
    requirement_id: str,
    name: str,
    description: str,
    check_type: str = "automated",
    check_method: str = "code_analysis",
    **kwargs
) -> ComplianceCheck:
    """Create a compliance check with common defaults"""
    return ComplianceCheck(
        check_id=check_id,
        requirement_id=requirement_id,
        name=name,
        description=description,
        check_type=check_type,
        check_method=check_method,
        **kwargs
    )


def calculate_compliance_score(results: List[ComplianceResult]) -> float:
    """Calculate compliance score from results"""
    if not results:
        return 0.0
    
    applicable_results = [
        r for r in results 
        if r.status != ComplianceStatus.NOT_APPLICABLE
    ]
    
    if not applicable_results:
        return 1.0  # All not applicable = fully compliant
    
    compliant_count = sum(
        1 for r in applicable_results 
        if r.status == ComplianceStatus.COMPLIANT
    )
    
    partially_compliant_count = sum(
        1 for r in applicable_results 
        if r.status == ComplianceStatus.PARTIALLY_COMPLIANT
    )
    
    score = (compliant_count + partially_compliant_count * 0.5) / len(applicable_results)
    return score