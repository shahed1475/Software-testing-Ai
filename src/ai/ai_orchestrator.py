"""
AI Orchestrator

Coordinates all AI-powered testing features including failure diagnosis,
test generation, selector healing, risk assessment, and bug reporting.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .llm_service import LLMService, LLMRequest, LLMProvider
from .prompt_manager import PromptManager, PromptCategory

logger = logging.getLogger(__name__)


@dataclass
class AITaskResult:
    """Result from an AI-powered task"""
    task_type: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AIOrchestrator:
    """Main orchestrator for AI-powered testing features"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.config = config or {}
        self.llm_service = LLMService(llm_provider, config)
        self.prompt_manager = PromptManager()
        self.task_history: List[AITaskResult] = []
        
        # Feature flags
        self.features_enabled = {
            "failure_diagnosis": True,
            "test_generation": True,
            "selector_healing": True,
            "risk_assessment": True,
            "bug_reporting": True
        }
        
        logger.info(f"AI Orchestrator initialized with {llm_provider.value} provider")
    
    async def diagnose_failure(self, 
                             error_message: str,
                             test_context: Dict[str, Any]) -> AITaskResult:
        """Diagnose test failure and provide human-readable explanation"""
        start_time = datetime.now()
        
        try:
            if not self.features_enabled.get("failure_diagnosis", True):
                return AITaskResult(
                    task_type="failure_diagnosis",
                    success=False,
                    result=None,
                    error="Failure diagnosis feature is disabled"
                )
            
            # Determine the appropriate prompt based on test type
            test_type = test_context.get("test_type", "web")
            prompt_id = f"failure_diagnosis_{test_type}"
            
            # Prepare variables for prompt
            variables = {
                "error_message": error_message,
                "test_name": test_context.get("test_name", "Unknown"),
                "test_file": test_context.get("test_file", "Unknown"),
                "browser": test_context.get("browser", "Unknown"),
                "environment": test_context.get("environment", "Unknown"),
                "url": test_context.get("url", "Unknown"),
                "has_screenshot": "Yes" if test_context.get("screenshot_path") else "No",
                "stack_trace": test_context.get("stack_trace", "Not available"),
                "page_state": test_context.get("page_state", "Not available")
            }
            
            # Get formatted prompt
            prompt_data = self.prompt_manager.get_prompt(prompt_id, variables)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                max_tokens=prompt_data["metadata"].get("max_tokens", 800),
                temperature=prompt_data["metadata"].get("temperature", 0.3)
            )
            
            # Generate response
            response = await self.llm_service.generate(request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AITaskResult(
                task_type="failure_diagnosis",
                success=response.success,
                result=response.content if response.success else None,
                error=response.error if not response.success else None,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate
            )
            
            self.task_history.append(result)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in failure diagnosis: {str(e)}")
            
            result = AITaskResult(
                task_type="failure_diagnosis",
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.task_history.append(result)
            return result
    
    async def generate_test_case(self,
                               requirements: str,
                               test_context: Dict[str, Any]) -> AITaskResult:
        """Generate test case from requirements"""
        start_time = datetime.now()
        
        try:
            if not self.features_enabled.get("test_generation", True):
                return AITaskResult(
                    task_type="test_generation",
                    success=False,
                    result=None,
                    error="Test generation feature is disabled"
                )
            
            # Prepare variables for prompt
            variables = {
                "feature_name": test_context.get("feature_name", "Unknown Feature"),
                "requirements": requirements,
                "app_type": test_context.get("app_type", "web"),
                "framework": test_context.get("framework", "pytest + selenium"),
                "browsers": test_context.get("browsers", "Chrome, Firefox"),
                "environment": test_context.get("environment", "test"),
                "additional_context": test_context.get("additional_context", "")
            }
            
            # Get formatted prompt
            prompt_data = self.prompt_manager.get_prompt("test_generation_functional", variables)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                max_tokens=prompt_data["metadata"].get("max_tokens", 1200),
                temperature=prompt_data["metadata"].get("temperature", 0.4)
            )
            
            # Generate response
            response = await self.llm_service.generate(request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AITaskResult(
                task_type="test_generation",
                success=response.success,
                result=response.content if response.success else None,
                error=response.error if not response.success else None,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate
            )
            
            self.task_history.append(result)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in test generation: {str(e)}")
            
            result = AITaskResult(
                task_type="test_generation",
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.task_history.append(result)
            return result
    
    async def heal_selector(self,
                          failed_selector: str,
                          page_context: Dict[str, Any]) -> AITaskResult:
        """Suggest alternative selectors when original fails"""
        start_time = datetime.now()
        
        try:
            if not self.features_enabled.get("selector_healing", True):
                return AITaskResult(
                    task_type="selector_healing",
                    success=False,
                    result=None,
                    error="Selector healing feature is disabled"
                )
            
            # Prepare variables for prompt
            variables = {
                "failed_selector": failed_selector,
                "test_name": page_context.get("test_name", "Unknown"),
                "element_purpose": page_context.get("element_purpose", "Unknown element"),
                "last_success_date": page_context.get("last_success_date", "Unknown"),
                "page_html": page_context.get("page_html", "HTML not available"),
                "page_url": page_context.get("page_url", "URL not available")
            }
            
            # Get formatted prompt
            prompt_data = self.prompt_manager.get_prompt("selector_healing_web", variables)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                max_tokens=prompt_data["metadata"].get("max_tokens", 600),
                temperature=prompt_data["metadata"].get("temperature", 0.2)
            )
            
            # Generate response
            response = await self.llm_service.generate(request)
            
            # Parse selectors from response
            selectors = []
            if response.success:
                lines = response.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract selector (before the first ' - ' if present)
                        if ' - ' in line:
                            selector = line.split(' - ')[0].strip()
                            if selector.startswith('`') and selector.endswith('`'):
                                selector = selector[1:-1]  # Remove backticks
                            selectors.append(selector)
                        elif line.startswith(('.', '#', '[', '//')):
                            selectors.append(line)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AITaskResult(
                task_type="selector_healing",
                success=response.success,
                result=selectors if response.success else None,
                error=response.error if not response.success else None,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate
            )
            
            self.task_history.append(result)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in selector healing: {str(e)}")
            
            result = AITaskResult(
                task_type="selector_healing",
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.task_history.append(result)
            return result
    
    async def assess_risk(self,
                        change_context: Dict[str, Any]) -> AITaskResult:
        """Assess testing risk based on code changes"""
        start_time = datetime.now()
        
        try:
            if not self.features_enabled.get("risk_assessment", True):
                return AITaskResult(
                    task_type="risk_assessment",
                    success=False,
                    result=None,
                    error="Risk assessment feature is disabled"
                )
            
            # Prepare variables for prompt
            variables = {
                "changed_files": change_context.get("changed_files", []),
                "diff_summary": change_context.get("diff_summary", "No diff available"),
                "change_type": change_context.get("change_type", "Unknown"),
                "author": change_context.get("author", "Unknown"),
                "branch": change_context.get("branch", "Unknown"),
                "available_tests": change_context.get("available_tests", []),
                "recent_failures": change_context.get("recent_failures", []),
                "change_frequency": change_context.get("change_frequency", "Unknown")
            }
            
            # Get formatted prompt
            prompt_data = self.prompt_manager.get_prompt("risk_assessment_changes", variables)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                max_tokens=prompt_data["metadata"].get("max_tokens", 800),
                temperature=prompt_data["metadata"].get("temperature", 0.3)
            )
            
            # Generate response
            response = await self.llm_service.generate(request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AITaskResult(
                task_type="risk_assessment",
                success=response.success,
                result=response.content if response.success else None,
                error=response.error if not response.success else None,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate
            )
            
            self.task_history.append(result)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in risk assessment: {str(e)}")
            
            result = AITaskResult(
                task_type="risk_assessment",
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.task_history.append(result)
            return result
    
    async def generate_bug_report(self,
                                failure_context: Dict[str, Any]) -> AITaskResult:
        """Generate comprehensive bug report from test failure"""
        start_time = datetime.now()
        
        try:
            if not self.features_enabled.get("bug_reporting", True):
                return AITaskResult(
                    task_type="bug_reporting",
                    success=False,
                    result=None,
                    error="Bug reporting feature is disabled"
                )
            
            # Prepare variables for prompt
            variables = {
                "test_name": failure_context.get("test_name", "Unknown Test"),
                "error_message": failure_context.get("error_message", "No error message"),
                "environment": failure_context.get("environment", "Unknown"),
                "browser": failure_context.get("browser", "Unknown"),
                "build_version": failure_context.get("build_version", "Unknown"),
                "timestamp": failure_context.get("timestamp", datetime.now().isoformat()),
                "test_steps": failure_context.get("test_steps", "Steps not available"),
                "expected_result": failure_context.get("expected_result", "Not specified"),
                "actual_result": failure_context.get("actual_result", "Not specified"),
                "screenshots": failure_context.get("screenshots", "None"),
                "logs": failure_context.get("logs", "None"),
                "network_logs": failure_context.get("network_logs", "None")
            }
            
            # Get formatted prompt
            prompt_data = self.prompt_manager.get_prompt("bug_report_generation", variables)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                max_tokens=prompt_data["metadata"].get("max_tokens", 1000),
                temperature=prompt_data["metadata"].get("temperature", 0.4)
            )
            
            # Generate response
            response = await self.llm_service.generate(request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AITaskResult(
                task_type="bug_reporting",
                success=response.success,
                result=response.content if response.success else None,
                error=response.error if not response.success else None,
                execution_time=execution_time,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate
            )
            
            self.task_history.append(result)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in bug report generation: {str(e)}")
            
            result = AITaskResult(
                task_type="bug_reporting",
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            self.task_history.append(result)
            return result
    
    async def batch_process(self, tasks: List[Dict[str, Any]]) -> List[AITaskResult]:
        """Process multiple AI tasks in batch"""
        results = []
        
        # Process tasks concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def process_task(task):
            async with semaphore:
                task_type = task.get("type")
                
                if task_type == "failure_diagnosis":
                    return await self.diagnose_failure(
                        task.get("error_message", ""),
                        task.get("context", {})
                    )
                elif task_type == "test_generation":
                    return await self.generate_test_case(
                        task.get("requirements", ""),
                        task.get("context", {})
                    )
                elif task_type == "selector_healing":
                    return await self.heal_selector(
                        task.get("failed_selector", ""),
                        task.get("context", {})
                    )
                elif task_type == "risk_assessment":
                    return await self.assess_risk(task.get("context", {}))
                elif task_type == "bug_reporting":
                    return await self.generate_bug_report(task.get("context", {}))
                else:
                    return AITaskResult(
                        task_type=task_type,
                        success=False,
                        result=None,
                        error=f"Unknown task type: {task_type}"
                    )
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[process_task(task) for task in tasks])
        
        return results
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of AI features"""
        return self.features_enabled.copy()
    
    def enable_feature(self, feature_name: str):
        """Enable an AI feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = True
            logger.info(f"Enabled AI feature: {feature_name}")
        else:
            logger.warning(f"Unknown AI feature: {feature_name}")
    
    def disable_feature(self, feature_name: str):
        """Disable an AI feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = False
            logger.info(f"Disabled AI feature: {feature_name}")
        else:
            logger.warning(f"Unknown AI feature: {feature_name}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        total_tasks = len(self.task_history)
        successful_tasks = sum(1 for task in self.task_history if task.success)
        
        # Group by task type
        task_stats = {}
        for task in self.task_history:
            task_type = task.task_type
            if task_type not in task_stats:
                task_stats[task_type] = {"total": 0, "successful": 0, "total_time": 0.0}
            
            task_stats[task_type]["total"] += 1
            if task.success:
                task_stats[task_type]["successful"] += 1
            task_stats[task_type]["total_time"] += task.execution_time
        
        # Calculate averages
        for stats in task_stats.values():
            if stats["total"] > 0:
                stats["success_rate"] = stats["successful"] / stats["total"]
                stats["avg_time"] = stats["total_time"] / stats["total"]
        
        # Get LLM service stats
        llm_stats = self.llm_service.get_usage_stats()
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "overall_success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "task_breakdown": task_stats,
            "features_enabled": self.features_enabled,
            "llm_stats": llm_stats,
            "total_cost_estimate": sum(task.cost_estimate for task in self.task_history)
        }