"""
Cross-Domain Testing Framework

Enables unified testing across Web, API, and Mobile domains
in single test flows with shared context and data.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from pathlib import Path

# Third-party imports for different testing domains
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from appium import webdriver as appium_webdriver
    from appium.webdriver.common.appiumby import AppiumBy
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


class TestDomain(Enum):
    """Test domain types"""
    WEB = "web"
    API = "api"
    MOBILE = "mobile"
    DATABASE = "database"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class DomainContext:
    """Context for a specific testing domain"""
    domain: TestDomain
    config: Dict[str, Any] = field(default_factory=dict)
    driver: Optional[Any] = None
    session: Optional[Any] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def cleanup(self):
        """Clean up domain resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error cleaning up driver: {e}")
        
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error cleaning up session: {e}")


@dataclass
class TestStep:
    """Individual test step within a test case"""
    name: str
    domain: TestDomain
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: Optional[Any] = None
    timeout: int = 30
    retry_count: int = 0
    
    # Execution results
    status: TestStatus = TestStatus.PENDING
    actual_result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    screenshot_path: Optional[str] = None


@dataclass
class UnifiedTestCase:
    """Unified test case spanning multiple domains"""
    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    priority: str = "medium"
    
    # Execution metadata
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    
    def add_step(self, step: TestStep):
        """Add a test step to the test case"""
        self.steps.append(step)
    
    def get_steps_by_domain(self, domain: TestDomain) -> List[TestStep]:
        """Get all steps for a specific domain"""
        return [step for step in self.steps if step.domain == domain]


@dataclass
class TestFlow:
    """Collection of related test cases forming a complete flow"""
    name: str
    description: str
    test_cases: List[UnifiedTestCase] = field(default_factory=list)
    setup_steps: List[TestStep] = field(default_factory=list)
    teardown_steps: List[TestStep] = field(default_factory=list)
    global_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_test_case(self, test_case: UnifiedTestCase):
        """Add a test case to the flow"""
        self.test_cases.append(test_case)


class WebTestExecutor:
    """Executor for web-based test steps"""
    
    def __init__(self, context: DomainContext):
        self.context = context
        self.driver = context.driver
    
    async def execute_step(self, step: TestStep) -> Any:
        """Execute a web test step"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium not available for web testing")
        
        action = step.action.lower()
        params = step.parameters
        
        try:
            if action == "navigate":
                self.driver.get(params["url"])
                return {"url": self.driver.current_url}
            
            elif action == "click":
                element = self._find_element(params)
                element.click()
                return {"clicked": True}
            
            elif action == "type":
                element = self._find_element(params)
                element.clear()
                element.send_keys(params["text"])
                return {"text_entered": params["text"]}
            
            elif action == "get_text":
                element = self._find_element(params)
                text = element.text
                return {"text": text}
            
            elif action == "wait_for_element":
                wait = WebDriverWait(self.driver, step.timeout)
                element = wait.until(
                    EC.presence_of_element_located(self._get_locator(params))
                )
                return {"element_found": True}
            
            elif action == "screenshot":
                screenshot_path = f"screenshots/web_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                return {"screenshot_path": screenshot_path}
            
            else:
                raise ValueError(f"Unknown web action: {action}")
        
        except Exception as e:
            logger.error(f"Web step execution failed: {e}")
            raise
    
    def _find_element(self, params: Dict[str, Any]):
        """Find web element using various locator strategies"""
        locator = self._get_locator(params)
        return self.driver.find_element(*locator)
    
    def _get_locator(self, params: Dict[str, Any]) -> tuple:
        """Convert parameters to Selenium locator"""
        if "id" in params:
            return (By.ID, params["id"])
        elif "xpath" in params:
            return (By.XPATH, params["xpath"])
        elif "css" in params:
            return (By.CSS_SELECTOR, params["css"])
        elif "class_name" in params:
            return (By.CLASS_NAME, params["class_name"])
        elif "name" in params:
            return (By.NAME, params["name"])
        else:
            raise ValueError("No valid locator found in parameters")


class APITestExecutor:
    """Executor for API test steps"""
    
    def __init__(self, context: DomainContext):
        self.context = context
        self.session = context.session or requests.Session()
    
    async def execute_step(self, step: TestStep) -> Any:
        """Execute an API test step"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests library not available for API testing")
        
        action = step.action.lower()
        params = step.parameters
        
        try:
            if action in ["get", "post", "put", "delete", "patch"]:
                return await self._make_request(action, params)
            
            elif action == "validate_response":
                return self._validate_response(params)
            
            elif action == "extract_data":
                return self._extract_data(params)
            
            else:
                raise ValueError(f"Unknown API action: {action}")
        
        except Exception as e:
            logger.error(f"API step execution failed: {e}")
            raise
    
    async def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request"""
        url = params["url"]
        headers = params.get("headers", {})
        data = params.get("data")
        json_data = params.get("json")
        
        # Add authentication if provided
        auth = params.get("auth")
        if auth:
            if auth["type"] == "bearer":
                headers["Authorization"] = f"Bearer {auth['token']}"
            elif auth["type"] == "basic":
                self.session.auth = (auth["username"], auth["password"])
        
        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=data,
            json=json_data,
            timeout=30
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
        }
    
    def _validate_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API response"""
        # This would contain response validation logic
        return {"validation_passed": True}
    
    def _extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from API response"""
        # This would contain data extraction logic
        return {"extracted_data": {}}


class MobileTestExecutor:
    """Executor for mobile test steps"""
    
    def __init__(self, context: DomainContext):
        self.context = context
        self.driver = context.driver
    
    async def execute_step(self, step: TestStep) -> Any:
        """Execute a mobile test step"""
        if not APPIUM_AVAILABLE:
            raise RuntimeError("Appium not available for mobile testing")
        
        action = step.action.lower()
        params = step.parameters
        
        try:
            if action == "tap":
                element = self._find_element(params)
                element.click()
                return {"tapped": True}
            
            elif action == "type":
                element = self._find_element(params)
                element.clear()
                element.send_keys(params["text"])
                return {"text_entered": params["text"]}
            
            elif action == "swipe":
                start_x, start_y = params["start"]
                end_x, end_y = params["end"]
                self.driver.swipe(start_x, start_y, end_x, end_y, params.get("duration", 1000))
                return {"swiped": True}
            
            elif action == "screenshot":
                screenshot_path = f"screenshots/mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                return {"screenshot_path": screenshot_path}
            
            else:
                raise ValueError(f"Unknown mobile action: {action}")
        
        except Exception as e:
            logger.error(f"Mobile step execution failed: {e}")
            raise
    
    def _find_element(self, params: Dict[str, Any]):
        """Find mobile element using various locator strategies"""
        if "id" in params:
            return self.driver.find_element(AppiumBy.ID, params["id"])
        elif "xpath" in params:
            return self.driver.find_element(AppiumBy.XPATH, params["xpath"])
        elif "accessibility_id" in params:
            return self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, params["accessibility_id"])
        else:
            raise ValueError("No valid mobile locator found in parameters")


class CrossDomainTestRunner:
    """Main runner for cross-domain unified tests"""
    
    def __init__(self):
        self.contexts: Dict[TestDomain, DomainContext] = {}
        self.executors: Dict[TestDomain, Any] = {}
        self.results: List[Dict[str, Any]] = []
    
    def setup_domain(self, domain: TestDomain, config: Dict[str, Any]):
        """Setup a testing domain with configuration"""
        context = DomainContext(domain=domain, config=config)
        
        if domain == TestDomain.WEB and SELENIUM_AVAILABLE:
            # Setup web driver
            driver_type = config.get("driver", "chrome").lower()
            if driver_type == "chrome":
                options = webdriver.ChromeOptions()
                if config.get("headless", False):
                    options.add_argument("--headless")
                context.driver = webdriver.Chrome(options=options)
            elif driver_type == "firefox":
                options = webdriver.FirefoxOptions()
                if config.get("headless", False):
                    options.add_argument("--headless")
                context.driver = webdriver.Firefox(options=options)
            
            self.executors[domain] = WebTestExecutor(context)
        
        elif domain == TestDomain.API and REQUESTS_AVAILABLE:
            # Setup API session
            context.session = requests.Session()
            self.executors[domain] = APITestExecutor(context)
        
        elif domain == TestDomain.MOBILE and APPIUM_AVAILABLE:
            # Setup mobile driver
            desired_caps = config.get("capabilities", {})
            appium_server = config.get("server_url", "http://localhost:4723/wd/hub")
            context.driver = appium_webdriver.Remote(appium_server, desired_caps)
            self.executors[domain] = MobileTestExecutor(context)
        
        self.contexts[domain] = context
    
    async def execute_test_case(self, test_case: UnifiedTestCase) -> Dict[str, Any]:
        """Execute a unified test case across multiple domains"""
        logger.info(f"Executing test case: {test_case.name}")
        
        test_case.status = TestStatus.RUNNING
        test_case.start_time = datetime.now()
        
        try:
            for step in test_case.steps:
                await self._execute_step(step, test_case.shared_data)
                
                if step.status == TestStatus.FAILED:
                    test_case.status = TestStatus.FAILED
                    break
            
            if test_case.status == TestStatus.RUNNING:
                test_case.status = TestStatus.PASSED
        
        except Exception as e:
            logger.error(f"Test case execution failed: {e}")
            test_case.status = TestStatus.ERROR
        
        finally:
            test_case.end_time = datetime.now()
            if test_case.start_time:
                test_case.total_execution_time = (
                    test_case.end_time - test_case.start_time
                ).total_seconds()
        
        return self._create_test_result(test_case)
    
    async def execute_test_flow(self, test_flow: TestFlow) -> Dict[str, Any]:
        """Execute a complete test flow"""
        logger.info(f"Executing test flow: {test_flow.name}")
        
        results = {
            "flow_name": test_flow.name,
            "start_time": datetime.now(),
            "test_results": [],
            "setup_results": [],
            "teardown_results": []
        }
        
        try:
            # Execute setup steps
            for step in test_flow.setup_steps:
                step_result = await self._execute_step(step, test_flow.global_data)
                results["setup_results"].append(step_result)
            
            # Execute test cases
            for test_case in test_flow.test_cases:
                # Merge global data with test case data
                test_case.shared_data.update(test_flow.global_data)
                test_result = await self.execute_test_case(test_case)
                results["test_results"].append(test_result)
            
            # Execute teardown steps
            for step in test_flow.teardown_steps:
                step_result = await self._execute_step(step, test_flow.global_data)
                results["teardown_results"].append(step_result)
        
        except Exception as e:
            logger.error(f"Test flow execution failed: {e}")
            results["error"] = str(e)
        
        finally:
            results["end_time"] = datetime.now()
            results["total_execution_time"] = (
                results["end_time"] - results["start_time"]
            ).total_seconds()
        
        return results
    
    async def _execute_step(self, step: TestStep, shared_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step"""
        logger.info(f"Executing step: {step.name} ({step.domain.value})")
        
        step.status = TestStatus.RUNNING
        start_time = datetime.now()
        
        try:
            # Get executor for the domain
            executor = self.executors.get(step.domain)
            if not executor:
                raise RuntimeError(f"No executor available for domain: {step.domain}")
            
            # Replace placeholders in parameters with shared data
            resolved_params = self._resolve_parameters(step.parameters, shared_data)
            step.parameters = resolved_params
            
            # Execute the step
            result = await executor.execute_step(step)
            step.actual_result = result
            step.status = TestStatus.PASSED
            
            # Update shared data with step results
            if isinstance(result, dict):
                shared_data.update(result)
        
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            step.status = TestStatus.FAILED
            step.error_message = str(e)
            step.actual_result = None
        
        finally:
            end_time = datetime.now()
            step.execution_time = (end_time - start_time).total_seconds()
        
        return {
            "step_name": step.name,
            "domain": step.domain.value,
            "status": step.status.value,
            "execution_time": step.execution_time,
            "result": step.actual_result,
            "error": step.error_message
        }
    
    def _resolve_parameters(self, params: Dict[str, Any], shared_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter placeholders with shared data"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract variable name
                var_name = value[2:-1]
                resolved[key] = shared_data.get(var_name, value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _create_test_result(self, test_case: UnifiedTestCase) -> Dict[str, Any]:
        """Create test result summary"""
        return {
            "test_name": test_case.name,
            "status": test_case.status.value,
            "start_time": test_case.start_time,
            "end_time": test_case.end_time,
            "execution_time": test_case.total_execution_time,
            "steps": [
                {
                    "name": step.name,
                    "domain": step.domain.value,
                    "status": step.status.value,
                    "execution_time": step.execution_time,
                    "error": step.error_message
                }
                for step in test_case.steps
            ]
        }
    
    def cleanup(self):
        """Clean up all domain contexts"""
        for context in self.contexts.values():
            context.cleanup()
        
        self.contexts.clear()
        self.executors.clear()


# Example usage and test case builders
class TestCaseBuilder:
    """Builder for creating unified test cases"""
    
    def __init__(self, name: str, description: str):
        self.test_case = UnifiedTestCase(name=name, description=description)
    
    def web_step(self, name: str, action: str, **params) -> 'TestCaseBuilder':
        """Add a web test step"""
        step = TestStep(name=name, domain=TestDomain.WEB, action=action, parameters=params)
        self.test_case.add_step(step)
        return self
    
    def api_step(self, name: str, action: str, **params) -> 'TestCaseBuilder':
        """Add an API test step"""
        step = TestStep(name=name, domain=TestDomain.API, action=action, parameters=params)
        self.test_case.add_step(step)
        return self
    
    def mobile_step(self, name: str, action: str, **params) -> 'TestCaseBuilder':
        """Add a mobile test step"""
        step = TestStep(name=name, domain=TestDomain.MOBILE, action=action, parameters=params)
        self.test_case.add_step(step)
        return self
    
    def build(self) -> UnifiedTestCase:
        """Build the test case"""
        return self.test_case


# Example unified test case
def create_example_unified_test() -> UnifiedTestCase:
    """Create an example unified test case spanning Web, API, and Mobile"""
    return (TestCaseBuilder("User Registration Flow", "Complete user registration across all platforms")
            .web_step("Navigate to registration", "navigate", url="https://example.com/register")
            .web_step("Fill registration form", "type", id="email", text="test@example.com")
            .web_step("Submit form", "click", id="submit-btn")
            .api_step("Verify user created", "get", url="https://api.example.com/users/${user_id}")
            .mobile_step("Open mobile app", "tap", id="app-icon")
            .mobile_step("Login with new account", "type", id="email-field", text="test@example.com")
            .build())