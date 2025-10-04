"""
Unified Testing & Security Integration Module

This module provides unified cross-domain testing capabilities,
integrating Web, API, and Mobile testing in single test flows,
along with security scanning and compliance checks.
"""

from .cross_domain_testing import (
    CrossDomainTestRunner,
    TestDomain,
    UnifiedTestCase,
    TestFlow,
    DomainContext
)

from .test_orchestrator import (
    UnifiedTestOrchestrator,
    TestExecutionPlan,
    TestResult,
    ExecutionContext
)

__all__ = [
    'CrossDomainTestRunner',
    'TestDomain',
    'UnifiedTestCase', 
    'TestFlow',
    'DomainContext',
    'UnifiedTestOrchestrator',
    'TestExecutionPlan',
    'TestResult',
    'ExecutionContext'
]

__version__ = "1.0.0"