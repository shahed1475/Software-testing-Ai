"""
Unified Test Orchestrator

Coordinates cross-domain testing (Web, API, Mobile) with integrated security scanning
and compliance checks to provide comprehensive end-to-end testing coverage.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .cross_domain_testing import (
    CrossDomainTestRunner,
    TestDomain,
    TestFlow,
    UnifiedTestCase,
    DomainContext
)
from .test_orchestrator import (
    UnifiedTestOrchestrator,
    TestExecutionPlan,
    ExecutionMode,
    TestPriority,
    TestResult
)
from ..security.security_orchestrator import (
    SecurityOrchestrator,
    SecurityScanPlan,
    ConsolidatedSecurityResult
)
from ..compliance.compliance_orchestrator import (
    ComplianceOrchestrator,
    ComplianceAssessmentPlan,
    ConsolidatedComplianceResult,
    ComplianceScope
)

logger = logging.getLogger(__name__)


class UnifiedTestingScope(Enum):
    """Unified testing scope"""
    FUNCTIONAL_ONLY = "functional_only"
    SECURITY_ONLY = "security_only"
    COMPLIANCE_ONLY = "compliance_only"
    FUNCTIONAL_SECURITY = "functional_security"
    FUNCTIONAL_COMPLIANCE = "functional_compliance"
    SECURITY_COMPLIANCE = "security_compliance"
    COMPREHENSIVE = "comprehensive"


class UnifiedExecutionStrategy(Enum):
    """Unified execution strategy"""
    SEQUENTIAL = "sequential"  # Functional -> Security -> Compliance
    PARALLEL = "parallel"      # All in parallel
    LAYERED = "layered"        # Functional first, then Security & Compliance in parallel
    INTEGRATED = "integrated"  # Interleaved execution with dependencies


class UnifiedTestPlan:
    """Comprehensive test plan covering functional, security, and compliance testing"""
    
    def __init__(
        self,
        plan_id: str,
        name: str,
        scope: UnifiedTestingScope,
        strategy: UnifiedExecutionStrategy = UnifiedExecutionStrategy.LAYERED
    ):
        self.plan_id = plan_id
        self.name = name
        self.scope = scope
        self.strategy = strategy
        self.created_at = datetime.now()
        
        # Component plans
        self.functional_plan: Optional[TestExecutionPlan] = None
        self.security_plan: Optional[SecurityScanPlan] = None
        self.compliance_plan: Optional[ComplianceAssessmentPlan] = None
        
        # Execution configuration
        self.domains: List[TestDomain] = []
        self.test_flows: List[TestFlow] = []
        self.parallel_execution: bool = True
        self.timeout_seconds: int = 3600  # 1 hour default
        
        # Dependencies and ordering
        self.execution_dependencies: Dict[str, List[str]] = {}
        self.critical_path: List[str] = []
        
        # Metrics
        self.estimated_duration: float = 0.0
        self.total_test_cases: int = 0
        self.total_security_scans: int = 0
        self.total_compliance_checks: int = 0


class UnifiedTestResult:
    """Consolidated results from unified testing execution"""
    
    def __init__(self):
        self.execution_id: str = ""
        self.plan: Optional[UnifiedTestPlan] = None
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0
        self.status: str = "UNKNOWN"
        
        # Component results
        self.functional_results: List[TestResult] = []
        self.security_results: Optional[ConsolidatedSecurityResult] = None
        self.compliance_results: Optional[ConsolidatedComplianceResult] = None
        
        # Consolidated metrics
        self.total_tests_executed: int = 0
        self.functional_pass_rate: float = 0.0
        self.security_score: float = 0.0
        self.compliance_score: float = 0.0
        self.overall_quality_score: float = 0.0
        
        # Cross-domain analysis
        self.domain_coverage: Dict[str, float] = {}
        self.integration_issues: List[Dict[str, Any]] = []
        self.security_vulnerabilities: List[Dict[str, Any]] = []
        self.compliance_gaps: List[Dict[str, Any]] = []
        
        # Risk assessment
        self.risk_level: str = "UNKNOWN"
        self.critical_issues: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        
        # Traceability
        self.test_coverage_matrix: Dict[str, Any] = {}
        self.requirement_coverage: Dict[str, float] = {}


class UnifiedTestingOrchestrator:
    """Master orchestrator for unified testing across all domains and aspects"""
    
    def __init__(self):
        self.name = "Unified Testing Orchestrator"
        self.version = "1.0.0"
        
        # Component orchestrators
        self.functional_orchestrator = UnifiedTestOrchestrator()
        self.security_orchestrator = SecurityOrchestrator()
        self.compliance_orchestrator = ComplianceOrchestrator()
        self.cross_domain_runner = CrossDomainTestRunner()
        
        # Execution tracking
        self.active_executions: Dict[str, UnifiedTestResult] = {}
        self.execution_history: List[UnifiedTestResult] = []
        
        # Configuration
        self.max_parallel_executions = 3
        self.default_timeout = 3600
    
    def create_unified_plan(
        self,
        name: str,
        scope: UnifiedTestingScope,
        strategy: UnifiedExecutionStrategy = UnifiedExecutionStrategy.LAYERED,
        domains: Optional[List[TestDomain]] = None,
        test_flows: Optional[List[TestFlow]] = None
    ) -> UnifiedTestPlan:
        """Create a unified test plan"""
        
        plan_id = f"unified_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = UnifiedTestPlan(
            plan_id=plan_id,
            name=name,
            scope=scope,
            strategy=strategy
        )
        
        # Set domains (default to all if not specified)
        plan.domains = domains or [TestDomain.WEB, TestDomain.API, TestDomain.MOBILE]
        plan.test_flows = test_flows or []
        
        # Create component plans based on scope
        if scope in [UnifiedTestingScope.FUNCTIONAL_ONLY, UnifiedTestingScope.FUNCTIONAL_SECURITY, 
                    UnifiedTestingScope.FUNCTIONAL_COMPLIANCE, UnifiedTestingScope.COMPREHENSIVE]:
            plan.functional_plan = self._create_functional_plan(plan)
        
        if scope in [UnifiedTestingScope.SECURITY_ONLY, UnifiedTestingScope.FUNCTIONAL_SECURITY,
                    UnifiedTestingScope.SECURITY_COMPLIANCE, UnifiedTestingScope.COMPREHENSIVE]:
            plan.security_plan = self._create_security_plan(plan)
        
        if scope in [UnifiedTestingScope.COMPLIANCE_ONLY, UnifiedTestingScope.FUNCTIONAL_COMPLIANCE,
                    UnifiedTestingScope.SECURITY_COMPLIANCE, UnifiedTestingScope.COMPREHENSIVE]:
            plan.compliance_plan = self._create_compliance_plan(plan)
        
        # Calculate metrics
        self._calculate_plan_metrics(plan)
        
        return plan
    
    def _create_functional_plan(self, unified_plan: UnifiedTestPlan) -> TestExecutionPlan:
        """Create functional test execution plan"""
        
        return TestExecutionPlan(
            plan_id=f"{unified_plan.plan_id}_functional",
            name=f"{unified_plan.name} - Functional Tests",
            test_cases=[],  # Will be populated with actual test cases
            execution_mode=ExecutionMode.PARALLEL if unified_plan.strategy != UnifiedExecutionStrategy.SEQUENTIAL else ExecutionMode.SEQUENTIAL,
            priority=TestPriority.HIGH,
            timeout_seconds=unified_plan.timeout_seconds // 3,  # Allocate 1/3 of time to functional
            parallel_workers=4,
            domains=unified_plan.domains
        )
    
    def _create_security_plan(self, unified_plan: UnifiedTestPlan) -> SecurityScanPlan:
        """Create security scan plan"""
        
        from ..security.security_orchestrator import SecurityScanStrategy, SecurityScanPriority
        
        return SecurityScanPlan(
            plan_id=f"{unified_plan.plan_id}_security",
            name=f"{unified_plan.name} - Security Scans",
            strategy=SecurityScanStrategy.COMPREHENSIVE,
            priority=SecurityScanPriority.HIGH,
            target_domains=unified_plan.domains,
            scan_types=["web_security", "api_security", "dependency_scan", "container_scan"],
            parallel_execution=unified_plan.strategy in [UnifiedExecutionStrategy.PARALLEL, UnifiedExecutionStrategy.LAYERED]
        )
    
    def _create_compliance_plan(self, unified_plan: UnifiedTestPlan) -> ComplianceAssessmentPlan:
        """Create compliance assessment plan"""
        
        from ..compliance.compliance_orchestrator import ComplianceScope, ComplianceExecutionMode
        
        return ComplianceAssessmentPlan(
            plan_id=f"{unified_plan.plan_id}_compliance",
            name=f"{unified_plan.name} - Compliance Checks",
            scope=ComplianceScope.ALL_STANDARDS,
            standards=[],  # Will be determined by orchestrator
            execution_mode=ComplianceExecutionMode.PARALLEL if unified_plan.strategy != UnifiedExecutionStrategy.SEQUENTIAL else ComplianceExecutionMode.SEQUENTIAL
        )
    
    def _calculate_plan_metrics(self, plan: UnifiedTestPlan):
        """Calculate plan metrics and estimates"""
        
        # Count test cases
        if plan.functional_plan:
            plan.total_test_cases = len(plan.functional_plan.test_cases)
        
        # Count security scans
        if plan.security_plan:
            plan.total_security_scans = len(plan.security_plan.scan_types)
        
        # Count compliance checks
        if plan.compliance_plan:
            plan.total_compliance_checks = plan.compliance_plan.total_checks
        
        # Estimate duration based on strategy
        functional_time = plan.total_test_cases * 30  # 30 seconds per test case
        security_time = plan.total_security_scans * 300  # 5 minutes per scan
        compliance_time = plan.total_compliance_checks * 10  # 10 seconds per check
        
        if plan.strategy == UnifiedExecutionStrategy.SEQUENTIAL:
            plan.estimated_duration = functional_time + security_time + compliance_time
        elif plan.strategy == UnifiedExecutionStrategy.PARALLEL:
            plan.estimated_duration = max(functional_time, security_time, compliance_time)
        elif plan.strategy == UnifiedExecutionStrategy.LAYERED:
            plan.estimated_duration = functional_time + max(security_time, compliance_time)
        else:  # INTEGRATED
            plan.estimated_duration = max(functional_time, security_time, compliance_time) * 1.2  # 20% overhead
    
    async def execute_unified_testing(
        self,
        plan: UnifiedTestPlan,
        context: Dict[str, Any]
    ) -> UnifiedTestResult:
        """Execute unified testing according to the plan"""
        
        execution_id = f"unified_exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        result = UnifiedTestResult()
        result.execution_id = execution_id
        result.plan = plan
        result.start_time = datetime.now()
        
        # Track active execution
        self.active_executions[execution_id] = result
        
        try:
            logger.info(f"Starting unified testing execution: {plan.name}")
            
            # Execute based on strategy
            if plan.strategy == UnifiedExecutionStrategy.SEQUENTIAL:
                await self._execute_sequential_strategy(plan, context, result)
            elif plan.strategy == UnifiedExecutionStrategy.PARALLEL:
                await self._execute_parallel_strategy(plan, context, result)
            elif plan.strategy == UnifiedExecutionStrategy.LAYERED:
                await self._execute_layered_strategy(plan, context, result)
            else:  # INTEGRATED
                await self._execute_integrated_strategy(plan, context, result)
            
            # Perform cross-domain analysis
            await self._perform_unified_analysis(result)
            
            # Calculate consolidated metrics
            self._calculate_unified_metrics(result)
            
            # Generate unified recommendations
            await self._generate_unified_recommendations(result)
            
            result.status = "COMPLETED"
            
        except Exception as e:
            logger.error(f"Unified testing execution failed: {str(e)}")
            result.status = "FAILED"
            result.critical_issues.append({
                "type": "execution_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # Move to history
            self.execution_history.append(result)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return result
    
    async def _execute_sequential_strategy(
        self,
        plan: UnifiedTestPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute with sequential strategy: Functional -> Security -> Compliance"""
        
        # 1. Execute functional tests
        if plan.functional_plan:
            logger.info("Executing functional tests...")
            functional_results = await self.functional_orchestrator.execute_plan(
                plan.functional_plan, context
            )
            result.functional_results = functional_results.results
        
        # 2. Execute security scans
        if plan.security_plan:
            logger.info("Executing security scans...")
            result.security_results = await self.security_orchestrator.execute_scan_plan(
                plan.security_plan, context
            )
        
        # 3. Execute compliance checks
        if plan.compliance_plan:
            logger.info("Executing compliance checks...")
            result.compliance_results = await self.compliance_orchestrator.execute_assessment(
                plan.compliance_plan, context
            )
    
    async def _execute_parallel_strategy(
        self,
        plan: UnifiedTestPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute with parallel strategy: All components in parallel"""
        
        tasks = []
        
        # Create tasks for each component
        if plan.functional_plan:
            task = self._execute_functional_component(plan.functional_plan, context, result)
            tasks.append(task)
        
        if plan.security_plan:
            task = self._execute_security_component(plan.security_plan, context, result)
            tasks.append(task)
        
        if plan.compliance_plan:
            task = self._execute_compliance_component(plan.compliance_plan, context, result)
            tasks.append(task)
        
        # Execute all in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_layered_strategy(
        self,
        plan: UnifiedTestPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute with layered strategy: Functional first, then Security & Compliance in parallel"""
        
        # 1. Execute functional tests first
        if plan.functional_plan:
            logger.info("Executing functional tests (layer 1)...")
            functional_results = await self.functional_orchestrator.execute_plan(
                plan.functional_plan, context
            )
            result.functional_results = functional_results.results
        
        # 2. Execute security and compliance in parallel
        tasks = []
        
        if plan.security_plan:
            task = self._execute_security_component(plan.security_plan, context, result)
            tasks.append(task)
        
        if plan.compliance_plan:
            task = self._execute_compliance_component(plan.compliance_plan, context, result)
            tasks.append(task)
        
        if tasks:
            logger.info("Executing security and compliance (layer 2)...")
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_integrated_strategy(
        self,
        plan: UnifiedTestPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute with integrated strategy: Interleaved execution with dependencies"""
        
        # This is a more complex strategy that interleaves different types of testing
        # based on dependencies and optimal resource utilization
        
        # Phase 1: Quick functional smoke tests
        if plan.functional_plan:
            logger.info("Phase 1: Functional smoke tests...")
            # Execute a subset of critical functional tests first
            smoke_results = await self._execute_smoke_tests(plan.functional_plan, context)
            result.functional_results.extend(smoke_results)
        
        # Phase 2: Security and compliance baseline (parallel)
        tasks = []
        
        if plan.security_plan:
            task = self._execute_baseline_security_scans(plan.security_plan, context, result)
            tasks.append(task)
        
        if plan.compliance_plan:
            task = self._execute_baseline_compliance_checks(plan.compliance_plan, context, result)
            tasks.append(task)
        
        if tasks:
            logger.info("Phase 2: Security and compliance baseline...")
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Phase 3: Comprehensive testing (all remaining tests)
        remaining_tasks = []
        
        if plan.functional_plan:
            task = self._execute_remaining_functional_tests(plan.functional_plan, context, result)
            remaining_tasks.append(task)
        
        if plan.security_plan:
            task = self._execute_comprehensive_security_scans(plan.security_plan, context, result)
            remaining_tasks.append(task)
        
        if plan.compliance_plan:
            task = self._execute_comprehensive_compliance_checks(plan.compliance_plan, context, result)
            remaining_tasks.append(task)
        
        if remaining_tasks:
            logger.info("Phase 3: Comprehensive testing...")
            await asyncio.gather(*remaining_tasks, return_exceptions=True)
    
    async def _execute_functional_component(
        self,
        functional_plan: TestExecutionPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute functional testing component"""
        
        try:
            functional_results = await self.functional_orchestrator.execute_plan(
                functional_plan, context
            )
            result.functional_results = functional_results.results
        except Exception as e:
            logger.error(f"Functional testing failed: {str(e)}")
    
    async def _execute_security_component(
        self,
        security_plan: SecurityScanPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute security scanning component"""
        
        try:
            result.security_results = await self.security_orchestrator.execute_scan_plan(
                security_plan, context
            )
        except Exception as e:
            logger.error(f"Security scanning failed: {str(e)}")
    
    async def _execute_compliance_component(
        self,
        compliance_plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute compliance checking component"""
        
        try:
            result.compliance_results = await self.compliance_orchestrator.execute_assessment(
                compliance_plan, context
            )
        except Exception as e:
            logger.error(f"Compliance checking failed: {str(e)}")
    
    async def _execute_smoke_tests(
        self,
        functional_plan: TestExecutionPlan,
        context: Dict[str, Any]
    ) -> List[TestResult]:
        """Execute smoke tests (subset of functional tests)"""
        
        # Mock implementation - would execute critical/smoke tests only
        return []
    
    async def _execute_baseline_security_scans(
        self,
        security_plan: SecurityScanPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute baseline security scans"""
        
        # Mock implementation - would execute quick security checks
        pass
    
    async def _execute_baseline_compliance_checks(
        self,
        compliance_plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute baseline compliance checks"""
        
        # Mock implementation - would execute critical compliance checks
        pass
    
    async def _execute_remaining_functional_tests(
        self,
        functional_plan: TestExecutionPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute remaining functional tests"""
        
        # Mock implementation - would execute remaining functional tests
        pass
    
    async def _execute_comprehensive_security_scans(
        self,
        security_plan: SecurityScanPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute comprehensive security scans"""
        
        # Mock implementation - would execute comprehensive security scans
        pass
    
    async def _execute_comprehensive_compliance_checks(
        self,
        compliance_plan: ComplianceAssessmentPlan,
        context: Dict[str, Any],
        result: UnifiedTestResult
    ):
        """Execute comprehensive compliance checks"""
        
        # Mock implementation - would execute comprehensive compliance checks
        pass
    
    async def _perform_unified_analysis(self, result: UnifiedTestResult):
        """Perform cross-domain analysis across all testing aspects"""
        
        # Analyze domain coverage
        for domain in [TestDomain.WEB, TestDomain.API, TestDomain.MOBILE]:
            domain_tests = [r for r in result.functional_results if getattr(r, 'domain', None) == domain]
            if domain_tests:
                passed_tests = [r for r in domain_tests if r.passed]
                result.domain_coverage[domain.value] = len(passed_tests) / len(domain_tests)
            else:
                result.domain_coverage[domain.value] = 0.0
        
        # Identify integration issues
        if result.functional_results:
            failed_tests = [r for r in result.functional_results if not r.passed]
            for failed_test in failed_tests:
                result.integration_issues.append({
                    "test_id": failed_test.test_id,
                    "domain": getattr(failed_test, 'domain', 'unknown'),
                    "error": failed_test.error_message,
                    "impact": "integration"
                })
        
        # Consolidate security vulnerabilities
        if result.security_results:
            for vuln in result.security_results.vulnerabilities:
                result.security_vulnerabilities.append({
                    "vulnerability_id": vuln.vulnerability_id,
                    "severity": vuln.severity.value,
                    "description": vuln.description,
                    "affected_component": vuln.affected_component
                })
        
        # Consolidate compliance gaps
        if result.compliance_results:
            for gap in result.compliance_results.compliance_gaps:
                result.compliance_gaps.append(gap)
    
    def _calculate_unified_metrics(self, result: UnifiedTestResult):
        """Calculate unified metrics across all testing aspects"""
        
        # Functional metrics
        if result.functional_results:
            passed_functional = len([r for r in result.functional_results if r.passed])
            result.functional_pass_rate = passed_functional / len(result.functional_results)
        else:
            result.functional_pass_rate = 0.0
        
        # Security metrics
        if result.security_results:
            result.security_score = 1.0 - (result.security_results.risk_score / 100.0)
        else:
            result.security_score = 1.0
        
        # Compliance metrics
        if result.compliance_results:
            result.compliance_score = result.compliance_results.overall_compliance_score
        else:
            result.compliance_score = 1.0
        
        # Overall quality score (weighted average)
        weights = {
            'functional': 0.4,
            'security': 0.3,
            'compliance': 0.3
        }
        
        result.overall_quality_score = (
            result.functional_pass_rate * weights['functional'] +
            result.security_score * weights['security'] +
            result.compliance_score * weights['compliance']
        )
        
        # Determine risk level
        if result.overall_quality_score >= 0.9:
            result.risk_level = "LOW"
        elif result.overall_quality_score >= 0.7:
            result.risk_level = "MEDIUM"
        elif result.overall_quality_score >= 0.5:
            result.risk_level = "HIGH"
        else:
            result.risk_level = "CRITICAL"
        
        # Count total tests executed
        result.total_tests_executed = len(result.functional_results)
        if result.security_results:
            result.total_tests_executed += len(result.security_results.scan_results)
        if result.compliance_results:
            result.total_tests_executed += result.compliance_results.total_checks
    
    async def _generate_unified_recommendations(self, result: UnifiedTestResult):
        """Generate unified recommendations based on all testing results"""
        
        # Overall quality recommendations
        if result.overall_quality_score < 0.7:
            result.recommendations.append({
                "priority": "critical",
                "category": "overall_quality",
                "title": "Improve Overall Quality Score",
                "description": f"Overall quality score is {result.overall_quality_score:.2f}",
                "actions": [
                    "Address functional test failures",
                    "Resolve security vulnerabilities",
                    "Fix compliance gaps",
                    "Implement quality gates"
                ]
            })
        
        # Functional recommendations
        if result.functional_pass_rate < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "functional",
                "title": "Improve Functional Test Coverage",
                "description": f"Functional pass rate: {result.functional_pass_rate:.2f}",
                "actions": [
                    "Fix failing functional tests",
                    "Improve test data management",
                    "Enhance cross-domain integration"
                ]
            })
        
        # Security recommendations
        if result.security_score < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "security",
                "title": "Address Security Vulnerabilities",
                "description": f"Security score: {result.security_score:.2f}",
                "actions": [
                    "Fix identified vulnerabilities",
                    "Implement security controls",
                    "Enhance security monitoring"
                ]
            })
        
        # Compliance recommendations
        if result.compliance_score < 0.8:
            result.recommendations.append({
                "priority": "high",
                "category": "compliance",
                "title": "Improve Compliance Posture",
                "description": f"Compliance score: {result.compliance_score:.2f}",
                "actions": [
                    "Address compliance gaps",
                    "Update policies and procedures",
                    "Implement compliance controls"
                ]
            })
        
        # Domain-specific recommendations
        for domain, coverage in result.domain_coverage.items():
            if coverage < 0.8:
                result.recommendations.append({
                    "priority": "medium",
                    "category": f"{domain}_coverage",
                    "title": f"Improve {domain.upper()} Domain Coverage",
                    "description": f"{domain.upper()} coverage: {coverage:.2f}",
                    "actions": [
                        f"Add more {domain} test cases",
                        f"Fix {domain} integration issues",
                        f"Enhance {domain} test automation"
                    ]
                })
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active execution"""
        
        if execution_id in self.active_executions:
            result = self.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": "running",
                "progress": {
                    "functional_tests": len(result.functional_results),
                    "security_scans": 1 if result.security_results else 0,
                    "compliance_checks": result.compliance_results.total_checks if result.compliance_results else 0,
                    "elapsed_time": (datetime.now() - result.start_time).total_seconds()
                }
            }
        
        return None
    
    def generate_unified_report(self, result: UnifiedTestResult) -> Dict[str, Any]:
        """Generate comprehensive unified testing report"""
        
        return {
            "execution_info": {
                "execution_id": result.execution_id,
                "plan_name": result.plan.name if result.plan else "Unknown",
                "execution_time": result.start_time.isoformat(),
                "duration": result.duration,
                "status": result.status,
                "scope": result.plan.scope.value if result.plan else "unknown"
            },
            "overall_metrics": {
                "quality_score": result.overall_quality_score,
                "risk_level": result.risk_level,
                "functional_pass_rate": result.functional_pass_rate,
                "security_score": result.security_score,
                "compliance_score": result.compliance_score,
                "total_tests_executed": result.total_tests_executed
            },
            "domain_coverage": result.domain_coverage,
            "functional_results": {
                "total_tests": len(result.functional_results),
                "passed_tests": len([r for r in result.functional_results if r.passed]),
                "failed_tests": len([r for r in result.functional_results if not r.passed]),
                "pass_rate": result.functional_pass_rate
            },
            "security_results": {
                "vulnerabilities_found": len(result.security_vulnerabilities),
                "security_score": result.security_score,
                "critical_vulnerabilities": len([v for v in result.security_vulnerabilities if v.get("severity") == "critical"])
            } if result.security_results else None,
            "compliance_results": {
                "compliance_score": result.compliance_score,
                "compliance_gaps": len(result.compliance_gaps),
                "critical_gaps": len([g for g in result.compliance_gaps if g.get("severity") == "critical"])
            } if result.compliance_results else None,
            "integration_analysis": {
                "integration_issues": result.integration_issues,
                "cross_domain_coverage": result.domain_coverage
            },
            "critical_issues": result.critical_issues,
            "recommendations": result.recommendations,
            "traceability": {
                "test_coverage_matrix": result.test_coverage_matrix,
                "requirement_coverage": result.requirement_coverage
            }
        }


# Utility functions
def create_comprehensive_unified_plan(
    name: str = "Comprehensive Unified Testing"
) -> UnifiedTestPlan:
    """Create a comprehensive unified testing plan"""
    
    orchestrator = UnifiedTestingOrchestrator()
    
    return orchestrator.create_unified_plan(
        name=name,
        scope=UnifiedTestingScope.COMPREHENSIVE,
        strategy=UnifiedExecutionStrategy.LAYERED,
        domains=[TestDomain.WEB, TestDomain.API, TestDomain.MOBILE]
    )


def create_comprehensive_test_plan(
    target_url: str,
    api_endpoints: Optional[List[str]] = None,
    mobile_apps: Optional[List[str]] = None,
    execution_strategy: UnifiedExecutionStrategy = UnifiedExecutionStrategy.INTEGRATED,
    include_security: bool = True,
    include_compliance: bool = True,
    name: str = "Comprehensive Test Plan"
) -> UnifiedTestPlan:
    """Create a comprehensive test plan with specified parameters"""
    
    orchestrator = UnifiedTestingOrchestrator()
    
    # Determine scope based on parameters
    if include_security and include_compliance:
        scope = UnifiedTestingScope.COMPREHENSIVE
    elif include_security:
        scope = UnifiedTestingScope.FUNCTIONAL_SECURITY
    elif include_compliance:
        scope = UnifiedTestingScope.FUNCTIONAL_COMPLIANCE
    else:
        scope = UnifiedTestingScope.FUNCTIONAL_ONLY
    
    # Create the plan
    plan = orchestrator.create_unified_plan(
        name=name,
        scope=scope,
        strategy=execution_strategy,
        domains=[TestDomain.WEB, TestDomain.API, TestDomain.MOBILE]
    )
    
    # Configure target settings
    plan.target_config = {
        "primary_target": target_url,
        "api_endpoints": api_endpoints or [],
        "mobile_apps": mobile_apps or []
    }
    
    # Configure test suites
    plan.test_suites = {
        "functional": {
            "web_tests": ["login", "navigation", "forms"],
            "api_tests": ["authentication", "data_validation"],
            "mobile_tests": ["ui_elements", "gestures"] if mobile_apps else []
        }
    }
    
    # Configure security scans if enabled
    if include_security:
        plan.security_scans = {
            "trivy": {
                "scan_filesystem": True,
                "scan_config": True
            }
        }
    
    # Configure compliance checks if enabled
    if include_compliance:
        plan.compliance_checks = {
            "GDPR": {
                "level": "basic",
                "automated_only": True
            }
        }
    
    return plan


def create_compliance_focused_plan(
    name: str = "Compliance-Focused Testing"
) -> UnifiedTestPlan:
    """Create a compliance-focused testing plan"""
    
    orchestrator = UnifiedTestingOrchestrator()
    
    return orchestrator.create_unified_plan(
        name=name,
        scope=UnifiedTestingScope.FUNCTIONAL_COMPLIANCE,
        strategy=UnifiedExecutionStrategy.INTEGRATED,
        domains=[TestDomain.WEB, TestDomain.API]
    )


def create_security_focused_plan(
    name: str = "Security-Focused Testing"
) -> UnifiedTestPlan:
    """Create a security-focused testing plan"""
    
    orchestrator = UnifiedTestingOrchestrator()
    
    return orchestrator.create_unified_plan(
        name=name,
        scope=UnifiedTestingScope.FUNCTIONAL_SECURITY,
        strategy=UnifiedExecutionStrategy.INTEGRATED,
        domains=[TestDomain.WEB, TestDomain.API]
    )


async def run_comprehensive_unified_testing(
    target_system: str,
    **kwargs
) -> UnifiedTestResult:
    """Run comprehensive unified testing"""
    
    orchestrator = UnifiedTestingOrchestrator()
    plan = create_comprehensive_unified_plan()
    
    context = {
        "target": target_system,
        "orchestrator": "Unified Testing Orchestrator",
        "scope": "Comprehensive Testing"
    }
    context.update(kwargs)
    
    return await orchestrator.execute_unified_testing(plan, context)