"""
Report Generator Module

This module provides a centralized report generation system that coordinates
functional, security, and compliance reporting to create comprehensive
unified reports across all testing domains.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .unified_reporter import UnifiedReporter, UnifiedReport, ReportFormat, ReportScope
from .security_reporter import SecurityReporter, SecurityReport
from .compliance_reporter import ComplianceReporter, ComplianceReport
from .functional_reporter import FunctionalReporter, FunctionalReport


class ReportGenerationMode(Enum):
    """Report generation modes"""
    UNIFIED_ONLY = "unified_only"
    DOMAIN_SPECIFIC = "domain_specific"
    COMPREHENSIVE = "comprehensive"
    EXECUTIVE_SUMMARY = "executive_summary"


class ReportOutputFormat(Enum):
    """Report output formats"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    ALL_FORMATS = "all_formats"


@dataclass
class ReportGenerationConfig:
    """Configuration for report generation"""
    output_directory: str
    report_name: str = "unified_test_report"
    generation_mode: ReportGenerationMode = ReportGenerationMode.COMPREHENSIVE
    output_formats: List[ReportOutputFormat] = field(default_factory=lambda: [ReportOutputFormat.HTML])
    include_raw_data: bool = False
    include_visualizations: bool = True
    include_recommendations: bool = True
    max_details_level: int = 3  # 1=summary, 2=detailed, 3=comprehensive
    custom_branding: Optional[Dict[str, str]] = None
    template_overrides: Optional[Dict[str, str]] = None


@dataclass
class ReportGenerationResult:
    """Result of report generation process"""
    success: bool
    generated_reports: List[str] = field(default_factory=list)
    generation_time: float = 0.0
    total_size_bytes: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """
    Centralized report generator that coordinates all reporting components
    """
    
    def __init__(self, config: Optional[ReportGenerationConfig] = None):
        """Initialize the report generator"""
        self.config = config or ReportGenerationConfig(output_directory="./reports")
        
        # Initialize component reporters
        self.unified_reporter = UnifiedReporter()
        self.security_reporter = SecurityReporter()
        self.compliance_reporter = ComplianceReporter()
        self.functional_reporter = FunctionalReporter()
        
        # Ensure output directory exists
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(
        self,
        functional_results: Optional[Any] = None,
        security_results: Optional[Any] = None,
        compliance_results: Optional[Any] = None,
        test_environment: str = "",
        execution_context: str = ""
    ) -> ReportGenerationResult:
        """
        Generate comprehensive reports across all domains
        """
        start_time = datetime.now()
        result = ReportGenerationResult(success=True)
        
        try:
            # Generate domain-specific reports if requested
            if self.config.generation_mode in [
                ReportGenerationMode.DOMAIN_SPECIFIC,
                ReportGenerationMode.COMPREHENSIVE
            ]:
                result = self._generate_domain_reports(
                    result, functional_results, security_results, 
                    compliance_results, test_environment, execution_context
                )
            
            # Generate unified report if requested
            if self.config.generation_mode in [
                ReportGenerationMode.UNIFIED_ONLY,
                ReportGenerationMode.COMPREHENSIVE,
                ReportGenerationMode.EXECUTIVE_SUMMARY
            ]:
                result = self._generate_unified_report(
                    result, functional_results, security_results,
                    compliance_results, test_environment, execution_context
                )
            
            # Calculate generation metrics
            end_time = datetime.now()
            result.generation_time = (end_time - start_time).total_seconds()
            result.total_size_bytes = self._calculate_total_size(result.generated_reports)
            
            # Generate index file
            self._generate_report_index(result)
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Report generation failed: {str(e)}")
        
        return result
    
    def _generate_domain_reports(
        self,
        result: ReportGenerationResult,
        functional_results: Optional[Any],
        security_results: Optional[Any],
        compliance_results: Optional[Any],
        test_environment: str,
        execution_context: str
    ) -> ReportGenerationResult:
        """Generate domain-specific reports"""
        
        # Generate functional report
        if functional_results:
            try:
                functional_report = self.functional_reporter.generate_functional_report(
                    test_results=functional_results,
                    test_environment=test_environment,
                    execution_context=execution_context
                )
                
                for format_type in self.config.output_formats:
                    if format_type != ReportOutputFormat.ALL_FORMATS:
                        file_path = self._save_domain_report(
                            functional_report, "functional", format_type
                        )
                        result.generated_reports.append(file_path)
                        
            except Exception as e:
                result.errors.append(f"Functional report generation failed: {str(e)}")
        
        # Generate security report
        if security_results:
            try:
                security_report = self.security_reporter.generate_security_report(
                    scan_results=security_results,
                    test_environment=test_environment,
                    execution_context=execution_context
                )
                
                for format_type in self.config.output_formats:
                    if format_type != ReportOutputFormat.ALL_FORMATS:
                        file_path = self._save_domain_report(
                            security_report, "security", format_type
                        )
                        result.generated_reports.append(file_path)
                        
            except Exception as e:
                result.errors.append(f"Security report generation failed: {str(e)}")
        
        # Generate compliance report
        if compliance_results:
            try:
                compliance_report = self.compliance_reporter.generate_compliance_report(
                    assessment_results=compliance_results,
                    test_environment=test_environment,
                    execution_context=execution_context
                )
                
                for format_type in self.config.output_formats:
                    if format_type != ReportOutputFormat.ALL_FORMATS:
                        file_path = self._save_domain_report(
                            compliance_report, "compliance", format_type
                        )
                        result.generated_reports.append(file_path)
                        
            except Exception as e:
                result.errors.append(f"Compliance report generation failed: {str(e)}")
        
        return result
    
    def _generate_unified_report(
        self,
        result: ReportGenerationResult,
        functional_results: Optional[Any],
        security_results: Optional[Any],
        compliance_results: Optional[Any],
        test_environment: str,
        execution_context: str
    ) -> ReportGenerationResult:
        """Generate unified report"""
        
        try:
            # Determine report scope based on available data
            scope = self._determine_report_scope(
                functional_results, security_results, compliance_results
            )
            
            unified_report = self.unified_reporter.generate_unified_report(
                functional_results=functional_results,
                security_results=security_results,
                compliance_results=compliance_results,
                report_scope=scope,
                test_environment=test_environment,
                execution_context=execution_context
            )
            
            for format_type in self.config.output_formats:
                if format_type != ReportOutputFormat.ALL_FORMATS:
                    file_path = self._save_unified_report(unified_report, format_type)
                    result.generated_reports.append(file_path)
                    
        except Exception as e:
            result.errors.append(f"Unified report generation failed: {str(e)}")
        
        return result
    
    def _save_domain_report(
        self,
        report: Union[FunctionalReport, SecurityReport, ComplianceReport],
        domain: str,
        format_type: ReportOutputFormat
    ) -> str:
        """Save domain-specific report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.report_name}_{domain}_{timestamp}.{format_type.value}"
        file_path = os.path.join(self.config.output_directory, filename)
        
        if format_type == ReportOutputFormat.JSON:
            content = self._get_json_content(report)
        elif format_type == ReportOutputFormat.HTML:
            content = self._get_html_content(report, domain)
        elif format_type == ReportOutputFormat.MARKDOWN:
            content = self._get_markdown_content(report, domain)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _save_unified_report(
        self,
        report: UnifiedReport,
        format_type: ReportOutputFormat
    ) -> str:
        """Save unified report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.report_name}_unified_{timestamp}.{format_type.value}"
        file_path = os.path.join(self.config.output_directory, filename)
        
        if format_type == ReportOutputFormat.JSON:
            content = self.unified_reporter.export_to_json(report)
        elif format_type == ReportOutputFormat.HTML:
            content = self.unified_reporter.export_to_html(report)
        elif format_type == ReportOutputFormat.MARKDOWN:
            content = self.unified_reporter.export_to_markdown(report)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _get_json_content(self, report: Any) -> str:
        """Get JSON content for domain report"""
        if hasattr(report, '__dict__'):
            return json.dumps(report.__dict__, default=str, indent=2)
        return json.dumps(report, default=str, indent=2)
    
    def _get_html_content(self, report: Any, domain: str) -> str:
        """Get HTML content for domain report"""
        if domain == "functional" and hasattr(self.functional_reporter, 'export_to_html'):
            return self.functional_reporter.export_to_html(report)
        elif domain == "security" and hasattr(self.security_reporter, 'export_to_html'):
            return self.security_reporter.export_to_html(report)
        elif domain == "compliance" and hasattr(self.compliance_reporter, 'export_to_html'):
            return self.compliance_reporter.export_to_html(report)
        else:
            # Fallback to basic HTML
            return f"""
            <html>
            <head><title>{domain.title()} Report</title></head>
            <body>
                <h1>{domain.title()} Report</h1>
                <pre>{json.dumps(report.__dict__ if hasattr(report, '__dict__') else report, default=str, indent=2)}</pre>
            </body>
            </html>
            """
    
    def _get_markdown_content(self, report: Any, domain: str) -> str:
        """Get Markdown content for domain report"""
        # Basic markdown generation
        content = f"# {domain.title()} Report\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if hasattr(report, 'title'):
            content += f"## {report.title}\n\n"
        
        if hasattr(report, 'executive_summary'):
            content += f"## Executive Summary\n\n{report.executive_summary}\n\n"
        
        # Add basic report data
        content += "## Report Data\n\n```json\n"
        content += json.dumps(report.__dict__ if hasattr(report, '__dict__') else report, default=str, indent=2)
        content += "\n```\n"
        
        return content
    
    def _determine_report_scope(
        self,
        functional_results: Optional[Any],
        security_results: Optional[Any],
        compliance_results: Optional[Any]
    ) -> ReportScope:
        """Determine appropriate report scope based on available data"""
        
        has_functional = functional_results is not None
        has_security = security_results is not None
        has_compliance = compliance_results is not None
        
        if has_functional and has_security and has_compliance:
            return ReportScope.COMPREHENSIVE
        elif (has_functional and has_security) or (has_functional and has_compliance) or (has_security and has_compliance):
            return ReportScope.CROSS_DOMAIN
        elif has_functional:
            return ReportScope.FUNCTIONAL_ONLY
        elif has_security:
            return ReportScope.SECURITY_ONLY
        elif has_compliance:
            return ReportScope.COMPLIANCE_ONLY
        else:
            return ReportScope.SUMMARY_ONLY
    
    def _calculate_total_size(self, file_paths: List[str]) -> int:
        """Calculate total size of generated reports"""
        total_size = 0
        for file_path in file_paths:
            try:
                total_size += os.path.getsize(file_path)
            except OSError:
                pass  # File might not exist or be accessible
        return total_size
    
    def _generate_report_index(self, result: ReportGenerationResult):
        """Generate an index file listing all generated reports"""
        
        index_content = f"""
# Test Report Index

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Generated Reports

"""
        
        for report_path in result.generated_reports:
            filename = os.path.basename(report_path)
            file_size = os.path.getsize(report_path) if os.path.exists(report_path) else 0
            index_content += f"- [{filename}](./{filename}) ({file_size:,} bytes)\n"
        
        index_content += f"""

## Generation Summary

- **Total Reports:** {len(result.generated_reports)}
- **Total Size:** {result.total_size_bytes:,} bytes
- **Generation Time:** {result.generation_time:.2f} seconds
- **Success:** {'Yes' if result.success else 'No'}

"""
        
        if result.errors:
            index_content += "## Errors\n\n"
            for error in result.errors:
                index_content += f"- {error}\n"
        
        if result.warnings:
            index_content += "## Warnings\n\n"
            for warning in result.warnings:
                index_content += f"- {warning}\n"
        
        # Save index file
        index_path = os.path.join(self.config.output_directory, "index.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        result.generated_reports.append(index_path)


# Utility functions for report generation

def generate_comprehensive_reports(
    functional_results: Optional[Any] = None,
    security_results: Optional[Any] = None,
    compliance_results: Optional[Any] = None,
    output_directory: str = "./reports",
    report_name: str = "comprehensive_test_report"
) -> ReportGenerationResult:
    """Generate comprehensive reports with default configuration"""
    
    config = ReportGenerationConfig(
        output_directory=output_directory,
        report_name=report_name,
        generation_mode=ReportGenerationMode.COMPREHENSIVE,
        output_formats=[ReportOutputFormat.HTML, ReportOutputFormat.JSON]
    )
    
    generator = ReportGenerator(config)
    return generator.generate_comprehensive_report(
        functional_results=functional_results,
        security_results=security_results,
        compliance_results=compliance_results
    )


def generate_executive_summary(
    functional_results: Optional[Any] = None,
    security_results: Optional[Any] = None,
    compliance_results: Optional[Any] = None,
    output_directory: str = "./reports"
) -> ReportGenerationResult:
    """Generate executive summary report"""
    
    config = ReportGenerationConfig(
        output_directory=output_directory,
        report_name="executive_summary",
        generation_mode=ReportGenerationMode.EXECUTIVE_SUMMARY,
        output_formats=[ReportOutputFormat.HTML],
        max_details_level=1
    )
    
    generator = ReportGenerator(config)
    return generator.generate_comprehensive_report(
        functional_results=functional_results,
        security_results=security_results,
        compliance_results=compliance_results
    )


def generate_domain_specific_reports(
    functional_results: Optional[Any] = None,
    security_results: Optional[Any] = None,
    compliance_results: Optional[Any] = None,
    output_directory: str = "./reports"
) -> ReportGenerationResult:
    """Generate domain-specific reports only"""
    
    config = ReportGenerationConfig(
        output_directory=output_directory,
        report_name="domain_specific",
        generation_mode=ReportGenerationMode.DOMAIN_SPECIFIC,
        output_formats=[ReportOutputFormat.HTML, ReportOutputFormat.JSON]
    )
    
    generator = ReportGenerator(config)
    return generator.generate_comprehensive_report(
        functional_results=functional_results,
        security_results=security_results,
        compliance_results=compliance_results
    )