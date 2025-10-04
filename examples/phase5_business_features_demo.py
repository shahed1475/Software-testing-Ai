#!/usr/bin/env python3
"""
Phase 5 - Business & Collaboration Features Demo

This demo showcases all the business intelligence and collaboration features
implemented in Phase 5 of the Software Testing AI Framework.

Features demonstrated:
- Historical trend analysis
- Trend reporting with business insights
- AI-generated executive summaries
- ChatOps integration (Slack/Teams)
- Business-friendly dashboards
- Voice summaries and notifications
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import modules directly to avoid package import issues
import importlib.util

def load_module_from_path(module_name, file_path):
    """Load a module from a specific file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load Phase 5 modules
src_path = Path(__file__).parent.parent / "src"

# Load trend reporter
trend_reporter_path = src_path / "agents" / "trend_reporter_agent.py"
trend_reporter = load_module_from_path("trend_reporter_agent", trend_reporter_path)

# Load executive summary agent
exec_summary_path = src_path / "agents" / "executive_summary_agent.py"
exec_summary = load_module_from_path("executive_summary_agent", exec_summary_path)

# Load historical analyzer
historical_path = src_path / "analytics" / "historical_analyzer.py"
historical = load_module_from_path("historical_analyzer", historical_path)

# Load ChatOps integration
chatops_path = src_path / "integrations" / "chatops_integration.py"
chatops = load_module_from_path("chatops_integration", chatops_path)

# Load business dashboard
dashboard_path = src_path / "dashboards" / "business_dashboard.py"
dashboard = load_module_from_path("business_dashboard", dashboard_path)

# Load visualization components
viz_path = src_path / "dashboards" / "visualization_components.py"
viz = load_module_from_spec("visualization_components", viz_path)

print("🚀 Phase 5 - Business & Collaboration Features Demo")
print("=" * 60)

async def run_demo():
    """Run the comprehensive Phase 5 demo"""
    
    print("\n📊 1. Historical Analysis Demo")
    print("-" * 40)
    
    # Initialize Historical Analyzer
    analyzer = historical.HistoricalAnalyzer()
    
    # Generate sample historical data
    print("Generating sample historical data...")
    await analyzer.collect_historical_data(
        start_date=datetime.now() - timedelta(days=90),
        end_date=datetime.now(),
        project_id="demo-project"
    )
    
    # Analyze failure rates
    failure_analysis = await analyzer.analyze_failure_rates(
        period=historical.AnalysisPeriod.LAST_30_DAYS,
        project_id="demo-project"
    )
    print(f"✅ Failure rate analysis completed: {failure_analysis.current_rate:.2%} failure rate")
    
    # Analyze flakiness
    flakiness_analysis = await analyzer.analyze_flakiness(
        period=historical.AnalysisPeriod.LAST_30_DAYS,
        project_id="demo-project"
    )
    print(f"✅ Flakiness analysis completed: {len(flakiness_analysis.flaky_tests)} flaky tests identified")
    
    print("\n📈 2. Trend Reporter Demo")
    print("-" * 40)
    
    # Initialize Trend Reporter
    reporter = trend_reporter.TrendReporterAgent()
    
    # Generate trend report
    trend_report = await reporter.generate_trend_report(
        period=trend_reporter.TrendPeriod.MONTHLY,
        project_id="demo-project"
    )
    print(f"✅ Trend report generated with {len(trend_report.insights)} business insights")
    
    # Generate business insights
    insights = await reporter.generate_business_insights(trend_report.metrics)
    print(f"✅ Generated {len(insights)} actionable business insights")
    
    print("\n📋 3. Executive Summary Demo")
    print("-" * 40)
    
    # Initialize Executive Summary Agent
    exec_agent = exec_summary.ExecutiveSummaryAgent()
    
    # Generate executive summary
    summary = await exec_agent.generate_summary(
        summary_type=exec_summary.SummaryType.WEEKLY,
        stakeholder_level=exec_summary.StakeholderLevel.EXECUTIVE,
        project_id="demo-project"
    )
    print(f"✅ Executive summary generated: {summary.title}")
    print(f"   Risk Level: {summary.risk_assessment.overall_risk}")
    print(f"   Key Insights: {len(summary.insights)} strategic insights")
    
    print("\n💬 4. ChatOps Integration Demo")
    print("-" * 40)
    
    # Initialize ChatOps
    chatops_config = chatops.ChatOpsConfig(
        slack_token="demo-token",
        teams_webhook="demo-webhook",
        default_channel="#qa-alerts"
    )
    chatops_integration = chatops.ChatOpsIntegration(chatops_config)
    
    # Send demo alert
    await chatops_integration.send_alert(
        platform=chatops.PlatformType.SLACK,
        message="Demo alert: Test suite completed successfully!",
        priority=chatops.Priority.INFO
    )
    print("✅ ChatOps alert sent (simulated)")
    
    # Generate voice summary
    voice_summary = await chatops_integration.generate_voice_summary(summary)
    print(f"✅ Voice summary generated: {len(voice_summary.text)} characters")
    
    print("\n📊 5. Business Dashboard Demo")
    print("-" * 40)
    
    # Initialize Business Dashboard
    business_dashboard = dashboard.BusinessDashboard()
    
    # Generate executive dashboard
    exec_dashboard = await business_dashboard.generate_dashboard(
        dashboard_type=dashboard.DashboardType.EXECUTIVE,
        time_range=dashboard.TimeRange.LAST_30_DAYS,
        project_id="demo-project"
    )
    print(f"✅ Executive dashboard generated with {len(exec_dashboard.widgets)} widgets")
    
    # Generate operational dashboard
    ops_dashboard = await business_dashboard.generate_dashboard(
        dashboard_type=dashboard.DashboardType.OPERATIONAL,
        time_range=dashboard.TimeRange.LAST_7_DAYS,
        project_id="demo-project"
    )
    print(f"✅ Operational dashboard generated with {len(ops_dashboard.widgets)} widgets")
    
    # Export dashboard to HTML
    html_file = "demo_dashboard.html"
    await business_dashboard.export_to_html(exec_dashboard, html_file)
    print(f"✅ Dashboard exported to {html_file}")
    
    print("\n🎯 6. End-to-End Business Intelligence Workflow")
    print("-" * 40)
    
    # Simulate a complete BI workflow
    print("Running complete business intelligence workflow...")
    
    # 1. Collect and analyze historical data
    historical_report = await analyzer.generate_historical_report(
        period=historical.AnalysisPeriod.LAST_30_DAYS,
        project_id="demo-project"
    )
    
    # 2. Generate trend insights
    trend_insights = await reporter.generate_business_insights(trend_report.metrics)
    
    # 3. Create executive summary
    exec_summary_full = await exec_agent.generate_summary(
        summary_type=exec_summary.SummaryType.MONTHLY,
        stakeholder_level=exec_summary.StakeholderLevel.EXECUTIVE,
        project_id="demo-project"
    )
    
    # 4. Send notifications
    await chatops_integration.send_daily_summary(
        platform=chatops.PlatformType.SLACK,
        summary=exec_summary_full
    )
    
    # 5. Generate comprehensive dashboard
    comprehensive_dashboard = await business_dashboard.generate_dashboard(
        dashboard_type=dashboard.DashboardType.EXECUTIVE,
        time_range=dashboard.TimeRange.LAST_30_DAYS,
        project_id="demo-project"
    )
    
    print("✅ Complete BI workflow executed successfully!")
    
    print("\n🎉 Phase 5 Demo Completed Successfully!")
    print("=" * 60)
    print("All business intelligence and collaboration features are working correctly.")
    print("The framework now provides:")
    print("• Historical trend analysis and predictions")
    print("• AI-generated executive summaries")
    print("• ChatOps integration with voice summaries")
    print("• Business-friendly dashboards and visualizations")
    print("• Comprehensive business intelligence workflows")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()