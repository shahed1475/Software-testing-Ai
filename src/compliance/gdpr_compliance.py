"""
GDPR Compliance Checker

Implementation of General Data Protection Regulation (GDPR) compliance checks
for data protection, privacy, and user rights verification.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .compliance_framework import (
    ComplianceChecker,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceRequirement,
    ComplianceResult,
    ComplianceStandard,
    ComplianceStatus,
    create_compliance_check,
    create_compliance_requirement
)

logger = logging.getLogger(__name__)


class GDPRChecker(ComplianceChecker):
    """GDPR compliance checker implementation"""
    
    def __init__(self):
        super().__init__("GDPR Checker", "1.0.0", ComplianceStandard.GDPR)
        self._initialize_requirements()
        self._initialize_checks()
    
    def _initialize_requirements(self):
        """Initialize GDPR compliance requirements"""
        
        # Article 5 - Principles of processing personal data
        self.requirements["gdpr_art5_lawfulness"] = create_compliance_requirement(
            id="gdpr_art5_lawfulness",
            standard=ComplianceStandard.GDPR,
            title="Lawfulness, fairness and transparency",
            description="Personal data shall be processed lawfully, fairly and in a transparent manner",
            level=ComplianceLevel.CRITICAL,
            section="Article 5",
            subsection="1(a)",
            implementation_guidance="Ensure legal basis for processing, provide clear privacy notices",
            testing_procedures=[
                "Verify privacy policy exists and is accessible",
                "Check legal basis documentation",
                "Validate consent mechanisms"
            ],
            evidence_requirements=[
                "Privacy policy document",
                "Legal basis assessment",
                "Consent records"
            ]
        )
        
        # Article 6 - Lawfulness of processing
        self.requirements["gdpr_art6_legal_basis"] = create_compliance_requirement(
            id="gdpr_art6_legal_basis",
            standard=ComplianceStandard.GDPR,
            title="Legal basis for processing",
            description="Processing shall be lawful only if at least one legal basis applies",
            level=ComplianceLevel.CRITICAL,
            section="Article 6",
            implementation_guidance="Document legal basis for each processing activity",
            testing_procedures=[
                "Review data processing inventory",
                "Verify legal basis documentation",
                "Check consent collection processes"
            ]
        )
        
        # Article 7 - Conditions for consent
        self.requirements["gdpr_art7_consent"] = create_compliance_requirement(
            id="gdpr_art7_consent",
            standard=ComplianceStandard.GDPR,
            title="Conditions for consent",
            description="Consent must be freely given, specific, informed and unambiguous",
            level=ComplianceLevel.CRITICAL,
            section="Article 7",
            implementation_guidance="Implement clear consent mechanisms with withdrawal options",
            testing_procedures=[
                "Test consent collection interfaces",
                "Verify consent withdrawal mechanisms",
                "Check consent records management"
            ]
        )
        
        # Article 12 - Transparent information
        self.requirements["gdpr_art12_transparency"] = create_compliance_requirement(
            id="gdpr_art12_transparency",
            standard=ComplianceStandard.GDPR,
            title="Transparent information and communication",
            description="Information shall be provided in concise, transparent, intelligible form",
            level=ComplianceLevel.HIGH,
            section="Article 12",
            implementation_guidance="Create clear, accessible privacy notices and communications"
        )
        
        # Article 15 - Right of access
        self.requirements["gdpr_art15_access"] = create_compliance_requirement(
            id="gdpr_art15_access",
            standard=ComplianceStandard.GDPR,
            title="Right of access by the data subject",
            description="Data subject has right to obtain confirmation and access to personal data",
            level=ComplianceLevel.CRITICAL,
            section="Article 15",
            implementation_guidance="Implement data access request handling procedures"
        )
        
        # Article 17 - Right to erasure
        self.requirements["gdpr_art17_erasure"] = create_compliance_requirement(
            id="gdpr_art17_erasure",
            standard=ComplianceStandard.GDPR,
            title="Right to erasure ('right to be forgotten')",
            description="Data subject has right to obtain erasure of personal data",
            level=ComplianceLevel.CRITICAL,
            section="Article 17",
            implementation_guidance="Implement data deletion procedures and verification"
        )
        
        # Article 25 - Data protection by design and by default
        self.requirements["gdpr_art25_by_design"] = create_compliance_requirement(
            id="gdpr_art25_by_design",
            standard=ComplianceStandard.GDPR,
            title="Data protection by design and by default",
            description="Implement appropriate technical and organisational measures",
            level=ComplianceLevel.HIGH,
            section="Article 25",
            implementation_guidance="Integrate privacy considerations into system design"
        )
        
        # Article 32 - Security of processing
        self.requirements["gdpr_art32_security"] = create_compliance_requirement(
            id="gdpr_art32_security",
            standard=ComplianceStandard.GDPR,
            title="Security of processing",
            description="Implement appropriate technical and organisational measures for security",
            level=ComplianceLevel.CRITICAL,
            section="Article 32",
            implementation_guidance="Implement encryption, access controls, and security monitoring"
        )
        
        # Article 33 - Notification of breach
        self.requirements["gdpr_art33_breach_notification"] = create_compliance_requirement(
            id="gdpr_art33_breach_notification",
            standard=ComplianceStandard.GDPR,
            title="Notification of personal data breach to supervisory authority",
            description="Notify supervisory authority of breach within 72 hours",
            level=ComplianceLevel.CRITICAL,
            section="Article 33",
            implementation_guidance="Establish breach detection and notification procedures"
        )
        
        # Article 35 - Data protection impact assessment
        self.requirements["gdpr_art35_dpia"] = create_compliance_requirement(
            id="gdpr_art35_dpia",
            standard=ComplianceStandard.GDPR,
            title="Data protection impact assessment",
            description="Carry out DPIA when processing likely to result in high risk",
            level=ComplianceLevel.HIGH,
            section="Article 35",
            implementation_guidance="Conduct DPIA for high-risk processing activities"
        )
    
    def _initialize_checks(self):
        """Initialize GDPR compliance checks"""
        
        # Privacy Policy Checks
        self.checks["gdpr_privacy_policy_exists"] = create_compliance_check(
            check_id="gdpr_privacy_policy_exists",
            requirement_id="gdpr_art12_transparency",
            name="Privacy Policy Exists",
            description="Verify that a privacy policy is accessible on the website",
            check_type="automated",
            automated=True,
            check_method="web_crawl",
            expected_result="Privacy policy found and accessible",
            pass_criteria=["Privacy policy URL accessible", "Policy content not empty"]
        )
        
        self.checks["gdpr_privacy_policy_content"] = create_compliance_check(
            check_id="gdpr_privacy_policy_content",
            requirement_id="gdpr_art12_transparency",
            name="Privacy Policy Content Analysis",
            description="Analyze privacy policy content for GDPR compliance",
            check_type="automated",
            automated=True,
            check_method="content_analysis",
            expected_result="Privacy policy contains required GDPR elements"
        )
        
        # Consent Mechanism Checks
        self.checks["gdpr_consent_collection"] = create_compliance_check(
            check_id="gdpr_consent_collection",
            requirement_id="gdpr_art7_consent",
            name="Consent Collection Mechanism",
            description="Verify proper consent collection interfaces",
            check_type="automated",
            automated=True,
            check_method="ui_analysis",
            expected_result="Clear consent mechanisms with opt-in/opt-out options"
        )
        
        self.checks["gdpr_consent_withdrawal"] = create_compliance_check(
            check_id="gdpr_consent_withdrawal",
            requirement_id="gdpr_art7_consent",
            name="Consent Withdrawal Mechanism",
            description="Verify users can easily withdraw consent",
            check_type="automated",
            automated=True,
            check_method="ui_analysis",
            expected_result="Consent withdrawal as easy as giving consent"
        )
        
        # Data Subject Rights Checks
        self.checks["gdpr_data_access_request"] = create_compliance_check(
            check_id="gdpr_data_access_request",
            requirement_id="gdpr_art15_access",
            name="Data Access Request Process",
            description="Verify data access request handling",
            check_type="hybrid",
            automated=True,
            check_method="api_test",
            expected_result="Data access requests can be submitted and processed"
        )
        
        self.checks["gdpr_data_deletion_request"] = create_compliance_check(
            check_id="gdpr_data_deletion_request",
            requirement_id="gdpr_art17_erasure",
            name="Data Deletion Request Process",
            description="Verify data deletion request handling",
            check_type="hybrid",
            automated=True,
            check_method="api_test",
            expected_result="Data deletion requests can be submitted and processed"
        )
        
        # Security Checks
        self.checks["gdpr_data_encryption"] = create_compliance_check(
            check_id="gdpr_data_encryption",
            requirement_id="gdpr_art32_security",
            name="Data Encryption in Transit and at Rest",
            description="Verify personal data is encrypted",
            check_type="automated",
            automated=True,
            check_method="security_scan",
            expected_result="Personal data encrypted in transit and at rest"
        )
        
        self.checks["gdpr_access_controls"] = create_compliance_check(
            check_id="gdpr_access_controls",
            requirement_id="gdpr_art32_security",
            name="Access Controls for Personal Data",
            description="Verify appropriate access controls are in place",
            check_type="automated",
            automated=True,
            check_method="security_scan",
            expected_result="Role-based access controls implemented"
        )
        
        # Cookie and Tracking Checks
        self.checks["gdpr_cookie_consent"] = create_compliance_check(
            check_id="gdpr_cookie_consent",
            requirement_id="gdpr_art7_consent",
            name="Cookie Consent Mechanism",
            description="Verify cookie consent banner and controls",
            check_type="automated",
            automated=True,
            check_method="web_analysis",
            expected_result="Cookie consent banner with granular controls"
        )
        
        self.checks["gdpr_tracking_consent"] = create_compliance_check(
            check_id="gdpr_tracking_consent",
            requirement_id="gdpr_art7_consent",
            name="Tracking and Analytics Consent",
            description="Verify consent for tracking and analytics",
            check_type="automated",
            automated=True,
            check_method="web_analysis",
            expected_result="No tracking without explicit consent"
        )
        
        # Data Processing Documentation
        self.checks["gdpr_processing_records"] = create_compliance_check(
            check_id="gdpr_processing_records",
            requirement_id="gdpr_art6_legal_basis",
            name="Records of Processing Activities",
            description="Verify documentation of processing activities",
            check_type="manual",
            automated=False,
            manual_steps=[
                "Review data processing inventory",
                "Verify legal basis documentation",
                "Check data flow documentation"
            ],
            expected_result="Complete records of processing activities maintained"
        )
    
    def get_supported_requirements(self) -> List[ComplianceRequirement]:
        """Get list of supported GDPR requirements"""
        return list(self.requirements.values())
    
    def get_available_checks(self) -> List[ComplianceCheck]:
        """Get list of available GDPR checks"""
        return list(self.checks.values())
    
    async def execute_check(self, check: ComplianceCheck, context: Dict[str, Any]) -> ComplianceResult:
        """Execute a single GDPR compliance check"""
        
        result = ComplianceResult(
            check_id=check.check_id,
            requirement_id=check.requirement_id,
            status=ComplianceStatus.UNKNOWN,
            start_time=datetime.now(),
            checker_name=self.name,
            checker_version=self.version
        )
        
        try:
            # Route to appropriate check method
            if check.check_method == "web_crawl":
                await self._check_web_crawl(check, context, result)
            elif check.check_method == "content_analysis":
                await self._check_content_analysis(check, context, result)
            elif check.check_method == "ui_analysis":
                await self._check_ui_analysis(check, context, result)
            elif check.check_method == "api_test":
                await self._check_api_test(check, context, result)
            elif check.check_method == "security_scan":
                await self._check_security_scan(check, context, result)
            elif check.check_method == "web_analysis":
                await self._check_web_analysis(check, context, result)
            else:
                result.status = ComplianceStatus.NOT_APPLICABLE
                result.findings.append(f"Check method '{check.check_method}' not implemented")
            
        except Exception as e:
            result.status = ComplianceStatus.ERROR
            result.error_message = str(e)
            result.passed = False
            
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _check_web_crawl(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check for privacy policy existence via web crawling"""
        
        base_url = context.get("base_url", "")
        if not base_url:
            result.status = ComplianceStatus.ERROR
            result.error_message = "Base URL not provided in context"
            return
        
        # Common privacy policy URLs to check
        privacy_urls = [
            f"{base_url}/privacy",
            f"{base_url}/privacy-policy",
            f"{base_url}/privacy.html",
            f"{base_url}/legal/privacy",
            f"{base_url}/terms-and-privacy"
        ]
        
        found_policy = False
        accessible_urls = []
        
        # Simulate checking URLs (in real implementation, use HTTP client)
        for url in privacy_urls:
            # Mock check - in real implementation, make HTTP request
            if "privacy" in url.lower():
                found_policy = True
                accessible_urls.append(url)
                result.evidence["privacy_policy_urls"] = accessible_urls
        
        if found_policy:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Privacy policy found and accessible")
            result.score = 1.0
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("No accessible privacy policy found")
            result.issues_found.append("Missing privacy policy")
            result.remediation_steps.append("Create and publish privacy policy")
            result.score = 0.0
    
    async def _check_content_analysis(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Analyze privacy policy content for GDPR compliance"""
        
        privacy_content = context.get("privacy_policy_content", "")
        if not privacy_content:
            result.status = ComplianceStatus.ERROR
            result.error_message = "Privacy policy content not provided"
            return
        
        # Required GDPR elements to check for
        required_elements = {
            "data_controller": ["controller", "data controller", "responsible"],
            "legal_basis": ["legal basis", "lawful basis", "legitimate interest"],
            "data_types": ["personal data", "data we collect", "information we collect"],
            "purposes": ["purpose", "why we collect", "use of data"],
            "retention": ["retention", "how long", "storage period"],
            "rights": ["your rights", "data subject rights", "access", "deletion"],
            "contact": ["contact", "email", "address", "dpo", "data protection officer"],
            "transfers": ["transfer", "third country", "international"],
            "cookies": ["cookies", "tracking", "analytics"]
        }
        
        content_lower = privacy_content.lower()
        found_elements = {}
        missing_elements = []
        
        for element, keywords in required_elements.items():
            found = any(keyword in content_lower for keyword in keywords)
            found_elements[element] = found
            if not found:
                missing_elements.append(element)
        
        result.evidence["content_analysis"] = found_elements
        
        # Calculate compliance score
        compliance_score = len([e for e in found_elements.values() if e]) / len(required_elements)
        result.score = compliance_score
        
        if compliance_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Privacy policy contains most required GDPR elements")
        elif compliance_score >= 0.6:
            result.status = ComplianceStatus.PARTIALLY_COMPLIANT
            result.passed = False
            result.findings.append("Privacy policy partially compliant with GDPR")
            result.issues_found.extend([f"Missing or unclear: {elem}" for elem in missing_elements])
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Privacy policy lacks essential GDPR elements")
            result.issues_found.extend([f"Missing: {elem}" for elem in missing_elements])
        
        if missing_elements:
            result.remediation_steps.append(f"Add missing elements: {', '.join(missing_elements)}")
    
    async def _check_ui_analysis(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Analyze UI for consent mechanisms"""
        
        # Mock UI analysis - in real implementation, use web driver
        ui_elements = context.get("ui_elements", {})
        
        if check.check_id == "gdpr_consent_collection":
            # Check for consent collection UI
            has_consent_banner = ui_elements.get("consent_banner", False)
            has_granular_controls = ui_elements.get("granular_controls", False)
            has_clear_language = ui_elements.get("clear_language", False)
            
            if has_consent_banner and has_granular_controls and has_clear_language:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Proper consent collection mechanism found")
                result.score = 1.0
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Consent collection mechanism needs improvement")
                
                if not has_consent_banner:
                    result.issues_found.append("Missing consent banner")
                if not has_granular_controls:
                    result.issues_found.append("Missing granular consent controls")
                if not has_clear_language:
                    result.issues_found.append("Consent language not clear")
                
                result.score = 0.0
        
        elif check.check_id == "gdpr_consent_withdrawal":
            # Check for consent withdrawal mechanism
            has_withdrawal_option = ui_elements.get("withdrawal_option", False)
            withdrawal_easy = ui_elements.get("withdrawal_easy", False)
            
            if has_withdrawal_option and withdrawal_easy:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Consent withdrawal mechanism available")
                result.score = 1.0
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Consent withdrawal mechanism inadequate")
                result.issues_found.append("Difficult or missing consent withdrawal")
                result.remediation_steps.append("Implement easy consent withdrawal")
                result.score = 0.0
    
    async def _check_api_test(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Test API endpoints for data subject rights"""
        
        api_base = context.get("api_base_url", "")
        if not api_base:
            result.status = ComplianceStatus.ERROR
            result.error_message = "API base URL not provided"
            return
        
        # Mock API testing - in real implementation, make actual API calls
        if check.check_id == "gdpr_data_access_request":
            # Test data access request endpoint
            access_endpoint_exists = context.get("access_endpoint_exists", False)
            access_endpoint_works = context.get("access_endpoint_works", False)
            
            if access_endpoint_exists and access_endpoint_works:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Data access request endpoint functional")
                result.score = 1.0
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Data access request endpoint not available")
                result.issues_found.append("Missing or non-functional access request API")
                result.remediation_steps.append("Implement data access request API")
                result.score = 0.0
        
        elif check.check_id == "gdpr_data_deletion_request":
            # Test data deletion request endpoint
            deletion_endpoint_exists = context.get("deletion_endpoint_exists", False)
            deletion_endpoint_works = context.get("deletion_endpoint_works", False)
            
            if deletion_endpoint_exists and deletion_endpoint_works:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Data deletion request endpoint functional")
                result.score = 1.0
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Data deletion request endpoint not available")
                result.issues_found.append("Missing or non-functional deletion request API")
                result.remediation_steps.append("Implement data deletion request API")
                result.score = 0.0
    
    async def _check_security_scan(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Perform security-related GDPR checks"""
        
        security_config = context.get("security_config", {})
        
        if check.check_id == "gdpr_data_encryption":
            # Check encryption settings
            https_enabled = security_config.get("https_enabled", False)
            database_encrypted = security_config.get("database_encrypted", False)
            file_encryption = security_config.get("file_encryption", False)
            
            encryption_score = sum([https_enabled, database_encrypted, file_encryption]) / 3
            
            if encryption_score >= 0.8:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Adequate encryption measures in place")
            elif encryption_score >= 0.5:
                result.status = ComplianceStatus.PARTIALLY_COMPLIANT
                result.passed = False
                result.findings.append("Some encryption measures in place")
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Insufficient encryption measures")
            
            result.score = encryption_score
            
            if not https_enabled:
                result.issues_found.append("HTTPS not enabled")
            if not database_encrypted:
                result.issues_found.append("Database not encrypted")
            if not file_encryption:
                result.issues_found.append("File encryption not implemented")
        
        elif check.check_id == "gdpr_access_controls":
            # Check access control settings
            rbac_enabled = security_config.get("rbac_enabled", False)
            mfa_enabled = security_config.get("mfa_enabled", False)
            audit_logging = security_config.get("audit_logging", False)
            
            access_score = sum([rbac_enabled, mfa_enabled, audit_logging]) / 3
            
            if access_score >= 0.8:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Strong access controls implemented")
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Insufficient access controls")
            
            result.score = access_score
    
    async def _check_web_analysis(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Analyze web elements for cookie and tracking compliance"""
        
        web_config = context.get("web_config", {})
        
        if check.check_id == "gdpr_cookie_consent":
            # Check cookie consent implementation
            cookie_banner = web_config.get("cookie_banner", False)
            granular_cookie_controls = web_config.get("granular_cookie_controls", False)
            cookie_policy = web_config.get("cookie_policy", False)
            
            cookie_score = sum([cookie_banner, granular_cookie_controls, cookie_policy]) / 3
            
            if cookie_score >= 0.8:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Compliant cookie consent mechanism")
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Cookie consent mechanism needs improvement")
            
            result.score = cookie_score
        
        elif check.check_id == "gdpr_tracking_consent":
            # Check tracking consent
            no_tracking_without_consent = web_config.get("no_tracking_without_consent", False)
            analytics_consent = web_config.get("analytics_consent", False)
            
            if no_tracking_without_consent and analytics_consent:
                result.status = ComplianceStatus.COMPLIANT
                result.passed = True
                result.findings.append("Tracking only with proper consent")
                result.score = 1.0
            else:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.passed = False
                result.findings.append("Tracking without proper consent detected")
                result.issues_found.append("Unauthorized tracking")
                result.remediation_steps.append("Implement consent-based tracking")
                result.score = 0.0


# Utility functions for GDPR compliance
def create_gdpr_assessment_context(
    base_url: str,
    api_base_url: str = "",
    privacy_policy_content: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Create assessment context for GDPR compliance check"""
    
    context = {
        "target": base_url,
        "base_url": base_url,
        "api_base_url": api_base_url or f"{base_url}/api",
        "privacy_policy_content": privacy_policy_content,
        "assessor": "GDPR Automated Checker",
        "scope": "GDPR Compliance Assessment",
        
        # Mock UI elements (in real implementation, extract from actual UI)
        "ui_elements": {
            "consent_banner": True,
            "granular_controls": True,
            "clear_language": True,
            "withdrawal_option": True,
            "withdrawal_easy": True
        },
        
        # Mock API availability (in real implementation, test actual APIs)
        "access_endpoint_exists": True,
        "access_endpoint_works": True,
        "deletion_endpoint_exists": True,
        "deletion_endpoint_works": True,
        
        # Mock security configuration (in real implementation, scan actual config)
        "security_config": {
            "https_enabled": True,
            "database_encrypted": True,
            "file_encryption": False,
            "rbac_enabled": True,
            "mfa_enabled": False,
            "audit_logging": True
        },
        
        # Mock web configuration (in real implementation, analyze actual site)
        "web_config": {
            "cookie_banner": True,
            "granular_cookie_controls": True,
            "cookie_policy": True,
            "no_tracking_without_consent": True,
            "analytics_consent": True
        }
    }
    
    # Add any additional context provided
    context.update(kwargs)
    
    return context


async def run_gdpr_assessment(base_url: str, **kwargs) -> Dict[str, Any]:
    """Run a complete GDPR compliance assessment"""
    
    checker = GDPRChecker()
    context = create_gdpr_assessment_context(base_url, **kwargs)
    
    # Execute full assessment
    report = await checker.execute_full_assessment(context)
    
    return {
        "report": report,
        "summary": {
            "compliance_score": report.overall_compliance_score,
            "critical_issues": len(report.critical_issues),
            "recommendations": len(report.recommendations),
            "status": "COMPLIANT" if report.overall_compliance_score >= 0.8 else "NON_COMPLIANT"
        }
    }