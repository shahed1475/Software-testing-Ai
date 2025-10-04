"""
Unified Reporting Module

Provides comprehensive reporting capabilities for functional testing, security scanning,
and compliance assessment results with integrated analytics and visualization.
"""

from .unified_reporter import (
    UnifiedReporter,
    ReportFormat,
    ReportScope,
    ReportTemplate,
    UnifiedReport,
    ReportSection,
    ReportMetrics,
    ReportVisualization
)

from .security_reporter import (
    SecurityReporter,
    SecurityReport,
    SecurityMetrics,
    VulnerabilityDetail,
    SecurityRecommendation,
    SecurityReportType,
    VulnerabilityCategory,
    ThreatLevel
)

from .compliance_reporter import (
    ComplianceReporter,
    ComplianceReport,
    ComplianceMetrics,
    ComplianceGap,
    ComplianceRecommendation,
    ComplianceReportType,
    ComplianceStatus,
    ComplianceRiskLevel
)

from .functional_reporter import (
    FunctionalReporter,
    FunctionalReport,
    FunctionalMetrics,
    TestResult,
    TestSuite,
    CoverageDetail,
    FunctionalReportType,
    TestStatus,
    TestPriority,
    TestCategory
)

from .report_generator import (
    ReportGenerator,
    ReportGenerationConfig,
    ReportGenerationResult,
    ReportGenerationMode,
    ReportOutputFormat
)

from .analytics_engine import (
    AnalyticsEngine,
    TrendAnalysis,
    PerformanceMetrics,
    RiskAssessment,
    QualityMetrics,
    CorrelationAnalysis,
    PredictiveInsights,
    AnalyticsResult,
    AnalyticsType,
    TrendDirection,
    RiskLevel
)

from .visualization_engine import (
    VisualizationEngine,
    ChartType,
    VisualizationTheme,
    ChartSize,
    ChartConfig,
    ChartData,
    Visualization
)

__all__ = [
    # Core reporting
    'UnifiedReporter',
    'ReportFormat',
    'ReportScope',
    'ReportTemplate',
    'UnifiedReport',
    'ReportSection',
    'ReportMetrics',
    'ReportVisualization',
    
    # Security reporting
    'SecurityReporter',
    'SecurityReport',
    'SecurityMetrics',
    'VulnerabilityDetail',
    'SecurityRecommendation',
    'SecurityReportType',
    'VulnerabilityCategory',
    'ThreatLevel',
    
    # Compliance reporting
    'ComplianceReporter',
    'ComplianceReport',
    'ComplianceMetrics',
    'ComplianceGap',
    'ComplianceRecommendation',
    'ComplianceReportType',
    'ComplianceStatus',
    'ComplianceRiskLevel',
    
    # Functional reporting
    'FunctionalReporter',
    'FunctionalReport',
    'FunctionalMetrics',
    'TestResult',
    'TestSuite',
    'CoverageDetail',
    'FunctionalReportType',
    'TestStatus',
    'TestPriority',
    'TestCategory',
    
    # Report generation and management
    'ReportGenerator',
    'ReportGenerationConfig',
    'ReportGenerationResult',
    'ReportGenerationMode',
    'ReportOutputFormat',
    
    # Analytics and insights
    'AnalyticsEngine',
    'TrendAnalysis',
    'PerformanceMetrics',
    'RiskAssessment',
    'QualityMetrics',
    'CorrelationAnalysis',
    'PredictiveInsights',
    'AnalyticsResult',
    'AnalyticsType',
    'TrendDirection',
    'RiskLevel',
    
    # Visualization
    'VisualizationEngine',
    'ChartType',
    'VisualizationTheme',
    'ChartSize',
    'ChartConfig',
    'ChartData',
    'Visualization'
]

__version__ = "1.0.0"
__author__ = "AI Testing Framework"
__description__ = "Unified reporting system for comprehensive test analysis and insights"