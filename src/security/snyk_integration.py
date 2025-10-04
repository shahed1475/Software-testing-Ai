"""
Snyk Integration

Integrates Snyk for dependency vulnerability scanning, license compliance,
and container security scanning within the unified testing framework.
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .security_scanner import (
    SecurityScanner, ScanConfiguration, SecurityScanResult,
    SecurityVulnerability, VulnerabilityLevel, ScanType, ScanStatus
)

logger = logging.getLogger(__name__)


@dataclass
class SnykScanConfig(ScanConfiguration):
    """Configuration for Snyk scans"""
    
    # Snyk authentication
    snyk_token: Optional[str] = None
    snyk_org: Optional[str] = None
    
    # Scan types
    test_dependencies: bool = True
    test_code: bool = False
    test_container: bool = False
    test_iac: bool = False  # Infrastructure as Code
    
    # Project configuration
    project_path: str = "."
    package_manager: Optional[str] = None  # npm, pip, maven, gradle, etc.
    manifest_file: Optional[str] = None
    
    # Vulnerability filtering
    severity_threshold: str = "low"  # low, medium, high, critical
    ignore_policy: bool = True
    include_dev_deps: bool = False
    
    # License scanning
    license_policy: Optional[str] = None
    fail_on_license_issues: bool = False
    
    # Container scanning
    dockerfile_path: Optional[str] = None
    base_image: Optional[str] = None
    
    # IaC scanning
    iac_file_types: List[str] = field(default_factory=lambda: ["terraform", "cloudformation", "kubernetes"])
    
    # Output configuration
    json_output: bool = True
    sarif_output: bool = False
    html_output: bool = False
    
    # Advanced options
    all_projects: bool = False
    detection_depth: int = 4
    exclude_base_image_vulns: bool = False
    trust_policies: bool = True


@dataclass
class SnykVulnerability:
    """Snyk-specific vulnerability information"""
    
    id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float] = None
    cve: Optional[str] = None
    cwe: Optional[List[str]] = None
    
    # Package information
    package_name: str = ""
    package_version: str = ""
    package_manager: str = ""
    
    # Fix information
    is_fixable: bool = False
    fix_version: Optional[str] = None
    upgrade_path: List[str] = field(default_factory=list)
    
    # Exploit information
    exploit_maturity: Optional[str] = None
    is_malicious: bool = False
    
    # References
    references: List[str] = field(default_factory=list)
    patches: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SnykLicenseIssue:
    """Snyk license compliance issue"""
    
    id: str
    license: str
    package_name: str
    package_version: str
    severity: str
    instruction: str
    package_manager: str


@dataclass
class SnykScanResult(SecurityScanResult):
    """Extended scan result for Snyk-specific data"""
    
    # Snyk-specific metrics
    dependency_count: int = 0
    license_issues: List[SnykLicenseIssue] = field(default_factory=list)
    
    # Package manager information
    package_manager: Optional[str] = None
    manifest_files: List[str] = field(default_factory=list)
    
    # Fix information
    fixable_vulnerabilities: int = 0
    upgrade_available: int = 0
    patch_available: int = 0
    
    # Project information
    project_name: Optional[str] = None
    project_id: Optional[str] = None


class SnykScanner(SecurityScanner):
    """Snyk security scanner implementation"""
    
    def __init__(self, snyk_path: Optional[str] = None):
        super().__init__("Snyk", "1.1000.0")
        self.snyk_path = snyk_path or "snyk"
        self._check_snyk_installation()
    
    def _check_snyk_installation(self):
        """Check if Snyk CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.snyk_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.version = result.stdout.strip()
                self.logger.info(f"Snyk CLI found: {self.version}")
            else:
                self.logger.warning("Snyk CLI not found or not accessible")
        except Exception as e:
            self.logger.warning(f"Failed to check Snyk installation: {e}")
    
    def is_available(self) -> bool:
        """Check if Snyk is available"""
        try:
            result = subprocess.run(
                [self.snyk_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def get_supported_scan_types(self) -> List[ScanType]:
        """Snyk supports dependency, container, and IaC scanning"""
        return [
            ScanType.DEPENDENCY,
            ScanType.CONTAINER,
            ScanType.INFRASTRUCTURE,
            ScanType.LICENSE_COMPLIANCE
        ]
    
    async def authenticate(self, config: SnykScanConfig) -> bool:
        """Authenticate with Snyk"""
        if not config.snyk_token:
            self.logger.warning("No Snyk token provided")
            return False
        
        try:
            # Set Snyk token
            cmd = [self.snyk_path, "config", "set", "api", config.snyk_token]
            result = await self._run_command(cmd)
            
            if result.returncode == 0:
                self.logger.info("Snyk authentication successful")
                return True
            else:
                self.logger.error(f"Snyk authentication failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Snyk authentication error: {e}")
            return False
    
    async def scan(self, config: SnykScanConfig) -> SnykScanResult:
        """Perform comprehensive Snyk security scan"""
        self.validate_config(config)
        
        result = SnykScanResult(
            scan_id=self.create_scan_result(config).scan_id,
            scan_type=config.scan_type,
            scanner_name=self.name,
            target=config.target or config.project_path,
            start_time=datetime.now(),
            scan_config=config.scan_options
        )
        
        try:
            result.status = ScanStatus.RUNNING
            
            # Authenticate with Snyk
            if not await self.authenticate(config):
                raise RuntimeError("Snyk authentication failed")
            
            # Perform dependency scanning
            if config.test_dependencies:
                await self._scan_dependencies(config, result)
            
            # Perform code scanning
            if config.test_code:
                await self._scan_code(config, result)
            
            # Perform container scanning
            if config.test_container:
                await self._scan_container(config, result)
            
            # Perform IaC scanning
            if config.test_iac:
                await self._scan_iac(config, result)
            
            # Generate reports
            await self._generate_reports(config, result)
            
            result.status = ScanStatus.COMPLETED
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            self.logger.info(f"Snyk scan completed: {result.total_vulnerabilities} vulnerabilities found")
        
        except Exception as e:
            self.logger.error(f"Snyk scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _scan_dependencies(self, config: SnykScanConfig, result: SnykScanResult):
        """Scan project dependencies for vulnerabilities"""
        try:
            self.logger.info("Starting dependency vulnerability scan")
            
            cmd = [self.snyk_path, "test"]
            
            # Add project path
            if config.project_path != ".":
                cmd.extend(["--file", config.project_path])
            
            # Add package manager
            if config.package_manager:
                cmd.extend(["--package-manager", config.package_manager])
            
            # Add severity threshold
            cmd.extend(["--severity-threshold", config.severity_threshold])
            
            # Add organization
            if config.snyk_org:
                cmd.extend(["--org", config.snyk_org])
            
            # Include dev dependencies
            if config.include_dev_deps:
                cmd.append("--dev")
            
            # JSON output
            cmd.append("--json")
            
            # Run scan
            result_data = await self._run_command(cmd)
            
            if result_data.stdout:
                scan_data = json.loads(result_data.stdout)
                await self._parse_dependency_results(scan_data, result)
            
            self.logger.info("Dependency scan completed")
        
        except Exception as e:
            self.logger.warning(f"Dependency scan failed: {e}")
    
    async def _scan_code(self, config: SnykScanConfig, result: SnykScanResult):
        """Scan source code for security issues"""
        try:
            self.logger.info("Starting code security scan")
            
            cmd = [self.snyk_path, "code", "test"]
            
            # Add project path
            if config.project_path != ".":
                cmd.append(config.project_path)
            
            # Add organization
            if config.snyk_org:
                cmd.extend(["--org", config.snyk_org])
            
            # JSON output
            cmd.append("--json")
            
            # Run scan
            result_data = await self._run_command(cmd)
            
            if result_data.stdout:
                scan_data = json.loads(result_data.stdout)
                await self._parse_code_results(scan_data, result)
            
            self.logger.info("Code scan completed")
        
        except Exception as e:
            self.logger.warning(f"Code scan failed: {e}")
    
    async def _scan_container(self, config: SnykScanConfig, result: SnykScanResult):
        """Scan container images for vulnerabilities"""
        try:
            self.logger.info("Starting container security scan")
            
            cmd = [self.snyk_path, "container", "test"]
            
            # Add container image or Dockerfile
            if config.dockerfile_path:
                cmd.extend(["--file", config.dockerfile_path])
            elif config.base_image:
                cmd.append(config.base_image)
            else:
                cmd.append(".")
            
            # Add organization
            if config.snyk_org:
                cmd.extend(["--org", config.snyk_org])
            
            # Exclude base image vulnerabilities
            if config.exclude_base_image_vulns:
                cmd.append("--exclude-base-image-vulns")
            
            # JSON output
            cmd.append("--json")
            
            # Run scan
            result_data = await self._run_command(cmd)
            
            if result_data.stdout:
                scan_data = json.loads(result_data.stdout)
                await self._parse_container_results(scan_data, result)
            
            self.logger.info("Container scan completed")
        
        except Exception as e:
            self.logger.warning(f"Container scan failed: {e}")
    
    async def _scan_iac(self, config: SnykScanConfig, result: SnykScanResult):
        """Scan Infrastructure as Code files"""
        try:
            self.logger.info("Starting IaC security scan")
            
            cmd = [self.snyk_path, "iac", "test"]
            
            # Add project path
            cmd.append(config.project_path)
            
            # Add organization
            if config.snyk_org:
                cmd.extend(["--org", config.snyk_org])
            
            # JSON output
            cmd.append("--json")
            
            # Run scan
            result_data = await self._run_command(cmd)
            
            if result_data.stdout:
                scan_data = json.loads(result_data.stdout)
                await self._parse_iac_results(scan_data, result)
            
            self.logger.info("IaC scan completed")
        
        except Exception as e:
            self.logger.warning(f"IaC scan failed: {e}")
    
    async def _parse_dependency_results(self, scan_data: Dict[str, Any], result: SnykScanResult):
        """Parse dependency scan results"""
        try:
            # Handle multiple project results
            if isinstance(scan_data, list):
                for project_data in scan_data:
                    await self._parse_single_project_results(project_data, result)
            else:
                await self._parse_single_project_results(scan_data, result)
        
        except Exception as e:
            self.logger.error(f"Failed to parse dependency results: {e}")
    
    async def _parse_single_project_results(self, project_data: Dict[str, Any], result: SnykScanResult):
        """Parse results for a single project"""
        try:
            # Extract project information
            result.project_name = project_data.get("projectName")
            result.package_manager = project_data.get("packageManager")
            result.dependency_count = project_data.get("dependencyCount", 0)
            
            # Parse vulnerabilities
            vulnerabilities = project_data.get("vulnerabilities", [])
            for vuln_data in vulnerabilities:
                vulnerability = self._create_vulnerability_from_snyk_data(vuln_data)
                result.add_vulnerability(vulnerability)
            
            # Parse license issues
            license_issues = project_data.get("licenseIssues", [])
            for license_data in license_issues:
                license_issue = self._create_license_issue_from_data(license_data)
                result.license_issues.append(license_issue)
            
            # Update fix statistics
            result.fixable_vulnerabilities = sum(
                1 for v in vulnerabilities if v.get("isFixable", False)
            )
        
        except Exception as e:
            self.logger.error(f"Failed to parse project results: {e}")
    
    async def _parse_code_results(self, scan_data: Dict[str, Any], result: SnykScanResult):
        """Parse code scan results"""
        try:
            runs = scan_data.get("runs", [])
            for run in runs:
                results_list = run.get("results", [])
                for vuln_data in results_list:
                    vulnerability = self._create_code_vulnerability_from_data(vuln_data)
                    result.add_vulnerability(vulnerability)
        
        except Exception as e:
            self.logger.error(f"Failed to parse code results: {e}")
    
    async def _parse_container_results(self, scan_data: Dict[str, Any], result: SnykScanResult):
        """Parse container scan results"""
        try:
            vulnerabilities = scan_data.get("vulnerabilities", [])
            for vuln_data in vulnerabilities:
                vulnerability = self._create_vulnerability_from_snyk_data(vuln_data)
                result.add_vulnerability(vulnerability)
        
        except Exception as e:
            self.logger.error(f"Failed to parse container results: {e}")
    
    async def _parse_iac_results(self, scan_data: Dict[str, Any], result: SnykScanResult):
        """Parse IaC scan results"""
        try:
            infrastructures = scan_data.get("infrastructures", [])
            for infra in infrastructures:
                issues = infra.get("issues", [])
                for issue_data in issues:
                    vulnerability = self._create_iac_vulnerability_from_data(issue_data)
                    result.add_vulnerability(vulnerability)
        
        except Exception as e:
            self.logger.error(f"Failed to parse IaC results: {e}")
    
    def _create_vulnerability_from_snyk_data(self, vuln_data: Dict[str, Any]) -> SecurityVulnerability:
        """Create SecurityVulnerability from Snyk vulnerability data"""
        # Map Snyk severity to our levels
        severity_mapping = {
            "critical": VulnerabilityLevel.CRITICAL,
            "high": VulnerabilityLevel.HIGH,
            "medium": VulnerabilityLevel.MEDIUM,
            "low": VulnerabilityLevel.LOW
        }
        
        severity = severity_mapping.get(
            vuln_data.get("severity", "medium").lower(),
            VulnerabilityLevel.MEDIUM
        )
        
        # Extract package information
        package_name = ""
        package_version = ""
        if "from" in vuln_data and vuln_data["from"]:
            package_info = vuln_data["from"][-1]  # Get the direct dependency
            if "@" in package_info:
                package_name, package_version = package_info.rsplit("@", 1)
            else:
                package_name = package_info
        
        return SecurityVulnerability(
            id=vuln_data.get("id", "SNYK-UNKNOWN"),
            title=vuln_data.get("title", "Unknown Vulnerability"),
            description=vuln_data.get("description", ""),
            severity=severity,
            category="Dependency Vulnerability",
            cwe_id=vuln_data.get("cwe"),
            cvss_score=vuln_data.get("cvssScore"),
            recommendation=vuln_data.get("remediation", {}).get("advice", ""),
            evidence={
                "package_name": package_name,
                "package_version": package_version,
                "is_fixable": vuln_data.get("isFixable", False),
                "fix_version": vuln_data.get("fixedIn", []),
                "exploit_maturity": vuln_data.get("exploitMaturity"),
                "upgrade_path": vuln_data.get("upgradePath", [])
            },
            references=vuln_data.get("references", []),
            scanner=self.name
        )
    
    def _create_code_vulnerability_from_data(self, vuln_data: Dict[str, Any]) -> SecurityVulnerability:
        """Create SecurityVulnerability from Snyk code analysis data"""
        rule_id = vuln_data.get("ruleId", "")
        message = vuln_data.get("message", {})
        
        # Map Snyk code severity
        level = vuln_data.get("level", "note")
        severity_mapping = {
            "error": VulnerabilityLevel.HIGH,
            "warning": VulnerabilityLevel.MEDIUM,
            "note": VulnerabilityLevel.LOW,
            "info": VulnerabilityLevel.INFO
        }
        
        severity = severity_mapping.get(level, VulnerabilityLevel.MEDIUM)
        
        # Extract location information
        locations = vuln_data.get("locations", [])
        file_path = ""
        line_number = 0
        if locations:
            physical_location = locations[0].get("physicalLocation", {})
            artifact_location = physical_location.get("artifactLocation", {})
            file_path = artifact_location.get("uri", "")
            region = physical_location.get("region", {})
            line_number = region.get("startLine", 0)
        
        return SecurityVulnerability(
            id=f"SNYK-CODE-{rule_id}",
            title=message.get("text", "Code Security Issue"),
            description=message.get("markdown", ""),
            severity=severity,
            category="Code Security",
            recommendation="Review and fix the identified code security issue",
            evidence={
                "file_path": file_path,
                "line_number": line_number,
                "rule_id": rule_id,
                "level": level
            },
            scanner=self.name
        )
    
    def _create_iac_vulnerability_from_data(self, issue_data: Dict[str, Any]) -> SecurityVulnerability:
        """Create SecurityVulnerability from Snyk IaC data"""
        severity_mapping = {
            "critical": VulnerabilityLevel.CRITICAL,
            "high": VulnerabilityLevel.HIGH,
            "medium": VulnerabilityLevel.MEDIUM,
            "low": VulnerabilityLevel.LOW
        }
        
        severity = severity_mapping.get(
            issue_data.get("severity", "medium").lower(),
            VulnerabilityLevel.MEDIUM
        )
        
        return SecurityVulnerability(
            id=issue_data.get("id", "SNYK-IAC-UNKNOWN"),
            title=issue_data.get("title", "IaC Security Issue"),
            description=issue_data.get("description", ""),
            severity=severity,
            category="Infrastructure as Code",
            recommendation=issue_data.get("remediation", ""),
            evidence={
                "resource": issue_data.get("resource", ""),
                "path": issue_data.get("path", []),
                "rule": issue_data.get("rule", "")
            },
            scanner=self.name
        )
    
    def _create_license_issue_from_data(self, license_data: Dict[str, Any]) -> SnykLicenseIssue:
        """Create SnykLicenseIssue from license data"""
        return SnykLicenseIssue(
            id=license_data.get("id", ""),
            license=license_data.get("license", ""),
            package_name=license_data.get("packageName", ""),
            package_version=license_data.get("packageVersion", ""),
            severity=license_data.get("severity", "medium"),
            instruction=license_data.get("instruction", ""),
            package_manager=license_data.get("packageManager", "")
        )
    
    async def _generate_reports(self, config: SnykScanConfig, result: SnykScanResult):
        """Generate Snyk scan reports"""
        try:
            output_dir = Path(config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            base_filename = f"snyk_scan_{result.scan_id}"
            
            # Generate JSON report (already have the data)
            if config.json_output:
                json_path = output_dir / f"{base_filename}.json"
                report_data = {
                    "scan_info": {
                        "scan_id": result.scan_id,
                        "scanner": result.scanner_name,
                        "target": result.target,
                        "start_time": result.start_time.isoformat(),
                        "end_time": result.end_time.isoformat() if result.end_time else None,
                        "duration": result.duration
                    },
                    "summary": {
                        "total_vulnerabilities": result.total_vulnerabilities,
                        "critical": result.critical_count,
                        "high": result.high_count,
                        "medium": result.medium_count,
                        "low": result.low_count,
                        "info": result.info_count,
                        "dependency_count": result.dependency_count,
                        "fixable_vulnerabilities": result.fixable_vulnerabilities
                    },
                    "vulnerabilities": [
                        {
                            "id": v.id,
                            "title": v.title,
                            "severity": v.severity.value,
                            "category": v.category,
                            "description": v.description,
                            "recommendation": v.recommendation,
                            "evidence": v.evidence
                        }
                        for v in result.vulnerabilities
                    ],
                    "license_issues": [
                        {
                            "license": li.license,
                            "package": f"{li.package_name}@{li.package_version}",
                            "severity": li.severity,
                            "instruction": li.instruction
                        }
                        for li in result.license_issues
                    ]
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                result.report_files.append(str(json_path))
            
            self.logger.info(f"Snyk reports generated: {len(result.report_files)} files")
        
        except Exception as e:
            self.logger.warning(f"Report generation failed: {e}")
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run Snyk command asynchronously"""
        try:
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )
        
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise


# Example usage
def create_example_snyk_config(project_path: str, snyk_token: str) -> SnykScanConfig:
    """Create example Snyk scan configuration"""
    return SnykScanConfig(
        scan_type=ScanType.DEPENDENCY,
        target=project_path,
        timeout_minutes=30,
        
        # Authentication
        snyk_token=snyk_token,
        
        # Scan configuration
        project_path=project_path,
        test_dependencies=True,
        test_code=True,
        test_container=False,
        test_iac=True,
        
        # Filtering
        severity_threshold="medium",
        include_dev_deps=False,
        
        # Output
        json_output=True,
        sarif_output=True
    )