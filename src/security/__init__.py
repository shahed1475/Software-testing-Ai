"""
Security Integration Module

This module provides integrated security scanning capabilities,
including OWASP ZAP, Snyk, and Trivy integration for comprehensive
security testing within the unified testing framework.
"""

from .security_scanner import (
    SecurityScanner,
    ScanType,
    SecurityScanResult,
    VulnerabilityLevel,
    SecurityVulnerability
)

from .owasp_zap_integration import (
    ZAPScanner,
    ZAPScanConfig,
    ZAPScanResult
)

from .snyk_integration import (
    SnykScanner,
    SnykScanConfig,
    SnykScanResult
)

from .trivy_integration import (
    TrivyScanner,
    TrivyScanConfig,
    TrivyScanResult
)

from .security_orchestrator import (
    SecurityOrchestrator,
    SecurityScanPlan,
    ConsolidatedSecurityResult
)

__all__ = [
    'SecurityScanner',
    'ScanType',
    'SecurityScanResult',
    'VulnerabilityLevel',
    'SecurityVulnerability',
    'ZAPScanner',
    'ZAPScanConfig',
    'ZAPScanResult',
    'SnykScanner',
    'SnykScanConfig',
    'SnykScanResult',
    'TrivyScanner',
    'TrivyScanConfig',
    'TrivyScanResult',
    'SecurityOrchestrator',
    'SecurityScanPlan',
    'ConsolidatedSecurityResult'
]

__version__ = "1.0.0"