"""
Compliance Orchestrator

Coordinates compliance checks across multiple standards (GDPR, PCI-DSS, HIPAA)
and provides unified compliance reporting and management.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .compliance_framework import (
    ComplianceChecker,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceReport,
    ComplianceRequirement,
    ComplianceResult,
    ComplianceStandard,
    ComplianceStatus
)
from .gdpr_compliance import GDPRChecker
from .pci_dss_compliance import PCIDSSChecker
from .hipaa_compliance import HIPAAChecker

logger = logging.getLogger(__name__)


class ComplianceScope(Enum):
    """Compliance assessment scope"""
    GDPR_ONLY = "gdpr_only"
    PCI_DSS_ONLY = "pci_dss_only"
    HIPAA_ONLY = "hipaa_only"
    GDPR_PCI = "gdpr_pci"
    GDPR_HIPAA = "gdpr_hipaa"
    PCI_HIPAA = "pci_hipaa"
    ALL_STANDARDS = "all_standards"
    CUSTOM = "custom"


class CompliancePriority(Enum):
    """Compliance check execution priority"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceExecutionMode(Enum):
    """Compliance execution mode"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    MIXED = "mixed"


class ComplianceAssessmentPlan:
    """Plan for compliance assessment execution"""
    
    def __init__(
        self,
        plan_id: str,
        name: str,
        scope: ComplianceScope,
        standards: List[ComplianceStandard],
        execution_mode: ComplianceExecutionMode = ComplianceExecutionMode.PARALLEL,
        priority_filter: Optional[List[CompliancePriority]] = None,
        custom_checks: Optional[List[str]] = None
    ):
        self.plan_id = plan_id
        self.name = name
        self.scope = scope
        self.standards = standards
        self.execution_mode = execution_mode
        self.priority_filter = priority_filter or []
        self.custom_checks = custom_checks or []
        self.created_at = datetime.now()
        self.estimated_duration = 0
        self.total_checks = 0


class ConsolidatedComplianceResult:
    """Consolidated compliance results across multiple standards"""
    
    def __init__(self):
        self.assessment_id: str = ""
        self.plan: Optional[ComplianceAssessmentPlan] = None
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0
        
        # Results by standard
        self.gdpr_results: List[ComplianceResult] = []
        self.pci_dss_results: List[ComplianceResult] = []
        self.hipaa_results: List[ComplianceResult] = []
        
        # Consolidated metrics
        self.total_checks: int = 0
        self.passed_checks: int = 0
        self.failed_checks: int = 0
        self.error_checks: int = 0
        self.overall_compliance_score: float = 0.0
        
        # Cross-standard analysis
        self.common_vulnerabilities: List[Dict[str, Any]] = []
        self.compliance_gaps: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        
        # Risk assessment
        self.risk_level: str = "UNKNOWN"
        self.critical_issues: List[Dict[str, Any]] = []
        self.regulatory_risks: List[Dict[str, Any]] = []


class ComplianceOrchestrator:
    """Orchestrates compliance checks across multiple standards"""
    
    def __init__(self):
        self.name = "Compliance Orchestrator"
        self.version = "1.0.0"
        
        # Initialize compliance checkers
        self.checkers: Dict[ComplianceStandard, ComplianceChecker] = {
            ComplianceStandard.GDPR: GDPRChecker(),
            ComplianceStandard.PCI_DSS: PCIDSSChecker(),
            ComplianceStandard.HIPAA: HIPAAChecker()
        }
        
        # Execution tracking
        self.active_assessments: Dict[str, ConsolidatedComplianceResult] = {}
        self.assessment_history: List[ConsolidatedComplianceResult] = []
    
    def create_assessment_plan(
        self,
        name: str,
        scope: ComplianceScope,
        execution_mode: ComplianceExecutionMode = ComplianceExecutionMode.PARALLEL,
        priority_filter: Optional[List[CompliancePriority]] = None,
        custom_checks: Optional[List[str]] = None
    ) -> ComplianceAssessmentPlan:
        """Create a compliance assessment plan"""
        
        plan_id = f"compliance_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine standards based on scope
        standards = self._get_standards_for_scope(scope)
        
        plan = ComplianceAssessmentPlan(
            plan_id=plan_id,
            name=name,
            scope=scope,
            standards=standards,
            execution_mode=execution_mode,
            priority_filter=priority_filter,
            custom_checks=custom_checks
        )
        
        # Calculate estimated metrics
        plan.total_checks = self._calculate_total_checks(plan)
        plan.estimated_duration = self._estimate_duration(plan)
        
        return plan
    
    def _get_standards_for_scope(self, scope: ComplianceScope) -> List[ComplianceStandard]:
        """Get compliance standards for the given scope"""
        
        scope_mapping = {
            ComplianceScope.GDPR_ONLY: [ComplianceStandard.GDPR],
            ComplianceScope.PCI_DSS_ONLY: [ComplianceStandard.PCI_DSS],
            ComplianceScope.HIPAA_ONLY: [ComplianceStandard.HIPAA],
            ComplianceScope.GDPR_PCI: [ComplianceStandard.GDPR, ComplianceStandard.PCI_DSS],
            ComplianceScope.GDPR_HIPAA: [ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
            ComplianceScope.PCI_HIPAA: [ComplianceStandard.PCI_DSS, ComplianceStandard.HIPAA],
            ComplianceScope.ALL_STANDARDS: [ComplianceStandard.GDPR, ComplianceStandard.PCI_DSS, ComplianceStandard.HIPAA],
            ComplianceScope.CUSTOM: []  # Will be determined by custom_checks
        }
        
        return scope_mapping.get(scope, [])
    
    def _calculate_total_checks(self, plan: ComplianceAssessmentPlan) -> int:
        """Calculate total number of checks for the plan"""
        
        total = 0
        for standard in plan.standards:
            if standard in self.checkers:
                checker = self.checkers[standard]
                checks = checker.get_available_checks()
                
                # Apply priority filter if specified
                if plan.priority_filter:
                    priority_levels = [p.value for p in plan.priority_filter]
                    checks = [c for c in checks if getattr(c, 'priority', 'medium') in priority_levels]
                
                total += len(checks)
        
        return total
    
    def _estimate_duration(self, plan: ComplianceAssessmentPlan) -> float:
        """Estimate assessment duration in seconds"""
        
        # Base time per check (seconds)
        base_time_per_check = 5.0
        
        # Execution mode multipliers
        mode_multipliers = {
            ComplianceExecutionMode.PARALLEL: 0.3,
            ComplianceExecutionMode.SEQUENTIAL: 1.0,
            ComplianceExecutionMode.MIXED: 0.6
        }
        
        multiplier = mode_multipliers.get(plan.execution_mode, 1.0)
        return plan.total_checks * base_time_per_check * multiplier
    
    async def execute_assessment(
        self,
        plan: ComplianceAssessmentPlan,
        context: Dict[str, Any]
    ) -> ConsolidatedComplianceResult:
        """Execute compliance assessment according to the plan"""
        
        assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        result = ConsolidatedComplianceResult()
        result.assessment_id = assessment_id
        result.plan = plan
        result.start_time = datetime.now()
        
        # Track active assessment
        self.active_assessments[assessment_id] = result
        
        try:
            logger.info(f"Starting compliance assessment: {plan.name}")
            
            # Execute checks for each standard
            if plan.execution_mode == ComplianceExecutionMode.PARALLEL:
                await self._execute_parallel_assessment(plan, context, result)
            elif plan.execution_mode == ComplianceExecutionMode.SEQUENTIAL:
                await self._execute_sequential_assessment(plan, context, result)
            else:  # MIXED
                await self._execute_mixed_assessment(plan, context, result)
            
            # Perform cross-standard analysis
            await self._perform_cross_standard_analysis(result)
            
            # Calculate consolidated metrics
            self._calculate_consolidated_metrics(result)
            
            # Generate recommendations
            await self._generate_recommendations(result)
            
        except Exception as e:
            logger.error(f"Assessment execution failed: {str(e)}")
            result.risk_level = "ERROR"
            
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # Move to history
            self.assessment_history.append(result)
            if assessment_id in self.active_assessments:
                del self.active_assessments[assessment_id]
        
        return result
    
    async def _execute_parallel_assessment(
        self,
        plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: ConsolidatedComplianceResult
    ):
        """Execute assessment with parallel execution"""
        
        tasks = []
        
        for standard in plan.standards:
            if standard in self.checkers:
                task = self._execute_standard_assessment(standard, context, result)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_sequential_assessment(
        self,
        plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: ConsolidatedComplianceResult
    ):
        """Execute assessment with sequential execution"""
        
        for standard in plan.standards:
            if standard in self.checkers:
                await self._execute_standard_assessment(standard, context, result)
    
    async def _execute_mixed_assessment(
        self,
        plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: ConsolidatedComplianceResult
    ):
        """Execute assessment with mixed execution (critical first, then parallel)"""
        
        # First, execute critical checks sequentially
        critical_standards = []
        other_standards = []
        
        for standard in plan.standards:
            if standard == ComplianceStandard.PCI_DSS:  # PCI-DSS often has critical security requirements
                critical_standards.append(standard)
            else:
                other_standards.append(standard)
        
        # Execute critical standards first
        for standard in critical_standards:
            if standard in self.checkers:
                await self._execute_standard_assessment(standard, context, result)
        
        # Execute other standards in parallel
        tasks = []
        for standard in other_standards:
            if standard in self.checkers:
                task = self._execute_standard_assessment(standard, context, result)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_standard_assessment(
        self,
        standard: ComplianceStandard,
        context: Dict[str, Any],
        result: ConsolidatedComplianceResult
    ):
        """Execute assessment for a specific compliance standard"""
        
        try:
            checker = self.checkers[standard]
            
            # Execute full assessment for the standard
            standard_report = await checker.execute_full_assessment(context)
            
            # Store results by standard
            if standard == ComplianceStandard.GDPR:
                result.gdpr_results = standard_report.results
            elif standard == ComplianceStandard.PCI_DSS:
                result.pci_dss_results = standard_report.results
            elif standard == ComplianceStandard.HIPAA:
                result.hipaa_results = standard_report.results
            
            logger.info(f"Completed {standard.value} assessment: {len(standard_report.results)} checks")
            
        except Exception as e:
            logger.error(f"Failed to execute {standard.value} assessment: {str(e)}")
    
    async def _perform_cross_standard_analysis(self, result: ConsolidatedComplianceResult):
        """Perform cross-standard analysis to identify common issues"""
        
        all_results = result.gdpr_results + result.pci_dss_results + result.hipaa_results
        
        # Identify common vulnerability patterns
        vulnerability_patterns = {}
        
        for compliance_result in all_results:
            for issue in compliance_result.issues_found:
                # Normalize issue description for pattern matching
                normalized_issue = self._normalize_issue_description(issue)
                
                if normalized_issue not in vulnerability_patterns:
                    vulnerability_patterns[normalized_issue] = {
                        "pattern": normalized_issue,
                        "occurrences": 0,
                        "standards": set(),
                        "severity": "medium"
                    }
                
                vulnerability_patterns[normalized_issue]["occurrences"] += 1
                vulnerability_patterns[normalized_issue]["standards"].add(
                    self._get_standard_from_result(compliance_result)
                )
        
        # Identify cross-standard vulnerabilities (appearing in multiple standards)
        for pattern, data in vulnerability_patterns.items():
            if len(data["standards"]) > 1:
                result.common_vulnerabilities.append({
                    "pattern": pattern,
                    "affected_standards": list(data["standards"]),
                    "occurrences": data["occurrences"],
                    "severity": self._calculate_cross_standard_severity(data)
                })
    
    def _normalize_issue_description(self, issue: str) -> str:
        """Normalize issue description for pattern matching"""
        
        # Common patterns to normalize
        normalizations = {
            r"encryption.*not.*implemented": "encryption_missing",
            r"access.*control.*insufficient": "access_control_weak",
            r"logging.*not.*configured": "logging_missing",
            r"authentication.*weak": "authentication_weak",
            r"data.*protection.*insufficient": "data_protection_weak",
            r"backup.*not.*configured": "backup_missing",
            r"monitoring.*not.*implemented": "monitoring_missing",
            r"policy.*not.*documented": "policy_missing"
        }
        
        import re
        
        issue_lower = issue.lower()
        for pattern, normalized in normalizations.items():
            if re.search(pattern, issue_lower):
                return normalized
        
        return issue_lower
    
    def _get_standard_from_result(self, compliance_result: ComplianceResult) -> str:
        """Determine which standard a result belongs to based on check ID"""
        
        check_id = compliance_result.check_id.lower()
        
        if check_id.startswith("gdpr_"):
            return "GDPR"
        elif check_id.startswith("pci_"):
            return "PCI-DSS"
        elif check_id.startswith("hipaa_"):
            return "HIPAA"
        else:
            return "UNKNOWN"
    
    def _calculate_cross_standard_severity(self, vulnerability_data: Dict[str, Any]) -> str:
        """Calculate severity for cross-standard vulnerabilities"""
        
        # Higher severity if affects multiple standards
        num_standards = len(vulnerability_data["standards"])
        occurrences = vulnerability_data["occurrences"]
        
        if num_standards >= 3 or occurrences >= 5:
            return "critical"
        elif num_standards >= 2 or occurrences >= 3:
            return "high"
        else:
            return "medium"
    
    def _calculate_consolidated_metrics(self, result: ConsolidatedComplianceResult):
        """Calculate consolidated compliance metrics"""
        
        all_results = result.gdpr_results + result.pci_dss_results + result.hipaa_results
        
        result.total_checks = len(all_results)
        result.passed_checks = len([r for r in all_results if r.passed])
        result.failed_checks = len([r for r in all_results if not r.passed and r.status != ComplianceStatus.ERROR])
        result.error_checks = len([r for r in all_results if r.status == ComplianceStatus.ERROR])
        
        # Calculate overall compliance score
        if result.total_checks > 0:
            result.overall_compliance_score = result.passed_checks / result.total_checks
        else:
            result.overall_compliance_score = 0.0
        
        # Determine risk level
        if result.overall_compliance_score >= 0.9:
            result.risk_level = "LOW"
        elif result.overall_compliance_score >= 0.7:
            result.risk_level = "MEDIUM"
        elif result.overall_compliance_score >= 0.5:
            result.risk_level = "HIGH"
        else:
            result.risk_level = "CRITICAL"
        
        # Identify critical issues
        for compliance_result in all_results:
            if not compliance_result.passed and compliance_result.score < 0.5:
                result.critical_issues.append({
                    "check_id": compliance_result.check_id,
                    "requirement_id": compliance_result.requirement_id,
                    "standard": self._get_standard_from_result(compliance_result),
                    "score": compliance_result.score,
                    "issues": compliance_result.issues_found
                })
    
    async def _generate_recommendations(self, result: ConsolidatedComplianceResult):
        """Generate recommendations based on assessment results"""
        
        # Priority-based recommendations
        if result.overall_compliance_score < 0.5:
            result.recommendations.append({
                "priority": "critical",
                "category": "overall_compliance",
                "title": "Immediate Compliance Action Required",
                "description": "Overall compliance score is critically low. Immediate action required.",
                "actions": [
                    "Conduct emergency compliance review",
                    "Implement critical security controls",
                    "Engage compliance consultant",
                    "Review and update policies"
                ]
            })
        
        # Cross-standard recommendations
        if result.common_vulnerabilities:
            result.recommendations.append({
                "priority": "high",
                "category": "cross_standard",
                "title": "Address Cross-Standard Vulnerabilities",
                "description": "Multiple compliance standards affected by common issues",
                "actions": [
                    f"Address {len(result.common_vulnerabilities)} common vulnerability patterns",
                    "Implement unified security controls",
                    "Standardize compliance procedures"
                ]
            })
        
        # Standard-specific recommendations
        gdpr_score = self._calculate_standard_score(result.gdpr_results)
        pci_score = self._calculate_standard_score(result.pci_dss_results)
        hipaa_score = self._calculate_standard_score(result.hipaa_results)
        
        if gdpr_score < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "gdpr",
                "title": "Improve GDPR Compliance",
                "description": f"GDPR compliance score: {gdpr_score:.2f}",
                "actions": [
                    "Review data processing activities",
                    "Update privacy policies",
                    "Implement data subject rights procedures"
                ]
            })
        
        if pci_score < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "pci_dss",
                "title": "Improve PCI-DSS Compliance",
                "description": f"PCI-DSS compliance score: {pci_score:.2f}",
                "actions": [
                    "Strengthen payment card security",
                    "Implement network segmentation",
                    "Enhance access controls"
                ]
            })
        
        if hipaa_score < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "hipaa",
                "title": "Improve HIPAA Compliance",
                "description": f"HIPAA compliance score: {hipaa_score:.2f}",
                "actions": [
                    "Strengthen PHI protection",
                    "Implement administrative safeguards",
                    "Enhance audit controls"
                ]
            })
    
    def _calculate_standard_score(self, results: List[ComplianceResult]) -> float:
        """Calculate compliance score for a specific standard"""
        
        if not results:
            return 0.0
        
        passed = len([r for r in results if r.passed])
        return passed / len(results)
    
    def get_assessment_status(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active assessment"""
        
        if assessment_id in self.active_assessments:
            result = self.active_assessments[assessment_id]
            return {
                "assessment_id": assessment_id,
                "status": "running",
                "progress": {
                    "total_checks": result.total_checks,
                    "completed_checks": len(result.gdpr_results + result.pci_dss_results + result.hipaa_results),
                    "elapsed_time": (datetime.now() - result.start_time).total_seconds()
                }
            }
        
        return None
    
    def get_assessment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get assessment history"""
        
        history = []
        for result in self.assessment_history[-limit:]:
            history.append({
                "assessment_id": result.assessment_id,
                "plan_name": result.plan.name if result.plan else "Unknown",
                "start_time": result.start_time.isoformat(),
                "duration": result.duration,
                "compliance_score": result.overall_compliance_score,
                "risk_level": result.risk_level,
                "total_checks": result.total_checks
            })
        
        return history
    
    def generate_compliance_report(self, result: ConsolidatedComplianceResult) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        return {
            "assessment_info": {
                "assessment_id": result.assessment_id,
                "plan_name": result.plan.name if result.plan else "Unknown",
                "execution_time": result.start_time.isoformat(),
                "duration": result.duration,
                "standards_assessed": [s.value for s in result.plan.standards] if result.plan else []
            },
            "overall_metrics": {
                "compliance_score": result.overall_compliance_score,
                "risk_level": result.risk_level,
                "total_checks": result.total_checks,
                "passed_checks": result.passed_checks,
                "failed_checks": result.failed_checks,
                "error_checks": result.error_checks
            },
            "standard_scores": {
                "gdpr": self._calculate_standard_score(result.gdpr_results),
                "pci_dss": self._calculate_standard_score(result.pci_dss_results),
                "hipaa": self._calculate_standard_score(result.hipaa_results)
            },
            "cross_standard_analysis": {
                "common_vulnerabilities": result.common_vulnerabilities,
                "compliance_gaps": result.compliance_gaps
            },
            "critical_issues": result.critical_issues,
            "recommendations": result.recommendations,
            "detailed_results": {
                "gdpr_results": [self._serialize_result(r) for r in result.gdpr_results],
                "pci_dss_results": [self._serialize_result(r) for r in result.pci_dss_results],
                "hipaa_results": [self._serialize_result(r) for r in result.hipaa_results]
            }
        }
    
    def _serialize_result(self, result: ComplianceResult) -> Dict[str, Any]:
        """Serialize compliance result for reporting"""
        
        return {
            "check_id": result.check_id,
            "requirement_id": result.requirement_id,
            "status": result.status.value,
            "passed": result.passed,
            "score": result.score,
            "duration": result.duration,
            "findings": result.findings,
            "issues_found": result.issues_found,
            "recommendations": result.recommendations
        }


# Utility functions
def create_comprehensive_assessment_plan() -> ComplianceAssessmentPlan:
    """Create a comprehensive assessment plan covering all standards"""
    
    orchestrator = ComplianceOrchestrator()
    
    return orchestrator.create_assessment_plan(
        name="Comprehensive Compliance Assessment",
        scope=ComplianceScope.ALL_STANDARDS,
        execution_mode=ComplianceExecutionMode.MIXED
    )


def create_targeted_assessment_plan(
    standards: List[ComplianceStandard],
    priority_filter: Optional[List[CompliancePriority]] = None
) -> ComplianceAssessmentPlan:
    """Create a targeted assessment plan for specific standards"""
    
    orchestrator = ComplianceOrchestrator()
    
    # Determine scope based on standards
    if len(standards) == 1:
        if standards[0] == ComplianceStandard.GDPR:
            scope = ComplianceScope.GDPR_ONLY
        elif standards[0] == ComplianceStandard.PCI_DSS:
            scope = ComplianceScope.PCI_DSS_ONLY
        elif standards[0] == ComplianceStandard.HIPAA:
            scope = ComplianceScope.HIPAA_ONLY
        else:
            scope = ComplianceScope.CUSTOM
    elif len(standards) == 2:
        if ComplianceStandard.GDPR in standards and ComplianceStandard.PCI_DSS in standards:
            scope = ComplianceScope.GDPR_PCI
        elif ComplianceStandard.GDPR in standards and ComplianceStandard.HIPAA in standards:
            scope = ComplianceScope.GDPR_HIPAA
        elif ComplianceStandard.PCI_DSS in standards and ComplianceStandard.HIPAA in standards:
            scope = ComplianceScope.PCI_HIPAA
        else:
            scope = ComplianceScope.CUSTOM
    else:
        scope = ComplianceScope.ALL_STANDARDS
    
    return orchestrator.create_assessment_plan(
        name=f"Targeted Assessment - {', '.join([s.value for s in standards])}",
        scope=scope,
        execution_mode=ComplianceExecutionMode.PARALLEL,
        priority_filter=priority_filter
    )


def create_multi_standard_plan(
    standards: List[ComplianceStandard] = None,
    scope: ComplianceScope = ComplianceScope.ALL_STANDARDS,
    execution_mode: ComplianceExecutionMode = ComplianceExecutionMode.MIXED,
    priority_filter: CompliancePriority = CompliancePriority.MEDIUM,
    name: str = "Multi-Standard Compliance Plan"
) -> ComplianceAssessmentPlan:
    """Create a compliance plan covering multiple standards"""
    
    if standards is None:
        standards = [
            ComplianceStandard.GDPR,
            ComplianceStandard.PCI_DSS,
            ComplianceStandard.HIPAA
        ]
    
    orchestrator = ComplianceOrchestrator()
    
    return orchestrator.create_assessment_plan(
        name=name,
        scope=scope,
        execution_mode=execution_mode,
        priority_filter=priority_filter,
        standards=standards
    )


async def run_comprehensive_compliance_assessment(
    target_system: str,
    **kwargs
) -> ConsolidatedComplianceResult:
    """Run a comprehensive compliance assessment across all standards"""
    
    orchestrator = ComplianceOrchestrator()
    plan = create_comprehensive_assessment_plan()
    
    # Create assessment context
    context = {
        "target": target_system,
        "assessor": "Compliance Orchestrator",
        "scope": "Comprehensive Compliance Assessment"
    }
    context.update(kwargs)
    
    return await orchestrator.execute_assessment(plan, context)