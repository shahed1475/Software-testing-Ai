"""
Smart Test Maintenance System

Provides self-healing capabilities for tests, automatically adapting to
selector changes, element updates, and UI modifications.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import re
import hashlib

from .ai_orchestrator import AIOrchestrator, AITaskResult
from .llm_service import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Information about a page element"""
    selector: str
    selector_type: str  # css, xpath, id, class, etc.
    element_purpose: str
    page_url: str
    last_seen: datetime
    success_count: int = 0
    failure_count: int = 0
    alternative_selectors: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    text_content: Optional[str] = None
    position: Optional[Dict[str, int]] = None  # x, y, width, height
    parent_info: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectorHealingResult:
    """Result of selector healing attempt"""
    original_selector: str
    healed_selector: Optional[str]
    alternative_selectors: List[str]
    confidence_score: float
    healing_method: str  # ai, pattern, fallback
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestMaintenanceReport:
    """Report of test maintenance activities"""
    test_file: str
    total_selectors: int
    healed_selectors: int
    failed_healings: int
    new_selectors_added: int
    deprecated_selectors_removed: int
    confidence_scores: List[float]
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class SelectorAnalyzer:
    """Analyzes and categorizes selectors"""
    
    def __init__(self):
        self.selector_patterns = {
            "id": r"^#[\w-]+$",
            "class": r"^\.[\w-]+$",
            "css": r"^[a-zA-Z][\w-]*(\[.*\])?$|^\.[\w-]+|^#[\w-]+",
            "xpath": r"^(//|/).*",
            "data_testid": r"\[data-testid=",
            "data_cy": r"\[data-cy=",
            "aria_label": r"\[aria-label=",
            "text_content": r"text\(\)|contains\(.*text.*\)"
        }
    
    def analyze_selector(self, selector: str) -> Dict[str, Any]:
        """Analyze selector and determine its characteristics"""
        analysis = {
            "type": "unknown",
            "stability": "medium",
            "specificity": "medium",
            "maintainability": "medium",
            "recommendations": []
        }
        
        # Determine selector type
        for selector_type, pattern in self.selector_patterns.items():
            if re.search(pattern, selector, re.IGNORECASE):
                analysis["type"] = selector_type
                break
        
        # Assess stability (how likely it is to break)
        if "data-testid" in selector or "data-cy" in selector:
            analysis["stability"] = "high"
            analysis["maintainability"] = "high"
        elif selector.startswith("#"):
            analysis["stability"] = "high"
            analysis["maintainability"] = "high"
        elif "aria-label" in selector:
            analysis["stability"] = "medium-high"
            analysis["maintainability"] = "high"
        elif selector.count(" ") > 3:  # Deep nesting
            analysis["stability"] = "low"
            analysis["maintainability"] = "low"
            analysis["recommendations"].append("Consider using data attributes or IDs")
        elif ":nth-child" in selector or ":nth-of-type" in selector:
            analysis["stability"] = "low"
            analysis["recommendations"].append("Avoid position-based selectors")
        
        # Assess specificity
        if selector.count(" ") > 2:
            analysis["specificity"] = "high"
        elif selector.count(" ") == 0:
            analysis["specificity"] = "low"
        
        return analysis
    
    def suggest_improvements(self, selector: str, element_info: ElementInfo) -> List[str]:
        """Suggest improvements for a selector"""
        suggestions = []
        analysis = self.analyze_selector(selector)
        
        if analysis["stability"] == "low":
            suggestions.append("Use data-testid or data-cy attributes for better stability")
        
        if ":nth-child" in selector:
            suggestions.append("Replace nth-child with more semantic selectors")
        
        if element_info.attributes:
            if "id" in element_info.attributes and not selector.startswith("#"):
                suggestions.append(f"Consider using ID selector: #{element_info.attributes['id']}")
            
            if "data-testid" in element_info.attributes:
                suggestions.append(f"Use data-testid: [data-testid='{element_info.attributes['data-testid']}']")
        
        if len(selector.split(" ")) > 4:
            suggestions.append("Simplify selector to reduce brittleness")
        
        return suggestions


class SelectorRepository:
    """Repository for storing and managing selector information"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("selector_repository.json")
        self.elements: Dict[str, ElementInfo] = {}
        self.selector_history: Dict[str, List[Dict]] = {}
        self.load_repository()
    
    def add_element(self, element_info: ElementInfo):
        """Add or update element information"""
        key = self._generate_element_key(element_info)
        
        if key in self.elements:
            # Update existing element
            existing = self.elements[key]
            existing.last_seen = element_info.last_seen
            existing.success_count += element_info.success_count
            existing.failure_count += element_info.failure_count
            
            # Merge alternative selectors
            for alt_selector in element_info.alternative_selectors:
                if alt_selector not in existing.alternative_selectors:
                    existing.alternative_selectors.append(alt_selector)
        else:
            self.elements[key] = element_info
        
        self.save_repository()
    
    def get_element(self, selector: str, page_url: str) -> Optional[ElementInfo]:
        """Get element information by selector and page"""
        key = f"{page_url}:{selector}"
        return self.elements.get(key)
    
    def get_alternatives(self, selector: str, page_url: str) -> List[str]:
        """Get alternative selectors for an element"""
        element = self.get_element(selector, page_url)
        return element.alternative_selectors if element else []
    
    def record_selector_change(self, 
                             old_selector: str, 
                             new_selector: str, 
                             page_url: str,
                             reason: str):
        """Record a selector change for historical tracking"""
        key = f"{page_url}:{old_selector}"
        
        if key not in self.selector_history:
            self.selector_history[key] = []
        
        self.selector_history[key].append({
            "old_selector": old_selector,
            "new_selector": new_selector,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        self.save_repository()
    
    def get_selector_history(self, selector: str, page_url: str) -> List[Dict]:
        """Get change history for a selector"""
        key = f"{page_url}:{selector}"
        return self.selector_history.get(key, [])
    
    def cleanup_old_entries(self, days: int = 30):
        """Remove entries older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up elements
        keys_to_remove = []
        for key, element in self.elements.items():
            if element.last_seen < cutoff_date:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.elements[key]
        
        # Clean up history
        for key, history in self.selector_history.items():
            self.selector_history[key] = [
                entry for entry in history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
            ]
        
        self.save_repository()
        logger.info(f"Cleaned up {len(keys_to_remove)} old selector entries")
    
    def _generate_element_key(self, element_info: ElementInfo) -> str:
        """Generate unique key for element"""
        return f"{element_info.page_url}:{element_info.selector}"
    
    def load_repository(self):
        """Load repository from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Load elements
                for key, element_data in data.get("elements", {}).items():
                    element_data["last_seen"] = datetime.fromisoformat(element_data["last_seen"])
                    self.elements[key] = ElementInfo(**element_data)
                
                # Load history
                self.selector_history = data.get("selector_history", {})
                
                logger.info(f"Loaded {len(self.elements)} elements from repository")
                
            except Exception as e:
                logger.error(f"Failed to load selector repository: {str(e)}")
    
    def save_repository(self):
        """Save repository to storage"""
        try:
            data = {
                "elements": {},
                "selector_history": self.selector_history
            }
            
            # Serialize elements
            for key, element in self.elements.items():
                element_dict = {
                    "selector": element.selector,
                    "selector_type": element.selector_type,
                    "element_purpose": element.element_purpose,
                    "page_url": element.page_url,
                    "last_seen": element.last_seen.isoformat(),
                    "success_count": element.success_count,
                    "failure_count": element.failure_count,
                    "alternative_selectors": element.alternative_selectors,
                    "attributes": element.attributes,
                    "text_content": element.text_content,
                    "position": element.position,
                    "parent_info": element.parent_info,
                    "metadata": element.metadata
                }
                data["elements"][key] = element_dict
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save selector repository: {str(e)}")


class SmartTestMaintenance:
    """Main service for smart test maintenance and self-healing"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.ai_orchestrator = AIOrchestrator(llm_provider, config)
        self.selector_analyzer = SelectorAnalyzer()
        self.selector_repository = SelectorRepository()
        self.healing_cache: Dict[str, SelectorHealingResult] = {}
        
        # Configuration
        self.config = config or {}
        self.max_healing_attempts = self.config.get("max_healing_attempts", 3)
        self.healing_confidence_threshold = self.config.get("healing_confidence_threshold", 0.7)
        self.enable_ai_healing = self.config.get("enable_ai_healing", True)
        
        logger.info("Smart Test Maintenance service initialized")
    
    async def heal_selector(self, 
                          failed_selector: str,
                          page_context: Dict[str, Any],
                          attempt_count: int = 0) -> SelectorHealingResult:
        """
        Attempt to heal a failed selector using multiple strategies
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"{page_context.get('page_url', '')}:{failed_selector}"
        if cache_key in self.healing_cache:
            cached_result = self.healing_cache[cache_key]
            # Use cached result if it's recent (within 1 hour)
            if (datetime.now() - cached_result.timestamp).seconds < 3600:
                logger.info(f"Using cached healing result for {failed_selector}")
                return cached_result
        
        try:
            # Step 1: Try repository alternatives
            alternatives = self.selector_repository.get_alternatives(
                failed_selector, 
                page_context.get("page_url", "")
            )
            
            if alternatives:
                logger.info(f"Found {len(alternatives)} alternative selectors in repository")
                result = SelectorHealingResult(
                    original_selector=failed_selector,
                    healed_selector=alternatives[0],
                    alternative_selectors=alternatives,
                    confidence_score=0.8,
                    healing_method="repository",
                    success=True,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                
                self.healing_cache[cache_key] = result
                return result
            
            # Step 2: Try pattern-based healing
            pattern_result = await self._try_pattern_healing(failed_selector, page_context)
            if pattern_result.success and pattern_result.confidence_score >= self.healing_confidence_threshold:
                self.healing_cache[cache_key] = pattern_result
                return pattern_result
            
            # Step 3: Try AI-powered healing
            if self.enable_ai_healing and attempt_count < self.max_healing_attempts:
                ai_result = await self._try_ai_healing(failed_selector, page_context)
                if ai_result.success:
                    self.healing_cache[cache_key] = ai_result
                    return ai_result
            
            # Step 4: Fallback strategies
            fallback_result = await self._try_fallback_healing(failed_selector, page_context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            fallback_result.execution_time = execution_time
            
            self.healing_cache[cache_key] = fallback_result
            return fallback_result
            
        except Exception as e:
            logger.error(f"Error during selector healing: {str(e)}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = SelectorHealingResult(
                original_selector=failed_selector,
                healed_selector=None,
                alternative_selectors=[],
                confidence_score=0.0,
                healing_method="error",
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
            
            return error_result
    
    async def _try_pattern_healing(self, 
                                 failed_selector: str, 
                                 page_context: Dict[str, Any]) -> SelectorHealingResult:
        """Try to heal selector using pattern-based approaches"""
        alternatives = []
        confidence = 0.5
        
        # Strategy 1: Remove fragile parts
        if ":nth-child" in failed_selector:
            # Remove nth-child selectors
            healed = re.sub(r':nth-child\(\d+\)', '', failed_selector)
            alternatives.append(healed)
            confidence = 0.6
        
        # Strategy 2: Generalize class selectors
        if "." in failed_selector and " " in failed_selector:
            # Try using just the last class
            parts = failed_selector.split(" ")
            if parts[-1].startswith("."):
                alternatives.append(parts[-1])
                confidence = 0.5
        
        # Strategy 3: Convert to more stable selectors
        if page_context.get("page_html"):
            html = page_context["page_html"]
            
            # Look for data attributes
            data_testid_match = re.search(r'data-testid="([^"]+)"', html)
            if data_testid_match:
                alternatives.append(f'[data-testid="{data_testid_match.group(1)}"]')
                confidence = 0.8
            
            # Look for unique IDs
            id_match = re.search(r'id="([^"]+)"', html)
            if id_match:
                alternatives.append(f'#{id_match.group(1)}')
                confidence = 0.7
        
        success = len(alternatives) > 0
        healed_selector = alternatives[0] if alternatives else None
        
        return SelectorHealingResult(
            original_selector=failed_selector,
            healed_selector=healed_selector,
            alternative_selectors=alternatives,
            confidence_score=confidence,
            healing_method="pattern",
            success=success
        )
    
    async def _try_ai_healing(self, 
                            failed_selector: str, 
                            page_context: Dict[str, Any]) -> SelectorHealingResult:
        """Try to heal selector using AI"""
        try:
            ai_result = await self.ai_orchestrator.heal_selector(failed_selector, page_context)
            
            if ai_result.success and ai_result.result:
                alternatives = ai_result.result if isinstance(ai_result.result, list) else [ai_result.result]
                
                return SelectorHealingResult(
                    original_selector=failed_selector,
                    healed_selector=alternatives[0] if alternatives else None,
                    alternative_selectors=alternatives,
                    confidence_score=0.8,  # AI results get high confidence
                    healing_method="ai",
                    success=len(alternatives) > 0
                )
            else:
                return SelectorHealingResult(
                    original_selector=failed_selector,
                    healed_selector=None,
                    alternative_selectors=[],
                    confidence_score=0.0,
                    healing_method="ai",
                    success=False,
                    error_message=ai_result.error
                )
                
        except Exception as e:
            return SelectorHealingResult(
                original_selector=failed_selector,
                healed_selector=None,
                alternative_selectors=[],
                confidence_score=0.0,
                healing_method="ai",
                success=False,
                error_message=str(e)
            )
    
    async def _try_fallback_healing(self, 
                                  failed_selector: str, 
                                  page_context: Dict[str, Any]) -> SelectorHealingResult:
        """Try fallback healing strategies"""
        alternatives = []
        
        # Fallback 1: Generic selectors based on element type
        element_purpose = page_context.get("element_purpose", "").lower()
        
        if "button" in element_purpose:
            alternatives.extend(["button", "input[type='button']", "[role='button']"])
        elif "link" in element_purpose:
            alternatives.extend(["a", "[role='link']"])
        elif "input" in element_purpose:
            alternatives.extend(["input", "textarea", "[role='textbox']"])
        elif "submit" in element_purpose:
            alternatives.extend(["input[type='submit']", "button[type='submit']"])
        
        # Fallback 2: Common UI patterns
        if "login" in element_purpose:
            alternatives.extend(["#login", ".login-button", "[data-testid*='login']"])
        elif "search" in element_purpose:
            alternatives.extend(["#search", ".search-input", "[placeholder*='search']"])
        
        success = len(alternatives) > 0
        confidence = 0.3 if success else 0.0
        
        return SelectorHealingResult(
            original_selector=failed_selector,
            healed_selector=alternatives[0] if alternatives else None,
            alternative_selectors=alternatives,
            confidence_score=confidence,
            healing_method="fallback",
            success=success
        )
    
    def record_selector_success(self, 
                              selector: str, 
                              page_url: str,
                              element_info: Optional[Dict] = None):
        """Record successful selector usage"""
        element = ElementInfo(
            selector=selector,
            selector_type=self.selector_analyzer.analyze_selector(selector)["type"],
            element_purpose=element_info.get("purpose", "Unknown") if element_info else "Unknown",
            page_url=page_url,
            last_seen=datetime.now(),
            success_count=1,
            attributes=element_info.get("attributes", {}) if element_info else {}
        )
        
        self.selector_repository.add_element(element)
    
    def record_selector_failure(self, 
                              selector: str, 
                              page_url: str,
                              error_message: str):
        """Record selector failure"""
        existing_element = self.selector_repository.get_element(selector, page_url)
        
        if existing_element:
            existing_element.failure_count += 1
            existing_element.last_seen = datetime.now()
            self.selector_repository.add_element(existing_element)
        else:
            # Create new element with failure
            element = ElementInfo(
                selector=selector,
                selector_type=self.selector_analyzer.analyze_selector(selector)["type"],
                element_purpose="Unknown",
                page_url=page_url,
                last_seen=datetime.now(),
                failure_count=1
            )
            self.selector_repository.add_element(element)
    
    async def maintain_test_file(self, 
                               test_file_path: Path,
                               dry_run: bool = True) -> TestMaintenanceReport:
        """
        Perform maintenance on a test file, updating selectors as needed
        """
        start_time = datetime.now()
        
        try:
            # Read test file
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract selectors from test file
            selectors = self._extract_selectors_from_test(content)
            
            healed_count = 0
            failed_healings = 0
            new_selectors = 0
            confidence_scores = []
            
            updated_content = content
            
            for selector_info in selectors:
                selector = selector_info["selector"]
                line_number = selector_info["line_number"]
                
                # Analyze selector
                analysis = self.selector_analyzer.analyze_selector(selector)
                
                # Check if selector needs healing (low stability)
                if analysis["stability"] == "low":
                    # Try to heal the selector
                    page_context = {
                        "test_name": test_file_path.stem,
                        "element_purpose": selector_info.get("purpose", "Unknown"),
                        "page_url": "test_context"
                    }
                    
                    healing_result = await self.heal_selector(selector, page_context)
                    
                    if healing_result.success and healing_result.confidence_score >= self.healing_confidence_threshold:
                        if not dry_run:
                            # Replace selector in content
                            updated_content = updated_content.replace(
                                selector, 
                                healing_result.healed_selector, 
                                1  # Replace only first occurrence
                            )
                        
                        healed_count += 1
                        confidence_scores.append(healing_result.confidence_score)
                        
                        logger.info(f"Healed selector in {test_file_path}:{line_number}: "
                                  f"{selector} -> {healing_result.healed_selector}")
                    else:
                        failed_healings += 1
                        logger.warning(f"Failed to heal selector in {test_file_path}:{line_number}: {selector}")
            
            # Write updated content if not dry run
            if not dry_run and updated_content != content:
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                logger.info(f"Updated test file: {test_file_path}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestMaintenanceReport(
                test_file=str(test_file_path),
                total_selectors=len(selectors),
                healed_selectors=healed_count,
                failed_healings=failed_healings,
                new_selectors_added=new_selectors,
                deprecated_selectors_removed=0,  # TODO: Implement
                confidence_scores=confidence_scores,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error maintaining test file {test_file_path}: {str(e)}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestMaintenanceReport(
                test_file=str(test_file_path),
                total_selectors=0,
                healed_selectors=0,
                failed_healings=1,
                new_selectors_added=0,
                deprecated_selectors_removed=0,
                confidence_scores=[],
                execution_time=execution_time
            )
    
    def _extract_selectors_from_test(self, content: str) -> List[Dict[str, Any]]:
        """Extract selectors from test file content"""
        selectors = []
        lines = content.split('\n')
        
        # Common patterns for finding selectors in test files
        selector_patterns = [
            r'find_element\([^,]*["\']([^"\']+)["\']',  # Selenium
            r'driver\.find\(["\']([^"\']+)["\']',        # WebDriver
            r'cy\.get\(["\']([^"\']+)["\']',             # Cypress
            r'page\.locator\(["\']([^"\']+)["\']',       # Playwright
            r'\.click\(["\']([^"\']+)["\']',             # Generic click
            r'\.type\(["\']([^"\']+)["\']',              # Generic type
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in selector_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    selectors.append({
                        "selector": match,
                        "line_number": line_num,
                        "purpose": self._infer_element_purpose(line, match)
                    })
        
        return selectors
    
    def _infer_element_purpose(self, line: str, selector: str) -> str:
        """Infer the purpose of an element from the test line"""
        line_lower = line.lower()
        
        if "click" in line_lower:
            return "clickable element"
        elif "type" in line_lower or "send_keys" in line_lower:
            return "input field"
        elif "submit" in line_lower:
            return "submit button"
        elif "login" in line_lower:
            return "login element"
        elif "search" in line_lower:
            return "search element"
        elif "button" in selector.lower():
            return "button"
        elif "input" in selector.lower():
            return "input field"
        else:
            return "unknown element"
    
    def get_maintenance_stats(self) -> Dict[str, Any]:
        """Get maintenance statistics"""
        # Get repository stats
        total_elements = len(self.selector_repository.elements)
        
        # Calculate success rates
        total_successes = sum(elem.success_count for elem in self.selector_repository.elements.values())
        total_failures = sum(elem.failure_count for elem in self.selector_repository.elements.values())
        
        success_rate = total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0
        
        # Healing cache stats
        healing_attempts = len(self.healing_cache)
        successful_healings = sum(1 for result in self.healing_cache.values() if result.success)
        
        healing_success_rate = successful_healings / healing_attempts if healing_attempts > 0 else 0
        
        return {
            "total_tracked_elements": total_elements,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": success_rate,
            "healing_attempts": healing_attempts,
            "successful_healings": successful_healings,
            "healing_success_rate": healing_success_rate,
            "cache_size": len(self.healing_cache)
        }