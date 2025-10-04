"""
AI-Powered Test Generation System

Generates comprehensive test cases and scripts from requirements, user stories,
and application specifications using advanced AI capabilities.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from enum import Enum
import re
import ast

from .ai_orchestrator import AIOrchestrator, AITaskResult
from .llm_service import LLMProvider

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests that can be generated"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    API = "api"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    VISUAL = "visual"


class TestFramework(Enum):
    """Supported test frameworks"""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    CYPRESS = "cypress"
    JEST = "jest"
    MOCHA = "mocha"
    POSTMAN = "postman"


@dataclass
class RequirementSpec:
    """Specification for a requirement or user story"""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str = "medium"  # low, medium, high, critical
    category: str = "functional"  # functional, non-functional, security, etc.
    user_role: Optional[str] = None
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestScenario:
    """Generated test scenario"""
    id: str
    name: str
    description: str
    test_type: TestType
    framework: TestFramework
    priority: str
    steps: List[Dict[str, str]]  # action, expected_result, data
    setup_steps: List[str] = field(default_factory=list)
    teardown_steps: List[str] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    assertions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # in seconds
    complexity: str = "medium"  # low, medium, high
    coverage_areas: List[str] = field(default_factory=list)


@dataclass
class GeneratedTestSuite:
    """Complete generated test suite"""
    requirement_id: str
    suite_name: str
    description: str
    scenarios: List[TestScenario]
    framework: TestFramework
    total_scenarios: int
    estimated_duration: int
    coverage_percentage: float
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestGenerationResult:
    """Result of test generation process"""
    requirement_id: str
    success: bool
    generated_suite: Optional[GeneratedTestSuite]
    generated_code: Optional[str]
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    generation_time: float = 0.0
    ai_confidence: float = 0.0
    coverage_analysis: Dict[str, Any] = field(default_factory=dict)


class RequirementParser:
    """Parses and analyzes requirements/user stories"""
    
    def __init__(self):
        self.user_story_pattern = r"As a (.+?), I want (.+?) so that (.+?)(?:\.|$)"
        self.acceptance_criteria_patterns = [
            r"Given (.+?) when (.+?) then (.+?)(?:\.|$)",
            r"Scenario: (.+?)(?:\n|$)",
            r"- (.+?)(?:\n|$)",
            r"\* (.+?)(?:\n|$)"
        ]
    
    def parse_user_story(self, text: str) -> Dict[str, Any]:
        """Parse user story format"""
        match = re.search(self.user_story_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return {
                "user_role": match.group(1).strip(),
                "functionality": match.group(2).strip(),
                "business_value": match.group(3).strip(),
                "format": "user_story"
            }
        
        return {"format": "free_text", "content": text}
    
    def extract_acceptance_criteria(self, text: str) -> List[str]:
        """Extract acceptance criteria from text"""
        criteria = []
        
        for pattern in self.acceptance_criteria_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    criteria.append(" ".join(match))
                else:
                    criteria.append(match)
        
        # Clean up and deduplicate
        criteria = [c.strip() for c in criteria if c.strip()]
        return list(dict.fromkeys(criteria))  # Remove duplicates while preserving order
    
    def identify_test_types(self, requirement: RequirementSpec) -> List[TestType]:
        """Identify appropriate test types for a requirement"""
        test_types = []
        
        text = f"{requirement.description} {' '.join(requirement.acceptance_criteria)}".lower()
        
        # Functional tests (always include for functional requirements)
        if requirement.category == "functional":
            test_types.append(TestType.E2E)
            test_types.append(TestType.INTEGRATION)
        
        # API tests
        if any(keyword in text for keyword in ["api", "endpoint", "service", "request", "response"]):
            test_types.append(TestType.API)
        
        # Performance tests
        if any(keyword in text for keyword in ["performance", "load", "speed", "response time", "throughput"]):
            test_types.append(TestType.PERFORMANCE)
        
        # Security tests
        if any(keyword in text for keyword in ["security", "authentication", "authorization", "login", "permission"]):
            test_types.append(TestType.SECURITY)
        
        # Accessibility tests
        if any(keyword in text for keyword in ["accessibility", "screen reader", "keyboard", "aria", "wcag"]):
            test_types.append(TestType.ACCESSIBILITY)
        
        # Visual tests
        if any(keyword in text for keyword in ["ui", "visual", "layout", "design", "appearance", "responsive"]):
            test_types.append(TestType.VISUAL)
        
        # Default to unit and integration if nothing specific identified
        if not test_types:
            test_types = [TestType.UNIT, TestType.INTEGRATION]
        
        return test_types
    
    def extract_test_data(self, requirement: RequirementSpec) -> Dict[str, Any]:
        """Extract test data from requirement"""
        test_data = {}
        
        text = f"{requirement.description} {' '.join(requirement.acceptance_criteria)}"
        
        # Extract common data patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            test_data["emails"] = emails
        
        # Extract numbers/amounts
        number_pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        numbers = re.findall(number_pattern, text)
        if numbers:
            test_data["amounts"] = numbers
        
        # Extract quoted strings (potential test values)
        quoted_pattern = r'"([^"]+)"'
        quoted_strings = re.findall(quoted_pattern, text)
        if quoted_strings:
            test_data["values"] = quoted_strings
        
        return test_data


class TestCodeGenerator:
    """Generates actual test code from test scenarios"""
    
    def __init__(self):
        self.framework_templates = {
            TestFramework.PYTEST: self._get_pytest_template(),
            TestFramework.SELENIUM: self._get_selenium_template(),
            TestFramework.PLAYWRIGHT: self._get_playwright_template(),
            TestFramework.CYPRESS: self._get_cypress_template(),
            TestFramework.JEST: self._get_jest_template()
        }
    
    def generate_test_code(self, 
                          test_suite: GeneratedTestSuite,
                          include_imports: bool = True,
                          include_setup: bool = True) -> str:
        """Generate complete test code for a test suite"""
        
        framework = test_suite.framework
        template = self.framework_templates.get(framework)
        
        if not template:
            raise ValueError(f"Unsupported framework: {framework}")
        
        # Generate code sections
        imports = self._generate_imports(framework) if include_imports else ""
        setup_code = self._generate_setup_code(framework, test_suite) if include_setup else ""
        test_methods = self._generate_test_methods(framework, test_suite)
        teardown_code = self._generate_teardown_code(framework, test_suite)
        
        # Combine all sections
        full_code = template.format(
            imports=imports,
            setup_code=setup_code,
            test_methods=test_methods,
            teardown_code=teardown_code,
            suite_name=test_suite.suite_name.replace(" ", "_"),
            description=test_suite.description
        )
        
        return full_code
    
    def _generate_imports(self, framework: TestFramework) -> str:
        """Generate import statements for framework"""
        imports_map = {
            TestFramework.PYTEST: """
import pytest
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
""",
            TestFramework.SELENIUM: """
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
""",
            TestFramework.PLAYWRIGHT: """
import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime
""",
            TestFramework.CYPRESS: """
// Cypress test imports are handled automatically
""",
            TestFramework.JEST: """
const { test, expect, beforeAll, afterAll } = require('@jest/globals');
const puppeteer = require('puppeteer');
"""
        }
        
        return imports_map.get(framework, "")
    
    def _generate_setup_code(self, framework: TestFramework, test_suite: GeneratedTestSuite) -> str:
        """Generate setup code for test suite"""
        setup_templates = {
            TestFramework.PYTEST: """
@pytest.fixture(scope="class")
def driver():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def setup_test_data():
    # Setup test data
    return {{
        "test_data": {test_data}
    }}
""",
            TestFramework.SELENIUM: """
def setUp(self):
    self.driver = webdriver.Chrome()
    self.driver.implicitly_wait(10)
    self.test_data = {test_data}

def tearDown(self):
    self.driver.quit()
""",
            TestFramework.PLAYWRIGHT: """
@pytest.fixture(scope="session")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        yield browser
        await browser.close()

@pytest.fixture(scope="function")
async def page(browser):
    page = await browser.new_page()
    yield page
    await page.close()
"""
        }
        
        template = setup_templates.get(framework, "")
        test_data = json.dumps(test_suite.scenarios[0].test_data if test_suite.scenarios else {}, indent=8)
        
        return template.format(test_data=test_data)
    
    def _generate_test_methods(self, framework: TestFramework, test_suite: GeneratedTestSuite) -> str:
        """Generate test methods for all scenarios"""
        methods = []
        
        for scenario in test_suite.scenarios:
            method_code = self._generate_single_test_method(framework, scenario)
            methods.append(method_code)
        
        return "\n\n".join(methods)
    
    def _generate_single_test_method(self, framework: TestFramework, scenario: TestScenario) -> str:
        """Generate code for a single test scenario"""
        method_name = scenario.name.lower().replace(" ", "_").replace("-", "_")
        
        if framework == TestFramework.PYTEST:
            return self._generate_pytest_method(method_name, scenario)
        elif framework == TestFramework.SELENIUM:
            return self._generate_selenium_method(method_name, scenario)
        elif framework == TestFramework.PLAYWRIGHT:
            return self._generate_playwright_method(method_name, scenario)
        elif framework == TestFramework.CYPRESS:
            return self._generate_cypress_method(method_name, scenario)
        elif framework == TestFramework.JEST:
            return self._generate_jest_method(method_name, scenario)
        
        return f"# TODO: Implement {method_name}"
    
    def _generate_pytest_method(self, method_name: str, scenario: TestScenario) -> str:
        """Generate pytest method"""
        steps_code = []
        
        for step in scenario.steps:
            action = step.get("action", "")
            expected = step.get("expected_result", "")
            
            if "click" in action.lower():
                steps_code.append(f'        # {action}')
                steps_code.append(f'        element = driver.find_element(By.CSS_SELECTOR, "selector_here")')
                steps_code.append(f'        element.click()')
            elif "type" in action.lower() or "enter" in action.lower():
                steps_code.append(f'        # {action}')
                steps_code.append(f'        element = driver.find_element(By.CSS_SELECTOR, "input_selector")')
                steps_code.append(f'        element.send_keys("test_data")')
            elif "verify" in action.lower() or "check" in action.lower():
                steps_code.append(f'        # {action}')
                steps_code.append(f'        assert "{expected}" in driver.page_source')
            else:
                steps_code.append(f'        # {action}')
                steps_code.append(f'        # TODO: Implement step')
        
        return f"""
def test_{method_name}(driver, setup_test_data):
    \"\"\"
    {scenario.description}
    
    Test Type: {scenario.test_type.value}
    Priority: {scenario.priority}
    \"\"\"
    try:
{chr(10).join(steps_code)}
        
        # Assertions
        {chr(10).join(f'        assert {assertion}' for assertion in scenario.assertions) if scenario.assertions else '        # Add assertions here'}
        
    except Exception as e:
        pytest.fail(f"Test failed: {{str(e)}}")
"""
    
    def _generate_selenium_method(self, method_name: str, scenario: TestScenario) -> str:
        """Generate Selenium unittest method"""
        return f"""
def test_{method_name}(self):
    \"\"\"
    {scenario.description}
    \"\"\"
    # TODO: Implement Selenium test steps
    self.fail("Test not implemented")
"""
    
    def _generate_playwright_method(self, method_name: str, scenario: TestScenario) -> str:
        """Generate Playwright method"""
        return f"""
async def test_{method_name}(page):
    \"\"\"
    {scenario.description}
    \"\"\"
    # TODO: Implement Playwright test steps
    await page.goto("https://example.com")
    assert False, "Test not implemented"
"""
    
    def _generate_cypress_method(self, method_name: str, scenario: TestScenario) -> str:
        """Generate Cypress method"""
        return f"""
it('{scenario.name}', () => {{
    // {scenario.description}
    // TODO: Implement Cypress test steps
    cy.visit('https://example.com');
    cy.get('selector').should('exist');
}});
"""
    
    def _generate_jest_method(self, method_name: str, scenario: TestScenario) -> str:
        """Generate Jest method"""
        return f"""
test('{scenario.name}', async () => {{
    // {scenario.description}
    // TODO: Implement Jest test steps
    expect(true).toBe(false); // Placeholder
}});
"""
    
    def _generate_teardown_code(self, framework: TestFramework, test_suite: GeneratedTestSuite) -> str:
        """Generate teardown code"""
        teardown_templates = {
            TestFramework.PYTEST: """
# Teardown is handled by fixtures
""",
            TestFramework.SELENIUM: """
# Teardown is handled in tearDown method
""",
            TestFramework.PLAYWRIGHT: """
# Teardown is handled by fixtures
"""
        }
        
        return teardown_templates.get(framework, "")
    
    def _get_pytest_template(self) -> str:
        """Get pytest template"""
        return """
{imports}

class Test{suite_name}:
    \"\"\"
    {description}
    \"\"\"
    
{setup_code}

{test_methods}

{teardown_code}
"""
    
    def _get_selenium_template(self) -> str:
        """Get Selenium unittest template"""
        return """
{imports}

class Test{suite_name}(unittest.TestCase):
    \"\"\"
    {description}
    \"\"\"
    
{setup_code}

{test_methods}

{teardown_code}

if __name__ == '__main__':
    unittest.main()
"""
    
    def _get_playwright_template(self) -> str:
        """Get Playwright template"""
        return """
{imports}

{setup_code}

{test_methods}

{teardown_code}
"""
    
    def _get_cypress_template(self) -> str:
        """Get Cypress template"""
        return """
{imports}

describe('{suite_name}', () => {{
    // {description}
    
    beforeEach(() => {{
        // Setup code
    }});
    
{test_methods}
    
    afterEach(() => {{
        // Teardown code
    }});
}});
"""
    
    def _get_jest_template(self) -> str:
        """Get Jest template"""
        return """
{imports}

describe('{suite_name}', () => {{
    // {description}
    
    beforeAll(async () => {{
        // Setup code
    }});
    
{test_methods}
    
    afterAll(async () => {{
        // Teardown code
    }});
}});
"""


class AITestGenerator:
    """Main service for AI-powered test generation"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.ai_orchestrator = AIOrchestrator(llm_provider, config)
        self.requirement_parser = RequirementParser()
        self.code_generator = TestCodeGenerator()
        
        # Configuration
        self.config = config or {}
        self.default_framework = TestFramework(self.config.get("default_framework", "pytest"))
        self.max_scenarios_per_requirement = self.config.get("max_scenarios_per_requirement", 10)
        self.enable_code_generation = self.config.get("enable_code_generation", True)
        
        logger.info("AI Test Generator initialized")
    
    async def generate_tests_from_requirement(self, 
                                            requirement: RequirementSpec,
                                            framework: Optional[TestFramework] = None,
                                            test_types: Optional[List[TestType]] = None) -> TestGenerationResult:
        """
        Generate comprehensive test suite from a requirement specification
        """
        start_time = datetime.now()
        framework = framework or self.default_framework
        
        try:
            # Step 1: Parse and analyze requirement
            parsed_requirement = self.requirement_parser.parse_user_story(requirement.description)
            
            if not test_types:
                test_types = self.requirement_parser.identify_test_types(requirement)
            
            test_data = self.requirement_parser.extract_test_data(requirement)
            
            # Step 2: Generate test scenarios using AI
            scenarios = await self._generate_test_scenarios(requirement, test_types, framework)
            
            if not scenarios:
                return TestGenerationResult(
                    requirement_id=requirement.id,
                    success=False,
                    generated_suite=None,
                    generated_code=None,
                    error_message="No test scenarios could be generated",
                    generation_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Step 3: Create test suite
            test_suite = GeneratedTestSuite(
                requirement_id=requirement.id,
                suite_name=f"Test_{requirement.title.replace(' ', '_')}",
                description=requirement.description,
                scenarios=scenarios,
                framework=framework,
                total_scenarios=len(scenarios),
                estimated_duration=sum(s.estimated_duration or 30 for s in scenarios),
                coverage_percentage=self._calculate_coverage_percentage(requirement, scenarios)
            )
            
            # Step 4: Generate code if enabled
            generated_code = None
            if self.enable_code_generation:
                try:
                    generated_code = self.code_generator.generate_test_code(test_suite)
                except Exception as e:
                    logger.warning(f"Code generation failed: {str(e)}")
            
            # Step 5: Analyze coverage
            coverage_analysis = self._analyze_test_coverage(requirement, scenarios)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return TestGenerationResult(
                requirement_id=requirement.id,
                success=True,
                generated_suite=test_suite,
                generated_code=generated_code,
                generation_time=generation_time,
                ai_confidence=0.8,  # TODO: Get from AI response
                coverage_analysis=coverage_analysis
            )
            
        except Exception as e:
            logger.error(f"Test generation failed for requirement {requirement.id}: {str(e)}")
            
            return TestGenerationResult(
                requirement_id=requirement.id,
                success=False,
                generated_suite=None,
                generated_code=None,
                error_message=str(e),
                generation_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _generate_test_scenarios(self, 
                                     requirement: RequirementSpec,
                                     test_types: List[TestType],
                                     framework: TestFramework) -> List[TestScenario]:
        """Generate test scenarios using AI"""
        scenarios = []
        
        for test_type in test_types:
            try:
                # Use AI to generate scenarios for this test type
                ai_result = await self.ai_orchestrator.generate_test_cases(
                    requirement.description,
                    {
                        "acceptance_criteria": requirement.acceptance_criteria,
                        "test_type": test_type.value,
                        "framework": framework.value,
                        "user_role": requirement.user_role,
                        "priority": requirement.priority
                    }
                )
                
                if ai_result.success and ai_result.result:
                    # Parse AI response into scenarios
                    ai_scenarios = self._parse_ai_scenarios(ai_result.result, test_type, framework)
                    scenarios.extend(ai_scenarios)
                
            except Exception as e:
                logger.warning(f"Failed to generate {test_type.value} scenarios: {str(e)}")
                
                # Fallback: Create basic scenario
                fallback_scenario = self._create_fallback_scenario(requirement, test_type, framework)
                scenarios.append(fallback_scenario)
        
        # Limit number of scenarios
        if len(scenarios) > self.max_scenarios_per_requirement:
            scenarios = scenarios[:self.max_scenarios_per_requirement]
        
        return scenarios
    
    def _parse_ai_scenarios(self, 
                          ai_response: Any,
                          test_type: TestType,
                          framework: TestFramework) -> List[TestScenario]:
        """Parse AI response into test scenarios"""
        scenarios = []
        
        try:
            if isinstance(ai_response, str):
                # Try to parse as JSON
                try:
                    ai_data = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Parse as text
                    ai_data = {"scenarios": [{"name": "Generated Test", "description": ai_response}]}
            else:
                ai_data = ai_response
            
            scenario_data = ai_data.get("scenarios", [ai_data]) if isinstance(ai_data, dict) else [ai_data]
            
            for i, scenario_info in enumerate(scenario_data):
                if isinstance(scenario_info, str):
                    scenario_info = {"name": f"Test Scenario {i+1}", "description": scenario_info}
                
                scenario = TestScenario(
                    id=f"{test_type.value}_{i+1}",
                    name=scenario_info.get("name", f"{test_type.value.title()} Test {i+1}"),
                    description=scenario_info.get("description", "AI-generated test scenario"),
                    test_type=test_type,
                    framework=framework,
                    priority=scenario_info.get("priority", "medium"),
                    steps=scenario_info.get("steps", []),
                    test_data=scenario_info.get("test_data", {}),
                    assertions=scenario_info.get("assertions", []),
                    estimated_duration=scenario_info.get("estimated_duration", 60),
                    complexity=scenario_info.get("complexity", "medium")
                )
                
                scenarios.append(scenario)
                
        except Exception as e:
            logger.error(f"Failed to parse AI scenarios: {str(e)}")
        
        return scenarios
    
    def _create_fallback_scenario(self, 
                                requirement: RequirementSpec,
                                test_type: TestType,
                                framework: TestFramework) -> TestScenario:
        """Create a basic fallback scenario"""
        return TestScenario(
            id=f"{test_type.value}_fallback",
            name=f"{test_type.value.title()} Test for {requirement.title}",
            description=f"Basic {test_type.value} test generated from requirement: {requirement.description[:100]}...",
            test_type=test_type,
            framework=framework,
            priority=requirement.priority,
            steps=[
                {"action": "Setup test environment", "expected_result": "Environment ready"},
                {"action": "Execute test logic", "expected_result": "Logic executes successfully"},
                {"action": "Verify results", "expected_result": "Results match expectations"}
            ],
            estimated_duration=60,
            complexity="medium"
        )
    
    def _calculate_coverage_percentage(self, 
                                     requirement: RequirementSpec,
                                     scenarios: List[TestScenario]) -> float:
        """Calculate test coverage percentage"""
        if not requirement.acceptance_criteria:
            return 50.0  # Default coverage
        
        # Simple heuristic: coverage based on number of scenarios vs acceptance criteria
        criteria_count = len(requirement.acceptance_criteria)
        scenario_count = len(scenarios)
        
        # Each scenario should ideally cover at least one acceptance criterion
        coverage = min(100.0, (scenario_count / criteria_count) * 100.0)
        
        return coverage
    
    def _analyze_test_coverage(self, 
                             requirement: RequirementSpec,
                             scenarios: List[TestScenario]) -> Dict[str, Any]:
        """Analyze test coverage comprehensively"""
        analysis = {
            "total_scenarios": len(scenarios),
            "test_types_covered": list(set(s.test_type.value for s in scenarios)),
            "priority_distribution": {},
            "complexity_distribution": {},
            "estimated_total_duration": sum(s.estimated_duration or 0 for s in scenarios),
            "coverage_gaps": [],
            "recommendations": []
        }
        
        # Priority distribution
        for scenario in scenarios:
            priority = scenario.priority
            analysis["priority_distribution"][priority] = analysis["priority_distribution"].get(priority, 0) + 1
        
        # Complexity distribution
        for scenario in scenarios:
            complexity = scenario.complexity
            analysis["complexity_distribution"][complexity] = analysis["complexity_distribution"].get(complexity, 0) + 1
        
        # Identify coverage gaps
        covered_types = set(s.test_type for s in scenarios)
        all_types = set(TestType)
        missing_types = all_types - covered_types
        
        if missing_types:
            analysis["coverage_gaps"].extend([f"Missing {t.value} tests" for t in missing_types])
        
        # Generate recommendations
        if len(scenarios) < len(requirement.acceptance_criteria):
            analysis["recommendations"].append("Consider adding more test scenarios to cover all acceptance criteria")
        
        if TestType.SECURITY not in covered_types and "security" in requirement.description.lower():
            analysis["recommendations"].append("Add security tests based on requirement content")
        
        if TestType.PERFORMANCE not in covered_types and "performance" in requirement.description.lower():
            analysis["recommendations"].append("Add performance tests based on requirement content")
        
        return analysis
    
    async def generate_tests_from_user_story(self, user_story: str, **kwargs) -> TestGenerationResult:
        """Generate tests from a user story string"""
        # Parse user story into requirement
        parsed = self.requirement_parser.parse_user_story(user_story)
        acceptance_criteria = self.requirement_parser.extract_acceptance_criteria(user_story)
        
        requirement = RequirementSpec(
            id=f"us_{hash(user_story) % 10000}",
            title=parsed.get("functionality", "User Story Test")[:50],
            description=user_story,
            acceptance_criteria=acceptance_criteria,
            user_role=parsed.get("user_role"),
            priority=kwargs.get("priority", "medium"),
            category=kwargs.get("category", "functional")
        )
        
        return await self.generate_tests_from_requirement(requirement, **kwargs)
    
    def save_generated_tests(self, 
                           result: TestGenerationResult,
                           output_path: Path,
                           include_metadata: bool = True) -> bool:
        """Save generated tests to file"""
        try:
            if not result.success or not result.generated_code:
                logger.error("Cannot save failed test generation result")
                return False
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write test code
            with open(output_path, 'w', encoding='utf-8') as f:
                if include_metadata:
                    f.write(f'"""\n')
                    f.write(f'Generated Test Suite\n')
                    f.write(f'Requirement ID: {result.requirement_id}\n')
                    f.write(f'Generated at: {datetime.now().isoformat()}\n')
                    f.write(f'Generation time: {result.generation_time:.2f}s\n')
                    f.write(f'AI Confidence: {result.ai_confidence:.2f}\n')
                    f.write(f'Total scenarios: {result.generated_suite.total_scenarios if result.generated_suite else 0}\n')
                    f.write(f'"""\n\n')
                
                f.write(result.generated_code)
            
            logger.info(f"Generated tests saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save generated tests: {str(e)}")
            return False
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get test generation statistics"""
        # This would typically track statistics across multiple generations
        return {
            "total_requirements_processed": 0,  # TODO: Implement tracking
            "total_scenarios_generated": 0,
            "average_generation_time": 0.0,
            "success_rate": 0.0,
            "most_common_test_types": [],
            "framework_usage": {}
        }