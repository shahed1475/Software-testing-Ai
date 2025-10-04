"""
Trivy Integration

Integrates Trivy for comprehensive vulnerability scanning of containers,
filesystems, Git repositories, and Kubernetes clusters within the unified testing framework.
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
class TrivyScanConfig(ScanConfiguration):
    """Configuration for Trivy scans"""
    
    # Scan target types
    scan_target_type: str = "image"  # image, fs, repo, k8s, vm, sbom
    
    # Vulnerability scanning
    vuln_type: List[str] = field(default_factory=lambda: ["os", "library"])
    security_checks: List[str] = field(default_factory=lambda: ["vuln", "secret", "config"])
    
    # Severity filtering
    severity: List[str] = field(default_factory=lambda: ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
    ignore_unfixed: bool = False
    
    # Container/Image scanning
    image_name: Optional[str] = None
    dockerfile_path: Optional[str] = None
    
    # Filesystem scanning
    filesystem_path: str = "."
    
    # Repository scanning
    repo_url: Optional[str] = None
    
    # Kubernetes scanning
    k8s_namespace: Optional[str] = None
    k8s_cluster_context: Optional[str] = None
    
    # Database and cache
    cache_dir: Optional[str] = None
    skip_db_update: bool = False
    offline_scan: bool = False
    
    # Output configuration
    format: str = "json"  # json, table, sarif, cyclonedx, spdx
    template: Optional[str] = None
    
    # Ignore policies
    ignorefile: Optional[str] = None
    ignore_policy: Optional[str] = None
    
    # Secret scanning
    secret_config: Optional[str] = None
    
    # Misconfiguration scanning
    config_policy: Optional[str] = None
    config_data: Optional[str] = None
    
    # License scanning
    license_full: bool = False
    
    # Advanced options
    timeout: int = 300
    parallel: int = 5
    quiet: bool = False
    debug: bool = False


@dataclass
class TrivyVulnerability:
    """Trivy-specific vulnerability information"""
    
    vulnerability_id: str
    pkg_name: str
    pkg_version: str
    pkg_type: str
    severity: str
    title: str
    description: str
    
    # Fix information
    fixed_version: Optional[str] = None
    
    # References and metadata
    references: List[str] = field(default_factory=list)
    cvss: Optional[Dict[str, Any]] = None
    cwe_ids: List[str] = field(default_factory=list)
    
    # Package path information
    pkg_path: Optional[str] = None
    pkg_identifier: Optional[Dict[str, Any]] = None
    
    # Layer information (for container images)
    layer: Optional[Dict[str, Any]] = None


@dataclass
class TrivySecret:
    """Trivy secret detection result"""
    
    rule_id: str
    category: str
    severity: str
    title: str
    start_line: int
    end_line: int
    code: Dict[str, Any]
    match: str
    
    # File information
    filepath: str
    
    # Additional metadata
    layer: Optional[Dict[str, Any]] = None


@dataclass
class TrivyMisconfiguration:
    """Trivy misconfiguration detection result"""
    
    type: str
    id: str
    avd_id: str
    title: str
    description: str
    message: str
    severity: str
    
    # Resolution information
    resolution: str
    
    # References
    primary_url: str
    
    # Status
    status: str  # PASS, FAIL, etc.
    
    # Location information
    filepath: str
    start_line: int
    end_line: int
    
    # Optional fields with defaults
    references: List[str] = field(default_factory=list)


@dataclass
class TrivyScanResult(SecurityScanResult):
    """Extended scan result for Trivy-specific data"""
    
    # Trivy-specific results
    secrets: List[TrivySecret] = field(default_factory=list)
    misconfigurations: List[TrivyMisconfiguration] = field(default_factory=list)
    
    # Scan metadata
    artifact_name: Optional[str] = None
    artifact_type: Optional[str] = None
    schema_version: Optional[int] = None
    
    # Results by target
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrivyScanner(SecurityScanner):
    """Trivy security scanner implementation"""
    
    def __init__(self, trivy_path: Optional[str] = None):
        super().__init__("Trivy", "0.45.0")
        self.trivy_path = trivy_path or "trivy"
        self._check_trivy_installation()
    
    def _check_trivy_installation(self):
        """Check if Trivy is installed and accessible"""
        try:
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse version from output
                version_line = result.stdout.split('\n')[0]
                if 'Version:' in version_line:
                    self.version = version_line.split('Version:')[1].strip()
                self.logger.info(f"Trivy found: {self.version}")
            else:
                self.logger.warning("Trivy not found or not accessible")
        except Exception as e:
            self.logger.warning(f"Failed to check Trivy installation: {e}")
    
    def is_available(self) -> bool:
        """Check if Trivy is available"""
        try:
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def get_supported_scan_types(self) -> List[ScanType]:
        """Trivy supports multiple scan types"""
        return [
            ScanType.CONTAINER,
            ScanType.DEPENDENCY,
            ScanType.INFRASTRUCTURE,
            ScanType.SECRET_DETECTION,
            ScanType.MISCONFIGURATION
        ]
    
    async def scan(self, config: TrivyScanConfig) -> TrivyScanResult:
        """Perform comprehensive Trivy security scan"""
        self.validate_config(config)
        
        result = TrivyScanResult(
            scan_id=self.create_scan_result(config).scan_id,
            scan_type=config.scan_type,
            scanner_name=self.name,
            target=config.target or self._get_scan_target(config),
            start_time=datetime.now(),
            scan_config=config.scan_options
        )
        
        try:
            result.status = ScanStatus.RUNNING
            
            # Update database if not skipped
            if not config.skip_db_update and not config.offline_scan:
                await self._update_database(config)
            
            # Perform scan based on target type
            if config.scan_target_type == "image":
                await self._scan_image(config, result)
            elif config.scan_target_type == "fs":
                await self._scan_filesystem(config, result)
            elif config.scan_target_type == "repo":
                await self._scan_repository(config, result)
            elif config.scan_target_type == "k8s":
                await self._scan_kubernetes(config, result)
            else:
                raise ValueError(f"Unsupported scan target type: {config.scan_target_type}")
            
            # Generate reports
            await self._generate_reports(config, result)
            
            result.status = ScanStatus.COMPLETED
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            self.logger.info(f"Trivy scan completed: {result.total_vulnerabilities} vulnerabilities found")
        
        except Exception as e:
            self.logger.error(f"Trivy scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def _get_scan_target(self, config: TrivyScanConfig) -> str:
        """Get the scan target based on configuration"""
        if config.scan_target_type == "image" and config.image_name:
            return config.image_name
        elif config.scan_target_type == "fs":
            return config.filesystem_path
        elif config.scan_target_type == "repo" and config.repo_url:
            return config.repo_url
        elif config.scan_target_type == "k8s":
            return f"k8s-cluster:{config.k8s_cluster_context or 'default'}"
        else:
            return config.target or "."
    
    async def _update_database(self, config: TrivyScanConfig):
        """Update Trivy vulnerability database"""
        try:
            self.logger.info("Updating Trivy database")
            
            cmd = [self.trivy_path, "image", "--download-db-only"]
            
            if config.cache_dir:
                cmd.extend(["--cache-dir", config.cache_dir])
            
            await self._run_command(cmd, timeout=300)
            self.logger.info("Database update completed")
        
        except Exception as e:
            self.logger.warning(f"Database update failed: {e}")
    
    async def _scan_image(self, config: TrivyScanConfig, result: TrivyScanResult):
        """Scan container image for vulnerabilities"""
        try:
            self.logger.info(f"Scanning container image: {config.image_name}")
            
            cmd = [self.trivy_path, "image"]
            
            # Add common options
            self._add_common_options(cmd, config)
            
            # Add image name
            cmd.append(config.image_name or config.target)
            
            # Run scan
            scan_result = await self._run_command(cmd)
            
            if scan_result.stdout:
                await self._parse_scan_results(scan_result.stdout, result)
            
            self.logger.info("Image scan completed")
        
        except Exception as e:
            self.logger.error(f"Image scan failed: {e}")
            raise
    
    async def _scan_filesystem(self, config: TrivyScanConfig, result: TrivyScanResult):
        """Scan filesystem for vulnerabilities"""
        try:
            self.logger.info(f"Scanning filesystem: {config.filesystem_path}")
            
            cmd = [self.trivy_path, "fs"]
            
            # Add common options
            self._add_common_options(cmd, config)
            
            # Add filesystem path
            cmd.append(config.filesystem_path)
            
            # Run scan
            scan_result = await self._run_command(cmd)
            
            if scan_result.stdout:
                await self._parse_scan_results(scan_result.stdout, result)
            
            self.logger.info("Filesystem scan completed")
        
        except Exception as e:
            self.logger.error(f"Filesystem scan failed: {e}")
            raise
    
    async def _scan_repository(self, config: TrivyScanConfig, result: TrivyScanResult):
        """Scan Git repository for vulnerabilities"""
        try:
            self.logger.info(f"Scanning repository: {config.repo_url}")
            
            cmd = [self.trivy_path, "repo"]
            
            # Add common options
            self._add_common_options(cmd, config)
            
            # Add repository URL
            cmd.append(config.repo_url or config.target)
            
            # Run scan
            scan_result = await self._run_command(cmd)
            
            if scan_result.stdout:
                await self._parse_scan_results(scan_result.stdout, result)
            
            self.logger.info("Repository scan completed")
        
        except Exception as e:
            self.logger.error(f"Repository scan failed: {e}")
            raise
    
    async def _scan_kubernetes(self, config: TrivyScanConfig, result: TrivyScanResult):
        """Scan Kubernetes cluster for misconfigurations"""
        try:
            self.logger.info("Scanning Kubernetes cluster")
            
            cmd = [self.trivy_path, "k8s"]
            
            # Add common options
            self._add_common_options(cmd, config)
            
            # Add namespace if specified
            if config.k8s_namespace:
                cmd.extend(["--namespace", config.k8s_namespace])
            
            # Add cluster context if specified
            if config.k8s_cluster_context:
                cmd.extend(["--context", config.k8s_cluster_context])
            
            # Scan all resources by default
            cmd.append("all")
            
            # Run scan
            scan_result = await self._run_command(cmd)
            
            if scan_result.stdout:
                await self._parse_scan_results(scan_result.stdout, result)
            
            self.logger.info("Kubernetes scan completed")
        
        except Exception as e:
            self.logger.error(f"Kubernetes scan failed: {e}")
            raise
    
    def _add_common_options(self, cmd: List[str], config: TrivyScanConfig):
        """Add common Trivy command options"""
        # Output format
        cmd.extend(["--format", config.format])
        
        # Security checks
        if config.security_checks:
            cmd.extend(["--security-checks", ",".join(config.security_checks)])
        
        # Vulnerability types
        if config.vuln_type:
            cmd.extend(["--vuln-type", ",".join(config.vuln_type)])
        
        # Severity filtering
        if config.severity:
            cmd.extend(["--severity", ",".join(config.severity)])
        
        # Ignore unfixed vulnerabilities
        if config.ignore_unfixed:
            cmd.append("--ignore-unfixed")
        
        # Cache directory
        if config.cache_dir:
            cmd.extend(["--cache-dir", config.cache_dir])
        
        # Offline scan
        if config.offline_scan:
            cmd.append("--offline-scan")
        
        # Ignore file
        if config.ignorefile:
            cmd.extend(["--ignorefile", config.ignorefile])
        
        # Timeout
        cmd.extend(["--timeout", f"{config.timeout}s"])
        
        # Quiet mode
        if config.quiet:
            cmd.append("--quiet")
        
        # Debug mode
        if config.debug:
            cmd.append("--debug")
    
    async def _parse_scan_results(self, scan_output: str, result: TrivyScanResult):
        """Parse Trivy scan results from JSON output"""
        try:
            if not scan_output.strip():
                self.logger.warning("Empty scan output received")
                return
            
            scan_data = json.loads(scan_output)
            
            # Extract metadata
            result.artifact_name = scan_data.get("ArtifactName")
            result.artifact_type = scan_data.get("ArtifactType")
            result.schema_version = scan_data.get("SchemaVersion")
            result.metadata = scan_data.get("Metadata", {})
            
            # Parse results
            results = scan_data.get("Results", [])
            result.results = results
            
            for target_result in results:
                await self._parse_target_result(target_result, result)
            
            self.logger.info(f"Parsed {len(result.vulnerabilities)} vulnerabilities")
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON output: {e}")
            # Try to extract any useful information from non-JSON output
            self.logger.debug(f"Raw output: {scan_output[:500]}...")
        except Exception as e:
            self.logger.error(f"Failed to parse scan results: {e}")
    
    async def _parse_target_result(self, target_result: Dict[str, Any], result: TrivyScanResult):
        """Parse results for a single target"""
        try:
            target = target_result.get("Target", "")
            target_type = target_result.get("Type", "")
            
            # Parse vulnerabilities
            vulnerabilities = target_result.get("Vulnerabilities", [])
            for vuln_data in vulnerabilities:
                vulnerability = self._create_vulnerability_from_trivy_data(vuln_data, target)
                result.add_vulnerability(vulnerability)
            
            # Parse secrets
            secrets = target_result.get("Secrets", [])
            for secret_data in secrets:
                secret = self._create_secret_from_trivy_data(secret_data, target)
                result.secrets.append(secret)
            
            # Parse misconfigurations
            misconfigs = target_result.get("Misconfigurations", [])
            for misconfig_data in misconfigs:
                misconfig = self._create_misconfiguration_from_trivy_data(misconfig_data, target)
                result.misconfigurations.append(misconfig)
        
        except Exception as e:
            self.logger.error(f"Failed to parse target result: {e}")
    
    def _create_vulnerability_from_trivy_data(self, vuln_data: Dict[str, Any], target: str) -> SecurityVulnerability:
        """Create SecurityVulnerability from Trivy vulnerability data"""
        # Map Trivy severity to our levels
        severity_mapping = {
            "CRITICAL": VulnerabilityLevel.CRITICAL,
            "HIGH": VulnerabilityLevel.HIGH,
            "MEDIUM": VulnerabilityLevel.MEDIUM,
            "LOW": VulnerabilityLevel.LOW,
            "UNKNOWN": VulnerabilityLevel.INFO
        }
        
        severity = severity_mapping.get(
            vuln_data.get("Severity", "UNKNOWN"),
            VulnerabilityLevel.MEDIUM
        )
        
        # Extract CVSS score
        cvss_score = None
        cvss_data = vuln_data.get("CVSS", {})
        if cvss_data:
            # Try to get CVSS v3 score first, then v2
            for version in ["nvd", "redhat", "ubuntu"]:
                if version in cvss_data and "V3Score" in cvss_data[version]:
                    cvss_score = cvss_data[version]["V3Score"]
                    break
                elif version in cvss_data and "V2Score" in cvss_data[version]:
                    cvss_score = cvss_data[version]["V2Score"]
                    break
        
        return SecurityVulnerability(
            id=vuln_data.get("VulnerabilityID", "TRIVY-UNKNOWN"),
            title=vuln_data.get("Title", "Unknown Vulnerability"),
            description=vuln_data.get("Description", ""),
            severity=severity,
            category="Package Vulnerability",
            cwe_id=vuln_data.get("CweIDs", [None])[0] if vuln_data.get("CweIDs") else None,
            cvss_score=cvss_score,
            recommendation=f"Upgrade to version {vuln_data.get('FixedVersion', 'latest')}" if vuln_data.get("FixedVersion") else "No fix available",
            evidence={
                "package_name": vuln_data.get("PkgName", ""),
                "package_version": vuln_data.get("InstalledVersion", ""),
                "package_type": vuln_data.get("PkgType", ""),
                "fixed_version": vuln_data.get("FixedVersion"),
                "target": target,
                "layer": vuln_data.get("Layer", {}),
                "pkg_path": vuln_data.get("PkgPath", ""),
                "data_source": vuln_data.get("DataSource", {})
            },
            references=vuln_data.get("References", []),
            scanner=self.name
        )
    
    def _create_secret_from_trivy_data(self, secret_data: Dict[str, Any], target: str) -> TrivySecret:
        """Create TrivySecret from Trivy secret data"""
        return TrivySecret(
            rule_id=secret_data.get("RuleID", ""),
            category=secret_data.get("Category", ""),
            severity=secret_data.get("Severity", ""),
            title=secret_data.get("Title", ""),
            start_line=secret_data.get("StartLine", 0),
            end_line=secret_data.get("EndLine", 0),
            code=secret_data.get("Code", {}),
            match=secret_data.get("Match", ""),
            filepath=target,
            layer=secret_data.get("Layer", {})
        )
    
    def _create_misconfiguration_from_trivy_data(self, misconfig_data: Dict[str, Any], target: str) -> TrivyMisconfiguration:
        """Create TrivyMisconfiguration from Trivy misconfiguration data"""
        return TrivyMisconfiguration(
            type=misconfig_data.get("Type", ""),
            id=misconfig_data.get("ID", ""),
            avd_id=misconfig_data.get("AVDID", ""),
            title=misconfig_data.get("Title", ""),
            description=misconfig_data.get("Description", ""),
            message=misconfig_data.get("Message", ""),
            severity=misconfig_data.get("Severity", ""),
            resolution=misconfig_data.get("Resolution", ""),
            primary_url=misconfig_data.get("PrimaryURL", ""),
            references=misconfig_data.get("References", []),
            status=misconfig_data.get("Status", ""),
            filepath=target,
            start_line=misconfig_data.get("CauseMetadata", {}).get("StartLine", 0),
            end_line=misconfig_data.get("CauseMetadata", {}).get("EndLine", 0)
        )
    
    async def _generate_reports(self, config: TrivyScanConfig, result: TrivyScanResult):
        """Generate Trivy scan reports"""
        try:
            output_dir = Path(config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            base_filename = f"trivy_scan_{result.scan_id}"
            
            # Generate comprehensive JSON report
            json_path = output_dir / f"{base_filename}.json"
            report_data = {
                "scan_info": {
                    "scan_id": result.scan_id,
                    "scanner": result.scanner_name,
                    "target": result.target,
                    "artifact_name": result.artifact_name,
                    "artifact_type": result.artifact_type,
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
                    "secrets_found": len(result.secrets),
                    "misconfigurations_found": len(result.misconfigurations)
                },
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "severity": v.severity.value,
                        "category": v.category,
                        "description": v.description,
                        "recommendation": v.recommendation,
                        "evidence": v.evidence,
                        "cvss_score": v.cvss_score
                    }
                    for v in result.vulnerabilities
                ],
                "secrets": [
                    {
                        "rule_id": s.rule_id,
                        "category": s.category,
                        "severity": s.severity,
                        "title": s.title,
                        "filepath": s.filepath,
                        "start_line": s.start_line,
                        "end_line": s.end_line,
                        "match": s.match
                    }
                    for s in result.secrets
                ],
                "misconfigurations": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "severity": m.severity,
                        "description": m.description,
                        "message": m.message,
                        "resolution": m.resolution,
                        "filepath": m.filepath,
                        "status": m.status
                    }
                    for m in result.misconfigurations
                ],
                "metadata": result.metadata
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            result.report_files.append(str(json_path))
            
            self.logger.info(f"Trivy reports generated: {len(result.report_files)} files")
        
        except Exception as e:
            self.logger.warning(f"Report generation failed: {e}")
    
    async def _run_command(self, cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run Trivy command asynchronously"""
        try:
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
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
def create_example_trivy_config(target: str, scan_type: str = "image") -> TrivyScanConfig:
    """Create example Trivy scan configuration"""
    return TrivyScanConfig(
        scan_type=ScanType.CONTAINER,
        target=target,
        timeout_minutes=30,
        
        # Scan configuration
        scan_target_type=scan_type,
        image_name=target if scan_type == "image" else None,
        filesystem_path=target if scan_type == "fs" else ".",
        
        # Security checks
        security_checks=["vuln", "secret", "config"],
        vuln_type=["os", "library"],
        
        # Severity filtering
        severity=["MEDIUM", "HIGH", "CRITICAL"],
        ignore_unfixed=False,
        
        # Output
        format="json",
        
        # Performance
        timeout=300,
        parallel=5
    )