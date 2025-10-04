"""
One-Click Bug Ticket Creation System

Automatically creates detailed bug tickets in Jira, GitHub, or other issue tracking
systems from failed test results, with AI-powered analysis and context gathering.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum
import re
import base64
import hashlib

from .ai_orchestrator import AIOrchestrator, AITaskResult
from .llm_service import LLMProvider
from .failure_diagnosis import FailureDiagnosisService, DiagnosisResult

logger = logging.getLogger(__name__)


class IssueTracker(Enum):
    """Supported issue tracking systems"""
    GITHUB = "github"
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"
    GITLAB = "gitlab"
    LINEAR = "linear"
    TRELLO = "trello"


class IssuePriority(Enum):
    """Issue priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(Enum):
    """Types of issues"""
    BUG = "bug"
    REGRESSION = "regression"
    FLAKY_TEST = "flaky_test"
    INFRASTRUCTURE = "infrastructure"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class TestFailure:
    """Represents a test failure"""
    test_id: str
    test_name: str
    test_file: str
    failure_message: str
    stack_trace: str
    execution_time: float
    timestamp: datetime
    environment: Dict[str, str] = field(default_factory=dict)
    browser_info: Optional[Dict[str, str]] = None
    screenshots: List[str] = field(default_factory=list)  # Base64 encoded or file paths
    logs: List[str] = field(default_factory=list)
    test_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    is_flaky: bool = False
    previous_failures: List[datetime] = field(default_factory=list)
    related_changes: List[str] = field(default_factory=list)  # Recent code changes
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BugTicket:
    """Represents a bug ticket to be created"""
    title: str
    description: str
    priority: IssuePriority
    issue_type: IssueType
    labels: List[str]
    assignee: Optional[str] = None
    component: Optional[str] = None
    affects_version: Optional[str] = None
    environment: Optional[str] = None
    steps_to_reproduce: List[str] = field(default_factory=list)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    attachments: List[Dict[str, str]] = field(default_factory=list)  # name, content, type
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    related_issues: List[str] = field(default_factory=list)
    watchers: List[str] = field(default_factory=list)


@dataclass
class TicketCreationResult:
    """Result of ticket creation"""
    success: bool
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    error_message: Optional[str] = None
    tracker: Optional[IssueTracker] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IssueTrackerClient:
    """Base class for issue tracker clients"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "")
        self.auth_token = config.get("auth_token", "")
        self.project_key = config.get("project_key", "")
    
    async def create_issue(self, ticket: BugTicket) -> TicketCreationResult:
        """Create an issue in the tracking system"""
        raise NotImplementedError("Subclasses must implement create_issue")
    
    async def update_issue(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing issue"""
        raise NotImplementedError("Subclasses must implement update_issue")
    
    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search for existing issues"""
        raise NotImplementedError("Subclasses must implement search_issues")
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to an issue"""
        raise NotImplementedError("Subclasses must implement add_comment")


class GitHubClient(IssueTrackerClient):
    """GitHub Issues client"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.owner = config.get("owner", "")
        self.repo = config.get("repo", "")
    
    async def create_issue(self, ticket: BugTicket) -> TicketCreationResult:
        """Create a GitHub issue"""
        try:
            # Simulate GitHub API call (replace with actual implementation)
            issue_data = {
                "title": ticket.title,
                "body": self._format_github_description(ticket),
                "labels": ticket.labels,
                "assignees": [ticket.assignee] if ticket.assignee else []
            }
            
            # Mock response (replace with actual GitHub API call)
            ticket_id = f"#{hash(ticket.title) % 10000}"
            ticket_url = f"https://github.com/{self.owner}/{self.repo}/issues/{ticket_id[1:]}"
            
            logger.info(f"Created GitHub issue: {ticket_url}")
            
            return TicketCreationResult(
                success=True,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                tracker=IssueTracker.GITHUB,
                metadata={"issue_data": issue_data}
            )
            
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {str(e)}")
            return TicketCreationResult(
                success=False,
                error_message=str(e),
                tracker=IssueTracker.GITHUB
            )
    
    def _format_github_description(self, ticket: BugTicket) -> str:
        """Format ticket description for GitHub"""
        sections = []
        
        # Main description
        sections.append(ticket.description)
        
        # Environment info
        if ticket.environment:
            sections.append(f"**Environment:** {ticket.environment}")
        
        # Steps to reproduce
        if ticket.steps_to_reproduce:
            sections.append("## Steps to Reproduce")
            for i, step in enumerate(ticket.steps_to_reproduce, 1):
                sections.append(f"{i}. {step}")
        
        # Expected vs Actual behavior
        if ticket.expected_behavior:
            sections.append(f"**Expected Behavior:** {ticket.expected_behavior}")
        
        if ticket.actual_behavior:
            sections.append(f"**Actual Behavior:** {ticket.actual_behavior}")
        
        # Additional info
        if ticket.component:
            sections.append(f"**Component:** {ticket.component}")
        
        if ticket.affects_version:
            sections.append(f"**Affects Version:** {ticket.affects_version}")
        
        return "\n\n".join(sections)
    
    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search GitHub issues"""
        # Mock implementation
        return []


class JiraClient(IssueTrackerClient):
    """Jira client"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_key = config.get("project_key", "")
    
    async def create_issue(self, ticket: BugTicket) -> TicketCreationResult:
        """Create a Jira issue"""
        try:
            # Map issue type
            jira_issue_type = self._map_issue_type(ticket.issue_type)
            
            # Map priority
            jira_priority = self._map_priority(ticket.priority)
            
            issue_data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": ticket.title,
                    "description": self._format_jira_description(ticket),
                    "issuetype": {"name": jira_issue_type},
                    "priority": {"name": jira_priority},
                    "labels": ticket.labels
                }
            }
            
            # Add optional fields
            if ticket.assignee:
                issue_data["fields"]["assignee"] = {"name": ticket.assignee}
            
            if ticket.component:
                issue_data["fields"]["components"] = [{"name": ticket.component}]
            
            if ticket.affects_version:
                issue_data["fields"]["versions"] = [{"name": ticket.affects_version}]
            
            if ticket.environment:
                issue_data["fields"]["environment"] = ticket.environment
            
            # Add custom fields
            issue_data["fields"].update(ticket.custom_fields)
            
            # Mock response (replace with actual Jira API call)
            ticket_id = f"{self.project_key}-{hash(ticket.title) % 10000}"
            ticket_url = f"{self.base_url}/browse/{ticket_id}"
            
            logger.info(f"Created Jira issue: {ticket_url}")
            
            return TicketCreationResult(
                success=True,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                tracker=IssueTracker.JIRA,
                metadata={"issue_data": issue_data}
            )
            
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {str(e)}")
            return TicketCreationResult(
                success=False,
                error_message=str(e),
                tracker=IssueTracker.JIRA
            )
    
    def _map_issue_type(self, issue_type: IssueType) -> str:
        """Map internal issue type to Jira issue type"""
        mapping = {
            IssueType.BUG: "Bug",
            IssueType.REGRESSION: "Bug",
            IssueType.FLAKY_TEST: "Task",
            IssueType.INFRASTRUCTURE: "Task",
            IssueType.PERFORMANCE: "Bug",
            IssueType.SECURITY: "Bug"
        }
        return mapping.get(issue_type, "Bug")
    
    def _map_priority(self, priority: IssuePriority) -> str:
        """Map internal priority to Jira priority"""
        mapping = {
            IssuePriority.CRITICAL: "Critical",
            IssuePriority.HIGH: "High",
            IssuePriority.MEDIUM: "Medium",
            IssuePriority.LOW: "Low"
        }
        return mapping.get(priority, "Medium")
    
    def _format_jira_description(self, ticket: BugTicket) -> str:
        """Format ticket description for Jira"""
        sections = []
        
        # Main description
        sections.append(ticket.description)
        
        # Steps to reproduce
        if ticket.steps_to_reproduce:
            sections.append("h3. Steps to Reproduce")
            for i, step in enumerate(ticket.steps_to_reproduce, 1):
                sections.append(f"# {step}")
        
        # Expected vs Actual behavior
        if ticket.expected_behavior:
            sections.append(f"h3. Expected Behavior\n{ticket.expected_behavior}")
        
        if ticket.actual_behavior:
            sections.append(f"h3. Actual Behavior\n{ticket.actual_behavior}")
        
        return "\n\n".join(sections)


class MockClient(IssueTrackerClient):
    """Mock client for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.created_issues = []
    
    async def create_issue(self, ticket: BugTicket) -> TicketCreationResult:
        """Create a mock issue"""
        ticket_id = f"MOCK-{len(self.created_issues) + 1}"
        ticket_url = f"https://mock-tracker.com/issues/{ticket_id}"
        
        self.created_issues.append({
            "id": ticket_id,
            "ticket": ticket,
            "created_at": datetime.now()
        })
        
        logger.info(f"Created mock issue: {ticket_id}")
        
        return TicketCreationResult(
            success=True,
            ticket_id=ticket_id,
            ticket_url=ticket_url,
            tracker=IssueTracker.GITHUB,  # Default to GitHub for mock
            metadata={"mock": True}
        )


class BugReportGenerator:
    """Generates detailed bug reports from test failures"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.ai_orchestrator = AIOrchestrator(llm_provider, config)
        self.failure_diagnosis = FailureDiagnosisService(llm_provider, config)
        self.config = config or {}
        
        # Template configurations
        self.title_templates = {
            IssueType.BUG: "[BUG] {test_name} - {short_description}",
            IssueType.REGRESSION: "[REGRESSION] {test_name} - {short_description}",
            IssueType.FLAKY_TEST: "[FLAKY] {test_name} - Intermittent failure",
            IssueType.INFRASTRUCTURE: "[INFRA] {test_name} - Infrastructure issue",
            IssueType.PERFORMANCE: "[PERF] {test_name} - Performance degradation",
            IssueType.SECURITY: "[SECURITY] {test_name} - Security issue"
        }
    
    async def generate_bug_ticket(self, failure: TestFailure) -> BugTicket:
        """Generate a comprehensive bug ticket from test failure"""
        try:
            # Step 1: Diagnose the failure
            diagnosis = await self.failure_diagnosis.diagnose_failure(
                failure.test_name,
                failure.failure_message,
                failure.stack_trace,
                {
                    "test_file": failure.test_file,
                    "execution_time": failure.execution_time,
                    "environment": failure.environment,
                    "browser_info": failure.browser_info,
                    "retry_count": failure.retry_count,
                    "is_flaky": failure.is_flaky
                }
            )
            
            # Step 2: Determine issue type and priority
            issue_type = self._determine_issue_type(failure, diagnosis)
            priority = self._determine_priority(failure, diagnosis)
            
            # Step 3: Generate AI-powered bug report
            ai_report = await self._generate_ai_bug_report(failure, diagnosis)
            
            # Step 4: Create comprehensive ticket
            ticket = BugTicket(
                title=self._generate_title(failure, issue_type, ai_report),
                description=self._generate_description(failure, diagnosis, ai_report),
                priority=priority,
                issue_type=issue_type,
                labels=self._generate_labels(failure, diagnosis),
                component=self._extract_component(failure),
                environment=self._format_environment(failure.environment),
                steps_to_reproduce=self._generate_reproduction_steps(failure, ai_report),
                expected_behavior=ai_report.get("expected_behavior"),
                actual_behavior=ai_report.get("actual_behavior"),
                attachments=self._prepare_attachments(failure),
                custom_fields=self._generate_custom_fields(failure, diagnosis)
            )
            
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to generate bug ticket: {str(e)}")
            
            # Return minimal ticket
            return BugTicket(
                title=f"[BUG] {failure.test_name} - Test failure",
                description=f"Test failed with error: {failure.failure_message}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.BUG,
                labels=["automated", "test-failure"]
            )
    
    async def _generate_ai_bug_report(self, 
                                    failure: TestFailure,
                                    diagnosis: DiagnosisResult) -> Dict[str, Any]:
        """Generate AI-powered bug report analysis"""
        try:
            context = {
                "test_name": failure.test_name,
                "test_file": failure.test_file,
                "failure_message": failure.failure_message,
                "stack_trace": failure.stack_trace,
                "diagnosis": diagnosis.explanation if diagnosis else "No diagnosis available",
                "environment": failure.environment,
                "is_flaky": failure.is_flaky,
                "retry_count": failure.retry_count
            }
            
            ai_result = await self.ai_orchestrator.generate_bug_report(
                failure.test_name,
                context
            )
            
            if ai_result.success and ai_result.result:
                return ai_result.result if isinstance(ai_result.result, dict) else {}
            
        except Exception as e:
            logger.warning(f"AI bug report generation failed: {str(e)}")
        
        return {}
    
    def _determine_issue_type(self, 
                            failure: TestFailure,
                            diagnosis: Optional[DiagnosisResult]) -> IssueType:
        """Determine the type of issue based on failure characteristics"""
        
        # Check for flaky test
        if failure.is_flaky or failure.retry_count > 2:
            return IssueType.FLAKY_TEST
        
        # Check for infrastructure issues
        infra_keywords = ["connection", "timeout", "network", "server", "database", "service"]
        if any(keyword in failure.failure_message.lower() for keyword in infra_keywords):
            return IssueType.INFRASTRUCTURE
        
        # Check for performance issues
        perf_keywords = ["slow", "timeout", "performance", "memory", "cpu"]
        if (failure.execution_time > 300 or  # 5 minutes
            any(keyword in failure.failure_message.lower() for keyword in perf_keywords)):
            return IssueType.PERFORMANCE
        
        # Check for security issues
        security_keywords = ["security", "authentication", "authorization", "permission", "access"]
        if any(keyword in failure.failure_message.lower() for keyword in security_keywords):
            return IssueType.SECURITY
        
        # Check for regression (based on recent changes)
        if failure.related_changes:
            return IssueType.REGRESSION
        
        # Default to bug
        return IssueType.BUG
    
    def _determine_priority(self, 
                          failure: TestFailure,
                          diagnosis: Optional[DiagnosisResult]) -> IssuePriority:
        """Determine issue priority"""
        
        # Critical: Security issues, production blockers
        critical_keywords = ["security", "production", "critical", "blocker", "crash"]
        if any(keyword in failure.failure_message.lower() for keyword in critical_keywords):
            return IssuePriority.CRITICAL
        
        # High: Functional failures, regressions
        if failure.related_changes or "regression" in failure.failure_message.lower():
            return IssuePriority.HIGH
        
        # Low: Flaky tests, minor issues
        if failure.is_flaky:
            return IssuePriority.LOW
        
        # Medium: Default
        return IssuePriority.MEDIUM
    
    def _generate_title(self, 
                       failure: TestFailure,
                       issue_type: IssueType,
                       ai_report: Dict[str, Any]) -> str:
        """Generate issue title"""
        template = self.title_templates.get(issue_type, self.title_templates[IssueType.BUG])
        
        # Extract short description from failure message or AI report
        short_description = ai_report.get("short_summary", "")
        if not short_description:
            # Extract first meaningful part of error message
            error_parts = failure.failure_message.split('\n')[0].split(':')
            short_description = error_parts[-1].strip()[:50] + "..." if len(error_parts[-1]) > 50 else error_parts[-1].strip()
        
        return template.format(
            test_name=failure.test_name,
            short_description=short_description
        )
    
    def _generate_description(self, 
                            failure: TestFailure,
                            diagnosis: Optional[DiagnosisResult],
                            ai_report: Dict[str, Any]) -> str:
        """Generate comprehensive issue description"""
        sections = []
        
        # AI-generated summary
        if ai_report.get("summary"):
            sections.append(f"## Summary\n{ai_report['summary']}")
        
        # Test information
        sections.append(f"## Test Information")
        sections.append(f"- **Test Name:** {failure.test_name}")
        sections.append(f"- **Test File:** {failure.test_file}")
        sections.append(f"- **Execution Time:** {failure.execution_time:.2f}s")
        sections.append(f"- **Timestamp:** {failure.timestamp.isoformat()}")
        
        if failure.retry_count > 0:
            sections.append(f"- **Retry Count:** {failure.retry_count}")
        
        if failure.is_flaky:
            sections.append(f"- **Flaky Test:** Yes")
        
        # Failure details
        sections.append(f"## Failure Details")
        sections.append(f"**Error Message:**")
        sections.append(f"```\n{failure.failure_message}\n```")
        
        if failure.stack_trace:
            sections.append(f"**Stack Trace:**")
            sections.append(f"```\n{failure.stack_trace}\n```")
        
        # AI diagnosis
        if diagnosis and diagnosis.explanation:
            sections.append(f"## AI Diagnosis")
            sections.append(diagnosis.explanation)
            
            if diagnosis.suggested_fixes:
                sections.append(f"**Suggested Fixes:**")
                for fix in diagnosis.suggested_fixes:
                    sections.append(f"- {fix}")
        
        # Environment information
        if failure.environment:
            sections.append(f"## Environment")
            for key, value in failure.environment.items():
                sections.append(f"- **{key}:** {value}")
        
        # Browser information
        if failure.browser_info:
            sections.append(f"## Browser Information")
            for key, value in failure.browser_info.items():
                sections.append(f"- **{key}:** {value}")
        
        # Related changes
        if failure.related_changes:
            sections.append(f"## Related Changes")
            for change in failure.related_changes:
                sections.append(f"- {change}")
        
        # Additional context from AI
        if ai_report.get("additional_context"):
            sections.append(f"## Additional Context")
            sections.append(ai_report["additional_context"])
        
        return "\n\n".join(sections)
    
    def _generate_labels(self, 
                        failure: TestFailure,
                        diagnosis: Optional[DiagnosisResult]) -> List[str]:
        """Generate appropriate labels for the issue"""
        labels = ["automated", "test-failure"]
        
        # Add test type labels
        if "unit" in failure.test_file.lower():
            labels.append("unit-test")
        elif "integration" in failure.test_file.lower():
            labels.append("integration-test")
        elif "e2e" in failure.test_file.lower() or "end-to-end" in failure.test_file.lower():
            labels.append("e2e-test")
        
        # Add flaky label
        if failure.is_flaky:
            labels.append("flaky")
        
        # Add environment labels
        if failure.environment:
            if failure.environment.get("browser"):
                labels.append(f"browser-{failure.environment['browser'].lower()}")
            if failure.environment.get("os"):
                labels.append(f"os-{failure.environment['os'].lower().replace(' ', '-')}")
        
        # Add diagnosis-based labels
        if diagnosis and diagnosis.category:
            labels.append(f"category-{diagnosis.category.lower().replace(' ', '-')}")
        
        return labels
    
    def _extract_component(self, failure: TestFailure) -> Optional[str]:
        """Extract component from test file path"""
        path_parts = Path(failure.test_file).parts
        
        # Look for common component indicators
        for part in path_parts:
            if part in ["auth", "user", "payment", "order", "product", "admin", "api", "ui"]:
                return part.title()
        
        # Use directory name if available
        if len(path_parts) > 1:
            return path_parts[-2].title()
        
        return None
    
    def _format_environment(self, environment: Dict[str, str]) -> Optional[str]:
        """Format environment information"""
        if not environment:
            return None
        
        env_parts = []
        for key, value in environment.items():
            env_parts.append(f"{key}: {value}")
        
        return ", ".join(env_parts)
    
    def _generate_reproduction_steps(self, 
                                   failure: TestFailure,
                                   ai_report: Dict[str, Any]) -> List[str]:
        """Generate steps to reproduce the issue"""
        steps = []
        
        # Use AI-generated steps if available
        if ai_report.get("reproduction_steps"):
            return ai_report["reproduction_steps"]
        
        # Generate basic steps
        steps.append(f"Run the test: {failure.test_name}")
        steps.append(f"Test file: {failure.test_file}")
        
        if failure.environment:
            env_desc = ", ".join([f"{k}={v}" for k, v in failure.environment.items()])
            steps.append(f"Environment: {env_desc}")
        
        steps.append("Observe the failure")
        
        return steps
    
    def _prepare_attachments(self, failure: TestFailure) -> List[Dict[str, str]]:
        """Prepare attachments for the issue"""
        attachments = []
        
        # Add screenshots
        for i, screenshot in enumerate(failure.screenshots):
            attachments.append({
                "name": f"screenshot_{i+1}.png",
                "content": screenshot,
                "type": "image/png"
            })
        
        # Add logs
        for i, log in enumerate(failure.logs):
            attachments.append({
                "name": f"log_{i+1}.txt",
                "content": log,
                "type": "text/plain"
            })
        
        return attachments
    
    def _generate_custom_fields(self, 
                              failure: TestFailure,
                              diagnosis: Optional[DiagnosisResult]) -> Dict[str, Any]:
        """Generate custom fields for the issue tracker"""
        custom_fields = {}
        
        # Add test metadata
        if failure.test_data:
            custom_fields["test_data"] = json.dumps(failure.test_data)
        
        # Add diagnosis confidence
        if diagnosis:
            custom_fields["diagnosis_confidence"] = diagnosis.confidence
        
        # Add failure frequency
        if failure.previous_failures:
            custom_fields["failure_frequency"] = len(failure.previous_failures)
        
        return custom_fields


class BugReportingService:
    """Main service for one-click bug ticket creation"""
    
    def __init__(self, 
                 llm_provider: LLMProvider = LLMProvider.MOCK,
                 config: Optional[Dict] = None):
        self.config = config or {}
        self.bug_generator = BugReportGenerator(llm_provider, config)
        
        # Initialize issue tracker clients
        self.clients = {}
        self._initialize_clients()
        
        # Configuration
        self.auto_create_enabled = self.config.get("auto_create_enabled", True)
        self.duplicate_detection_enabled = self.config.get("duplicate_detection_enabled", True)
        self.min_failure_count = self.config.get("min_failure_count", 1)
        
        # Storage for created tickets
        self.created_tickets = []
        
        logger.info("Bug Reporting Service initialized")
    
    def _initialize_clients(self):
        """Initialize issue tracker clients based on configuration"""
        trackers_config = self.config.get("issue_trackers", {})
        
        for tracker_name, tracker_config in trackers_config.items():
            try:
                tracker_type = IssueTracker(tracker_name.lower())
                
                if tracker_type == IssueTracker.GITHUB:
                    self.clients[tracker_type] = GitHubClient(tracker_config)
                elif tracker_type == IssueTracker.JIRA:
                    self.clients[tracker_type] = JiraClient(tracker_config)
                else:
                    logger.warning(f"Unsupported tracker type: {tracker_name}")
                    
            except ValueError:
                logger.warning(f"Unknown tracker type: {tracker_name}")
        
        # Add mock client if no real clients configured
        if not self.clients:
            self.clients[IssueTracker.GITHUB] = MockClient({})
            logger.info("Using mock client for testing")
    
    async def create_bug_ticket(self, 
                              failure: TestFailure,
                              tracker: Optional[IssueTracker] = None,
                              auto_assign: bool = True) -> TicketCreationResult:
        """Create a bug ticket from test failure"""
        try:
            # Check if auto-creation is enabled
            if not self.auto_create_enabled:
                return TicketCreationResult(
                    success=False,
                    error_message="Auto-creation is disabled"
                )
            
            # Check minimum failure count
            if len(failure.previous_failures) < self.min_failure_count - 1:
                return TicketCreationResult(
                    success=False,
                    error_message=f"Minimum failure count not met ({len(failure.previous_failures) + 1} < {self.min_failure_count})"
                )
            
            # Select tracker
            if not tracker:
                tracker = list(self.clients.keys())[0]  # Use first available
            
            if tracker not in self.clients:
                return TicketCreationResult(
                    success=False,
                    error_message=f"Tracker {tracker.value} not configured"
                )
            
            client = self.clients[tracker]
            
            # Check for duplicates
            if self.duplicate_detection_enabled:
                existing_ticket = await self._find_duplicate_ticket(failure, client)
                if existing_ticket:
                    # Add comment to existing ticket instead
                    comment = f"Test failed again at {failure.timestamp.isoformat()}\n\nError: {failure.failure_message}"
                    await client.add_comment(existing_ticket["id"], comment)
                    
                    return TicketCreationResult(
                        success=True,
                        ticket_id=existing_ticket["id"],
                        ticket_url=existing_ticket.get("url"),
                        tracker=tracker,
                        metadata={"duplicate": True, "action": "commented"}
                    )
            
            # Generate bug ticket
            ticket = await self.bug_generator.generate_bug_ticket(failure)
            
            # Auto-assign if enabled
            if auto_assign and not ticket.assignee:
                ticket.assignee = self._determine_assignee(failure)
            
            # Create ticket
            result = await client.create_issue(ticket)
            
            if result.success:
                # Store created ticket info
                self.created_tickets.append({
                    "ticket_id": result.ticket_id,
                    "failure": failure,
                    "created_at": result.created_at,
                    "tracker": tracker
                })
                
                logger.info(f"Successfully created bug ticket: {result.ticket_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create bug ticket: {str(e)}")
            return TicketCreationResult(
                success=False,
                error_message=str(e)
            )
    
    async def create_bulk_tickets(self, 
                                failures: List[TestFailure],
                                tracker: Optional[IssueTracker] = None) -> List[TicketCreationResult]:
        """Create multiple bug tickets from test failures"""
        results = []
        
        for failure in failures:
            result = await self.create_bug_ticket(failure, tracker)
            results.append(result)
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return results
    
    async def _find_duplicate_ticket(self, 
                                   failure: TestFailure,
                                   client: IssueTrackerClient) -> Optional[Dict[str, Any]]:
        """Find existing ticket for the same test failure"""
        try:
            # Search for tickets with similar test name
            search_query = f"{failure.test_name} test failure"
            existing_issues = await client.search_issues(search_query)
            
            # Simple duplicate detection (can be enhanced)
            for issue in existing_issues:
                if (failure.test_name in issue.get("title", "") and
                    "test failure" in issue.get("title", "").lower()):
                    return issue
            
        except Exception as e:
            logger.warning(f"Duplicate detection failed: {str(e)}")
        
        return None
    
    def _determine_assignee(self, failure: TestFailure) -> Optional[str]:
        """Determine who should be assigned the ticket"""
        # Simple logic - can be enhanced with team mapping, code ownership, etc.
        assignee_rules = self.config.get("assignee_rules", {})
        
        # Check file-based rules
        for pattern, assignee in assignee_rules.get("file_patterns", {}).items():
            if pattern in failure.test_file:
                return assignee
        
        # Check component-based rules
        component = self.bug_generator._extract_component(failure)
        if component and component.lower() in assignee_rules.get("components", {}):
            return assignee_rules["components"][component.lower()]
        
        # Default assignee
        return assignee_rules.get("default")
    
    def get_reporting_stats(self) -> Dict[str, Any]:
        """Get bug reporting statistics"""
        total_tickets = len(self.created_tickets)
        
        if total_tickets == 0:
            return {
                "total_tickets_created": 0,
                "success_rate": 0.0,
                "tracker_distribution": {},
                "issue_type_distribution": {},
                "average_creation_time": 0.0
            }
        
        # Calculate tracker distribution
        tracker_dist = {}
        for ticket in self.created_tickets:
            tracker = ticket["tracker"].value
            tracker_dist[tracker] = tracker_dist.get(tracker, 0) + 1
        
        return {
            "total_tickets_created": total_tickets,
            "tracker_distribution": tracker_dist,
            "tickets_created_today": len([
                t for t in self.created_tickets 
                if t["created_at"].date() == datetime.now().date()
            ])
        }
    
    async def update_ticket_status(self, 
                                 ticket_id: str,
                                 status: str,
                                 tracker: IssueTracker) -> bool:
        """Update the status of an existing ticket"""
        if tracker not in self.clients:
            return False
        
        try:
            client = self.clients[tracker]
            return await client.update_issue(ticket_id, {"status": status})
        except Exception as e:
            logger.error(f"Failed to update ticket status: {str(e)}")
            return False