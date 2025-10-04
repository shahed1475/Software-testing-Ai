"""
Base Security Scanner Framework

Provides common interfaces and data structures for all security scanning tools,
enabling unified security testing across different scanners and vulnerability types.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

logger = logging.getLogger(__name__)


class ScanType(Enum):
    """Types of security scans"""
    WEB_APPLICATION = "web_application"
    API = "api"
    CONTAINER = "container"
    DEPENDENCY = "dependency"
    INFRASTRUCTURE = "infrastructure"
    SOURCE_CODE = "source_code"
    NETWORK = "network"


class VulnerabilityLevel(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanStatus(Enum):
    """Security scan status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability"""
    id: str
    title: str
    description: str
    severity: VulnerabilityLevel
    category: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    
    # Location information
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    url: Optional[str] = None
    parameter: Optional[str] = None
    
    # Remediation
    recommendation: Optional[str] = None
    remediation_effort: Optional[str] = None
    
    # Evidence
    evidence: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    
    # Metadata
    scanner: Optional[str] = None
    scan_id: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityScanResult:
    """Results from a security scan"""
    scan_id: str
    scan_type: ScanType
    scanner_name: str
    target: str
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Status
    status: ScanStatus = ScanStatus.PENDING
    error_message: Optional[str] = None
    
    # Results
    vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    
    # Scan configuration
    scan_config: Dict[str, Any] = field(default_factory=dict)
    
    # Raw results
    raw_output: Optional[str] = None
    report_files: List[str] = field(default_factory=list)
    
    def add_vulnerability(self, vulnerability: SecurityVulnerability):
        """Add a vulnerability to the scan results"""
        vulnerability.scan_id = self.scan_id
        self.vulnerabilities.append(vulnerability)
        self._update_counts()
    
    def _update_counts(self):
        """Update vulnerability counts"""
        self.total_vulnerabilities = len(self.vulnerabilities)
        self.critical_count = sum(1 for v in self.vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL)
        self.high_count = sum(1 for v in self.vulnerabilities if v.severity == VulnerabilityLevel.HIGH)
        self.medium_count = sum(1 for v in self.vulnerabilities if v.severity == VulnerabilityLevel.MEDIUM)
        self.low_count = sum(1 for v in self.vulnerabilities if v.severity == VulnerabilityLevel.LOW)
        self.info_count = sum(1 for v in self.vulnerabilities if v.severity == VulnerabilityLevel.INFO)
    
    def get_vulnerabilities_by_severity(self, severity: VulnerabilityLevel) -> List[SecurityVulnerability]:
        """Get vulnerabilities filtered by severity"""
        return [v for v in self.vulnerabilities if v.severity == severity]
    
    def get_risk_score(self) -> float:
        """Calculate overall risk score"""
        weights = {
            VulnerabilityLevel.CRITICAL: 10.0,
            VulnerabilityLevel.HIGH: 7.0,
            VulnerabilityLevel.MEDIUM: 4.0,
            VulnerabilityLevel.LOW: 1.0,
            VulnerabilityLevel.INFO: 0.1
        }
        
        total_score = sum(weights[v.severity] for v in self.vulnerabilities)
        return min(total_score, 100.0)  # Cap at 100


@dataclass
class ScanConfiguration:
    """Base configuration for security scans"""
    scan_type: ScanType
    target: str
    timeout_minutes: int = 30
    output_format: str = "json"
    output_directory: str = "security_reports"
    
    # Authentication
    auth_config: Optional[Dict[str, Any]] = None
    
    # Scan options
    scan_options: Dict[str, Any] = field(default_factory=dict)
    
    # Exclusions
    exclude_paths: List[str] = field(default_factory=list)
    exclude_vulnerabilities: List[str] = field(default_factory=list)


class SecurityScanner(ABC):
    """Abstract base class for security scanners"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def scan(self, config: ScanConfiguration) -> SecurityScanResult:
        """Perform security scan"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is available and properly configured"""
        pass
    
    @abstractmethod
    def get_supported_scan_types(self) -> List[ScanType]:
        """Get list of supported scan types"""
        pass
    
    def validate_config(self, config: ScanConfiguration) -> bool:
        """Validate scan configuration"""
        if config.scan_type not in self.get_supported_scan_types():
            raise ValueError(f"Scan type {config.scan_type} not supported by {self.name}")
        
        if not config.target:
            raise ValueError("Target is required for security scan")
        
        return True
    
    def create_scan_result(self, config: ScanConfiguration) -> SecurityScanResult:
        """Create initial scan result object"""
        return SecurityScanResult(
            scan_id=str(uuid.uuid4()),
            scan_type=config.scan_type,
            scanner_name=self.name,
            target=config.target,
            start_time=datetime.now(),
            scan_config=config.scan_options
        )
    
    def parse_vulnerability_severity(self, severity_str: str) -> VulnerabilityLevel:
        """Parse vulnerability severity from string"""
        severity_mapping = {
            "critical": VulnerabilityLevel.CRITICAL,
            "high": VulnerabilityLevel.HIGH,
            "medium": VulnerabilityLevel.MEDIUM,
            "low": VulnerabilityLevel.LOW,
            "info": VulnerabilityLevel.INFO,
            "informational": VulnerabilityLevel.INFO
        }
        
        return severity_mapping.get(severity_str.lower(), VulnerabilityLevel.MEDIUM)
    
    async def save_report(self, result: SecurityScanResult, output_path: str):
        """Save scan report to file"""
        report_data = {
            "scan_id": result.scan_id,
            "scanner": result.scanner_name,
            "scan_type": result.scan_type.value,
            "target": result.target,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration": result.duration,
            "status": result.status.value,
            "summary": {
                "total_vulnerabilities": result.total_vulnerabilities,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "info": result.info_count,
                "risk_score": result.get_risk_score()
            },
            "vulnerabilities": [
                {
                    "id": v.id,
                    "title": v.title,
                    "description": v.description,
                    "severity": v.severity.value,
                    "category": v.category,
                    "cwe_id": v.cwe_id,
                    "cvss_score": v.cvss_score,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "url": v.url,
                    "parameter": v.parameter,
                    "recommendation": v.recommendation,
                    "evidence": v.evidence,
                    "references": v.references
                }
                for v in result.vulnerabilities
            ]
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"Security report saved to: {output_path}")


class MockSecurityScanner(SecurityScanner):
    """Mock security scanner for testing purposes"""
    
    def __init__(self):
        super().__init__("MockScanner", "1.0.0")
    
    async def scan(self, config: ScanConfiguration) -> SecurityScanResult:
        """Perform mock security scan"""
        self.validate_config(config)
        result = self.create_scan_result(config)
        
        # Simulate scan duration
        await asyncio.sleep(2)
        
        # Add mock vulnerabilities
        vulnerabilities = [
            SecurityVulnerability(
                id="MOCK-001",
                title="SQL Injection Vulnerability",
                description="Potential SQL injection in user input field",
                severity=VulnerabilityLevel.HIGH,
                category="Injection",
                cwe_id="CWE-89",
                cvss_score=8.1,
                url=f"{config.target}/login",
                parameter="username",
                recommendation="Use parameterized queries",
                scanner=self.name
            ),
            SecurityVulnerability(
                id="MOCK-002",
                title="Cross-Site Scripting (XSS)",
                description="Reflected XSS vulnerability in search parameter",
                severity=VulnerabilityLevel.MEDIUM,
                category="XSS",
                cwe_id="CWE-79",
                cvss_score=6.1,
                url=f"{config.target}/search",
                parameter="q",
                recommendation="Implement proper input validation and output encoding",
                scanner=self.name
            )
        ]
        
        for vuln in vulnerabilities:
            result.add_vulnerability(vuln)
        
        result.status = ScanStatus.COMPLETED
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def is_available(self) -> bool:
        """Mock scanner is always available"""
        return True
    
    def get_supported_scan_types(self) -> List[ScanType]:
        """Mock scanner supports all scan types"""
        return list(ScanType)


# Utility functions
def create_vulnerability_from_dict(data: Dict[str, Any]) -> SecurityVulnerability:
    """Create SecurityVulnerability from dictionary data"""
    return SecurityVulnerability(
        id=data.get("id", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        severity=VulnerabilityLevel(data.get("severity", "medium")),
        category=data.get("category", ""),
        cwe_id=data.get("cwe_id"),
        cvss_score=data.get("cvss_score"),
        file_path=data.get("file_path"),
        line_number=data.get("line_number"),
        url=data.get("url"),
        parameter=data.get("parameter"),
        recommendation=data.get("recommendation"),
        evidence=data.get("evidence", {}),
        references=data.get("references", [])
    )


def filter_vulnerabilities_by_severity(
    vulnerabilities: List[SecurityVulnerability],
    min_severity: VulnerabilityLevel
) -> List[SecurityVulnerability]:
    """Filter vulnerabilities by minimum severity level"""
    severity_order = {
        VulnerabilityLevel.INFO: 0,
        VulnerabilityLevel.LOW: 1,
        VulnerabilityLevel.MEDIUM: 2,
        VulnerabilityLevel.HIGH: 3,
        VulnerabilityLevel.CRITICAL: 4
    }
    
    min_level = severity_order[min_severity]
    return [v for v in vulnerabilities if severity_order[v.severity] >= min_level]


def merge_scan_results(results: List[SecurityScanResult]) -> SecurityScanResult:
    """Merge multiple scan results into a single result"""
    if not results:
        raise ValueError("No scan results to merge")
    
    # Use first result as base
    merged = results[0]
    merged.scan_id = str(uuid.uuid4())
    merged.scanner_name = "MergedScanners"
    
    # Merge vulnerabilities from all results
    all_vulnerabilities = []
    for result in results:
        all_vulnerabilities.extend(result.vulnerabilities)
    
    # Remove duplicates based on title and target
    unique_vulnerabilities = []
    seen = set()
    
    for vuln in all_vulnerabilities:
        key = (vuln.title, vuln.url or vuln.file_path or "")
        if key not in seen:
            seen.add(key)
            unique_vulnerabilities.append(vuln)
    
    merged.vulnerabilities = unique_vulnerabilities
    merged._update_counts()
    
    return merged