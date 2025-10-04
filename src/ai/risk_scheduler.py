"""
Risk-Based Test Scheduling System

Intelligently schedules and prioritizes tests based on code changes,
risk analysis, and historical test data to optimize test execution.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from enum import Enum
import hashlib
import subprocess
import ast
import re

from .ai_orchestrator import AIOrchestrator, AITaskResult
from .llm_service import LLMProvider

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for code changes"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ChangeType(Enum):
    """Types of code changes"""
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    DOCUMENTATION = "documentation"
    TEST = "test"
    HOTFIX = "hotfix"


@dataclass
class CodeChange:
    """Represents a code change"""
    file_path: str
    change_type: ChangeType
    lines_added: int
    lines_removed: int
    lines_modified: int
    functions_changed: List[str]
    classes_changed: List[str]
    imports_changed: List[str]
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    risk_indicators: List[str] = field(default_factory=list)


@dataclass
class TestCase:
    """Represents a test case"""
    id: str
    name: str
    file_path: str
    test_type: str  # unit, integration, e2e, etc.
    dependencies: List[str]  # Files/modules this test depends on
    execution_time: float  # Average execution time in seconds
    success_rate: float  # Historical success rate (0.0 to 1.0)
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    flakiness_score: float = 0.0  # 0.0 = stable, 1.0 = very flaky
    priority: str = "medium"  # low, medium, high, critical
    tags: List[str] = field(default_factory=list)
    coverage_areas: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Risk assessment for a code change"""
    change: CodeChange
    risk_level: RiskLevel
    risk_score: float  # 0.0 to 1.0
    impacted_areas: List[str]
    potential_failures: List[str]
    confidence: float
    reasoning: str
    recommended_tests: List[str]
    assessment_time: datetime = field(default_factory=datetime.now)


@dataclass
class TestSchedule:
    """Test execution schedule"""
    schedule_id: str
    changes: List[CodeChange]
    selected_tests: List[TestCase]
    total_tests_available: int
    estimated_execution_time: float
    risk_coverage: float
    priority_distribution: Dict[str, int]
    schedule_reasoning: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeAnalyzer:
    """Analyzes code changes and their impact"""
    
    def __init__(self):
        self.risk_patterns = {
            "database": [r"\.execute\(", r"CREATE TABLE", r"ALTER TABLE", r"DROP TABLE", r"INSERT INTO", r"UPDATE.*SET", r"DELETE FROM"],
            "authentication": [r"login", r"password", r"token", r"auth", r"session", r"security"],
            "api": [r"@app\.route", r"@api\.", r"request\.", r"response\.", r"endpoint"],
            "configuration": [r"config", r"settings", r"environment", r"\.env", r"properties"],
            "critical_business": [r"payment", r"billing", r"order", r"transaction", r"money", r"price"],
            "external_service": [r"requests\.", r"http", r"api_call", r"external", r"third_party"],
            "data_processing": [r"pandas", r"numpy", r"data_frame", r"process_data", r"transform"],
            "file_operations": [r"open\(", r"file\.", r"\.read\(", r"\.write\(", r"os\.path", r"pathlib"]
        }
    
    def analyze_code_change(self, change: CodeChange, file_content: Optional[str] = None) -> RiskAssessment:
        """Analyze a code change and assess its risk"""
        risk_score = 0.0
        risk_indicators = []
        impacted_areas = []
        potential_failures = []
        
        # Base risk from change metrics
        total_lines_changed = change.lines_added + change.lines_removed + change.lines_modified
        
        if total_lines_changed > 100:
            risk_score += 0.3
            risk_indicators.append("Large change (>100 lines)")
        elif total_lines_changed > 50:
            risk_score += 0.2
            risk_indicators.append("Medium change (>50 lines)")
        
        # Risk from change type
        change_type_risks = {
            ChangeType.HOTFIX: 0.4,
            ChangeType.NEW_FEATURE: 0.3,
            ChangeType.BUG_FIX: 0.2,
            ChangeType.REFACTOR: 0.25,
            ChangeType.DEPENDENCY: 0.35,
            ChangeType.CONFIGURATION: 0.3,
            ChangeType.TEST: 0.1,
            ChangeType.DOCUMENTATION: 0.05
        }
        
        risk_score += change_type_risks.get(change.change_type, 0.2)
        
        # Analyze file content for risk patterns
        if file_content:
            for area, patterns in self.risk_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, file_content, re.IGNORECASE):
                        risk_score += 0.1
                        impacted_areas.append(area)
                        risk_indicators.append(f"Touches {area} functionality")
                        
                        # Add potential failure scenarios
                        if area == "database":
                            potential_failures.append("Database connection issues")
                            potential_failures.append("Data integrity problems")
                        elif area == "authentication":
                            potential_failures.append("Login failures")
                            potential_failures.append("Security vulnerabilities")
                        elif area == "api":
                            potential_failures.append("API endpoint failures")
                            potential_failures.append("Request/response issues")
        
        # Risk from file path
        if any(keyword in change.file_path.lower() for keyword in ["core", "main", "critical", "production"]):
            risk_score += 0.2
            risk_indicators.append("Changes to critical system files")
        
        if any(keyword in change.file_path.lower() for keyword in ["config", "settings", "env"]):
            risk_score += 0.15
            risk_indicators.append("Configuration changes")
        
        # Risk from functions/classes changed
        if len(change.functions_changed) > 5:
            risk_score += 0.15
            risk_indicators.append("Multiple functions modified")
        
        if len(change.classes_changed) > 2:
            risk_score += 0.1
            risk_indicators.append("Multiple classes modified")
        
        # Normalize risk score
        risk_score = min(1.0, risk_score)
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL
        
        # Generate reasoning
        reasoning = self._generate_risk_reasoning(risk_level, risk_indicators, impacted_areas)
        
        return RiskAssessment(
            change=change,
            risk_level=risk_level,
            risk_score=risk_score,
            impacted_areas=list(set(impacted_areas)),
            potential_failures=list(set(potential_failures)),
            confidence=0.8,  # Static confidence for now
            reasoning=reasoning,
            recommended_tests=[]  # Will be populated by test selector
        )
    
    def _generate_risk_reasoning(self, 
                               risk_level: RiskLevel, 
                               risk_indicators: List[str],
                               impacted_areas: List[str]) -> str:
        """Generate human-readable risk reasoning"""
        reasoning_parts = [f"Risk Level: {risk_level.value.upper()}"]
        
        if risk_indicators:
            reasoning_parts.append(f"Risk Indicators: {', '.join(risk_indicators)}")
        
        if impacted_areas:
            reasoning_parts.append(f"Impacted Areas: {', '.join(impacted_areas)}")
        
        return " | ".join(reasoning_parts)
    
    def extract_dependencies(self, file_path: str, file_content: str) -> List[str]:
        """Extract dependencies from a file"""
        dependencies = []
        
        try:
            # Parse Python imports
            tree = ast.parse(file_content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        
        except SyntaxError:
            # Fallback to regex for non-Python files or syntax errors
            import_patterns = [
                r"import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
                r"from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
                r"require\(['\"]([^'\"]+)['\"]\)",  # JavaScript
                r"#include\s*[<\"]([^>\"]+)[>\"]"  # C/C++
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, file_content)
                dependencies.extend(matches)
        
        return list(set(dependencies))


class TestRepository:
    """Repository for managing test case information"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("test_repository.json")
        self.tests: Dict[str, TestCase] = {}
        self.test_dependencies: Dict[str, List[str]] = {}  # test_id -> [file_paths]
        self.file_to_tests: Dict[str, List[str]] = {}  # file_path -> [test_ids]
        self.load_repository()
    
    def add_test(self, test: TestCase):
        """Add or update a test case"""
        self.tests[test.id] = test
        
        # Update dependency mappings
        for dependency in test.dependencies:
            if dependency not in self.file_to_tests:
                self.file_to_tests[dependency] = []
            if test.id not in self.file_to_tests[dependency]:
                self.file_to_tests[dependency].append(test.id)
        
        self.save_repository()
    
    def get_tests_for_files(self, file_paths: List[str]) -> List[TestCase]:
        """Get tests that depend on the given files"""
        test_ids = set()
        
        for file_path in file_paths:
            # Direct dependencies
            if file_path in self.file_to_tests:
                test_ids.update(self.file_to_tests[file_path])
            
            # Pattern matching for related files
            for test_file, tests in self.file_to_tests.items():
                if self._files_related(file_path, test_file):
                    test_ids.update(tests)
        
        return [self.tests[test_id] for test_id in test_ids if test_id in self.tests]
    
    def get_tests_by_type(self, test_type: str) -> List[TestCase]:
        """Get tests by type"""
        return [test for test in self.tests.values() if test.test_type == test_type]
    
    def get_tests_by_priority(self, priority: str) -> List[TestCase]:
        """Get tests by priority"""
        return [test for test in self.tests.values() if test.priority == priority]
    
    def update_test_metrics(self, 
                          test_id: str,
                          execution_time: Optional[float] = None,
                          success: Optional[bool] = None,
                          flakiness_score: Optional[float] = None):
        """Update test execution metrics"""
        if test_id not in self.tests:
            return
        
        test = self.tests[test_id]
        
        if execution_time is not None:
            # Update average execution time
            if test.execution_time > 0:
                test.execution_time = (test.execution_time + execution_time) / 2
            else:
                test.execution_time = execution_time
        
        if success is not None:
            if not success:
                test.failure_count += 1
                test.last_failure = datetime.now()
            
            # Update success rate (simple moving average)
            total_runs = test.metadata.get("total_runs", 0) + 1
            successful_runs = test.metadata.get("successful_runs", 0) + (1 if success else 0)
            test.success_rate = successful_runs / total_runs
            
            test.metadata["total_runs"] = total_runs
            test.metadata["successful_runs"] = successful_runs
        
        if flakiness_score is not None:
            test.flakiness_score = flakiness_score
        
        self.save_repository()
    
    def _files_related(self, file1: str, file2: str) -> bool:
        """Check if two files are related (same module, similar names, etc.)"""
        # Simple heuristic: same directory or similar names
        path1 = Path(file1)
        path2 = Path(file2)
        
        # Same directory
        if path1.parent == path2.parent:
            return True
        
        # Similar names (e.g., user.py and test_user.py)
        name1 = path1.stem.replace("test_", "").replace("_test", "")
        name2 = path2.stem.replace("test_", "").replace("_test", "")
        
        return name1 == name2
    
    def load_repository(self):
        """Load repository from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Load tests
                for test_id, test_data in data.get("tests", {}).items():
                    if "last_failure" in test_data and test_data["last_failure"]:
                        test_data["last_failure"] = datetime.fromisoformat(test_data["last_failure"])
                    else:
                        test_data["last_failure"] = None
                    
                    self.tests[test_id] = TestCase(**test_data)
                
                # Load mappings
                self.file_to_tests = data.get("file_to_tests", {})
                
                logger.info(f"Loaded {len(self.tests)} tests from repository")
                
            except Exception as e:
                logger.error(f"Failed to load test repository: {str(e)}")
    
    def save_repository(self):
        """Save repository to storage"""
        try:
            data = {
                "tests": {},
                "file_to_tests": self.file_to_tests
            }
            
            # Serialize tests
            for test_id, test in self.tests.items():
                test_dict = {
                    "id": test.id,
                    "name": test.name,
                    "file_path": test.file_path,
                    "test_type": test.test_type,
                    "dependencies": test.dependencies,
                    "execution_time": test.execution_time,
                    "success_rate": test.success_rate,
                    "last_failure": test.last_failure.isoformat() if test.last_failure else None,
                    "failure_count": test.failure_count,
                    "flakiness_score": test.flakiness_score,
                    "priority": test.priority,
                    "tags": test.tags,
                    "coverage_areas": test.coverage_areas,
                    "metadata": test.metadata
                }
                data["tests"][test_id] = test_dict
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save test repository: {str(e)}")


class RiskBasedScheduler:
    """Main service for risk-based test scheduling"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.ai_orchestrator = AIOrchestrator(llm_provider, config)
        self.code_analyzer = CodeAnalyzer()
        self.test_repository = TestRepository()
        
        # Configuration
        self.config = config or {}
        self.max_execution_time = self.config.get("max_execution_time", 3600)  # 1 hour
        self.min_risk_coverage = self.config.get("min_risk_coverage", 0.8)
        self.enable_ai_analysis = self.config.get("enable_ai_analysis", True)
        self.flakiness_threshold = self.config.get("flakiness_threshold", 0.3)
        
        logger.info("Risk-Based Scheduler initialized")
    
    async def create_test_schedule(self, 
                                 changes: List[CodeChange],
                                 constraints: Optional[Dict] = None) -> TestSchedule:
        """
        Create an optimized test schedule based on code changes and risk analysis
        """
        constraints = constraints or {}
        max_time = constraints.get("max_execution_time", self.max_execution_time)
        
        try:
            # Step 1: Analyze risks for each change
            risk_assessments = []
            for change in changes:
                # Get file content if available
                file_content = self._get_file_content(change.file_path)
                assessment = self.code_analyzer.analyze_risk_assessment(change, file_content)
                
                # Enhance with AI analysis if enabled
                if self.enable_ai_analysis:
                    ai_assessment = await self._enhance_risk_with_ai(assessment)
                    if ai_assessment:
                        assessment = ai_assessment
                
                risk_assessments.append(assessment)
            
            # Step 2: Identify impacted tests
            all_impacted_tests = []
            for assessment in risk_assessments:
                impacted_tests = self._find_impacted_tests(assessment)
                all_impacted_tests.extend(impacted_tests)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tests = []
            for test in all_impacted_tests:
                if test.id not in seen:
                    unique_tests.append(test)
                    seen.add(test.id)
            
            # Step 3: Prioritize and select tests
            selected_tests = self._select_optimal_tests(
                unique_tests, 
                risk_assessments, 
                max_time
            )
            
            # Step 4: Calculate metrics
            total_execution_time = sum(test.execution_time for test in selected_tests)
            risk_coverage = self._calculate_risk_coverage(risk_assessments, selected_tests)
            priority_dist = self._calculate_priority_distribution(selected_tests)
            
            # Step 5: Generate reasoning
            reasoning = self._generate_schedule_reasoning(
                changes, 
                risk_assessments, 
                selected_tests, 
                total_execution_time
            )
            
            schedule = TestSchedule(
                schedule_id=f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                changes=changes,
                selected_tests=selected_tests,
                total_tests_available=len(unique_tests),
                estimated_execution_time=total_execution_time,
                risk_coverage=risk_coverage,
                priority_distribution=priority_dist,
                schedule_reasoning=reasoning
            )
            
            logger.info(f"Created test schedule with {len(selected_tests)} tests "
                       f"(coverage: {risk_coverage:.2f}, time: {total_execution_time:.0f}s)")
            
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to create test schedule: {str(e)}")
            
            # Return minimal schedule
            return TestSchedule(
                schedule_id=f"error_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                changes=changes,
                selected_tests=[],
                total_tests_available=0,
                estimated_execution_time=0,
                risk_coverage=0.0,
                priority_distribution={},
                schedule_reasoning=f"Error creating schedule: {str(e)}"
            )
    
    async def _enhance_risk_with_ai(self, assessment: RiskAssessment) -> Optional[RiskAssessment]:
        """Enhance risk assessment using AI"""
        try:
            change_context = {
                "file_path": assessment.change.file_path,
                "change_type": assessment.change.change_type.value,
                "lines_changed": (assessment.change.lines_added + 
                                assessment.change.lines_removed + 
                                assessment.change.lines_modified),
                "functions_changed": assessment.change.functions_changed,
                "classes_changed": assessment.change.classes_changed,
                "description": assessment.change.description or ""
            }
            
            ai_result = await self.ai_orchestrator.assess_change_risk(
                assessment.change.file_path,
                change_context
            )
            
            if ai_result.success and ai_result.result:
                # Parse AI response and update assessment
                ai_data = ai_result.result if isinstance(ai_result.result, dict) else {}
                
                # Update risk score if AI provides one
                if "risk_score" in ai_data:
                    assessment.risk_score = max(assessment.risk_score, ai_data["risk_score"])
                
                # Add AI-identified areas
                if "impacted_areas" in ai_data:
                    assessment.impacted_areas.extend(ai_data["impacted_areas"])
                    assessment.impacted_areas = list(set(assessment.impacted_areas))
                
                # Add AI-identified potential failures
                if "potential_failures" in ai_data:
                    assessment.potential_failures.extend(ai_data["potential_failures"])
                    assessment.potential_failures = list(set(assessment.potential_failures))
                
                # Update reasoning with AI insights
                if "reasoning" in ai_data:
                    assessment.reasoning += f" | AI Analysis: {ai_data['reasoning']}"
                
                # Update confidence
                assessment.confidence = min(1.0, assessment.confidence + 0.1)
            
            return assessment
            
        except Exception as e:
            logger.warning(f"AI risk enhancement failed: {str(e)}")
            return None
    
    def _find_impacted_tests(self, assessment: RiskAssessment) -> List[TestCase]:
        """Find tests impacted by a code change"""
        impacted_tests = []
        
        # Get tests that directly depend on the changed file
        direct_tests = self.test_repository.get_tests_for_files([assessment.change.file_path])
        impacted_tests.extend(direct_tests)
        
        # Get tests for impacted areas
        for area in assessment.impacted_areas:
            area_tests = self._get_tests_for_area(area)
            impacted_tests.extend(area_tests)
        
        # Get tests based on risk level
        if assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            # Include integration and e2e tests for high-risk changes
            integration_tests = self.test_repository.get_tests_by_type("integration")
            e2e_tests = self.test_repository.get_tests_by_type("e2e")
            impacted_tests.extend(integration_tests)
            impacted_tests.extend(e2e_tests)
        
        # Remove duplicates
        seen = set()
        unique_tests = []
        for test in impacted_tests:
            if test.id not in seen:
                unique_tests.append(test)
                seen.add(test.id)
        
        return unique_tests
    
    def _get_tests_for_area(self, area: str) -> List[TestCase]:
        """Get tests related to a specific functional area"""
        area_tests = []
        
        for test in self.test_repository.tests.values():
            # Check if test covers this area
            if area in test.coverage_areas:
                area_tests.append(test)
                continue
            
            # Check tags
            if any(area.lower() in tag.lower() for tag in test.tags):
                area_tests.append(test)
                continue
            
            # Check test name/path
            if area.lower() in test.name.lower() or area.lower() in test.file_path.lower():
                area_tests.append(test)
        
        return area_tests
    
    def _select_optimal_tests(self, 
                            available_tests: List[TestCase],
                            risk_assessments: List[RiskAssessment],
                            max_time: float) -> List[TestCase]:
        """Select optimal set of tests within time constraints"""
        
        # Calculate priority scores for each test
        test_scores = []
        for test in available_tests:
            score = self._calculate_test_priority_score(test, risk_assessments)
            test_scores.append((test, score))
        
        # Sort by priority score (descending)
        test_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select tests using greedy algorithm with time constraint
        selected_tests = []
        total_time = 0.0
        
        for test, score in test_scores:
            # Skip flaky tests unless they're high priority
            if test.flakiness_score > self.flakiness_threshold and test.priority not in ["high", "critical"]:
                continue
            
            # Check time constraint
            if total_time + test.execution_time <= max_time:
                selected_tests.append(test)
                total_time += test.execution_time
            elif test.priority == "critical":
                # Always include critical tests, even if over time limit
                selected_tests.append(test)
                total_time += test.execution_time
        
        # Ensure minimum coverage of critical areas
        self._ensure_critical_coverage(selected_tests, available_tests, risk_assessments)
        
        return selected_tests
    
    def _calculate_test_priority_score(self, 
                                     test: TestCase,
                                     risk_assessments: List[RiskAssessment]) -> float:
        """Calculate priority score for a test"""
        score = 0.0
        
        # Base score from test priority
        priority_scores = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }
        score += priority_scores.get(test.priority, 0.5)
        
        # Bonus for high success rate (reliable tests)
        score += test.success_rate * 0.3
        
        # Penalty for flakiness
        score -= test.flakiness_score * 0.4
        
        # Bonus for recent failures (might catch regressions)
        if test.last_failure and (datetime.now() - test.last_failure).days < 7:
            score += 0.2
        
        # Bonus based on risk assessment relevance
        for assessment in risk_assessments:
            # Test covers impacted areas
            for area in assessment.impacted_areas:
                if area in test.coverage_areas or any(area.lower() in tag.lower() for tag in test.tags):
                    score += assessment.risk_score * 0.3
            
            # Test type matches risk level
            if assessment.risk_level == RiskLevel.CRITICAL and test.test_type in ["integration", "e2e"]:
                score += 0.3
            elif assessment.risk_level == RiskLevel.HIGH and test.test_type in ["integration", "unit"]:
                score += 0.2
        
        # Efficiency bonus (shorter execution time)
        if test.execution_time > 0:
            efficiency_bonus = max(0, 0.2 - (test.execution_time / 300))  # Bonus for tests under 5 minutes
            score += efficiency_bonus
        
        return max(0.0, min(2.0, score))  # Normalize to 0-2 range
    
    def _ensure_critical_coverage(self, 
                                selected_tests: List[TestCase],
                                available_tests: List[TestCase],
                                risk_assessments: List[RiskAssessment]):
        """Ensure critical areas have test coverage"""
        selected_ids = {test.id for test in selected_tests}
        
        # Check coverage for critical risk areas
        for assessment in risk_assessments:
            if assessment.risk_level == RiskLevel.CRITICAL:
                # Ensure at least one test covers each critical area
                for area in assessment.impacted_areas:
                    area_covered = any(
                        area in test.coverage_areas or 
                        any(area.lower() in tag.lower() for tag in test.tags)
                        for test in selected_tests
                    )
                    
                    if not area_covered:
                        # Find and add a test for this area
                        for test in available_tests:
                            if (test.id not in selected_ids and 
                                (area in test.coverage_areas or 
                                 any(area.lower() in tag.lower() for tag in test.tags))):
                                selected_tests.append(test)
                                selected_ids.add(test.id)
                                break
    
    def _calculate_risk_coverage(self, 
                               risk_assessments: List[RiskAssessment],
                               selected_tests: List[TestCase]) -> float:
        """Calculate how well the selected tests cover the identified risks"""
        if not risk_assessments:
            return 1.0
        
        total_risk_weight = sum(assessment.risk_score for assessment in risk_assessments)
        covered_risk_weight = 0.0
        
        for assessment in risk_assessments:
            # Check if any selected test covers this risk
            risk_covered = False
            
            for test in selected_tests:
                # Test covers impacted areas
                if any(area in test.coverage_areas for area in assessment.impacted_areas):
                    risk_covered = True
                    break
                
                # Test has relevant tags
                if any(any(area.lower() in tag.lower() for tag in test.tags) 
                      for area in assessment.impacted_areas):
                    risk_covered = True
                    break
                
                # Test file path suggests relevance
                if any(area.lower() in test.file_path.lower() 
                      for area in assessment.impacted_areas):
                    risk_covered = True
                    break
            
            if risk_covered:
                covered_risk_weight += assessment.risk_score
        
        return covered_risk_weight / total_risk_weight if total_risk_weight > 0 else 1.0
    
    def _calculate_priority_distribution(self, tests: List[TestCase]) -> Dict[str, int]:
        """Calculate distribution of test priorities"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for test in tests:
            priority = test.priority
            if priority in distribution:
                distribution[priority] += 1
        
        return distribution
    
    def _generate_schedule_reasoning(self, 
                                   changes: List[CodeChange],
                                   risk_assessments: List[RiskAssessment],
                                   selected_tests: List[TestCase],
                                   execution_time: float) -> str:
        """Generate human-readable reasoning for the test schedule"""
        reasoning_parts = []
        
        # Summary of changes
        reasoning_parts.append(f"Analyzed {len(changes)} code changes")
        
        # Risk summary
        risk_levels = [assessment.risk_level.value for assessment in risk_assessments]
        risk_summary = {level: risk_levels.count(level) for level in set(risk_levels)}
        reasoning_parts.append(f"Risk distribution: {risk_summary}")
        
        # Test selection summary
        test_types = [test.test_type for test in selected_tests]
        type_summary = {test_type: test_types.count(test_type) for test_type in set(test_types)}
        reasoning_parts.append(f"Selected {len(selected_tests)} tests: {type_summary}")
        
        # Time estimate
        reasoning_parts.append(f"Estimated execution time: {execution_time:.0f} seconds")
        
        # High-risk areas
        high_risk_areas = []
        for assessment in risk_assessments:
            if assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                high_risk_areas.extend(assessment.impacted_areas)
        
        if high_risk_areas:
            unique_areas = list(set(high_risk_areas))
            reasoning_parts.append(f"High-risk areas: {', '.join(unique_areas[:5])}")
        
        return " | ".join(reasoning_parts)
    
    def _get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {str(e)}")
            return None
    
    async def analyze_git_changes(self, 
                                commit_range: Optional[str] = None,
                                branch: Optional[str] = None) -> List[CodeChange]:
        """Analyze git changes and convert to CodeChange objects"""
        changes = []
        
        try:
            # Get git diff
            if commit_range:
                cmd = ["git", "diff", "--name-status", commit_range]
            elif branch:
                cmd = ["git", "diff", "--name-status", f"origin/{branch}..HEAD"]
            else:
                cmd = ["git", "diff", "--name-status", "HEAD~1..HEAD"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            if result.returncode != 0:
                logger.error(f"Git command failed: {result.stderr}")
                return changes
            
            # Parse git diff output
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                status = parts[0]
                file_path = parts[1]
                
                # Determine change type
                change_type = ChangeType.BUG_FIX  # Default
                if status.startswith('A'):
                    change_type = ChangeType.NEW_FEATURE
                elif status.startswith('D'):
                    change_type = ChangeType.REFACTOR
                elif status.startswith('M'):
                    change_type = ChangeType.BUG_FIX
                
                # Get detailed diff stats
                stats_cmd = ["git", "diff", "--numstat", "HEAD~1..HEAD", file_path]
                stats_result = subprocess.run(stats_cmd, capture_output=True, text=True, cwd=".")
                
                lines_added = 0
                lines_removed = 0
                
                if stats_result.returncode == 0 and stats_result.stdout.strip():
                    stats_line = stats_result.stdout.strip().split('\t')
                    if len(stats_line) >= 2:
                        try:
                            lines_added = int(stats_line[0]) if stats_line[0] != '-' else 0
                            lines_removed = int(stats_line[1]) if stats_line[1] != '-' else 0
                        except ValueError:
                            pass
                
                change = CodeChange(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    lines_modified=0,  # Git doesn't distinguish modified from added/removed
                    functions_changed=[],  # TODO: Analyze function changes
                    classes_changed=[],    # TODO: Analyze class changes
                    imports_changed=[],    # TODO: Analyze import changes
                    timestamp=datetime.now()
                )
                
                changes.append(change)
            
        except Exception as e:
            logger.error(f"Failed to analyze git changes: {str(e)}")
        
        return changes
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_tests = len(self.test_repository.tests)
        
        # Calculate average metrics
        if total_tests > 0:
            avg_execution_time = sum(test.execution_time for test in self.test_repository.tests.values()) / total_tests
            avg_success_rate = sum(test.success_rate for test in self.test_repository.tests.values()) / total_tests
            avg_flakiness = sum(test.flakiness_score for test in self.test_repository.tests.values()) / total_tests
        else:
            avg_execution_time = avg_success_rate = avg_flakiness = 0.0
        
        # Test type distribution
        test_types = [test.test_type for test in self.test_repository.tests.values()]
        type_distribution = {test_type: test_types.count(test_type) for test_type in set(test_types)}
        
        return {
            "total_tests": total_tests,
            "average_execution_time": avg_execution_time,
            "average_success_rate": avg_success_rate,
            "average_flakiness_score": avg_flakiness,
            "test_type_distribution": type_distribution,
            "flaky_tests_count": sum(1 for test in self.test_repository.tests.values() 
                                   if test.flakiness_score > self.flakiness_threshold)
        }