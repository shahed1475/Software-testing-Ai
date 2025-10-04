"""
Unified Test Orchestrator

Coordinates and manages the execution of unified cross-domain tests,
handling scheduling, parallel execution, and result aggregation.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set
import uuid

from .cross_domain_testing import (
    CrossDomainTestRunner, TestFlow, UnifiedTestCase, 
    TestDomain, TestStatus, DomainContext
)

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Test execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"


class TestPriority(Enum):
    """Test priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExecutionContext:
    """Context for test execution"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_parallel_tests: int = 3
    timeout_minutes: int = 60
    environment: str = "test"
    tags: Set[str] = field(default_factory=set)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Results tracking
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0


@dataclass
class TestExecutionPlan:
    """Plan for executing a set of tests"""
    name: str
    description: str
    test_flows: List[TestFlow] = field(default_factory=list)
    test_cases: List[UnifiedTestCase] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    parallel_groups: List[List[str]] = field(default_factory=list)
    
    # Configuration
    domain_configs: Dict[TestDomain, Dict[str, Any]] = field(default_factory=dict)
    retry_failed_tests: bool = True
    max_retries: int = 2
    continue_on_failure: bool = True
    
    def add_test_flow(self, test_flow: TestFlow):
        """Add a test flow to the execution plan"""
        self.test_flows.append(test_flow)
    
    def add_test_case(self, test_case: UnifiedTestCase):
        """Add a standalone test case to the execution plan"""
        self.test_cases.append(test_case)
    
    def add_dependency(self, test_name: str, dependencies: List[str]):
        """Add dependencies for a test"""
        self.dependencies[test_name] = dependencies
    
    def create_parallel_group(self, test_names: List[str]):
        """Create a group of tests that can run in parallel"""
        self.parallel_groups.append(test_names)


@dataclass
class TestResult:
    """Comprehensive test result"""
    test_name: str
    test_type: str  # "flow" or "case"
    status: TestStatus
    start_time: datetime
    end_time: datetime
    execution_time: float
    
    # Detailed results
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    domain_results: Dict[TestDomain, Dict[str, Any]] = field(default_factory=dict)
    
    # Error information
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Artifacts
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    reports: List[str] = field(default_factory=list)
    
    # Metrics
    assertions_passed: int = 0
    assertions_failed: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class TestScheduler:
    """Schedules test execution based on dependencies and priorities"""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        self.test_priorities: Dict[str, TestPriority] = {}
    
    def build_dependency_graph(self, plan: TestExecutionPlan):
        """Build dependency graph from execution plan"""
        self.dependency_graph.clear()
        self.reverse_dependencies.clear()
        
        # Get all test names
        all_tests = set()
        for flow in plan.test_flows:
            all_tests.add(flow.name)
        for case in plan.test_cases:
            all_tests.add(case.name)
        
        # Build dependency relationships
        for test_name, deps in plan.dependencies.items():
            if test_name in all_tests:
                self.dependency_graph[test_name] = set(deps)
                for dep in deps:
                    if dep not in self.reverse_dependencies:
                        self.reverse_dependencies[dep] = set()
                    self.reverse_dependencies[dep].add(test_name)
        
        # Initialize tests with no dependencies
        for test_name in all_tests:
            if test_name not in self.dependency_graph:
                self.dependency_graph[test_name] = set()
    
    def get_execution_order(self, plan: TestExecutionPlan) -> List[List[str]]:
        """Get execution order respecting dependencies"""
        self.build_dependency_graph(plan)
        
        execution_batches = []
        remaining_tests = set(self.dependency_graph.keys())
        completed_tests = set()
        
        while remaining_tests:
            # Find tests with no pending dependencies
            ready_tests = []
            for test_name in remaining_tests:
                deps = self.dependency_graph[test_name]
                if deps.issubset(completed_tests):
                    ready_tests.append(test_name)
            
            if not ready_tests:
                # Circular dependency or missing dependency
                logger.warning(f"Circular dependency detected. Remaining tests: {remaining_tests}")
                ready_tests = list(remaining_tests)  # Force execution
            
            # Sort by priority
            ready_tests.sort(key=lambda x: self._get_priority_value(x))
            execution_batches.append(ready_tests)
            
            # Update tracking sets
            for test_name in ready_tests:
                remaining_tests.remove(test_name)
                completed_tests.add(test_name)
        
        return execution_batches
    
    def _get_priority_value(self, test_name: str) -> int:
        """Get numeric priority value for sorting"""
        priority = self.test_priorities.get(test_name, TestPriority.MEDIUM)
        priority_values = {
            TestPriority.CRITICAL: 0,
            TestPriority.HIGH: 1,
            TestPriority.MEDIUM: 2,
            TestPriority.LOW: 3
        }
        return priority_values[priority]


class ResultAggregator:
    """Aggregates and analyzes test results"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.execution_context: Optional[ExecutionContext] = None
    
    def add_result(self, result: TestResult):
        """Add a test result"""
        self.results.append(result)
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        if not self.results:
            return {"message": "No test results available"}
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        error = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        # Domain breakdown
        domain_stats = {}
        for result in self.results:
            for domain, domain_result in result.domain_results.items():
                if domain not in domain_stats:
                    domain_stats[domain] = {"tests": 0, "passed": 0, "failed": 0}
                domain_stats[domain]["tests"] += 1
                if domain_result.get("status") == "passed":
                    domain_stats[domain]["passed"] += 1
                else:
                    domain_stats[domain]["failed"] += 1
        
        return {
            "execution_summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "error": error,
                "skipped": skipped,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time,
                "average_execution_time": avg_time
            },
            "domain_breakdown": domain_stats,
            "failed_tests": [
                {
                    "name": r.test_name,
                    "error": r.error_message,
                    "execution_time": r.execution_time
                }
                for r in self.results if r.status in [TestStatus.FAILED, TestStatus.ERROR]
            ],
            "performance_metrics": self._calculate_performance_metrics()
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.results:
            return {}
        
        execution_times = [r.execution_time for r in self.results]
        execution_times.sort()
        
        n = len(execution_times)
        return {
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "median_execution_time": execution_times[n // 2],
            "p95_execution_time": execution_times[int(n * 0.95)] if n > 0 else 0,
            "total_assertions": sum(r.assertions_passed + r.assertions_failed for r in self.results),
            "assertion_success_rate": self._calculate_assertion_success_rate()
        }
    
    def _calculate_assertion_success_rate(self) -> float:
        """Calculate assertion success rate"""
        total_assertions = sum(r.assertions_passed + r.assertions_failed for r in self.results)
        passed_assertions = sum(r.assertions_passed for r in self.results)
        return (passed_assertions / total_assertions * 100) if total_assertions > 0 else 0


class UnifiedTestOrchestrator:
    """Main orchestrator for unified cross-domain testing"""
    
    def __init__(self):
        self.test_runner = CrossDomainTestRunner()
        self.scheduler = TestScheduler()
        self.result_aggregator = ResultAggregator()
        self.execution_context: Optional[ExecutionContext] = None
        
        # Execution state
        self.is_running = False
        self.current_execution_id: Optional[str] = None
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def execute_plan(self, plan: TestExecutionPlan, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a complete test execution plan"""
        logger.info(f"Starting execution plan: {plan.name}")
        
        self.execution_context = context
        self.result_aggregator.execution_context = context
        self.current_execution_id = context.execution_id
        self.is_running = True
        
        context.start_time = datetime.now()
        
        try:
            # Setup domain configurations
            await self._setup_domains(plan.domain_configs)
            
            # Execute based on mode
            if context.mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(plan)
            elif context.mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(plan)
            else:  # MIXED
                await self._execute_mixed(plan)
            
            # Generate final results
            summary = self.result_aggregator.generate_summary()
            
            # Update context with results
            context.total_tests = len(self.result_aggregator.results)
            context.passed_tests = summary["execution_summary"]["passed"]
            context.failed_tests = summary["execution_summary"]["failed"]
            context.error_tests = summary["execution_summary"]["error"]
            context.skipped_tests = summary["execution_summary"]["skipped"]
            
            return {
                "execution_id": context.execution_id,
                "status": "completed",
                "context": context,
                "summary": summary,
                "detailed_results": [
                    self._serialize_result(result) for result in self.result_aggregator.results
                ]
            }
        
        except Exception as e:
            logger.error(f"Execution plan failed: {e}")
            return {
                "execution_id": context.execution_id,
                "status": "failed",
                "error": str(e),
                "context": context
            }
        
        finally:
            context.end_time = datetime.now()
            self.is_running = False
            self.test_runner.cleanup()
    
    async def _setup_domains(self, domain_configs: Dict[TestDomain, Dict[str, Any]]):
        """Setup all required testing domains"""
        for domain, config in domain_configs.items():
            logger.info(f"Setting up domain: {domain.value}")
            self.test_runner.setup_domain(domain, config)
    
    async def _execute_sequential(self, plan: TestExecutionPlan):
        """Execute tests sequentially"""
        logger.info("Executing tests sequentially")
        
        # Execute test flows
        for test_flow in plan.test_flows:
            if not self.is_running:
                break
            
            result = await self._execute_test_flow(test_flow)
            self.result_aggregator.add_result(result)
        
        # Execute standalone test cases
        for test_case in plan.test_cases:
            if not self.is_running:
                break
            
            result = await self._execute_test_case(test_case)
            self.result_aggregator.add_result(result)
    
    async def _execute_parallel(self, plan: TestExecutionPlan):
        """Execute tests in parallel"""
        logger.info("Executing tests in parallel")
        
        max_workers = self.execution_context.max_parallel_tests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def execute_with_semaphore(coro):
            async with semaphore:
                return await coro
        
        # Create tasks for all tests
        tasks = []
        
        # Add test flows
        for test_flow in plan.test_flows:
            task = execute_with_semaphore(self._execute_test_flow(test_flow))
            tasks.append(task)
        
        # Add test cases
        for test_case in plan.test_cases:
            task = execute_with_semaphore(self._execute_test_case(test_case))
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Test execution failed: {result}")
            else:
                self.result_aggregator.add_result(result)
    
    async def _execute_mixed(self, plan: TestExecutionPlan):
        """Execute tests with mixed sequential/parallel approach"""
        logger.info("Executing tests with mixed approach")
        
        # Get execution batches respecting dependencies
        execution_batches = self.scheduler.get_execution_order(plan)
        
        for batch in execution_batches:
            if not self.is_running:
                break
            
            # Execute batch in parallel
            batch_tasks = []
            
            for test_name in batch:
                # Find the test (flow or case)
                test_flow = next((f for f in plan.test_flows if f.name == test_name), None)
                test_case = next((c for c in plan.test_cases if c.name == test_name), None)
                
                if test_flow:
                    batch_tasks.append(self._execute_test_flow(test_flow))
                elif test_case:
                    batch_tasks.append(self._execute_test_case(test_case))
            
            # Wait for batch completion
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch execution failed: {result}")
                    else:
                        self.result_aggregator.add_result(result)
    
    async def _execute_test_flow(self, test_flow: TestFlow) -> TestResult:
        """Execute a test flow and return result"""
        logger.info(f"Executing test flow: {test_flow.name}")
        
        start_time = datetime.now()
        
        try:
            flow_result = await self.test_runner.execute_test_flow(test_flow)
            end_time = datetime.now()
            
            # Determine overall status
            status = TestStatus.PASSED
            if any(tr.get("status") == "failed" for tr in flow_result.get("test_results", [])):
                status = TestStatus.FAILED
            elif "error" in flow_result:
                status = TestStatus.ERROR
            
            return TestResult(
                test_name=test_flow.name,
                test_type="flow",
                status=status,
                start_time=start_time,
                end_time=end_time,
                execution_time=(end_time - start_time).total_seconds(),
                step_results=flow_result.get("test_results", []),
                error_message=flow_result.get("error")
            )
        
        except Exception as e:
            end_time = datetime.now()
            logger.error(f"Test flow execution failed: {e}")
            
            return TestResult(
                test_name=test_flow.name,
                test_type="flow",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=end_time,
                execution_time=(end_time - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _execute_test_case(self, test_case: UnifiedTestCase) -> TestResult:
        """Execute a test case and return result"""
        logger.info(f"Executing test case: {test_case.name}")
        
        start_time = datetime.now()
        
        try:
            case_result = await self.test_runner.execute_test_case(test_case)
            end_time = datetime.now()
            
            return TestResult(
                test_name=test_case.name,
                test_type="case",
                status=test_case.status,
                start_time=start_time,
                end_time=end_time,
                execution_time=(end_time - start_time).total_seconds(),
                step_results=case_result.get("steps", [])
            )
        
        except Exception as e:
            end_time = datetime.now()
            logger.error(f"Test case execution failed: {e}")
            
            return TestResult(
                test_name=test_case.name,
                test_type="case",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=end_time,
                execution_time=(end_time - start_time).total_seconds(),
                error_message=str(e)
            )
    
    def _serialize_result(self, result: TestResult) -> Dict[str, Any]:
        """Serialize test result for JSON output"""
        return {
            "test_name": result.test_name,
            "test_type": result.test_type,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat(),
            "execution_time": result.execution_time,
            "step_results": result.step_results,
            "error_message": result.error_message,
            "assertions_passed": result.assertions_passed,
            "assertions_failed": result.assertions_failed,
            "screenshots": result.screenshots,
            "performance_metrics": result.performance_metrics
        }
    
    def stop_execution(self):
        """Stop current test execution"""
        logger.info("Stopping test execution")
        self.is_running = False
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            "is_running": self.is_running,
            "execution_id": self.current_execution_id,
            "context": self.execution_context,
            "completed_tests": len(self.result_aggregator.results)
        }
    
    def save_results(self, output_path: str):
        """Save execution results to file"""
        results_data = {
            "execution_id": self.current_execution_id,
            "context": self.execution_context,
            "summary": self.result_aggregator.generate_summary(),
            "detailed_results": [
                self._serialize_result(result) for result in self.result_aggregator.results
            ]
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_path}")


# Example usage
def create_example_execution_plan() -> TestExecutionPlan:
    """Create an example execution plan"""
    from .cross_domain_testing import create_example_unified_test
    
    plan = TestExecutionPlan(
        name="E-Commerce Integration Test",
        description="Complete e-commerce flow testing across web, API, and mobile"
    )
    
    # Add domain configurations
    plan.domain_configs[TestDomain.WEB] = {
        "driver": "chrome",
        "headless": True
    }
    plan.domain_configs[TestDomain.API] = {
        "base_url": "https://api.example.com",
        "timeout": 30
    }
    plan.domain_configs[TestDomain.MOBILE] = {
        "platform": "Android",
        "device": "emulator",
        "app": "/path/to/app.apk"
    }
    
    # Add test case
    test_case = create_example_unified_test()
    plan.add_test_case(test_case)
    
    return plan