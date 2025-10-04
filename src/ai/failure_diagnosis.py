"""
AI-Powered Failure Diagnosis System

Analyzes test failures and provides intelligent, human-readable explanations
to help developers quickly understand and fix issues.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re

from .ai_orchestrator import AIOrchestrator, AITaskResult
from .llm_service import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class FailureContext:
    """Context information for test failure analysis"""
    test_name: str
    test_file: str
    error_message: str
    stack_trace: Optional[str] = None
    test_type: str = "web"  # web, api, unit, integration
    browser: Optional[str] = None
    environment: str = "test"
    url: Optional[str] = None
    screenshot_path: Optional[str] = None
    page_source: Optional[str] = None
    network_logs: Optional[List[Dict]] = None
    console_logs: Optional[List[str]] = None
    test_duration: Optional[float] = None
    retry_count: int = 0
    previous_failures: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosisResult:
    """Result of failure diagnosis"""
    summary: str
    root_cause: str
    suggested_fixes: List[str]
    confidence_score: float
    category: str  # selector, network, timing, assertion, environment, etc.
    severity: str  # critical, high, medium, low
    is_flaky: bool
    related_issues: List[str] = field(default_factory=list)
    debugging_steps: List[str] = field(default_factory=list)
    prevention_tips: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class FailurePatternMatcher:
    """Matches common failure patterns for quick diagnosis"""
    
    def __init__(self):
        self.patterns = {
            "selector_not_found": {
                "regex": r"(NoSuchElementException|ElementNotFound|element not found|could not find element)",
                "category": "selector",
                "severity": "medium",
                "confidence": 0.9
            },
            "timeout": {
                "regex": r"(TimeoutException|timeout|timed out|wait.*timeout)",
                "category": "timing",
                "severity": "medium",
                "confidence": 0.85
            },
            "stale_element": {
                "regex": r"(StaleElementReferenceException|stale element|element is no longer attached)",
                "category": "selector",
                "severity": "medium",
                "confidence": 0.9
            },
            "network_error": {
                "regex": r"(ConnectionError|NetworkError|ERR_NETWORK|ERR_CONNECTION|connection refused)",
                "category": "network",
                "severity": "high",
                "confidence": 0.8
            },
            "assertion_error": {
                "regex": r"(AssertionError|assertion failed|expected.*but was|assert.*failed)",
                "category": "assertion",
                "severity": "high",
                "confidence": 0.95
            },
            "permission_denied": {
                "regex": r"(PermissionError|permission denied|access denied|forbidden)",
                "category": "environment",
                "severity": "high",
                "confidence": 0.9
            },
            "browser_crash": {
                "regex": r"(browser.*crash|chrome.*crash|firefox.*crash|session.*deleted)",
                "category": "environment",
                "severity": "critical",
                "confidence": 0.85
            }
        }
    
    def match_pattern(self, error_message: str, stack_trace: str = "") -> Optional[Dict]:
        """Match error against known patterns"""
        combined_text = f"{error_message} {stack_trace}".lower()
        
        for pattern_name, pattern_info in self.patterns.items():
            if re.search(pattern_info["regex"], combined_text, re.IGNORECASE):
                return {
                    "pattern": pattern_name,
                    "category": pattern_info["category"],
                    "severity": pattern_info["severity"],
                    "confidence": pattern_info["confidence"]
                }
        
        return None


class FlakynessDetector:
    """Detects if a test failure is likely flaky"""
    
    def __init__(self):
        self.flaky_indicators = [
            r"intermittent",
            r"sometimes",
            r"randomly",
            r"race condition",
            r"timing",
            r"network.*unstable",
            r"connection.*reset"
        ]
    
    def analyze_flakiness(self, 
                         failure_context: FailureContext,
                         historical_data: Optional[List[Dict]] = None) -> Tuple[bool, float, List[str]]:
        """
        Analyze if failure is likely flaky
        Returns: (is_flaky, confidence_score, reasons)
        """
        reasons = []
        flaky_score = 0.0
        
        # Check error message for flaky indicators
        error_text = failure_context.error_message.lower()
        for indicator in self.flaky_indicators:
            if re.search(indicator, error_text):
                reasons.append(f"Error message contains flaky indicator: '{indicator}'")
                flaky_score += 0.2
        
        # Check retry count
        if failure_context.retry_count > 0:
            reasons.append(f"Test was retried {failure_context.retry_count} times")
            flaky_score += min(failure_context.retry_count * 0.15, 0.3)
        
        # Check previous failures
        if len(failure_context.previous_failures) > 0:
            unique_errors = len(set(failure_context.previous_failures))
            if unique_errors > 1:
                reasons.append(f"Test has {unique_errors} different failure patterns")
                flaky_score += 0.25
        
        # Check timing-related failures
        if any(keyword in error_text for keyword in ["timeout", "timing", "wait"]):
            reasons.append("Failure involves timing/timeout issues")
            flaky_score += 0.2
        
        # Analyze historical data if available
        if historical_data:
            success_rate = self._calculate_success_rate(historical_data)
            if 0.3 < success_rate < 0.9:  # Intermittent failures
                reasons.append(f"Historical success rate is {success_rate:.1%} (indicates flakiness)")
                flaky_score += 0.3
        
        # Network-related failures are often flaky
        if any(keyword in error_text for keyword in ["network", "connection", "dns"]):
            reasons.append("Network-related failures are often flaky")
            flaky_score += 0.15
        
        is_flaky = flaky_score > 0.4
        confidence = min(flaky_score, 1.0)
        
        return is_flaky, confidence, reasons
    
    def _calculate_success_rate(self, historical_data: List[Dict]) -> float:
        """Calculate success rate from historical test data"""
        if not historical_data:
            return 1.0
        
        total_runs = len(historical_data)
        successful_runs = sum(1 for run in historical_data if run.get("status") == "passed")
        
        return successful_runs / total_runs if total_runs > 0 else 1.0


class FailureDiagnosisService:
    """Main service for AI-powered failure diagnosis"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.ai_orchestrator = AIOrchestrator(llm_provider, config)
        self.pattern_matcher = FailurePatternMatcher()
        self.flakiness_detector = FlakynessDetector()
        self.diagnosis_cache: Dict[str, DiagnosisResult] = {}
        
        logger.info("Failure Diagnosis Service initialized")
    
    async def diagnose_failure(self, 
                             failure_context: FailureContext,
                             use_cache: bool = True,
                             historical_data: Optional[List[Dict]] = None) -> DiagnosisResult:
        """
        Perform comprehensive failure diagnosis
        """
        start_time = datetime.now()
        
        # Generate cache key
        cache_key = self._generate_cache_key(failure_context)
        
        # Check cache first
        if use_cache and cache_key in self.diagnosis_cache:
            logger.info(f"Using cached diagnosis for {failure_context.test_name}")
            return self.diagnosis_cache[cache_key]
        
        try:
            # Step 1: Quick pattern matching
            pattern_match = self.pattern_matcher.match_pattern(
                failure_context.error_message,
                failure_context.stack_trace or ""
            )
            
            # Step 2: Flakiness analysis
            is_flaky, flaky_confidence, flaky_reasons = self.flakiness_detector.analyze_flakiness(
                failure_context, historical_data
            )
            
            # Step 3: Prepare context for AI analysis
            ai_context = self._prepare_ai_context(failure_context, pattern_match, is_flaky)
            
            # Step 4: Get AI diagnosis
            ai_result = await self.ai_orchestrator.diagnose_failure(
                failure_context.error_message,
                ai_context
            )
            
            # Step 5: Combine results
            diagnosis = self._combine_analysis_results(
                failure_context,
                pattern_match,
                is_flaky,
                flaky_reasons,
                ai_result,
                start_time
            )
            
            # Cache the result
            if use_cache:
                self.diagnosis_cache[cache_key] = diagnosis
            
            logger.info(f"Diagnosis completed for {failure_context.test_name} in {diagnosis.execution_time:.2f}s")
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error during failure diagnosis: {str(e)}")
            
            # Return basic diagnosis on error
            execution_time = (datetime.now() - start_time).total_seconds()
            return DiagnosisResult(
                summary=f"Failed to analyze: {str(e)}",
                root_cause="Analysis error occurred",
                suggested_fixes=["Check logs for more details", "Retry the analysis"],
                confidence_score=0.1,
                category="unknown",
                severity="medium",
                is_flaky=False,
                execution_time=execution_time
            )
    
    def _generate_cache_key(self, failure_context: FailureContext) -> str:
        """Generate cache key for failure context"""
        key_components = [
            failure_context.test_name,
            failure_context.error_message,
            failure_context.test_type,
            str(failure_context.retry_count)
        ]
        return "|".join(key_components)
    
    def _prepare_ai_context(self, 
                          failure_context: FailureContext,
                          pattern_match: Optional[Dict],
                          is_flaky: bool) -> Dict[str, Any]:
        """Prepare context for AI analysis"""
        context = {
            "test_name": failure_context.test_name,
            "test_file": failure_context.test_file,
            "test_type": failure_context.test_type,
            "environment": failure_context.environment,
            "browser": failure_context.browser or "Unknown",
            "url": failure_context.url or "Unknown",
            "stack_trace": failure_context.stack_trace or "Not available",
            "screenshot_path": failure_context.screenshot_path,
            "retry_count": failure_context.retry_count,
            "test_duration": failure_context.test_duration,
            "is_likely_flaky": is_flaky
        }
        
        # Add pattern match info if available
        if pattern_match:
            context["pattern_category"] = pattern_match["category"]
            context["pattern_severity"] = pattern_match["severity"]
            context["pattern_confidence"] = pattern_match["confidence"]
        
        # Add console logs if available
        if failure_context.console_logs:
            context["console_logs"] = "\n".join(failure_context.console_logs[-10:])  # Last 10 logs
        
        # Add network logs summary if available
        if failure_context.network_logs:
            failed_requests = [log for log in failure_context.network_logs 
                             if log.get("status", 200) >= 400]
            if failed_requests:
                context["failed_network_requests"] = len(failed_requests)
                context["network_errors"] = [f"{req.get('url', 'Unknown')}: {req.get('status', 'Unknown')}" 
                                           for req in failed_requests[:5]]
        
        # Add page state info
        if failure_context.page_source:
            # Extract useful info from page source
            context["page_state"] = self._extract_page_state_info(failure_context.page_source)
        
        return context
    
    def _extract_page_state_info(self, page_source: str) -> str:
        """Extract useful information from page source"""
        info_parts = []
        
        # Check for error messages in page
        error_patterns = [
            r'<div[^>]*error[^>]*>(.*?)</div>',
            r'<span[^>]*error[^>]*>(.*?)</span>',
            r'<p[^>]*error[^>]*>(.*?)</p>'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
            if matches:
                info_parts.append(f"Page errors found: {', '.join(matches[:3])}")
        
        # Check for loading states
        if "loading" in page_source.lower():
            info_parts.append("Page appears to be in loading state")
        
        # Check for JavaScript errors
        if "javascript" in page_source.lower() and "error" in page_source.lower():
            info_parts.append("Possible JavaScript errors detected")
        
        return "; ".join(info_parts) if info_parts else "No specific issues detected in page state"
    
    def _combine_analysis_results(self,
                                failure_context: FailureContext,
                                pattern_match: Optional[Dict],
                                is_flaky: bool,
                                flaky_reasons: List[str],
                                ai_result: AITaskResult,
                                start_time: datetime) -> DiagnosisResult:
        """Combine all analysis results into final diagnosis"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Default values
        category = "unknown"
        severity = "medium"
        confidence_score = 0.5
        
        # Use pattern match results if available
        if pattern_match:
            category = pattern_match["category"]
            severity = pattern_match["severity"]
            confidence_score = pattern_match["confidence"]
        
        # Parse AI result if successful
        summary = "Analysis failed"
        root_cause = "Unable to determine root cause"
        suggested_fixes = ["Check error logs", "Retry the test"]
        debugging_steps = []
        prevention_tips = []
        
        if ai_result.success and ai_result.result:
            try:
                # Try to parse structured response
                ai_content = ai_result.result
                
                # Extract sections using simple parsing
                lines = ai_content.split('\n')
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Identify sections
                    if line.lower().startswith('summary:'):
                        current_section = 'summary'
                        summary = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('root cause:'):
                        current_section = 'root_cause'
                        root_cause = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('suggested fixes:'):
                        current_section = 'fixes'
                        suggested_fixes = []
                    elif line.lower().startswith('debugging steps:'):
                        current_section = 'debugging'
                        debugging_steps = []
                    elif line.lower().startswith('prevention:'):
                        current_section = 'prevention'
                        prevention_tips = []
                    elif line.startswith('-') or line.startswith('•'):
                        # List item
                        item = line[1:].strip()
                        if current_section == 'fixes':
                            suggested_fixes.append(item)
                        elif current_section == 'debugging':
                            debugging_steps.append(item)
                        elif current_section == 'prevention':
                            prevention_tips.append(item)
                
                # Increase confidence if AI analysis was successful
                confidence_score = min(confidence_score + 0.2, 1.0)
                
            except Exception as e:
                logger.warning(f"Failed to parse AI response: {str(e)}")
                # Use raw AI response as summary
                summary = ai_result.result[:200] + "..." if len(ai_result.result) > 200 else ai_result.result
        
        # Add flakiness information
        if is_flaky:
            summary += f" (Likely flaky test - {', '.join(flaky_reasons[:2])})"
            prevention_tips.extend([
                "Consider adding explicit waits",
                "Review test for race conditions",
                "Add retry logic for flaky scenarios"
            ])
        
        # Ensure we have some suggested fixes
        if not suggested_fixes:
            if pattern_match:
                pattern_name = pattern_match.get("pattern", "")
                if "selector" in pattern_name:
                    suggested_fixes = [
                        "Update element selector",
                        "Add explicit wait for element",
                        "Check if element exists before interaction"
                    ]
                elif "timeout" in pattern_name:
                    suggested_fixes = [
                        "Increase timeout duration",
                        "Add explicit waits",
                        "Check for slow loading elements"
                    ]
                elif "network" in pattern_name:
                    suggested_fixes = [
                        "Check network connectivity",
                        "Verify API endpoints",
                        "Add network error handling"
                    ]
        
        return DiagnosisResult(
            summary=summary,
            root_cause=root_cause,
            suggested_fixes=suggested_fixes,
            confidence_score=confidence_score,
            category=category,
            severity=severity,
            is_flaky=is_flaky,
            related_issues=flaky_reasons if is_flaky else [],
            debugging_steps=debugging_steps,
            prevention_tips=prevention_tips,
            execution_time=execution_time
        )
    
    def get_diagnosis_stats(self) -> Dict[str, Any]:
        """Get statistics about diagnosis performance"""
        if not self.diagnosis_cache:
            return {"total_diagnoses": 0}
        
        diagnoses = list(self.diagnosis_cache.values())
        
        # Category breakdown
        categories = {}
        severities = {}
        flaky_count = 0
        
        for diagnosis in diagnoses:
            # Count categories
            categories[diagnosis.category] = categories.get(diagnosis.category, 0) + 1
            
            # Count severities
            severities[diagnosis.severity] = severities.get(diagnosis.severity, 0) + 1
            
            # Count flaky tests
            if diagnosis.is_flaky:
                flaky_count += 1
        
        avg_confidence = sum(d.confidence_score for d in diagnoses) / len(diagnoses)
        avg_execution_time = sum(d.execution_time for d in diagnoses) / len(diagnoses)
        
        return {
            "total_diagnoses": len(diagnoses),
            "category_breakdown": categories,
            "severity_breakdown": severities,
            "flaky_tests": flaky_count,
            "flaky_percentage": (flaky_count / len(diagnoses)) * 100,
            "average_confidence": avg_confidence,
            "average_execution_time": avg_execution_time,
            "cache_size": len(self.diagnosis_cache)
        }
    
    def clear_cache(self):
        """Clear diagnosis cache"""
        self.diagnosis_cache.clear()
        logger.info("Diagnosis cache cleared")