"""
Large Language Model Service

Provides integration with various LLM providers for AI-powered testing features.
Supports OpenAI, Anthropic, and local models.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import aiohttp
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"  # For testing


@dataclass
class LLMRequest:
    """Request structure for LLM calls"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    model: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response structure from LLM calls"""
    content: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key
        self.config = config or {}
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model for this provider"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.base_url = "https://api.openai.com/v1"
        self.default_model = "gpt-4"
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            payload = {
                "model": request.model or self.default_model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data["usage"]["total_tokens"]
                        
                        return LLMResponse(
                            content=content,
                            provider="openai",
                            model=request.model or self.default_model,
                            tokens_used=tokens_used,
                            cost_estimate=self._calculate_cost(tokens_used),
                            timestamp=datetime.now(),
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return LLMResponse(
                            content="",
                            provider="openai",
                            model=request.model or self.default_model,
                            tokens_used=0,
                            cost_estimate=0.0,
                            timestamp=datetime.now(),
                            success=False,
                            error=f"API Error: {response.status}"
                        )
                        
        except Exception as e:
            logger.error(f"OpenAI provider error: {str(e)}")
            return LLMResponse(
                content="",
                provider="openai",
                model=request.model or self.default_model,
                tokens_used=0,
                cost_estimate=0.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def get_default_model(self) -> str:
        return self.default_model
    
    def _calculate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage"""
        # GPT-4 pricing (approximate)
        cost_per_1k_tokens = 0.03
        return (tokens / 1000) * cost_per_1k_tokens


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for testing"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.default_model = "mock-model"
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate mock response"""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        mock_responses = {
            "failure_diagnosis": "This test failed because the element with selector '.submit-button' was not found. This commonly happens when: 1) The page hasn't fully loaded, 2) The selector has changed, or 3) There's a timing issue.",
            "test_generation": "Based on the requirements, here's a generated test case:\n\n```python\ndef test_user_login():\n    # Navigate to login page\n    driver.get('/login')\n    # Enter credentials\n    driver.find_element(By.ID, 'username').send_keys('testuser')\n    driver.find_element(By.ID, 'password').send_keys('password123')\n    # Click login\n    driver.find_element(By.ID, 'login-btn').click()\n    # Verify success\n    assert 'dashboard' in driver.current_url\n```",
            "selector_healing": "The original selector '.old-button' is no longer valid. Suggested alternatives: ['.new-button', '#submit-btn', '[data-testid=\"submit\"]']"
        }
        
        # Simple keyword matching for mock responses
        content = "Mock AI response generated successfully."
        for keyword, response in mock_responses.items():
            if keyword in request.prompt.lower():
                content = response
                break
                
        return LLMResponse(
            content=content,
            provider="mock",
            model=self.default_model,
            tokens_used=100,
            cost_estimate=0.0,
            timestamp=datetime.now(),
            success=True
        )
    
    def get_default_model(self) -> str:
        return self.default_model


class LLMService:
    """Main LLM service orchestrator"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.MOCK, config: Optional[Dict] = None):
        self.provider_type = provider
        self.config = config or {}
        self.provider = self._create_provider()
        self.request_history: List[LLMRequest] = []
        self.response_history: List[LLMResponse] = []
        
    def _create_provider(self) -> BaseLLMProvider:
        """Create appropriate provider instance"""
        if self.provider_type == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY") or self.config.get("openai_api_key")
            return OpenAIProvider(api_key, self.config)
        elif self.provider_type == LLMProvider.MOCK:
            return MockLLMProvider(config=self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider_type}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using configured provider"""
        logger.info(f"Generating LLM response with {self.provider_type.value} provider")
        
        # Store request
        self.request_history.append(request)
        
        # Generate response
        response = await self.provider.generate(request)
        
        # Store response
        self.response_history.append(response)
        
        if response.success:
            logger.info(f"LLM response generated successfully. Tokens: {response.tokens_used}")
        else:
            logger.error(f"LLM generation failed: {response.error}")
            
        return response
    
    async def explain_failure(self, error_message: str, test_context: Dict[str, Any]) -> str:
        """Explain test failure in human language"""
        system_prompt = """You are an expert test automation engineer. Your job is to analyze test failures and explain them in clear, human language that helps developers understand what went wrong and how to fix it."""
        
        prompt = f"""
        Test Failure Analysis:
        
        Error Message: {error_message}
        
        Test Context:
        - Test Name: {test_context.get('test_name', 'Unknown')}
        - Test File: {test_context.get('test_file', 'Unknown')}
        - Browser: {test_context.get('browser', 'Unknown')}
        - Environment: {test_context.get('environment', 'Unknown')}
        - Timestamp: {test_context.get('timestamp', 'Unknown')}
        
        Please provide:
        1. A clear explanation of what went wrong
        2. Possible root causes
        3. Suggested fixes
        4. Prevention strategies
        
        Keep the explanation concise but comprehensive.
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        response = await self.generate(request)
        return response.content if response.success else f"Failed to generate explanation: {response.error}"
    
    async def generate_test_case(self, requirements: str, test_type: str = "functional") -> str:
        """Generate test case from requirements"""
        system_prompt = """You are an expert test automation engineer. Generate comprehensive, maintainable test cases based on requirements. Use best practices for test automation including proper assertions, error handling, and clear test structure."""
        
        prompt = f"""
        Generate a {test_type} test case based on these requirements:
        
        {requirements}
        
        Please provide:
        1. A complete test function with proper naming
        2. Clear setup and teardown if needed
        3. Appropriate assertions
        4. Error handling
        5. Comments explaining the test logic
        
        Use Python with pytest framework and Selenium WebDriver.
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1200,
            temperature=0.4
        )
        
        response = await self.generate(request)
        return response.content if response.success else f"Failed to generate test case: {response.error}"
    
    async def suggest_selector_alternatives(self, failed_selector: str, page_html: str) -> List[str]:
        """Suggest alternative selectors when original fails"""
        system_prompt = """You are an expert in web automation and CSS/XPath selectors. Analyze HTML and suggest robust, maintainable selector alternatives."""
        
        prompt = f"""
        The selector "{failed_selector}" is no longer working.
        
        Page HTML snippet:
        {page_html[:2000]}  # Truncate for token limits
        
        Please suggest 3-5 alternative selectors that would be more robust, in order of preference:
        1. Most specific and reliable
        2. Backup options
        
        Consider:
        - Data attributes (data-testid, data-cy, etc.)
        - Semantic HTML elements
        - Stable class names
        - Unique IDs
        - Text content matching
        
        Return only the selectors, one per line.
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=400,
            temperature=0.2
        )
        
        response = await self.generate(request)
        if response.success:
            # Parse selectors from response
            selectors = [line.strip() for line in response.content.split('\n') if line.strip()]
            return selectors
        else:
            logger.error(f"Failed to generate selector alternatives: {response.error}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_requests = len(self.request_history)
        successful_responses = sum(1 for r in self.response_history if r.success)
        total_tokens = sum(r.tokens_used for r in self.response_history)
        total_cost = sum(r.cost_estimate for r in self.response_history)
        
        return {
            "total_requests": total_requests,
            "successful_responses": successful_responses,
            "success_rate": successful_responses / total_requests if total_requests > 0 else 0,
            "total_tokens_used": total_tokens,
            "estimated_cost": total_cost,
            "provider": self.provider_type.value
        }