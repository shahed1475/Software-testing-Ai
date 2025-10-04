"""
Functional Reporter

Specialized reporting for functional testing results, test execution analysis,
coverage metrics, and test quality insights.
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


class FunctionalReportType(Enum):
    """Functional report types"""
    TEST_EXECUTION = "test_execution"
    COVERAGE_ANALYSIS = "coverage_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    REGRESSION_ANALYSIS = "regression_analysis"
    CROSS_DOMAIN_ANALYSIS = "cross_domain_analysis"
    API_TEST_REPORT = "api_test_report"
    WEB_TEST_REPORT = "web_test_report"
    MOBILE_TEST_REPORT = "mobile_test_report"
    INTEGRATION_TEST_REPORT = "integration_test_report"
    END_TO_END_REPORT = "end_to_end_report"


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


class TestPriority(Enum):
    """Test priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestCategory(Enum):
    """Test categories"""
    FUNCTIONAL = "functional"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    SMOKE = "smoke"
    SANITY = "sanity"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    COMPATIBILITY = "compatibility"


@dataclass
class FunctionalMetrics:
    """Functional testing metrics"""
    
    # Execution metrics
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    blocked_tests: int = 0
    
    # Success rates
    pass_rate: float = 0.0
    fail_rate: float = 0.0
    skip_rate: float = 0.0
    error_rate: float = 0.0
    
    # Coverage metrics
    code_coverage: float = 0.0
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    statement_coverage: float = 0.0
    
    # Domain-specific metrics
    api_coverage: float = 0.0
    web_coverage: float = 0.0
    mobile_coverage: float = 0.0
    
    # Performance metrics
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    fastest_test: float = 0.0
    slowest_test: float = 0.0
    
    # Quality metrics
    test_stability: float = 0.0  # Consistency of results
    test_reliability: float = 0.0  # Absence of flaky tests
    defect_detection_rate: float = 0.0
    
    # Trend data
    execution_trend: List[float] = field(default_factory=list)
    coverage_trend: List[float] = field(default_factory=list)
    quality_trend: List[float] = field(default_factory=list)
    
    # Category breakdown
    category_metrics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    priority_metrics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Cross-domain metrics
    cross_domain_tests: int = 0
    unified_test_flows: int = 0
    integration_points_tested: int = 0


@dataclass
class TestResult:
    """Individual test result details"""
    
    test_id: str
    test_name: str
    test_description: str
    status: TestStatus
    
    # Test classification
    category: TestCategory
    priority: TestPriority
    domain: str  # web, api, mobile
    tags: List[str] = field(default_factory=list)
    
    # Execution details
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Results
    expected_result: str = ""
    actual_result: str = ""
    assertion_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Test data
    test_data: Dict[str, Any] = field(default_factory=dict)
    environment: str = ""
    
    # Coverage information
    lines_covered: List[int] = field(default_factory=list)
    functions_covered: List[str] = field(default_factory=list)
    branches_covered: List[str] = field(default_factory=list)
    
    # Screenshots/artifacts
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # Retry information
    retry_count: int = 0
    max_retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_description": self.test_description,
            "status": self.status.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "domain": self.domain,
            "tags": self.tags,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "assertion_results": self.assertion_results,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "test_data": self.test_data,
            "environment": self.environment,
            "lines_covered": self.lines_covered,
            "functions_covered": self.functions_covered,
            "branches_covered": self.branches_covered,
            "screenshots": self.screenshots,
            "logs": self.logs,
            "artifacts": self.artifacts,
            "dependencies": self.dependencies,
            "prerequisites": self.prerequisites,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


@dataclass
class TestSuite:
    """Test suite information"""
    
    suite_id: str
    suite_name: str
    description: str
    
    # Suite classification
    domain: str
    category: TestCategory
    priority: TestPriority
    
    # Test results
    tests: List[TestResult] = field(default_factory=list)
    
    # Suite metrics
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    
    # Execution details
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Environment
    environment: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "description": self.description,
            "domain": self.domain,
            "category": self.category.value,
            "priority": self.priority.value,
            "tests": [test.to_dict() for test in self.tests],
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "environment": self.environment,
            "configuration": self.configuration
        }


@dataclass
class CoverageDetail:
    """Detailed coverage information"""
    
    file_path: str
    total_lines: int
    covered_lines: int
    uncovered_lines: List[int] = field(default_factory=list)
    
    # Function coverage
    total_functions: int = 0
    covered_functions: int = 0
    uncovered_functions: List[str] = field(default_factory=list)
    
    # Branch coverage
    total_branches: int = 0
    covered_branches: int = 0
    uncovered_branches: List[str] = field(default_factory=list)
    
    # Coverage percentages
    line_coverage_percent: float = 0.0
    function_coverage_percent: float = 0.0
    branch_coverage_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "uncovered_lines": self.uncovered_lines,
            "total_functions": self.total_functions,
            "covered_functions": self.covered_functions,
            "uncovered_functions": self.uncovered_functions,
            "total_branches": self.total_branches,
            "covered_branches": self.covered_branches,
            "uncovered_branches": self.uncovered_branches,
            "line_coverage_percent": self.line_coverage_percent,
            "function_coverage_percent": self.function_coverage_percent,
            "branch_coverage_percent": self.branch_coverage_percent
        }


@dataclass
class FunctionalReport:
    """Comprehensive functional testing report"""
    
    report_id: str
    title: str
    report_type: FunctionalReportType
    generated_at: datetime
    
    # Report metadata
    test_environment: str = ""
    test_configuration: Dict[str, Any] = field(default_factory=dict)
    execution_context: str = ""
    
    # Executive summary
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    
    # Metrics and analysis
    metrics: Optional[FunctionalMetrics] = None
    test_suites: List[TestSuite] = field(default_factory=list)
    failed_tests: List[TestResult] = field(default_factory=list)
    
    # Coverage analysis
    coverage_details: List[CoverageDetail] = field(default_factory=list)
    coverage_summary: Dict[str, float] = field(default_factory=dict)
    
    # Performance analysis
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    slow_tests: List[TestResult] = field(default_factory=list)
    
    # Quality analysis
    flaky_tests: List[TestResult] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    
    # Cross-domain analysis
    cross_domain_results: Dict[str, Any] = field(default_factory=dict)
    integration_results: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Trends and history
    historical_data: Dict[str, Any] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Artifacts
    test_artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "test_environment": self.test_environment,
            "test_configuration": self.test_configuration,
            "execution_context": self.execution_context,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "metrics": self._metrics_to_dict() if self.metrics else None,
            "test_suites": [suite.to_dict() for suite in self.test_suites],
            "failed_tests": [test.to_dict() for test in self.failed_tests],
            "coverage_details": [detail.to_dict() for detail in self.coverage_details],
            "coverage_summary": self.coverage_summary,
            "performance_metrics": self.performance_metrics,
            "slow_tests": [test.to_dict() for test in self.slow_tests],
            "flaky_tests": [test.to_dict() for test in self.flaky_tests],
            "quality_issues": self.quality_issues,
            "cross_domain_results": self.cross_domain_results,
            "integration_results": self.integration_results,
            "recommendations": self.recommendations,
            "historical_data": self.historical_data,
            "trend_analysis": self.trend_analysis,
            "test_artifacts": self.test_artifacts,
            "logs": self.logs,
            "screenshots": self.screenshots
        }
    
    def _metrics_to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        if not self.metrics:
            return {}
        
        return {
            "execution": {
                "total_tests": self.metrics.total_tests,
                "passed_tests": self.metrics.passed_tests,
                "failed_tests": self.metrics.failed_tests,
                "skipped_tests": self.metrics.skipped_tests,
                "error_tests": self.metrics.error_tests,
                "blocked_tests": self.metrics.blocked_tests
            },
            "success_rates": {
                "pass_rate": self.metrics.pass_rate,
                "fail_rate": self.metrics.fail_rate,
                "skip_rate": self.metrics.skip_rate,
                "error_rate": self.metrics.error_rate
            },
            "coverage": {
                "code_coverage": self.metrics.code_coverage,
                "line_coverage": self.metrics.line_coverage,
                "branch_coverage": self.metrics.branch_coverage,
                "function_coverage": self.metrics.function_coverage,
                "statement_coverage": self.metrics.statement_coverage,
                "api_coverage": self.metrics.api_coverage,
                "web_coverage": self.metrics.web_coverage,
                "mobile_coverage": self.metrics.mobile_coverage
            },
            "performance": {
                "average_execution_time": self.metrics.average_execution_time,
                "total_execution_time": self.metrics.total_execution_time,
                "fastest_test": self.metrics.fastest_test,
                "slowest_test": self.metrics.slowest_test
            },
            "quality": {
                "test_stability": self.metrics.test_stability,
                "test_reliability": self.metrics.test_reliability,
                "defect_detection_rate": self.metrics.defect_detection_rate
            },
            "cross_domain": {
                "cross_domain_tests": self.metrics.cross_domain_tests,
                "unified_test_flows": self.metrics.unified_test_flows,
                "integration_points_tested": self.metrics.integration_points_tested
            },
            "trends": {
                "execution_trend": self.metrics.execution_trend,
                "coverage_trend": self.metrics.coverage_trend,
                "quality_trend": self.metrics.quality_trend
            },
            "category_metrics": self.metrics.category_metrics,
            "priority_metrics": self.metrics.priority_metrics
        }


class FunctionalReporter:
    """Functional testing reporter"""
    
    def __init__(self):
        self.name = "Functional Reporter"
        self.version = "1.0.0"
        
        # Report storage
        self.reports: Dict[str, FunctionalReport] = {}
        self.report_history: List[str] = []
        
        # Configuration
        self.output_directory = Path("reports/functional")
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Thresholds
        self.slow_test_threshold = 30.0  # seconds
        self.coverage_threshold = 80.0  # percentage
        self.flaky_test_threshold = 0.8  # success rate
    
    def generate_functional_report(
        self,
        test_results: Any,
        report_type: FunctionalReportType = FunctionalReportType.TEST_EXECUTION,
        test_environment: str = "",
        execution_context: str = ""
    ) -> FunctionalReport:
        """Generate comprehensive functional testing report"""
        
        # Create report
        report = FunctionalReport(
            report_id=str(uuid.uuid4()),
            title=self._generate_report_title(report_type, test_environment),
            report_type=report_type,
            generated_at=datetime.now(),
            test_environment=test_environment,
            execution_context=execution_context
        )
        
        # Extract test configuration
        report.test_configuration = self._extract_test_configuration(test_results)
        
        # Extract metrics
        report.metrics = self._extract_functional_metrics(test_results)
        
        # Extract test suites
        report.test_suites = self._extract_test_suites(test_results)
        
        # Extract failed tests
        report.failed_tests = self._extract_failed_tests(test_results)
        
        # Extract coverage details
        report.coverage_details = self._extract_coverage_details(test_results)
        report.coverage_summary = self._calculate_coverage_summary(report.coverage_details)
        
        # Extract performance metrics
        report.performance_metrics = self._extract_performance_metrics(test_results)
        report.slow_tests = self._identify_slow_tests(test_results)
        
        # Identify quality issues
        report.flaky_tests = self._identify_flaky_tests(test_results)
        report.quality_issues = self._identify_quality_issues(test_results, report.metrics)
        
        # Extract cross-domain results
        report.cross_domain_results = self._extract_cross_domain_results(test_results)
        report.integration_results = self._extract_integration_results(test_results)
        
        # Generate executive summary
        report.executive_summary = self._generate_executive_summary(report.metrics, report.failed_tests)
        
        # Extract key findings
        report.key_findings = self._extract_key_findings(report.metrics, report.failed_tests, report.quality_issues)
        
        # Generate recommendations
        report.recommendations = self._generate_functional_recommendations(report.metrics, report.quality_issues)
        
        # Extract artifacts
        report.test_artifacts = self._extract_test_artifacts(test_results)
        report.logs = self._extract_logs(test_results)
        report.screenshots = self._extract_screenshots(test_results)
        
        # Store report
        self.reports[report.report_id] = report
        self.report_history.append(report.report_id)
        
        return report
    
    def _generate_report_title(self, report_type: FunctionalReportType, test_environment: str) -> str:
        """Generate report title"""
        
        type_titles = {
            FunctionalReportType.TEST_EXECUTION: "Test Execution Report",
            FunctionalReportType.COVERAGE_ANALYSIS: "Coverage Analysis Report",
            FunctionalReportType.PERFORMANCE_ANALYSIS: "Performance Analysis Report",
            FunctionalReportType.REGRESSION_ANALYSIS: "Regression Analysis Report",
            FunctionalReportType.CROSS_DOMAIN_ANALYSIS: "Cross-Domain Analysis Report",
            FunctionalReportType.API_TEST_REPORT: "API Test Report",
            FunctionalReportType.WEB_TEST_REPORT: "Web Test Report",
            FunctionalReportType.MOBILE_TEST_REPORT: "Mobile Test Report",
            FunctionalReportType.INTEGRATION_TEST_REPORT: "Integration Test Report",
            FunctionalReportType.END_TO_END_REPORT: "End-to-End Test Report"
        }
        
        base_title = type_titles.get(report_type, "Functional Test Report")
        
        if test_environment:
            base_title += f" - {test_environment}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{base_title} ({timestamp})"
    
    def _extract_test_configuration(self, test_results: Any) -> Dict[str, Any]:
        """Extract test configuration"""
        
        return {
            "test_framework": getattr(test_results, 'test_framework', 'Unknown'),
            "test_runner": getattr(test_results, 'test_runner', 'Unknown'),
            "parallel_execution": getattr(test_results, 'parallel_execution', False),
            "max_workers": getattr(test_results, 'max_workers', 1),
            "timeout": getattr(test_results, 'timeout', 300),
            "retry_policy": getattr(test_results, 'retry_policy', {}),
            "environment_variables": getattr(test_results, 'environment_variables', {}),
            "browser_config": getattr(test_results, 'browser_config', {}),
            "mobile_config": getattr(test_results, 'mobile_config', {}),
            "api_config": getattr(test_results, 'api_config', {})
        }
    
    def _extract_functional_metrics(self, test_results: Any) -> FunctionalMetrics:
        """Extract functional testing metrics"""
        
        metrics = FunctionalMetrics()
        
        # Get all test results
        all_tests = self._get_all_tests(test_results)
        
        # Basic counts
        metrics.total_tests = len(all_tests)
        
        status_counts = {
            TestStatus.PASSED: 0,
            TestStatus.FAILED: 0,
            TestStatus.SKIPPED: 0,
            TestStatus.ERROR: 0,
            TestStatus.BLOCKED: 0
        }
        
        execution_times = []
        
        for test in all_tests:
            status = self._normalize_test_status(test.get('status', 'unknown'))
            if status in status_counts:
                status_counts[status] += 1
            
            # Collect execution times
            exec_time = test.get('execution_time', 0.0)
            if exec_time > 0:
                execution_times.append(exec_time)
        
        metrics.passed_tests = status_counts[TestStatus.PASSED]
        metrics.failed_tests = status_counts[TestStatus.FAILED]
        metrics.skipped_tests = status_counts[TestStatus.SKIPPED]
        metrics.error_tests = status_counts[TestStatus.ERROR]
        metrics.blocked_tests = status_counts[TestStatus.BLOCKED]
        
        # Calculate rates
        if metrics.total_tests > 0:
            metrics.pass_rate = metrics.passed_tests / metrics.total_tests
            metrics.fail_rate = metrics.failed_tests / metrics.total_tests
            metrics.skip_rate = metrics.skipped_tests / metrics.total_tests
            metrics.error_rate = metrics.error_tests / metrics.total_tests
        
        # Performance metrics
        if execution_times:
            metrics.average_execution_time = sum(execution_times) / len(execution_times)
            metrics.total_execution_time = sum(execution_times)
            metrics.fastest_test = min(execution_times)
            metrics.slowest_test = max(execution_times)
        
        # Coverage metrics
        metrics.code_coverage = getattr(test_results, 'code_coverage', 0.0)
        metrics.line_coverage = getattr(test_results, 'line_coverage', 0.0)
        metrics.branch_coverage = getattr(test_results, 'branch_coverage', 0.0)
        metrics.function_coverage = getattr(test_results, 'function_coverage', 0.0)
        metrics.statement_coverage = getattr(test_results, 'statement_coverage', 0.0)
        
        # Domain-specific coverage
        metrics.api_coverage = getattr(test_results, 'api_coverage', 0.0)
        metrics.web_coverage = getattr(test_results, 'web_coverage', 0.0)
        metrics.mobile_coverage = getattr(test_results, 'mobile_coverage', 0.0)
        
        # Quality metrics
        metrics.test_stability = self._calculate_test_stability(all_tests)
        metrics.test_reliability = self._calculate_test_reliability(all_tests)
        metrics.defect_detection_rate = self._calculate_defect_detection_rate(all_tests)
        
        # Cross-domain metrics
        metrics.cross_domain_tests = len([t for t in all_tests if t.get('is_cross_domain', False)])
        metrics.unified_test_flows = len([t for t in all_tests if t.get('is_unified_flow', False)])
        metrics.integration_points_tested = getattr(test_results, 'integration_points_tested', 0)
        
        # Category and priority breakdown
        metrics.category_metrics = self._calculate_category_metrics(all_tests)
        metrics.priority_metrics = self._calculate_priority_metrics(all_tests)
        
        return metrics
    
    def _get_all_tests(self, test_results: Any) -> List[Dict[str, Any]]:
        """Extract all test results"""
        
        all_tests = []
        
        # Check for different result structures
        if hasattr(test_results, 'test_results'):
            all_tests.extend(test_results.test_results)
        
        if hasattr(test_results, 'all_tests'):
            all_tests.extend(test_results.all_tests)
        
        if hasattr(test_results, 'suites'):
            for suite in test_results.suites:
                if hasattr(suite, 'tests'):
                    all_tests.extend(suite.tests)
        
        # If test_results is a list itself
        if isinstance(test_results, list):
            all_tests.extend(test_results)
        
        return all_tests
    
    def _normalize_test_status(self, status: str) -> TestStatus:
        """Normalize test status"""
        
        status = str(status).lower()
        
        if status in ['passed', 'pass', 'success', 'ok']:
            return TestStatus.PASSED
        elif status in ['failed', 'fail', 'failure']:
            return TestStatus.FAILED
        elif status in ['skipped', 'skip', 'ignored']:
            return TestStatus.SKIPPED
        elif status in ['error', 'exception']:
            return TestStatus.ERROR
        elif status in ['blocked', 'block']:
            return TestStatus.BLOCKED
        else:
            return TestStatus.NOT_RUN
    
    def _calculate_test_stability(self, all_tests: List[Dict[str, Any]]) -> float:
        """Calculate test stability (consistency of results)"""
        
        # This would require historical data
        # For now, return a placeholder based on retry counts
        
        total_retries = sum(test.get('retry_count', 0) for test in all_tests)
        total_tests = len(all_tests)
        
        if total_tests == 0:
            return 1.0
        
        # Higher stability means fewer retries needed
        stability = max(0.0, 1.0 - (total_retries / total_tests / 3.0))  # Normalize to 0-1
        return stability
    
    def _calculate_test_reliability(self, all_tests: List[Dict[str, Any]]) -> float:
        """Calculate test reliability (absence of flaky tests)"""
        
        # Count tests that required retries (potential flaky tests)
        flaky_tests = len([t for t in all_tests if t.get('retry_count', 0) > 0])
        total_tests = len(all_tests)
        
        if total_tests == 0:
            return 1.0
        
        reliability = 1.0 - (flaky_tests / total_tests)
        return reliability
    
    def _calculate_defect_detection_rate(self, all_tests: List[Dict[str, Any]]) -> float:
        """Calculate defect detection rate"""
        
        # This would require defect tracking integration
        # For now, use failed tests as a proxy
        
        failed_tests = len([t for t in all_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.FAILED])
        total_tests = len(all_tests)
        
        if total_tests == 0:
            return 0.0
        
        return failed_tests / total_tests
    
    def _calculate_category_metrics(self, all_tests: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Calculate metrics by test category"""
        
        category_metrics = {}
        
        for test in all_tests:
            category = test.get('category', 'unknown')
            status = self._normalize_test_status(test.get('status', 'unknown')).value
            
            if category not in category_metrics:
                category_metrics[category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'error': 0,
                    'blocked': 0
                }
            
            category_metrics[category]['total'] += 1
            category_metrics[category][status] = category_metrics[category].get(status, 0) + 1
        
        return category_metrics
    
    def _calculate_priority_metrics(self, all_tests: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Calculate metrics by test priority"""
        
        priority_metrics = {}
        
        for test in all_tests:
            priority = test.get('priority', 'unknown')
            status = self._normalize_test_status(test.get('status', 'unknown')).value
            
            if priority not in priority_metrics:
                priority_metrics[priority] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'error': 0,
                    'blocked': 0
                }
            
            priority_metrics[priority]['total'] += 1
            priority_metrics[priority][status] = priority_metrics[priority].get(status, 0) + 1
        
        return priority_metrics
    
    def _extract_test_suites(self, test_results: Any) -> List[TestSuite]:
        """Extract test suite information"""
        
        suites = []
        
        if hasattr(test_results, 'suites'):
            for suite_data in test_results.suites:
                suite = TestSuite(
                    suite_id=suite_data.get('suite_id', str(uuid.uuid4())),
                    suite_name=suite_data.get('suite_name', 'Unknown Suite'),
                    description=suite_data.get('description', ''),
                    domain=suite_data.get('domain', 'unknown'),
                    category=self._normalize_test_category(suite_data.get('category', 'functional')),
                    priority=self._normalize_test_priority(suite_data.get('priority', 'medium')),
                    environment=suite_data.get('environment', ''),
                    configuration=suite_data.get('configuration', {})
                )
                
                # Extract tests
                if 'tests' in suite_data:
                    for test_data in suite_data['tests']:
                        test = self._create_test_result(test_data)
                        suite.tests.append(test)
                
                # Calculate suite metrics
                suite.total_tests = len(suite.tests)
                suite.passed_tests = len([t for t in suite.tests if t.status == TestStatus.PASSED])
                suite.failed_tests = len([t for t in suite.tests if t.status == TestStatus.FAILED])
                suite.skipped_tests = len([t for t in suite.tests if t.status == TestStatus.SKIPPED])
                
                # Calculate execution time
                suite.execution_time = sum(t.execution_time for t in suite.tests)
                
                # Set start/end times
                if suite.tests:
                    start_times = [t.start_time for t in suite.tests if t.start_time]
                    end_times = [t.end_time for t in suite.tests if t.end_time]
                    
                    if start_times:
                        suite.start_time = min(start_times)
                    if end_times:
                        suite.end_time = max(end_times)
                
                suites.append(suite)
        
        return suites
    
    def _normalize_test_category(self, category: str) -> TestCategory:
        """Normalize test category"""
        
        category = str(category).lower()
        
        category_map = {
            'functional': TestCategory.FUNCTIONAL,
            'integration': TestCategory.INTEGRATION,
            'regression': TestCategory.REGRESSION,
            'smoke': TestCategory.SMOKE,
            'sanity': TestCategory.SANITY,
            'acceptance': TestCategory.ACCEPTANCE,
            'performance': TestCategory.PERFORMANCE,
            'security': TestCategory.SECURITY,
            'usability': TestCategory.USABILITY,
            'compatibility': TestCategory.COMPATIBILITY
        }
        
        return category_map.get(category, TestCategory.FUNCTIONAL)
    
    def _normalize_test_priority(self, priority: str) -> TestPriority:
        """Normalize test priority"""
        
        priority = str(priority).lower()
        
        priority_map = {
            'critical': TestPriority.CRITICAL,
            'high': TestPriority.HIGH,
            'medium': TestPriority.MEDIUM,
            'low': TestPriority.LOW
        }
        
        return priority_map.get(priority, TestPriority.MEDIUM)
    
    def _create_test_result(self, test_data: Dict[str, Any]) -> TestResult:
        """Create TestResult from test data"""
        
        test = TestResult(
            test_id=test_data.get('test_id', str(uuid.uuid4())),
            test_name=test_data.get('test_name', test_data.get('name', 'Unknown Test')),
            test_description=test_data.get('test_description', test_data.get('description', '')),
            status=self._normalize_test_status(test_data.get('status', 'not_run')),
            category=self._normalize_test_category(test_data.get('category', 'functional')),
            priority=self._normalize_test_priority(test_data.get('priority', 'medium')),
            domain=test_data.get('domain', 'unknown'),
            tags=test_data.get('tags', []),
            execution_time=test_data.get('execution_time', 0.0),
            expected_result=test_data.get('expected_result', ''),
            actual_result=test_data.get('actual_result', ''),
            assertion_results=test_data.get('assertion_results', []),
            error_message=test_data.get('error_message'),
            error_type=test_data.get('error_type'),
            stack_trace=test_data.get('stack_trace'),
            test_data=test_data.get('test_data', {}),
            environment=test_data.get('environment', ''),
            lines_covered=test_data.get('lines_covered', []),
            functions_covered=test_data.get('functions_covered', []),
            branches_covered=test_data.get('branches_covered', []),
            screenshots=test_data.get('screenshots', []),
            logs=test_data.get('logs', []),
            artifacts=test_data.get('artifacts', []),
            dependencies=test_data.get('dependencies', []),
            prerequisites=test_data.get('prerequisites', []),
            retry_count=test_data.get('retry_count', 0),
            max_retries=test_data.get('max_retries', 0)
        )
        
        # Parse timestamps
        if 'start_time' in test_data:
            try:
                test.start_time = datetime.fromisoformat(test_data['start_time'])
            except (ValueError, TypeError):
                pass
        
        if 'end_time' in test_data:
            try:
                test.end_time = datetime.fromisoformat(test_data['end_time'])
            except (ValueError, TypeError):
                pass
        
        return test
    
    def _extract_failed_tests(self, test_results: Any) -> List[TestResult]:
        """Extract failed test details"""
        
        failed_tests = []
        all_tests = self._get_all_tests(test_results)
        
        for test_data in all_tests:
            status = self._normalize_test_status(test_data.get('status', ''))
            if status in [TestStatus.FAILED, TestStatus.ERROR]:
                test = self._create_test_result(test_data)
                failed_tests.append(test)
        
        return failed_tests
    
    def _extract_coverage_details(self, test_results: Any) -> List[CoverageDetail]:
        """Extract detailed coverage information"""
        
        coverage_details = []
        
        if hasattr(test_results, 'coverage_data'):
            coverage_data = test_results.coverage_data
            
            if isinstance(coverage_data, dict):
                for file_path, file_coverage in coverage_data.items():
                    detail = CoverageDetail(
                        file_path=file_path,
                        total_lines=file_coverage.get('total_lines', 0),
                        covered_lines=file_coverage.get('covered_lines', 0),
                        uncovered_lines=file_coverage.get('uncovered_lines', []),
                        total_functions=file_coverage.get('total_functions', 0),
                        covered_functions=file_coverage.get('covered_functions', 0),
                        uncovered_functions=file_coverage.get('uncovered_functions', []),
                        total_branches=file_coverage.get('total_branches', 0),
                        covered_branches=file_coverage.get('covered_branches', 0),
                        uncovered_branches=file_coverage.get('uncovered_branches', [])
                    )
                    
                    # Calculate percentages
                    if detail.total_lines > 0:
                        detail.line_coverage_percent = detail.covered_lines / detail.total_lines * 100
                    
                    if detail.total_functions > 0:
                        detail.function_coverage_percent = detail.covered_functions / detail.total_functions * 100
                    
                    if detail.total_branches > 0:
                        detail.branch_coverage_percent = detail.covered_branches / detail.total_branches * 100
                    
                    coverage_details.append(detail)
        
        return coverage_details
    
    def _calculate_coverage_summary(self, coverage_details: List[CoverageDetail]) -> Dict[str, float]:
        """Calculate overall coverage summary"""
        
        if not coverage_details:
            return {}
        
        total_lines = sum(detail.total_lines for detail in coverage_details)
        covered_lines = sum(detail.covered_lines for detail in coverage_details)
        
        total_functions = sum(detail.total_functions for detail in coverage_details)
        covered_functions = sum(detail.covered_functions for detail in coverage_details)
        
        total_branches = sum(detail.total_branches for detail in coverage_details)
        covered_branches = sum(detail.covered_branches for detail in coverage_details)
        
        summary = {}
        
        if total_lines > 0:
            summary['line_coverage'] = covered_lines / total_lines * 100
        
        if total_functions > 0:
            summary['function_coverage'] = covered_functions / total_functions * 100
        
        if total_branches > 0:
            summary['branch_coverage'] = covered_branches / total_branches * 100
        
        # Overall coverage (weighted average)
        if total_lines > 0 and total_functions > 0:
            summary['overall_coverage'] = (
                summary.get('line_coverage', 0) * 0.5 +
                summary.get('function_coverage', 0) * 0.3 +
                summary.get('branch_coverage', 0) * 0.2
            )
        
        return summary
    
    def _extract_performance_metrics(self, test_results: Any) -> Dict[str, Any]:
        """Extract performance metrics"""
        
        all_tests = self._get_all_tests(test_results)
        execution_times = [t.get('execution_time', 0.0) for t in all_tests if t.get('execution_time', 0.0) > 0]
        
        if not execution_times:
            return {}
        
        return {
            'total_execution_time': sum(execution_times),
            'average_execution_time': sum(execution_times) / len(execution_times),
            'median_execution_time': sorted(execution_times)[len(execution_times) // 2],
            'fastest_test': min(execution_times),
            'slowest_test': max(execution_times),
            'tests_over_threshold': len([t for t in execution_times if t > self.slow_test_threshold]),
            'performance_distribution': {
                'fast_tests': len([t for t in execution_times if t < 5.0]),
                'medium_tests': len([t for t in execution_times if 5.0 <= t < 30.0]),
                'slow_tests': len([t for t in execution_times if t >= 30.0])
            }
        }
    
    def _identify_slow_tests(self, test_results: Any) -> List[TestResult]:
        """Identify slow-running tests"""
        
        slow_tests = []
        all_tests = self._get_all_tests(test_results)
        
        for test_data in all_tests:
            execution_time = test_data.get('execution_time', 0.0)
            if execution_time > self.slow_test_threshold:
                test = self._create_test_result(test_data)
                slow_tests.append(test)
        
        # Sort by execution time (slowest first)
        slow_tests.sort(key=lambda t: t.execution_time, reverse=True)
        
        return slow_tests
    
    def _identify_flaky_tests(self, test_results: Any) -> List[TestResult]:
        """Identify potentially flaky tests"""
        
        flaky_tests = []
        all_tests = self._get_all_tests(test_results)
        
        for test_data in all_tests:
            retry_count = test_data.get('retry_count', 0)
            max_retries = test_data.get('max_retries', 0)
            
            # Consider a test flaky if it required retries
            if retry_count > 0 or max_retries > 0:
                test = self._create_test_result(test_data)
                flaky_tests.append(test)
        
        return flaky_tests
    
    def _identify_quality_issues(self, test_results: Any, metrics: FunctionalMetrics) -> List[str]:
        """Identify test quality issues"""
        
        issues = []
        
        # Low pass rate
        if metrics.pass_rate < 0.8:
            issues.append(f"Low pass rate: {metrics.pass_rate:.1%} (target: 80%+)")
        
        # High error rate
        if metrics.error_rate > 0.05:
            issues.append(f"High error rate: {metrics.error_rate:.1%} (target: <5%)")
        
        # Low coverage
        if metrics.code_coverage < self.coverage_threshold / 100:
            issues.append(f"Low code coverage: {metrics.code_coverage:.1%} (target: {self.coverage_threshold}%+)")
        
        # Slow tests
        all_tests = self._get_all_tests(test_results)
        slow_tests = len([t for t in all_tests if t.get('execution_time', 0.0) > self.slow_test_threshold])
        if slow_tests > 0:
            issues.append(f"{slow_tests} slow tests (>{self.slow_test_threshold}s)")
        
        # Flaky tests
        flaky_tests = len([t for t in all_tests if t.get('retry_count', 0) > 0])
        if flaky_tests > 0:
            issues.append(f"{flaky_tests} potentially flaky tests")
        
        # Missing test data
        tests_without_data = len([t for t in all_tests if not t.get('test_data')])
        if tests_without_data > metrics.total_tests * 0.2:  # More than 20%
            issues.append(f"{tests_without_data} tests missing test data")
        
        # Missing assertions
        tests_without_assertions = len([t for t in all_tests if not t.get('assertion_results')])
        if tests_without_assertions > 0:
            issues.append(f"{tests_without_assertions} tests without assertion results")
        
        return issues
    
    def _extract_cross_domain_results(self, test_results: Any) -> Dict[str, Any]:
        """Extract cross-domain test results"""
        
        all_tests = self._get_all_tests(test_results)
        cross_domain_tests = [t for t in all_tests if t.get('is_cross_domain', False)]
        
        if not cross_domain_tests:
            return {}
        
        # Analyze cross-domain test results
        domains_tested = set()
        integration_points = set()
        
        for test in cross_domain_tests:
            domains = test.get('domains_involved', [])
            domains_tested.update(domains)
            
            integrations = test.get('integration_points', [])
            integration_points.update(integrations)
        
        return {
            'total_cross_domain_tests': len(cross_domain_tests),
            'passed_cross_domain_tests': len([t for t in cross_domain_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.PASSED]),
            'failed_cross_domain_tests': len([t for t in cross_domain_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.FAILED]),
            'domains_tested': list(domains_tested),
            'integration_points_tested': list(integration_points),
            'cross_domain_pass_rate': len([t for t in cross_domain_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.PASSED]) / len(cross_domain_tests) if cross_domain_tests else 0.0
        }
    
    def _extract_integration_results(self, test_results: Any) -> Dict[str, Any]:
        """Extract integration test results"""
        
        all_tests = self._get_all_tests(test_results)
        integration_tests = [t for t in all_tests if t.get('category', '').lower() == 'integration']
        
        if not integration_tests:
            return {}
        
        return {
            'total_integration_tests': len(integration_tests),
            'passed_integration_tests': len([t for t in integration_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.PASSED]),
            'failed_integration_tests': len([t for t in integration_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.FAILED]),
            'integration_pass_rate': len([t for t in integration_tests if self._normalize_test_status(t.get('status', '')) == TestStatus.PASSED]) / len(integration_tests) if integration_tests else 0.0,
            'average_integration_time': sum(t.get('execution_time', 0.0) for t in integration_tests) / len(integration_tests) if integration_tests else 0.0
        }
    
    def _generate_executive_summary(self, metrics: FunctionalMetrics, failed_tests: List[TestResult]) -> str:
        """Generate executive summary"""
        
        summary_parts = []
        
        # Overall results
        summary_parts.append(f"Test Execution Summary:")
        summary_parts.append(f"- Total Tests: {metrics.total_tests}")
        summary_parts.append(f"- Passed: {metrics.passed_tests} ({metrics.pass_rate:.1%})")
        summary_parts.append(f"- Failed: {metrics.failed_tests} ({metrics.fail_rate:.1%})")
        summary_parts.append(f"- Skipped: {metrics.skipped_tests} ({metrics.skip_rate:.1%})")
        
        if metrics.error_tests > 0:
            summary_parts.append(f"- Errors: {metrics.error_tests} ({metrics.error_rate:.1%})")
        
        # Coverage summary
        summary_parts.append(f"\nCoverage Summary:")
        summary_parts.append(f"- Code Coverage: {metrics.code_coverage:.1%}")
        summary_parts.append(f"- Line Coverage: {metrics.line_coverage:.1%}")
        summary_parts.append(f"- Branch Coverage: {metrics.branch_coverage:.1%}")
        
        # Performance summary
        summary_parts.append(f"\nPerformance Summary:")
        summary_parts.append(f"- Total Execution Time: {metrics.total_execution_time:.1f}s")
        summary_parts.append(f"- Average Test Time: {metrics.average_execution_time:.1f}s")
        
        # Quality indicators
        summary_parts.append(f"\nQuality Indicators:")
        summary_parts.append(f"- Test Stability: {metrics.test_stability:.1%}")
        summary_parts.append(f"- Test Reliability: {metrics.test_reliability:.1%}")
        
        # Cross-domain testing
        if metrics.cross_domain_tests > 0:
            summary_parts.append(f"\nCross-Domain Testing:")
            summary_parts.append(f"- Cross-Domain Tests: {metrics.cross_domain_tests}")
            summary_parts.append(f"- Unified Test Flows: {metrics.unified_test_flows}")
            summary_parts.append(f"- Integration Points: {metrics.integration_points_tested}")
        
        # Key concerns
        if metrics.fail_rate > 0.1:
            summary_parts.append(f"\n⚠️  HIGH FAILURE RATE: {metrics.fail_rate:.1%} of tests failed")
        
        if metrics.code_coverage < 0.8:
            summary_parts.append(f"\n⚠️  LOW COVERAGE: {metrics.code_coverage:.1%} code coverage")
        
        if failed_tests:
            critical_failures = len([t for t in failed_tests if t.priority == TestPriority.CRITICAL])
            if critical_failures > 0:
                summary_parts.append(f"\n🚨 CRITICAL: {critical_failures} critical test failures")
        
        return "\n".join(summary_parts)
    
    def _extract_key_findings(
        self,
        metrics: FunctionalMetrics,
        failed_tests: List[TestResult],
        quality_issues: List[str]
    ) -> List[str]:
        """Extract key findings"""
        
        findings = []
        
        # Test execution findings
        if metrics.pass_rate >= 0.95:
            findings.append(f"Excellent test pass rate: {metrics.pass_rate:.1%}")
        elif metrics.pass_rate < 0.8:
            findings.append(f"Low test pass rate requires attention: {metrics.pass_rate:.1%}")
        
        # Coverage findings
        if metrics.code_coverage >= 0.9:
            findings.append(f"Excellent code coverage: {metrics.code_coverage:.1%}")
        elif metrics.code_coverage < 0.7:
            findings.append(f"Code coverage below recommended threshold: {metrics.code_coverage:.1%}")
        
        # Performance findings
        if metrics.average_execution_time > 30:
            findings.append(f"Tests are running slowly (avg: {metrics.average_execution_time:.1f}s)")
        
        # Critical test failures
        critical_failures = [t for t in failed_tests if t.priority == TestPriority.CRITICAL]
        if critical_failures:
            findings.append(f"{len(critical_failures)} critical tests failed - immediate attention required")
        
        # Cross-domain findings
        if metrics.cross_domain_tests > 0:
            cross_domain_pass_rate = 1.0 - (len([t for t in failed_tests if 'cross_domain' in t.tags]) / metrics.cross_domain_tests)
            findings.append(f"Cross-domain testing: {metrics.cross_domain_tests} tests with {cross_domain_pass_rate:.1%} pass rate")
        
        # Quality issues
        if quality_issues:
            findings.append(f"{len(quality_issues)} quality issues identified")
        
        # Domain-specific findings
        if metrics.api_coverage > 0:
            findings.append(f"API test coverage: {metrics.api_coverage:.1%}")
        
        if metrics.web_coverage > 0:
            findings.append(f"Web test coverage: {metrics.web_coverage:.1%}")
        
        if metrics.mobile_coverage > 0:
            findings.append(f"Mobile test coverage: {metrics.mobile_coverage:.1%}")
        
        return findings
    
    def _generate_functional_recommendations(
        self,
        metrics: FunctionalMetrics,
        quality_issues: List[str]
    ) -> List[str]:
        """Generate functional testing recommendations"""
        
        recommendations = []
        
        # Pass rate recommendations
        if metrics.pass_rate < 0.8:
            recommendations.append("Investigate and fix failing tests to improve pass rate")
            recommendations.append("Review test design and implementation quality")
        
        # Coverage recommendations
        if metrics.code_coverage < 0.8:
            recommendations.append("Increase test coverage by adding tests for uncovered code paths")
            recommendations.append("Focus on critical business logic and edge cases")
        
        # Performance recommendations
        if metrics.average_execution_time > 30:
            recommendations.append("Optimize slow-running tests to improve execution time")
            recommendations.append("Consider parallel test execution to reduce overall runtime")
        
        # Quality recommendations
        if metrics.test_reliability < 0.9:
            recommendations.append("Identify and fix flaky tests to improve reliability")
            recommendations.append("Implement better test isolation and cleanup")
        
        # Cross-domain recommendations
        if metrics.cross_domain_tests == 0:
            recommendations.append("Implement cross-domain testing to validate end-to-end workflows")
            recommendations.append("Add unified test flows covering web, API, and mobile interactions")
        
        # Specific quality issue recommendations
        for issue in quality_issues:
            if "slow tests" in issue:
                recommendations.append("Profile and optimize slow tests")
            elif "flaky tests" in issue:
                recommendations.append("Stabilize flaky tests with better synchronization")
            elif "missing test data" in issue:
                recommendations.append("Implement comprehensive test data management")
            elif "missing assertion" in issue:
                recommendations.append("Add proper assertions to all tests")
        
        # General recommendations
        recommendations.append("Implement continuous test monitoring and reporting")
        recommendations.append("Establish test quality gates and metrics tracking")
        recommendations.append("Regular test suite maintenance and refactoring")
        
        return recommendations
    
    def _extract_test_artifacts(self, test_results: Any) -> List[str]:
        """Extract test artifacts"""
        
        artifacts = []
        
        if hasattr(test_results, 'artifacts'):
            artifacts.extend(test_results.artifacts)
        
        # Extract from individual tests
        all_tests = self._get_all_tests(test_results)
        for test in all_tests:
            test_artifacts = test.get('artifacts', [])
            artifacts.extend(test_artifacts)
        
        return list(set(artifacts))  # Remove duplicates
    
    def _extract_logs(self, test_results: Any) -> List[str]:
        """Extract test logs"""
        
        logs = []
        
        if hasattr(test_results, 'logs'):
            logs.extend(test_results.logs)
        
        # Extract from individual tests
        all_tests = self._get_all_tests(test_results)
        for test in all_tests:
            test_logs = test.get('logs', [])
            logs.extend(test_logs)
        
        return list(set(logs))  # Remove duplicates
    
    def _extract_screenshots(self, test_results: Any) -> List[str]:
        """Extract test screenshots"""
        
        screenshots = []
        
        if hasattr(test_results, 'screenshots'):
            screenshots.extend(test_results.screenshots)
        
        # Extract from individual tests
        all_tests = self._get_all_tests(test_results)
        for test in all_tests:
            test_screenshots = test.get('screenshots', [])
            screenshots.extend(test_screenshots)
        
        return list(set(screenshots))  # Remove duplicates
    
    def export_functional_report(
        self,
        report: FunctionalReport,
        format: str = "html",
        output_path: Optional[Path] = None
    ) -> Path:
        """Export functional report"""
        
        output_path = output_path or self.output_directory
        
        # Generate filename
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"functional_report_{timestamp}.{format}"
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
        
        logger.info(f"Functional report exported to: {full_path}")
        return full_path
    
    def _export_json(self, report: FunctionalReport, path: Path):
        """Export as JSON"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _export_html(self, report: FunctionalReport, path: Path):
        """Export as HTML"""
        
        html_content = self._generate_html_functional_report(report)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_pdf(self, report: FunctionalReport, path: Path):
        """Export as PDF (placeholder)"""
        
        # This would require a PDF generation library
        # For now, export as HTML
        html_path = path.with_suffix('.html')
        self._export_html(report, html_path)
        logger.warning(f"PDF export not implemented, exported as HTML: {html_path}")
    
    def _generate_html_functional_report(self, report: FunctionalReport) -> str:
        """Generate HTML functional report"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .passed {{ color: #4caf50; }}
                .failed {{ color: #f44336; }}
                .skipped {{ color: #ff9800; }}
                .error {{ color: #9c27b0; }}
                .test-suite {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .test-result {{ margin: 5px 0; padding: 8px; border-radius: 3px; }}
                .test-result.passed {{ background-color: #e8f5e8; }}
                .test-result.failed {{ background-color: #fde8e8; }}
                .test-result.skipped {{ background-color: #fff3e0; }}
                .test-result.error {{ background-color: #f3e5f5; }}
                .coverage-bar {{ width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }}
                .coverage-fill {{ height: 100%; background-color: #4caf50; }}
                .recommendations {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; }}
                .quality-issues {{ background-color: #fff3e0; padding: 15px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Environment:</strong> {report.test_environment}</p>
                <p><strong>Report Type:</strong> {report.report_type.value}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <pre>{report.executive_summary}</pre>
            </div>
        """
        
        # Add metrics section
        if report.metrics:
            html += f"""
            <div class="section">
                <h2>Test Execution Metrics</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3 class="passed">{report.metrics.passed_tests}</h3>
                        <p>Passed ({report.metrics.pass_rate:.1%})</p>
                    </div>
                    <div class="metric">
                        <h3 class="failed">{report.metrics.failed_tests}</h3>
                        <p>Failed ({report.metrics.fail_rate:.1%})</p>
                    </div>
                    <div class="metric">
                        <h3 class="skipped">{report.metrics.skipped_tests}</h3>
                        <p>Skipped ({report.metrics.skip_rate:.1%})</p>
                    </div>
                    <div class="metric">
                        <h3>{report.metrics.total_tests}</h3>
                        <p>Total Tests</p>
                    </div>
                </div>
                
                <h3>Coverage Summary</h3>
                <div style="margin: 20px 0;">
                    <p>Code Coverage: {report.metrics.code_coverage:.1%}</p>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {report.metrics.code_coverage * 100}%;"></div>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <p>Line Coverage: {report.metrics.line_coverage:.1%}</p>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {report.metrics.line_coverage * 100}%;"></div>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <p>Branch Coverage: {report.metrics.branch_coverage:.1%}</p>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {report.metrics.branch_coverage * 100}%;"></div>
                    </div>
                </div>
            </div>
            """
        
        # Add key findings
        if report.key_findings:
            html += f"""
            <div class="section">
                <h2>Key Findings</h2>
                <ul>
                    {''.join(f'<li>{finding}</li>' for finding in report.key_findings)}
                </ul>
            </div>
            """
        
        # Add failed tests
        if report.failed_tests:
            html += f"""
            <div class="section">
                <h2>Failed Tests ({len(report.failed_tests)})</h2>
                <table>
                    <tr>
                        <th>Test Name</th>
                        <th>Domain</th>
                        <th>Priority</th>
                        <th>Error Message</th>
                        <th>Execution Time</th>
                    </tr>
            """
            
            for test in report.failed_tests[:20]:  # Limit to first 20
                html += f"""
                    <tr>
                        <td>{test.test_name}</td>
                        <td>{test.domain}</td>
                        <td>{test.priority.value}</td>
                        <td>{test.error_message or 'N/A'}</td>
                        <td>{test.execution_time:.2f}s</td>
                    </tr>
                """
            
            html += "</table></div>"
        
        # Add quality issues
        if report.quality_issues:
            html += f"""
            <div class="section">
                <h2>Quality Issues</h2>
                <div class="quality-issues">
                    <ul>
                        {''.join(f'<li>{issue}</li>' for issue in report.quality_issues)}
                    </ul>
                </div>
            </div>
            """
        
        # Add recommendations
        if report.recommendations:
            html += f"""
            <div class="section">
                <h2>Recommendations</h2>
                <div class="recommendations">
                    <ul>
                        {''.join(f'<li>{rec}</li>' for rec in report.recommendations)}
                    </ul>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


# Utility functions for generating specific functional reports

def generate_test_execution_report(test_results: Any, environment: str = "") -> FunctionalReport:
    """Generate a test execution report"""
    
    reporter = FunctionalReporter()
    return reporter.generate_functional_report(
        test_results=test_results,
        report_type=FunctionalReportType.TEST_EXECUTION,
        test_environment=environment,
        execution_context="Test Execution Analysis"
    )


def generate_coverage_analysis_report(test_results: Any, environment: str = "") -> FunctionalReport:
    """Generate a coverage analysis report"""
    
    reporter = FunctionalReporter()
    return reporter.generate_functional_report(
        test_results=test_results,
        report_type=FunctionalReportType.COVERAGE_ANALYSIS,
        test_environment=environment,
        execution_context="Coverage Analysis"
    )


def generate_cross_domain_report(test_results: Any, environment: str = "") -> FunctionalReport:
    """Generate a cross-domain analysis report"""
    
    reporter = FunctionalReporter()
    return reporter.generate_functional_report(
        test_results=test_results,
        report_type=FunctionalReportType.CROSS_DOMAIN_ANALYSIS,
        test_environment=environment,
        execution_context="Cross-Domain Testing Analysis"
    )


def generate_performance_analysis_report(test_results: Any, environment: str = "") -> FunctionalReport:
    """Generate a performance analysis report"""
    
    reporter = FunctionalReporter()
    return reporter.generate_functional_report(
        test_results=test_results,
        report_type=FunctionalReportType.PERFORMANCE_ANALYSIS,
        test_environment=environment,
        execution_context="Performance Analysis"
    )