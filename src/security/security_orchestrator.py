"""
Security Orchestrator

Coordinates and manages security scanning across multiple tools (OWASP ZAP, Snyk, Trivy)
within the unified testing framework, providing centralized security testing capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .security_scanner import (
    SecurityScanner, ScanConfiguration, SecurityScanResult,
    SecurityVulnerability, VulnerabilityLevel, ScanType, ScanStatus
)
from .owasp_zap_integration import ZAPScanner, ZAPScanConfig
from .snyk_integration import SnykScanner, SnykScanConfig
from .trivy_integration import TrivyScanner, TrivyScanConfig

logger = logging.getLogger(__name__)


class SecurityScanPriority(Enum):
    """Security scan priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityScanStrategy(Enum):
    """Security scanning strategies"""
    COMPREHENSIVE = "comprehensive"  # All available scanners
    FAST = "fast"  # Quick scans only
    TARGETED = "targeted"  # Specific scanners based on context
    COMPLIANCE = "compliance"  # Compliance-focused scans


@dataclass
class SecurityScanPlan:
    """Plan for coordinated security scanning"""
    
    plan_id: str
    name: str
    description: str
    strategy: SecurityScanStrategy
    priority: SecurityScanPriority
    
    # Scan configurations
    zap_config: Optional[ZAPScanConfig] = None
    snyk_config: Optional[SnykScanConfig] = None
    trivy_config: Optional[TrivyScanConfig] = None
    
    # Execution settings
    parallel_execution: bool = True
    max_concurrent_scans: int = 3
    timeout_minutes: int = 60
    
    # Filtering and thresholds
    min_severity: VulnerabilityLevel = VulnerabilityLevel.MEDIUM
    max_vulnerabilities: Optional[int] = None
    fail_on_critical: bool = True
    
    # Output settings
    output_directory: str = "security_reports"
    generate_consolidated_report: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class SecurityScanExecution:
    """Execution context for security scans"""
    
    execution_id: str
    plan: SecurityScanPlan
    start_time: datetime
    
    # Scanner instances
    zap_scanner: Optional[ZAPScanner] = None
    snyk_scanner: Optional[SnykScanner] = None
    trivy_scanner: Optional[TrivyScanner] = None
    
    # Execution state
    status: ScanStatus = ScanStatus.PENDING
    current_scanner: Optional[str] = None
    completed_scanners: Set[str] = field(default_factory=set)
    failed_scanners: Set[str] = field(default_factory=set)
    
    # Results
    scan_results: Dict[str, SecurityScanResult] = field(default_factory=dict)
    consolidated_result: Optional['ConsolidatedSecurityResult'] = None
    
    # Timing
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Error handling
    errors: List[str] = field(default_factory=list)


@dataclass
class ConsolidatedSecurityResult:
    """Consolidated results from multiple security scanners"""
    
    execution_id: str
    plan_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    
    # Overall status
    status: ScanStatus
    success: bool
    
    # Scanner results
    zap_result: Optional[SecurityScanResult] = None
    snyk_result: Optional[SecurityScanResult] = None
    trivy_result: Optional[SecurityScanResult] = None
    
    # Consolidated vulnerabilities
    all_vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    unique_vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    
    # Summary statistics
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    
    # Scanner statistics
    scanners_executed: List[str] = field(default_factory=list)
    scanners_successful: List[str] = field(default_factory=list)
    scanners_failed: List[str] = field(default_factory=list)
    
    # Risk assessment
    overall_risk_level: VulnerabilityLevel = VulnerabilityLevel.INFO
    compliance_issues: List[str] = field(default_factory=list)
    
    # Reports
    report_files: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class SecurityOrchestrator:
    """Orchestrates security scanning across multiple tools"""
    
    def __init__(self, 
                 zap_path: Optional[str] = None,
                 snyk_token: Optional[str] = None,
                 trivy_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize scanners
        self.scanners: Dict[str, SecurityScanner] = {}
        
        # Initialize ZAP scanner
        try:
            self.zap_scanner = ZAPScanner(zap_path)
            if self.zap_scanner.is_available():
                self.scanners["zap"] = self.zap_scanner
                self.logger.info("OWASP ZAP scanner initialized")
            else:
                self.logger.warning("OWASP ZAP not available")
        except Exception as e:
            self.logger.warning(f"Failed to initialize ZAP scanner: {e}")
        
        # Initialize Snyk scanner
        try:
            self.snyk_scanner = SnykScanner(snyk_token)
            if self.snyk_scanner.is_available():
                self.scanners["snyk"] = self.snyk_scanner
                self.logger.info("Snyk scanner initialized")
            else:
                self.logger.warning("Snyk not available")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Snyk scanner: {e}")
        
        # Initialize Trivy scanner
        try:
            self.trivy_scanner = TrivyScanner(trivy_path)
            if self.trivy_scanner.is_available():
                self.scanners["trivy"] = self.trivy_scanner
                self.logger.info("Trivy scanner initialized")
            else:
                self.logger.warning("Trivy not available")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Trivy scanner: {e}")
        
        self.logger.info(f"Security orchestrator initialized with {len(self.scanners)} scanners")
    
    def get_available_scanners(self) -> List[str]:
        """Get list of available scanner names"""
        return list(self.scanners.keys())
    
    def is_scanner_available(self, scanner_name: str) -> bool:
        """Check if a specific scanner is available"""
        return scanner_name in self.scanners
    
    async def execute_security_scan(self, plan: SecurityScanPlan) -> ConsolidatedSecurityResult:
        """Execute a comprehensive security scan plan"""
        execution = SecurityScanExecution(
            execution_id=f"sec_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            plan=plan,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"Starting security scan execution: {plan.name}")
            execution.status = ScanStatus.RUNNING
            
            # Prepare scanners based on plan
            await self._prepare_scanners(execution)
            
            # Execute scans
            if plan.parallel_execution:
                await self._execute_parallel_scans(execution)
            else:
                await self._execute_sequential_scans(execution)
            
            # Consolidate results
            consolidated_result = await self._consolidate_results(execution)
            
            # Generate reports
            await self._generate_consolidated_reports(execution, consolidated_result)
            
            execution.status = ScanStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            
            consolidated_result.end_time = execution.end_time
            consolidated_result.duration = execution.duration
            consolidated_result.status = ScanStatus.COMPLETED
            consolidated_result.success = len(execution.failed_scanners) == 0
            
            self.logger.info(f"Security scan execution completed: {consolidated_result.total_vulnerabilities} vulnerabilities found")
            
            return consolidated_result
        
        except Exception as e:
            self.logger.error(f"Security scan execution failed: {e}")
            execution.status = ScanStatus.FAILED
            execution.errors.append(str(e))
            
            # Create minimal consolidated result for failed execution
            consolidated_result = ConsolidatedSecurityResult(
                execution_id=execution.execution_id,
                plan_name=plan.name,
                start_time=execution.start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - execution.start_time).total_seconds(),
                status=ScanStatus.FAILED,
                success=False
            )
            
            return consolidated_result
    
    async def _prepare_scanners(self, execution: SecurityScanExecution):
        """Prepare scanners based on the execution plan"""
        plan = execution.plan
        
        # Prepare ZAP scanner
        if plan.zap_config and "zap" in self.scanners:
            execution.zap_scanner = self.scanners["zap"]
            self.logger.debug("ZAP scanner prepared")
        
        # Prepare Snyk scanner
        if plan.snyk_config and "snyk" in self.scanners:
            execution.snyk_scanner = self.scanners["snyk"]
            self.logger.debug("Snyk scanner prepared")
        
        # Prepare Trivy scanner
        if plan.trivy_config and "trivy" in self.scanners:
            execution.trivy_scanner = self.scanners["trivy"]
            self.logger.debug("Trivy scanner prepared")
    
    async def _execute_parallel_scans(self, execution: SecurityScanExecution):
        """Execute security scans in parallel"""
        tasks = []
        
        # Create scan tasks
        if execution.zap_scanner and execution.plan.zap_config:
            tasks.append(self._execute_zap_scan(execution))
        
        if execution.snyk_scanner and execution.plan.snyk_config:
            tasks.append(self._execute_snyk_scan(execution))
        
        if execution.trivy_scanner and execution.plan.trivy_config:
            tasks.append(self._execute_trivy_scan(execution))
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(execution.plan.max_concurrent_scans)
        
        async def limited_task(task):
            async with semaphore:
                return await task
        
        # Wait for all scans to complete
        if tasks:
            await asyncio.gather(*[limited_task(task) for task in tasks], return_exceptions=True)
    
    async def _execute_sequential_scans(self, execution: SecurityScanExecution):
        """Execute security scans sequentially"""
        # Execute ZAP scan
        if execution.zap_scanner and execution.plan.zap_config:
            await self._execute_zap_scan(execution)
        
        # Execute Snyk scan
        if execution.snyk_scanner and execution.plan.snyk_config:
            await self._execute_snyk_scan(execution)
        
        # Execute Trivy scan
        if execution.trivy_scanner and execution.plan.trivy_config:
            await self._execute_trivy_scan(execution)
    
    async def _execute_zap_scan(self, execution: SecurityScanExecution):
        """Execute OWASP ZAP scan"""
        try:
            self.logger.info("Starting OWASP ZAP scan")
            execution.current_scanner = "zap"
            
            result = await execution.zap_scanner.scan(execution.plan.zap_config)
            execution.scan_results["zap"] = result
            
            if result.status == ScanStatus.COMPLETED:
                execution.completed_scanners.add("zap")
                self.logger.info(f"ZAP scan completed: {result.total_vulnerabilities} vulnerabilities")
            else:
                execution.failed_scanners.add("zap")
                self.logger.error(f"ZAP scan failed: {result.error_message}")
        
        except Exception as e:
            self.logger.error(f"ZAP scan execution failed: {e}")
            execution.failed_scanners.add("zap")
            execution.errors.append(f"ZAP scan error: {e}")
    
    async def _execute_snyk_scan(self, execution: SecurityScanExecution):
        """Execute Snyk scan"""
        try:
            self.logger.info("Starting Snyk scan")
            execution.current_scanner = "snyk"
            
            result = await execution.snyk_scanner.scan(execution.plan.snyk_config)
            execution.scan_results["snyk"] = result
            
            if result.status == ScanStatus.COMPLETED:
                execution.completed_scanners.add("snyk")
                self.logger.info(f"Snyk scan completed: {result.total_vulnerabilities} vulnerabilities")
            else:
                execution.failed_scanners.add("snyk")
                self.logger.error(f"Snyk scan failed: {result.error_message}")
        
        except Exception as e:
            self.logger.error(f"Snyk scan execution failed: {e}")
            execution.failed_scanners.add("snyk")
            execution.errors.append(f"Snyk scan error: {e}")
    
    async def _execute_trivy_scan(self, execution: SecurityScanExecution):
        """Execute Trivy scan"""
        try:
            self.logger.info("Starting Trivy scan")
            execution.current_scanner = "trivy"
            
            result = await execution.trivy_scanner.scan(execution.plan.trivy_config)
            execution.scan_results["trivy"] = result
            
            if result.status == ScanStatus.COMPLETED:
                execution.completed_scanners.add("trivy")
                self.logger.info(f"Trivy scan completed: {result.total_vulnerabilities} vulnerabilities")
            else:
                execution.failed_scanners.add("trivy")
                self.logger.error(f"Trivy scan failed: {result.error_message}")
        
        except Exception as e:
            self.logger.error(f"Trivy scan execution failed: {e}")
            execution.failed_scanners.add("trivy")
            execution.errors.append(f"Trivy scan error: {e}")
    
    async def _consolidate_results(self, execution: SecurityScanExecution) -> ConsolidatedSecurityResult:
        """Consolidate results from all scanners"""
        consolidated = ConsolidatedSecurityResult(
            execution_id=execution.execution_id,
            plan_name=execution.plan.name,
            start_time=execution.start_time,
            end_time=datetime.now(),
            duration=0,  # Will be set later
            status=ScanStatus.COMPLETED,
            success=len(execution.failed_scanners) == 0
        )
        
        # Collect results from each scanner
        if "zap" in execution.scan_results:
            consolidated.zap_result = execution.scan_results["zap"]
            consolidated.scanners_executed.append("zap")
            if "zap" in execution.completed_scanners:
                consolidated.scanners_successful.append("zap")
            else:
                consolidated.scanners_failed.append("zap")
        
        if "snyk" in execution.scan_results:
            consolidated.snyk_result = execution.scan_results["snyk"]
            consolidated.scanners_executed.append("snyk")
            if "snyk" in execution.completed_scanners:
                consolidated.scanners_successful.append("snyk")
            else:
                consolidated.scanners_failed.append("snyk")
        
        if "trivy" in execution.scan_results:
            consolidated.trivy_result = execution.scan_results["trivy"]
            consolidated.scanners_executed.append("trivy")
            if "trivy" in execution.completed_scanners:
                consolidated.scanners_successful.append("trivy")
            else:
                consolidated.scanners_failed.append("trivy")
        
        # Consolidate vulnerabilities
        await self._consolidate_vulnerabilities(consolidated)
        
        # Calculate risk level
        consolidated.overall_risk_level = self._calculate_overall_risk(consolidated)
        
        # Generate recommendations
        consolidated.recommendations = self._generate_recommendations(consolidated)
        
        return consolidated
    
    async def _consolidate_vulnerabilities(self, consolidated: ConsolidatedSecurityResult):
        """Consolidate vulnerabilities from all scanners"""
        all_vulns = []
        
        # Collect vulnerabilities from all scanners
        for result in [consolidated.zap_result, consolidated.snyk_result, consolidated.trivy_result]:
            if result and result.vulnerabilities:
                all_vulns.extend(result.vulnerabilities)
        
        consolidated.all_vulnerabilities = all_vulns
        
        # Deduplicate vulnerabilities based on ID and title
        seen = set()
        unique_vulns = []
        
        for vuln in all_vulns:
            # Create a unique key based on vulnerability characteristics
            key = (vuln.id, vuln.title.lower(), vuln.category)
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        consolidated.unique_vulnerabilities = unique_vulns
        
        # Calculate statistics
        consolidated.total_vulnerabilities = len(unique_vulns)
        
        for vuln in unique_vulns:
            if vuln.severity == VulnerabilityLevel.CRITICAL:
                consolidated.critical_count += 1
            elif vuln.severity == VulnerabilityLevel.HIGH:
                consolidated.high_count += 1
            elif vuln.severity == VulnerabilityLevel.MEDIUM:
                consolidated.medium_count += 1
            elif vuln.severity == VulnerabilityLevel.LOW:
                consolidated.low_count += 1
            else:
                consolidated.info_count += 1
    
    def _calculate_overall_risk(self, consolidated: ConsolidatedSecurityResult) -> VulnerabilityLevel:
        """Calculate overall risk level based on vulnerabilities"""
        if consolidated.critical_count > 0:
            return VulnerabilityLevel.CRITICAL
        elif consolidated.high_count > 0:
            return VulnerabilityLevel.HIGH
        elif consolidated.medium_count > 0:
            return VulnerabilityLevel.MEDIUM
        elif consolidated.low_count > 0:
            return VulnerabilityLevel.LOW
        else:
            return VulnerabilityLevel.INFO
    
    def _generate_recommendations(self, consolidated: ConsolidatedSecurityResult) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []
        
        # Critical vulnerabilities
        if consolidated.critical_count > 0:
            recommendations.append(
                f"URGENT: Address {consolidated.critical_count} critical vulnerabilities immediately"
            )
        
        # High vulnerabilities
        if consolidated.high_count > 0:
            recommendations.append(
                f"High Priority: Fix {consolidated.high_count} high-severity vulnerabilities"
            )
        
        # Scanner-specific recommendations
        if consolidated.zap_result and consolidated.zap_result.total_vulnerabilities > 0:
            recommendations.append("Review web application security findings from OWASP ZAP")
        
        if consolidated.snyk_result and consolidated.snyk_result.total_vulnerabilities > 0:
            recommendations.append("Update dependencies to fix vulnerabilities found by Snyk")
        
        if consolidated.trivy_result and consolidated.trivy_result.total_vulnerabilities > 0:
            recommendations.append("Address container and infrastructure vulnerabilities found by Trivy")
        
        # General recommendations
        if consolidated.total_vulnerabilities == 0:
            recommendations.append("No vulnerabilities found - maintain current security practices")
        else:
            recommendations.append("Implement regular security scanning in CI/CD pipeline")
            recommendations.append("Consider security training for development team")
        
        return recommendations
    
    async def _generate_consolidated_reports(self, execution: SecurityScanExecution, 
                                           consolidated: ConsolidatedSecurityResult):
        """Generate consolidated security reports"""
        try:
            output_dir = Path(execution.plan.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate consolidated JSON report
            report_path = output_dir / f"consolidated_security_report_{execution.execution_id}.json"
            
            report_data = {
                "execution_info": {
                    "execution_id": execution.execution_id,
                    "plan_name": execution.plan.name,
                    "strategy": execution.plan.strategy.value,
                    "priority": execution.plan.priority.value,
                    "start_time": consolidated.start_time.isoformat(),
                    "end_time": consolidated.end_time.isoformat(),
                    "duration": consolidated.duration
                },
                "summary": {
                    "total_vulnerabilities": consolidated.total_vulnerabilities,
                    "critical": consolidated.critical_count,
                    "high": consolidated.high_count,
                    "medium": consolidated.medium_count,
                    "low": consolidated.low_count,
                    "info": consolidated.info_count,
                    "overall_risk_level": consolidated.overall_risk_level.value,
                    "success": consolidated.success
                },
                "scanners": {
                    "executed": consolidated.scanners_executed,
                    "successful": consolidated.scanners_successful,
                    "failed": consolidated.scanners_failed
                },
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "severity": v.severity.value,
                        "category": v.category,
                        "scanner": v.scanner,
                        "description": v.description,
                        "recommendation": v.recommendation,
                        "cvss_score": v.cvss_score
                    }
                    for v in consolidated.unique_vulnerabilities
                ],
                "recommendations": consolidated.recommendations,
                "compliance_issues": consolidated.compliance_issues
            }
            
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            consolidated.report_files.append(str(report_path))
            
            self.logger.info(f"Consolidated security report generated: {report_path}")
        
        except Exception as e:
            self.logger.warning(f"Failed to generate consolidated report: {e}")
    
    def create_comprehensive_scan_plan(self, 
                                     target: str,
                                     web_url: Optional[str] = None,
                                     project_path: Optional[str] = None,
                                     container_image: Optional[str] = None) -> SecurityScanPlan:
        """Create a comprehensive security scan plan"""
        plan_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        configs = {}
        
        # Configure ZAP for web application scanning
        if web_url and "zap" in self.scanners:
            from .owasp_zap_integration import ZAPScanConfig
            configs["zap_config"] = ZAPScanConfig(
                scan_type=ScanType.WEB_APPLICATION,
                target=web_url,
                timeout_minutes=30,
                target_url=web_url,
                scan_types=["spider", "ajax_spider", "passive", "active"],
                spider_max_depth=5,
                ajax_spider_max_duration=10,
                active_scan_policy="Default Policy"
            )
        
        # Configure Snyk for dependency scanning
        if project_path and "snyk" in self.scanners:
            from .snyk_integration import SnykScanConfig
            configs["snyk_config"] = SnykScanConfig(
                scan_type=ScanType.DEPENDENCY,
                target=project_path,
                timeout_minutes=20,
                project_path=project_path,
                scan_types=["dependencies", "code"],
                severity_threshold="medium",
                fail_on_issues=False
            )
        
        # Configure Trivy for container/filesystem scanning
        if container_image and "trivy" in self.scanners:
            from .trivy_integration import TrivyScanConfig
            configs["trivy_config"] = TrivyScanConfig(
                scan_type=ScanType.CONTAINER,
                target=container_image,
                timeout_minutes=25,
                scan_target_type="image",
                image_name=container_image,
                security_checks=["vuln", "secret", "config"],
                severity=["MEDIUM", "HIGH", "CRITICAL"]
            )
        elif project_path and "trivy" in self.scanners:
            from .trivy_integration import TrivyScanConfig
            configs["trivy_config"] = TrivyScanConfig(
                scan_type=ScanType.INFRASTRUCTURE,
                target=project_path,
                timeout_minutes=25,
                scan_target_type="fs",
                filesystem_path=project_path,
                security_checks=["vuln", "secret", "config"],
                severity=["MEDIUM", "HIGH", "CRITICAL"]
            )
        
        return SecurityScanPlan(
            plan_id=plan_id,
            name=f"Comprehensive Security Scan - {target}",
            description="Comprehensive security scanning using all available tools",
            strategy=SecurityScanStrategy.COMPREHENSIVE,
            priority=SecurityScanPriority.HIGH,
            parallel_execution=True,
            max_concurrent_scans=3,
            timeout_minutes=60,
            min_severity=VulnerabilityLevel.MEDIUM,
            fail_on_critical=True,
            **configs
        )


# Example usage functions
def create_web_security_plan(web_url: str) -> SecurityScanPlan:
    """Create a security plan focused on web application testing"""
    from .owasp_zap_integration import ZAPScanConfig
    
    return SecurityScanPlan(
        plan_id=f"web_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=f"Web Security Scan - {web_url}",
        description="Web application security scanning with OWASP ZAP",
        strategy=SecurityScanStrategy.TARGETED,
        priority=SecurityScanPriority.HIGH,
        zap_config=ZAPScanConfig(
            scan_type=ScanType.WEB_APPLICATION,
            target=web_url,
            target_url=web_url,
            scan_types=["spider", "ajax_spider", "passive", "active"],
            timeout_minutes=30
        ),
        parallel_execution=False,
        timeout_minutes=45
    )


def create_dependency_security_plan(project_path: str) -> SecurityScanPlan:
    """Create a security plan focused on dependency scanning"""
    from .snyk_integration import SnykScanConfig
    from .trivy_integration import TrivyScanConfig
    
    return SecurityScanPlan(
        plan_id=f"dependency_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=f"Dependency Security Scan - {project_path}",
        description="Dependency and code security scanning",
        strategy=SecurityScanStrategy.TARGETED,
        priority=SecurityScanPriority.MEDIUM,
        snyk_config=SnykScanConfig(
            scan_type=ScanType.DEPENDENCY,
            target=project_path,
            project_path=project_path,
            scan_types=["dependencies", "code"],
            timeout_minutes=15
        ),
        trivy_config=TrivyScanConfig(
            scan_type=ScanType.INFRASTRUCTURE,
            target=project_path,
            scan_target_type="fs",
            filesystem_path=project_path,
            security_checks=["vuln", "secret"],
            timeout_minutes=15
        ),
        parallel_execution=True,
        timeout_minutes=30
    )


def create_comprehensive_security_plan(
    target: str,
    web_url: Optional[str] = None,
    project_path: Optional[str] = None,
    container_image: Optional[str] = None,
    name: str = "Comprehensive Security Plan"
) -> SecurityScanPlan:
    """Create a comprehensive security plan with all available scanners"""
    
    plan_id = f"comprehensive_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    configs = {}
    
    # Configure ZAP for web application scanning
    if web_url:
        from .owasp_zap_integration import ZAPScanConfig
        configs["zap_config"] = ZAPScanConfig(
            scan_type=ScanType.WEB_APPLICATION,
            target=web_url,
            timeout_minutes=30,
            target_url=web_url,
            scan_types=["spider", "ajax_spider", "passive", "active"],
            spider_max_depth=5,
            ajax_spider_max_duration=10,
            active_scan_policy="Default Policy"
        )
    
    # Configure Snyk for dependency scanning
    if project_path:
        from .snyk_integration import SnykScanConfig
        configs["snyk_config"] = SnykScanConfig(
            scan_type=ScanType.DEPENDENCY,
            target=project_path,
            timeout_minutes=20,
            project_path=project_path,
            scan_types=["dependencies", "code", "container"],
            severity_threshold="medium"
        )
    
    # Configure Trivy for infrastructure scanning
    if project_path or container_image:
        from .trivy_integration import TrivyScanConfig
        trivy_target = container_image if container_image else project_path
        scan_target_type = "image" if container_image else "fs"
        
        configs["trivy_config"] = TrivyScanConfig(
            scan_type=ScanType.INFRASTRUCTURE,
            target=trivy_target,
            timeout_minutes=15,
            scan_target_type=scan_target_type,
            filesystem_path=project_path if not container_image else None,
            container_image=container_image,
            security_checks=["vuln", "secret", "config"],
            severity_filter=["MEDIUM", "HIGH", "CRITICAL"]
        )
    
    return SecurityScanPlan(
        plan_id=plan_id,
        name=name,
        description="Comprehensive security assessment with multiple scanners",
        strategy=SecurityScanStrategy.COMPREHENSIVE,
        priority=SecurityScanPriority.HIGH,
        **configs,
        parallel_execution=True,
        max_concurrent_scans=3,
        timeout_minutes=60,
        min_severity=VulnerabilityLevel.MEDIUM,
        fail_on_critical=True,
        generate_consolidated_report=True
    )