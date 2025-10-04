"""
Prompt Management System

Manages AI prompts with versioning, templating, and optimization capabilities.
Provides structured prompts for different AI-powered testing features.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml

logger = logging.getLogger(__name__)


class PromptCategory(Enum):
    """Categories of prompts for different AI features"""
    FAILURE_DIAGNOSIS = "failure_diagnosis"
    TEST_GENERATION = "test_generation"
    SELECTOR_HEALING = "selector_healing"
    RISK_ASSESSMENT = "risk_assessment"
    BUG_REPORTING = "bug_reporting"
    CODE_ANALYSIS = "code_analysis"


@dataclass
class PromptTemplate:
    """Template structure for AI prompts"""
    id: str
    category: PromptCategory
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    variables: List[str]
    version: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    examples: List[Dict[str, str]]
    metadata: Dict[str, Any]


class PromptManager:
    """Manages AI prompts with templating and versioning"""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path("src/ai/prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, PromptTemplate] = {}
        self.load_default_prompts()
    
    def load_default_prompts(self):
        """Load default prompt templates"""
        default_prompts = self._get_default_prompts()
        for prompt in default_prompts:
            self.templates[prompt.id] = prompt
            
    def _get_default_prompts(self) -> List[PromptTemplate]:
        """Define default prompt templates"""
        return [
            # Failure Diagnosis Prompts
            PromptTemplate(
                id="failure_diagnosis_web",
                category=PromptCategory.FAILURE_DIAGNOSIS,
                name="Web Test Failure Diagnosis",
                description="Diagnose web automation test failures",
                system_prompt="""You are an expert test automation engineer specializing in web testing. 
                Your job is to analyze test failures and provide clear, actionable explanations that help developers 
                understand what went wrong and how to fix it. Focus on common web testing issues like timing, 
                selectors, browser compatibility, and environmental factors.""",
                user_prompt_template="""
                Analyze this web test failure:
                
                **Error Message:** {error_message}
                **Test Details:**
                - Test Name: {test_name}
                - Test File: {test_file}
                - Browser: {browser}
                - Environment: {environment}
                - URL: {url}
                - Screenshot Available: {has_screenshot}
                
                **Stack Trace:**
                {stack_trace}
                
                **Page State:**
                {page_state}
                
                Please provide:
                1. **Root Cause Analysis**: What exactly went wrong?
                2. **Common Scenarios**: Why does this typically happen?
                3. **Immediate Fix**: How to resolve this specific failure?
                4. **Prevention Strategy**: How to prevent similar failures?
                5. **Test Improvement**: Suggestions to make the test more robust?
                
                Keep explanations clear and actionable for developers of all skill levels.
                """,
                variables=["error_message", "test_name", "test_file", "browser", "environment", 
                          "url", "has_screenshot", "stack_trace", "page_state"],
                version="1.0",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["web", "diagnosis", "selenium", "debugging"],
                examples=[
                    {
                        "input": "ElementNotFound: Unable to locate element with selector '.submit-btn'",
                        "output": "This error indicates the submit button couldn't be found. Common causes include..."
                    }
                ],
                metadata={"max_tokens": 800, "temperature": 0.3}
            ),
            
            # Test Generation Prompts
            PromptTemplate(
                id="test_generation_functional",
                category=PromptCategory.TEST_GENERATION,
                name="Functional Test Generation",
                description="Generate functional test cases from requirements",
                system_prompt="""You are an expert test automation engineer. Generate comprehensive, 
                maintainable test cases based on requirements. Follow testing best practices including 
                proper test structure, clear assertions, error handling, and maintainable selectors. 
                Use the Page Object Model pattern when appropriate.""",
                user_prompt_template="""
                Generate a functional test case based on these requirements:
                
                **Feature:** {feature_name}
                **Requirements:**
                {requirements}
                
                **Test Context:**
                - Application Type: {app_type}
                - Framework: {framework}
                - Browser Support: {browsers}
                - Test Environment: {environment}
                
                **Additional Context:**
                {additional_context}
                
                Please generate:
                1. **Test Function**: Complete test method with proper naming
                2. **Setup/Teardown**: Any necessary setup or cleanup
                3. **Test Steps**: Clear, logical test flow
                4. **Assertions**: Comprehensive validation points
                5. **Error Handling**: Appropriate exception handling
                6. **Comments**: Explanatory comments for complex logic
                
                Use Python with pytest framework and follow PEP 8 conventions.
                Include data-testid selectors for better maintainability.
                """,
                variables=["feature_name", "requirements", "app_type", "framework", 
                          "browsers", "environment", "additional_context"],
                version="1.0",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["test-generation", "functional", "pytest", "automation"],
                examples=[
                    {
                        "input": "User login functionality with email and password",
                        "output": "def test_user_login_with_valid_credentials():\n    # Test implementation..."
                    }
                ],
                metadata={"max_tokens": 1200, "temperature": 0.4}
            ),
            
            # Selector Healing Prompts
            PromptTemplate(
                id="selector_healing_web",
                category=PromptCategory.SELECTOR_HEALING,
                name="Web Selector Healing",
                description="Suggest alternative selectors when original fails",
                system_prompt="""You are an expert in web automation and CSS/XPath selectors. 
                Your job is to analyze HTML and suggest robust, maintainable selector alternatives 
                when original selectors fail. Prioritize stability, uniqueness, and maintainability.""",
                user_prompt_template="""
                The selector "{failed_selector}" is no longer working.
                
                **Context:**
                - Test: {test_name}
                - Element Purpose: {element_purpose}
                - Previous Success: {last_success_date}
                
                **Current Page HTML:**
                ```html
                {page_html}
                ```
                
                **Page URL:** {page_url}
                
                Please suggest 5 alternative selectors in order of preference:
                1. **Most Robust**: Highest reliability and maintainability
                2. **Backup Options**: Good alternatives if primary fails
                3. **Fallback Options**: Last resort selectors
                
                Consider:
                - Data attributes (data-testid, data-cy, data-qa)
                - Semantic HTML elements and ARIA attributes
                - Stable class names and IDs
                - Text content and labels
                - Structural relationships (parent/child)
                
                Format: Return each selector on a new line with explanation:
                `selector` - Explanation of why this selector is reliable
                """,
                variables=["failed_selector", "test_name", "element_purpose", "last_success_date",
                          "page_html", "page_url"],
                version="1.0",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["selector-healing", "web", "maintenance", "css", "xpath"],
                examples=[
                    {
                        "input": "Failed selector: .old-submit-btn",
                        "output": "[data-testid='submit-button'] - Most reliable using test-specific attribute"
                    }
                ],
                metadata={"max_tokens": 600, "temperature": 0.2}
            ),
            
            # Risk Assessment Prompts
            PromptTemplate(
                id="risk_assessment_changes",
                category=PromptCategory.RISK_ASSESSMENT,
                name="Code Change Risk Assessment",
                description="Assess testing risk based on code changes",
                system_prompt="""You are an expert software engineer and test strategist. 
                Analyze code changes to assess testing risk and recommend which tests should be run. 
                Consider impact radius, change complexity, and historical failure patterns.""",
                user_prompt_template="""
                Analyze the testing risk for these code changes:
                
                **Changed Files:**
                {changed_files}
                
                **Diff Summary:**
                {diff_summary}
                
                **Change Type:** {change_type}
                **Author:** {author}
                **Branch:** {branch}
                
                **Available Test Suites:**
                {available_tests}
                
                **Historical Data:**
                - Recent Failures: {recent_failures}
                - Change Frequency: {change_frequency}
                
                Please provide:
                1. **Risk Level**: HIGH/MEDIUM/LOW with justification
                2. **Impact Analysis**: What areas are affected?
                3. **Recommended Tests**: Which specific tests to run?
                4. **Test Priority**: Order of test execution
                5. **Risk Mitigation**: Additional testing recommendations
                
                Focus on efficiency - run only necessary tests while maintaining confidence.
                """,
                variables=["changed_files", "diff_summary", "change_type", "author", "branch",
                          "available_tests", "recent_failures", "change_frequency"],
                version="1.0",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["risk-assessment", "ci-cd", "test-selection", "impact-analysis"],
                examples=[
                    {
                        "input": "Modified authentication service",
                        "output": "Risk Level: HIGH - Authentication changes affect all user flows..."
                    }
                ],
                metadata={"max_tokens": 800, "temperature": 0.3}
            ),
            
            # Bug Reporting Prompts
            PromptTemplate(
                id="bug_report_generation",
                category=PromptCategory.BUG_REPORTING,
                name="Automated Bug Report Generation",
                description="Generate comprehensive bug reports from test failures",
                system_prompt="""You are an expert QA engineer who creates detailed, actionable bug reports. 
                Transform test failure information into comprehensive bug reports that developers can 
                easily understand and reproduce. Include all necessary technical details while keeping 
                the report clear and structured.""",
                user_prompt_template="""
                Create a bug report for this test failure:
                
                **Test Failure Details:**
                - Test: {test_name}
                - Error: {error_message}
                - Environment: {environment}
                - Browser: {browser}
                - Build: {build_version}
                - Timestamp: {timestamp}
                
                **Reproduction Steps:**
                {test_steps}
                
                **Expected vs Actual:**
                - Expected: {expected_result}
                - Actual: {actual_result}
                
                **Additional Context:**
                - Screenshots: {screenshots}
                - Logs: {logs}
                - Network Activity: {network_logs}
                
                Generate a structured bug report with:
                1. **Title**: Clear, descriptive bug title
                2. **Summary**: Brief description of the issue
                3. **Environment**: Technical environment details
                4. **Steps to Reproduce**: Clear reproduction steps
                5. **Expected Result**: What should happen
                6. **Actual Result**: What actually happened
                7. **Severity**: Bug severity assessment
                8. **Priority**: Suggested priority level
                9. **Labels**: Relevant tags for categorization
                10. **Attachments**: List of supporting files
                
                Format for GitHub Issues or Jira tickets.
                """,
                variables=["test_name", "error_message", "environment", "browser", "build_version",
                          "timestamp", "test_steps", "expected_result", "actual_result", 
                          "screenshots", "logs", "network_logs"],
                version="1.0",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["bug-reporting", "github", "jira", "automation", "qa"],
                examples=[
                    {
                        "input": "Login test failed with timeout error",
                        "output": "# Login Button Not Responding on Chrome\n\n## Summary\nLogin button..."
                    }
                ],
                metadata={"max_tokens": 1000, "temperature": 0.4}
            )
        ]
    
    def get_prompt(self, prompt_id: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Get formatted prompt with variables substituted"""
        if prompt_id not in self.templates:
            raise ValueError(f"Prompt template '{prompt_id}' not found")
        
        template = self.templates[prompt_id]
        
        # Validate required variables
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            logger.warning(f"Missing variables for prompt '{prompt_id}': {missing_vars}")
            # Fill missing variables with empty strings
            for var in missing_vars:
                variables[var] = ""
        
        # Format the prompt template
        try:
            formatted_prompt = template.user_prompt_template.format(**variables)
            return {
                "system_prompt": template.system_prompt,
                "user_prompt": formatted_prompt,
                "metadata": template.metadata
            }
        except KeyError as e:
            raise ValueError(f"Error formatting prompt '{prompt_id}': Missing variable {e}")
    
    def add_prompt(self, template: PromptTemplate):
        """Add a new prompt template"""
        self.templates[template.id] = template
        logger.info(f"Added prompt template: {template.id}")
    
    def update_prompt(self, prompt_id: str, **updates):
        """Update an existing prompt template"""
        if prompt_id not in self.templates:
            raise ValueError(f"Prompt template '{prompt_id}' not found")
        
        template = self.templates[prompt_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        logger.info(f"Updated prompt template: {prompt_id}")
    
    def list_prompts(self, category: Optional[PromptCategory] = None) -> List[PromptTemplate]:
        """List available prompt templates"""
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())
    
    def save_prompts(self, file_path: Optional[Path] = None):
        """Save prompt templates to file"""
        file_path = file_path or self.prompts_dir / "prompts.yaml"
        
        # Convert templates to serializable format
        prompts_data = {}
        for prompt_id, template in self.templates.items():
            data = asdict(template)
            # Convert datetime objects to strings
            data['created_at'] = template.created_at.isoformat()
            data['updated_at'] = template.updated_at.isoformat()
            data['category'] = template.category.value
            prompts_data[prompt_id] = data
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(prompts_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Saved {len(self.templates)} prompt templates to {file_path}")
    
    def load_prompts(self, file_path: Optional[Path] = None):
        """Load prompt templates from file"""
        file_path = file_path or self.prompts_dir / "prompts.yaml"
        
        if not file_path.exists():
            logger.warning(f"Prompts file not found: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts_data = yaml.safe_load(f)
        
        for prompt_id, data in prompts_data.items():
            # Convert string dates back to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            data['category'] = PromptCategory(data['category'])
            
            template = PromptTemplate(**data)
            self.templates[prompt_id] = template
        
        logger.info(f"Loaded {len(prompts_data)} prompt templates from {file_path}")
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """Get statistics about prompt usage"""
        stats = {
            "total_prompts": len(self.templates),
            "by_category": {},
            "recent_updates": []
        }
        
        # Count by category
        for template in self.templates.values():
            category = template.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # Recent updates (last 7 days)
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent = [t for t in self.templates.values() if t.updated_at > week_ago]
        stats["recent_updates"] = [{"id": t.id, "name": t.name, "updated": t.updated_at.isoformat()} 
                                  for t in recent]
        
        return stats