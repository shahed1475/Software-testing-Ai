"""
HIPAA Compliance Checker

Implementation of Health Insurance Portability and Accountability Act (HIPAA) compliance checks
for organizations that handle protected health information (PHI).
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


class HIPAAChecker(ComplianceChecker):
    """HIPAA compliance checker implementation"""
    
    def __init__(self):
        super().__init__("HIPAA Checker", "1.0.0", ComplianceStandard.HIPAA)
        self._initialize_requirements()
        self._initialize_checks()
    
    def _initialize_requirements(self):
        """Initialize HIPAA compliance requirements"""
        
        # Administrative Safeguards
        self.requirements["hipaa_admin_safeguards"] = create_compliance_requirement(
            id="hipaa_admin_safeguards",
            standard=ComplianceStandard.HIPAA,
            title="Administrative Safeguards",
            description="Implement administrative actions and policies to manage security measures",
            level=ComplianceLevel.CRITICAL,
            section="164.308 Administrative Safeguards",
            implementation_guidance="Establish security officer, workforce training, access management",
            testing_procedures=[
                "Review security policies and procedures",
                "Verify workforce training records",
                "Check access management processes"
            ],
            evidence_requirements=[
                "Security policies documentation",
                "Training records",
                "Access control procedures"
            ]
        )
        
        # Physical Safeguards
        self.requirements["hipaa_physical_safeguards"] = create_compliance_requirement(
            id="hipaa_physical_safeguards",
            standard=ComplianceStandard.HIPAA,
            title="Physical Safeguards",
            description="Protect physical access to electronic PHI and workstations",
            level=ComplianceLevel.HIGH,
            section="164.310 Physical Safeguards",
            implementation_guidance="Control facility access, workstation use, and device controls"
        )
        
        # Technical Safeguards
        self.requirements["hipaa_technical_safeguards"] = create_compliance_requirement(
            id="hipaa_technical_safeguards",
            standard=ComplianceStandard.HIPAA,
            title="Technical Safeguards",
            description="Control access to electronic PHI and protect it from alteration or destruction",
            level=ComplianceLevel.CRITICAL,
            section="164.312 Technical Safeguards",
            implementation_guidance="Implement access control, audit controls, integrity, and transmission security"
        )
        
        # Privacy Rule Requirements
        self.requirements["hipaa_privacy_rule"] = create_compliance_requirement(
            id="hipaa_privacy_rule",
            standard=ComplianceStandard.HIPAA,
            title="Privacy Rule Compliance",
            description="Protect the privacy of individually identifiable health information",
            level=ComplianceLevel.CRITICAL,
            section="164.500 Privacy Rule",
            implementation_guidance="Implement minimum necessary standard, individual rights, and privacy practices"
        )
        
        # Security Rule Requirements
        self.requirements["hipaa_security_rule"] = create_compliance_requirement(
            id="hipaa_security_rule",
            standard=ComplianceStandard.HIPAA,
            title="Security Rule Compliance",
            description="Protect electronic PHI through administrative, physical, and technical safeguards",
            level=ComplianceLevel.CRITICAL,
            section="164.300 Security Rule",
            implementation_guidance="Ensure confidentiality, integrity, and availability of ePHI"
        )
        
        # Breach Notification Rule
        self.requirements["hipaa_breach_notification"] = create_compliance_requirement(
            id="hipaa_breach_notification",
            standard=ComplianceStandard.HIPAA,
            title="Breach Notification Rule",
            description="Notify individuals, HHS, and media of breaches of unsecured PHI",
            level=ComplianceLevel.HIGH,
            section="164.400 Breach Notification",
            implementation_guidance="Implement breach detection, assessment, and notification procedures"
        )
        
        # Business Associate Agreements
        self.requirements["hipaa_business_associates"] = create_compliance_requirement(
            id="hipaa_business_associates",
            standard=ComplianceStandard.HIPAA,
            title="Business Associate Agreements",
            description="Ensure business associates protect PHI through written agreements",
            level=ComplianceLevel.HIGH,
            section="164.502 Business Associate Requirements",
            implementation_guidance="Execute BAAs with all business associates handling PHI"
        )
        
        # Individual Rights
        self.requirements["hipaa_individual_rights"] = create_compliance_requirement(
            id="hipaa_individual_rights",
            standard=ComplianceStandard.HIPAA,
            title="Individual Rights",
            description="Provide individuals with rights over their PHI",
            level=ComplianceLevel.HIGH,
            section="164.520 Individual Rights",
            implementation_guidance="Implement processes for access, amendment, restriction, and accounting"
        )
    
    def _initialize_checks(self):
        """Initialize HIPAA compliance checks"""
        
        # Administrative Safeguards Checks
        self.checks["hipaa_security_officer"] = create_compliance_check(
            check_id="hipaa_security_officer",
            requirement_id="hipaa_admin_safeguards",
            name="Security Officer Assignment",
            description="Verify a security officer is assigned and responsible for security",
            check_type="manual",
            automated=False,
            manual_steps=[
                "Review organizational chart",
                "Verify security officer designation",
                "Check security responsibilities documentation"
            ],
            expected_result="Designated security officer with documented responsibilities"
        )
        
        self.checks["hipaa_workforce_training"] = create_compliance_check(
            check_id="hipaa_workforce_training",
            requirement_id="hipaa_admin_safeguards",
            name="Workforce Training Program",
            description="Verify workforce receives appropriate HIPAA training",
            check_type="automated",
            automated=True,
            check_method="training_verification",
            expected_result="All workforce members receive regular HIPAA training"
        )
        
        self.checks["hipaa_access_management"] = create_compliance_check(
            check_id="hipaa_access_management",
            requirement_id="hipaa_admin_safeguards",
            name="Access Management Procedures",
            description="Verify procedures for granting and revoking access to PHI",
            check_type="automated",
            automated=True,
            check_method="access_procedure_check",
            expected_result="Documented procedures for access management"
        )
        
        self.checks["hipaa_contingency_plan"] = create_compliance_check(
            check_id="hipaa_contingency_plan",
            requirement_id="hipaa_admin_safeguards",
            name="Contingency Plan",
            description="Verify contingency plan for emergency access to PHI",
            check_type="manual",
            automated=False,
            manual_steps=[
                "Review contingency plan documentation",
                "Verify emergency access procedures",
                "Check plan testing records"
            ],
            expected_result="Documented and tested contingency plan"
        )
        
        # Physical Safeguards Checks
        self.checks["hipaa_facility_access"] = create_compliance_check(
            check_id="hipaa_facility_access",
            requirement_id="hipaa_physical_safeguards",
            name="Facility Access Controls",
            description="Verify physical access controls to facilities containing PHI",
            check_type="automated",
            automated=True,
            check_method="physical_access_check",
            expected_result="Appropriate physical access controls implemented"
        )
        
        self.checks["hipaa_workstation_controls"] = create_compliance_check(
            check_id="hipaa_workstation_controls",
            requirement_id="hipaa_physical_safeguards",
            name="Workstation Use Controls",
            description="Verify controls for workstation access and use",
            check_type="automated",
            automated=True,
            check_method="workstation_check",
            expected_result="Workstation access and use properly controlled"
        )
        
        self.checks["hipaa_device_controls"] = create_compliance_check(
            check_id="hipaa_device_controls",
            requirement_id="hipaa_physical_safeguards",
            name="Device and Media Controls",
            description="Verify controls for hardware and electronic media containing PHI",
            check_type="automated",
            automated=True,
            check_method="device_control_check",
            expected_result="Proper controls for devices and media"
        )
        
        # Technical Safeguards Checks
        self.checks["hipaa_access_control"] = create_compliance_check(
            check_id="hipaa_access_control",
            requirement_id="hipaa_technical_safeguards",
            name="Access Control Implementation",
            description="Verify technical access controls for PHI systems",
            check_type="automated",
            automated=True,
            check_method="technical_access_check",
            expected_result="Appropriate technical access controls implemented"
        )
        
        self.checks["hipaa_audit_controls"] = create_compliance_check(
            check_id="hipaa_audit_controls",
            requirement_id="hipaa_technical_safeguards",
            name="Audit Controls",
            description="Verify audit controls to record access to PHI",
            check_type="automated",
            automated=True,
            check_method="audit_control_check",
            expected_result="Comprehensive audit controls implemented"
        )
        
        self.checks["hipaa_integrity_controls"] = create_compliance_check(
            check_id="hipaa_integrity_controls",
            requirement_id="hipaa_technical_safeguards",
            name="Integrity Controls",
            description="Verify PHI is not improperly altered or destroyed",
            check_type="automated",
            automated=True,
            check_method="integrity_check",
            expected_result="PHI integrity protection implemented"
        )
        
        self.checks["hipaa_transmission_security"] = create_compliance_check(
            check_id="hipaa_transmission_security",
            requirement_id="hipaa_technical_safeguards",
            name="Transmission Security",
            description="Verify PHI transmission security measures",
            check_type="automated",
            automated=True,
            check_method="transmission_security_check",
            expected_result="Secure PHI transmission implemented"
        )
        
        # Privacy Rule Checks
        self.checks["hipaa_minimum_necessary"] = create_compliance_check(
            check_id="hipaa_minimum_necessary",
            requirement_id="hipaa_privacy_rule",
            name="Minimum Necessary Standard",
            description="Verify minimum necessary standard is applied to PHI use and disclosure",
            check_type="automated",
            automated=True,
            check_method="minimum_necessary_check",
            expected_result="Minimum necessary standard properly implemented"
        )
        
        self.checks["hipaa_notice_of_privacy"] = create_compliance_check(
            check_id="hipaa_notice_of_privacy",
            requirement_id="hipaa_privacy_rule",
            name="Notice of Privacy Practices",
            description="Verify notice of privacy practices is provided to individuals",
            check_type="automated",
            automated=True,
            check_method="privacy_notice_check",
            expected_result="Notice of privacy practices provided and documented"
        )
        
        # Security Rule Checks
        self.checks["hipaa_encryption"] = create_compliance_check(
            check_id="hipaa_encryption",
            requirement_id="hipaa_security_rule",
            name="Encryption Implementation",
            description="Verify encryption of PHI at rest and in transit",
            check_type="automated",
            automated=True,
            check_method="encryption_check",
            expected_result="PHI properly encrypted at rest and in transit"
        )
        
        # Breach Notification Checks
        self.checks["hipaa_breach_procedures"] = create_compliance_check(
            check_id="hipaa_breach_procedures",
            requirement_id="hipaa_breach_notification",
            name="Breach Response Procedures",
            description="Verify breach detection and notification procedures",
            check_type="manual",
            automated=False,
            manual_steps=[
                "Review breach response procedures",
                "Verify notification templates",
                "Check incident response team"
            ],
            expected_result="Documented breach response procedures"
        )
        
        # Business Associate Checks
        self.checks["hipaa_baa_agreements"] = create_compliance_check(
            check_id="hipaa_baa_agreements",
            requirement_id="hipaa_business_associates",
            name="Business Associate Agreements",
            description="Verify BAAs are in place with all business associates",
            check_type="manual",
            automated=False,
            manual_steps=[
                "Review list of business associates",
                "Verify BAA execution",
                "Check BAA compliance monitoring"
            ],
            expected_result="Valid BAAs with all business associates"
        )
        
        # Individual Rights Checks
        self.checks["hipaa_individual_access"] = create_compliance_check(
            check_id="hipaa_individual_access",
            requirement_id="hipaa_individual_rights",
            name="Individual Access Rights",
            description="Verify individuals can access their PHI",
            check_type="automated",
            automated=True,
            check_method="individual_access_check",
            expected_result="Individual access rights properly implemented"
        )
    
    def get_supported_requirements(self) -> List[ComplianceRequirement]:
        """Get list of supported HIPAA requirements"""
        return list(self.requirements.values())
    
    def get_available_checks(self) -> List[ComplianceCheck]:
        """Get list of available HIPAA checks"""
        return list(self.checks.values())
    
    async def execute_check(self, check: ComplianceCheck, context: Dict[str, Any]) -> ComplianceResult:
        """Execute a single HIPAA compliance check"""
        
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
            if check.check_method == "training_verification":
                await self._check_training_verification(check, context, result)
            elif check.check_method == "access_procedure_check":
                await self._check_access_procedures(check, context, result)
            elif check.check_method == "physical_access_check":
                await self._check_physical_access(check, context, result)
            elif check.check_method == "workstation_check":
                await self._check_workstation_controls(check, context, result)
            elif check.check_method == "device_control_check":
                await self._check_device_controls(check, context, result)
            elif check.check_method == "technical_access_check":
                await self._check_technical_access(check, context, result)
            elif check.check_method == "audit_control_check":
                await self._check_audit_controls(check, context, result)
            elif check.check_method == "integrity_check":
                await self._check_integrity_controls(check, context, result)
            elif check.check_method == "transmission_security_check":
                await self._check_transmission_security(check, context, result)
            elif check.check_method == "minimum_necessary_check":
                await self._check_minimum_necessary(check, context, result)
            elif check.check_method == "privacy_notice_check":
                await self._check_privacy_notice(check, context, result)
            elif check.check_method == "encryption_check":
                await self._check_encryption(check, context, result)
            elif check.check_method == "individual_access_check":
                await self._check_individual_access(check, context, result)
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
    
    async def _check_training_verification(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check workforce training implementation"""
        
        training_config = context.get("training_config", {})
        
        training_program_exists = training_config.get("training_program_exists", False)
        regular_training_schedule = training_config.get("regular_training_schedule", False)
        training_records_maintained = training_config.get("training_records_maintained", False)
        role_based_training = training_config.get("role_based_training", False)
        
        training_score = sum([
            training_program_exists,
            regular_training_schedule,
            training_records_maintained,
            role_based_training
        ]) / 4
        
        if training_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Workforce training program properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Workforce training program deficiencies found")
            
            if not training_program_exists:
                result.issues_found.append("No formal training program")
            if not regular_training_schedule:
                result.issues_found.append("No regular training schedule")
            if not training_records_maintained:
                result.issues_found.append("Training records not maintained")
            if not role_based_training:
                result.issues_found.append("Training not role-based")
        
        result.score = training_score
    
    async def _check_access_procedures(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check access management procedures"""
        
        access_config = context.get("access_config", {})
        
        documented_procedures = access_config.get("documented_procedures", False)
        access_authorization = access_config.get("access_authorization", False)
        access_review_process = access_config.get("access_review_process", False)
        termination_procedures = access_config.get("termination_procedures", False)
        
        access_score = sum([
            documented_procedures,
            access_authorization,
            access_review_process,
            termination_procedures
        ]) / 4
        
        if access_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Access management procedures properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Access management procedure deficiencies")
        
        result.score = access_score
    
    async def _check_physical_access(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check physical access controls"""
        
        physical_config = context.get("physical_config", {})
        
        facility_access_controls = physical_config.get("facility_access_controls", False)
        visitor_management = physical_config.get("visitor_management", False)
        physical_security_monitoring = physical_config.get("physical_security_monitoring", False)
        secure_areas_defined = physical_config.get("secure_areas_defined", False)
        
        physical_score = sum([
            facility_access_controls,
            visitor_management,
            physical_security_monitoring,
            secure_areas_defined
        ]) / 4
        
        if physical_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Physical access controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Physical access control deficiencies")
        
        result.score = physical_score
    
    async def _check_workstation_controls(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check workstation use controls"""
        
        workstation_config = context.get("workstation_config", {})
        
        workstation_policies = workstation_config.get("workstation_policies", False)
        screen_locks = workstation_config.get("automatic_screen_locks", False)
        workstation_positioning = workstation_config.get("secure_positioning", False)
        remote_access_controls = workstation_config.get("remote_access_controls", False)
        
        workstation_score = sum([
            workstation_policies,
            screen_locks,
            workstation_positioning,
            remote_access_controls
        ]) / 4
        
        if workstation_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Workstation controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Workstation control deficiencies")
        
        result.score = workstation_score
    
    async def _check_device_controls(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check device and media controls"""
        
        device_config = context.get("device_config", {})
        
        device_inventory = device_config.get("device_inventory", False)
        media_disposal_procedures = device_config.get("media_disposal_procedures", False)
        device_encryption = device_config.get("device_encryption", False)
        mobile_device_management = device_config.get("mobile_device_management", False)
        
        device_score = sum([
            device_inventory,
            media_disposal_procedures,
            device_encryption,
            mobile_device_management
        ]) / 4
        
        if device_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Device and media controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Device and media control deficiencies")
        
        result.score = device_score
    
    async def _check_technical_access(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check technical access controls"""
        
        technical_config = context.get("technical_config", {})
        
        unique_user_identification = technical_config.get("unique_user_identification", False)
        automatic_logoff = technical_config.get("automatic_logoff", False)
        role_based_access = technical_config.get("role_based_access", False)
        authentication_controls = technical_config.get("strong_authentication", False)
        
        technical_score = sum([
            unique_user_identification,
            automatic_logoff,
            role_based_access,
            authentication_controls
        ]) / 4
        
        if technical_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Technical access controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Technical access control deficiencies")
        
        result.score = technical_score
    
    async def _check_audit_controls(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check audit controls implementation"""
        
        audit_config = context.get("audit_config", {})
        
        comprehensive_logging = audit_config.get("comprehensive_logging", False)
        log_integrity_protection = audit_config.get("log_integrity_protection", False)
        log_review_procedures = audit_config.get("log_review_procedures", False)
        audit_trail_protection = audit_config.get("audit_trail_protection", False)
        
        audit_score = sum([
            comprehensive_logging,
            log_integrity_protection,
            log_review_procedures,
            audit_trail_protection
        ]) / 4
        
        if audit_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Audit controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Audit control deficiencies")
        
        result.score = audit_score
    
    async def _check_integrity_controls(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check PHI integrity controls"""
        
        integrity_config = context.get("integrity_config", {})
        
        data_integrity_controls = integrity_config.get("data_integrity_controls", False)
        backup_procedures = integrity_config.get("backup_procedures", False)
        version_control = integrity_config.get("version_control", False)
        change_management = integrity_config.get("change_management", False)
        
        integrity_score = sum([
            data_integrity_controls,
            backup_procedures,
            version_control,
            change_management
        ]) / 4
        
        if integrity_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Integrity controls properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Integrity control deficiencies")
        
        result.score = integrity_score
    
    async def _check_transmission_security(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check transmission security controls"""
        
        transmission_config = context.get("transmission_config", {})
        
        encryption_in_transit = transmission_config.get("encryption_in_transit", False)
        secure_protocols = transmission_config.get("secure_protocols", False)
        network_security = transmission_config.get("network_security", False)
        email_security = transmission_config.get("email_security", False)
        
        transmission_score = sum([
            encryption_in_transit,
            secure_protocols,
            network_security,
            email_security
        ]) / 4
        
        if transmission_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Transmission security properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Transmission security deficiencies")
        
        result.score = transmission_score
    
    async def _check_minimum_necessary(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check minimum necessary standard implementation"""
        
        privacy_config = context.get("privacy_config", {})
        
        minimum_necessary_policies = privacy_config.get("minimum_necessary_policies", False)
        role_based_data_access = privacy_config.get("role_based_data_access", False)
        data_use_monitoring = privacy_config.get("data_use_monitoring", False)
        disclosure_controls = privacy_config.get("disclosure_controls", False)
        
        privacy_score = sum([
            minimum_necessary_policies,
            role_based_data_access,
            data_use_monitoring,
            disclosure_controls
        ]) / 4
        
        if privacy_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Minimum necessary standard properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Minimum necessary standard deficiencies")
        
        result.score = privacy_score
    
    async def _check_privacy_notice(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check notice of privacy practices"""
        
        notice_config = context.get("notice_config", {})
        
        notice_provided = notice_config.get("notice_provided", False)
        notice_content_compliant = notice_config.get("notice_content_compliant", False)
        acknowledgment_obtained = notice_config.get("acknowledgment_obtained", False)
        notice_updates_managed = notice_config.get("notice_updates_managed", False)
        
        notice_score = sum([
            notice_provided,
            notice_content_compliant,
            acknowledgment_obtained,
            notice_updates_managed
        ]) / 4
        
        if notice_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Notice of privacy practices properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Notice of privacy practices deficiencies")
        
        result.score = notice_score
    
    async def _check_encryption(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check encryption implementation"""
        
        encryption_config = context.get("encryption_config", {})
        
        data_at_rest_encrypted = encryption_config.get("data_at_rest_encrypted", False)
        data_in_transit_encrypted = encryption_config.get("data_in_transit_encrypted", False)
        strong_encryption_algorithms = encryption_config.get("strong_encryption_algorithms", False)
        key_management = encryption_config.get("proper_key_management", False)
        
        encryption_score = sum([
            data_at_rest_encrypted,
            data_in_transit_encrypted,
            strong_encryption_algorithms,
            key_management
        ]) / 4
        
        if encryption_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Encryption properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Encryption implementation deficiencies")
        
        result.score = encryption_score
    
    async def _check_individual_access(self, check: ComplianceCheck, context: Dict[str, Any], result: ComplianceResult):
        """Check individual access rights implementation"""
        
        individual_config = context.get("individual_config", {})
        
        access_procedures = individual_config.get("access_procedures", False)
        request_processing = individual_config.get("timely_request_processing", False)
        amendment_procedures = individual_config.get("amendment_procedures", False)
        accounting_disclosures = individual_config.get("accounting_disclosures", False)
        
        individual_score = sum([
            access_procedures,
            request_processing,
            amendment_procedures,
            accounting_disclosures
        ]) / 4
        
        if individual_score >= 0.8:
            result.status = ComplianceStatus.COMPLIANT
            result.passed = True
            result.findings.append("Individual access rights properly implemented")
        else:
            result.status = ComplianceStatus.NON_COMPLIANT
            result.passed = False
            result.findings.append("Individual access rights deficiencies")
        
        result.score = individual_score


# Utility functions for HIPAA compliance
def create_hipaa_assessment_context(
    target_system: str,
    **kwargs
) -> Dict[str, Any]:
    """Create assessment context for HIPAA compliance check"""
    
    context = {
        "target": target_system,
        "assessor": "HIPAA Automated Checker",
        "scope": "HIPAA Compliance Assessment",
        
        # Mock training configuration
        "training_config": {
            "training_program_exists": True,
            "regular_training_schedule": True,
            "training_records_maintained": True,
            "role_based_training": False  # Common gap
        },
        
        # Mock access configuration
        "access_config": {
            "documented_procedures": True,
            "access_authorization": True,
            "access_review_process": True,
            "termination_procedures": True
        },
        
        # Mock physical configuration
        "physical_config": {
            "facility_access_controls": True,
            "visitor_management": True,
            "physical_security_monitoring": False,  # Common gap
            "secure_areas_defined": True
        },
        
        # Mock workstation configuration
        "workstation_config": {
            "workstation_policies": True,
            "automatic_screen_locks": True,
            "secure_positioning": True,
            "remote_access_controls": False  # Common gap
        },
        
        # Mock device configuration
        "device_config": {
            "device_inventory": True,
            "media_disposal_procedures": True,
            "device_encryption": True,
            "mobile_device_management": False  # Common gap
        },
        
        # Mock technical configuration
        "technical_config": {
            "unique_user_identification": True,
            "automatic_logoff": True,
            "role_based_access": True,
            "strong_authentication": True
        },
        
        # Mock audit configuration
        "audit_config": {
            "comprehensive_logging": True,
            "log_integrity_protection": True,
            "log_review_procedures": False,  # Common gap
            "audit_trail_protection": True
        },
        
        # Mock integrity configuration
        "integrity_config": {
            "data_integrity_controls": True,
            "backup_procedures": True,
            "version_control": True,
            "change_management": True
        },
        
        # Mock transmission configuration
        "transmission_config": {
            "encryption_in_transit": True,
            "secure_protocols": True,
            "network_security": True,
            "email_security": False  # Common gap
        },
        
        # Mock privacy configuration
        "privacy_config": {
            "minimum_necessary_policies": True,
            "role_based_data_access": True,
            "data_use_monitoring": False,  # Common gap
            "disclosure_controls": True
        },
        
        # Mock notice configuration
        "notice_config": {
            "notice_provided": True,
            "notice_content_compliant": True,
            "acknowledgment_obtained": True,
            "notice_updates_managed": True
        },
        
        # Mock encryption configuration
        "encryption_config": {
            "data_at_rest_encrypted": True,
            "data_in_transit_encrypted": True,
            "strong_encryption_algorithms": True,
            "proper_key_management": True
        },
        
        # Mock individual configuration
        "individual_config": {
            "access_procedures": True,
            "timely_request_processing": True,
            "amendment_procedures": True,
            "accounting_disclosures": False  # Common gap
        }
    }
    
    # Add any additional context provided
    context.update(kwargs)
    
    return context


async def run_hipaa_assessment(target_system: str, **kwargs) -> Dict[str, Any]:
    """Run a complete HIPAA compliance assessment"""
    
    checker = HIPAAChecker()
    context = create_hipaa_assessment_context(target_system, **kwargs)
    
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