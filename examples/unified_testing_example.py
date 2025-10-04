#!/usr/bin/env python3
"""
Unified Testing Framework - Example Usage

This example demonstrates how to use the unified testing framework
to perform comprehensive testing across web, API, and mobile domains
with integrated security scanning and compliance checks.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List

# Import unified testing components
from src.unified.unified_orchestrator import (
    UnifiedTestingOrchestrator,
    UnifiedTestPlan,
    UnifiedTestingScope,
    UnifiedExecutionStrategy,
    create_comprehensive_test_plan,
    create_security_focused_plan,
    create_compliance_focused_plan
)

# Import security components
from src.security.security_orchestrator import (
    SecurityOrchestrator,
    create_comprehensive_security_plan
)

# Import compliance components
from src.compliance.compliance_orchestrator import (
    ComplianceOrchestrator,
    create_multi_standard_plan
)

# Import reporting components
from src.reporting.report_generator import ReportGenerator
from src.reporting.visualization_engine import generate_executive_dashboard


class UnifiedTestingExample:
    """
    Example class demonstrating unified testing capabilities
    """
    
    def __init__(self):
        """Initialize the example with orchestrators"""
        self.unified_orchestrator = UnifiedTestingOrchestrator()
        self.security_orchestrator = SecurityOrchestrator()
        self.compliance_orchestrator = ComplianceOrchestrator()
        self.report_generator = ReportGenerator()
    
    async def example_1_basic_unified_testing(self):
        """
        Example 1: Basic unified testing across all domains
        """
        print("🚀 Example 1: Basic Unified Testing")
        print("=" * 50)
        
        # Create a comprehensive test plan
        plan = create_comprehensive_test_plan(
            target_url="https://demo.testfire.net",
            api_endpoints=[
                "https://demo.testfire.net/api/login",
                "https://demo.testfire.net/api/account"
            ],
            mobile_apps=["com.example.testapp"],
            execution_strategy=UnifiedExecutionStrategy.INTEGRATED
        )
        
        print(f"📋 Created test plan with {len(plan.test_suites)} test suites")
        print(f"🎯 Target: {plan.target_config.primary_target}")
        print(f"⚙️ Strategy: {plan.execution_strategy.value}")
        
        # Execute the unified test plan
        print("\n🔄 Executing unified test plan...")
        result = await self.unified_orchestrator.execute_unified_plan(plan)
        
        # Display results summary
        print(f"\n📊 Test Results Summary:")
        print(f"   • Total Tests: {result.total_tests}")
        print(f"   • Passed: {result.passed_tests}")
        print(f"   • Failed: {result.failed_tests}")
        print(f"   • Skipped: {result.skipped_tests}")
        print(f"   • Success Rate: {result.success_rate:.2%}")
        print(f"   • Execution Time: {result.execution_time:.2f}s")
        
        # Generate unified report
        print("\n📄 Generating unified report...")
        report = await self.unified_orchestrator.generate_unified_report(result)
        
        # Save report
        report_path = f"reports/unified_basic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report.html_content)
        
        print(f"✅ Report saved to: {report_path}")
        
        return result
    
    async def example_2_security_focused_testing(self):
        """
        Example 2: Security-focused testing with vulnerability assessment
        """
        print("\n🔒 Example 2: Security-Focused Testing")
        print("=" * 50)
        
        # Create security-focused test plan
        plan = create_security_focused_plan(
            target_url="https://demo.testfire.net",
            security_tools=["owasp_zap", "snyk"],
            vulnerability_threshold="medium"
        )
        
        print(f"🛡️ Created security plan with {len(plan.security_scans)} security scans")
        print(f"🎯 Target: {plan.target_config.primary_target}")
        print(f"🔧 Tools: {', '.join(plan.security_scans.keys())}")
        
        # Execute security assessment
        print("\n🔍 Executing security assessment...")
        result = await self.unified_orchestrator.execute_unified_plan(plan)
        
        # Display security results
        print(f"\n🛡️ Security Results Summary:")
        if hasattr(result, 'security_results'):
            security_results = result.security_results
            print(f"   • Vulnerabilities Found: {security_results.total_vulnerabilities}")
            print(f"   • Critical: {security_results.critical_count}")
            print(f"   • High: {security_results.high_count}")
            print(f"   • Medium: {security_results.medium_count}")
            print(f"   • Low: {security_results.low_count}")
            print(f"   • Security Score: {security_results.security_score:.2f}/100")
        
        # Generate security report
        print("\n📄 Generating security report...")
        report = await self.report_generator.generate_security_report(result)
        
        # Save report
        report_path = f"reports/security_focused_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report.html_content)
        
        print(f"✅ Security report saved to: {report_path}")
        
        return result
    
    async def example_3_compliance_assessment(self):
        """
        Example 3: Compliance assessment for multiple standards
        """
        print("\n📋 Example 3: Compliance Assessment")
        print("=" * 50)
        
        # Create compliance-focused test plan
        plan = create_compliance_focused_plan(
            target_url="https://demo.testfire.net",
            compliance_standards=["GDPR", "PCI_DSS"],
            compliance_level="comprehensive"
        )
        
        print(f"📜 Created compliance plan for {len(plan.compliance_checks)} standards")
        print(f"🎯 Target: {plan.target_config.primary_target}")
        print(f"📊 Standards: {', '.join(plan.compliance_checks.keys())}")
        
        # Execute compliance assessment
        print("\n🔍 Executing compliance assessment...")
        result = await self.unified_orchestrator.execute_unified_plan(plan)
        
        # Display compliance results
        print(f"\n📋 Compliance Results Summary:")
        if hasattr(result, 'compliance_results'):
            compliance_results = result.compliance_results
            print(f"   • Total Checks: {compliance_results.total_checks}")
            print(f"   • Passed: {compliance_results.passed_checks}")
            print(f"   • Failed: {compliance_results.failed_checks}")
            print(f"   • Not Applicable: {compliance_results.na_checks}")
            print(f"   • Compliance Score: {compliance_results.compliance_score:.2%}")
        
        # Generate compliance report
        print("\n📄 Generating compliance report...")
        report = await self.report_generator.generate_compliance_report(result)
        
        # Save report
        report_path = f"reports/compliance_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report.html_content)
        
        print(f"✅ Compliance report saved to: {report_path}")
        
        return result
    
    async def example_4_comprehensive_assessment(self):
        """
        Example 4: Comprehensive assessment with all features
        """
        print("\n🌟 Example 4: Comprehensive Assessment")
        print("=" * 50)
        
        # Create comprehensive test plan with all features
        plan = UnifiedTestPlan(
            plan_id=f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Comprehensive Assessment Example",
            description="Full assessment with functional, security, and compliance testing",
            scope=UnifiedTestingScope.COMPREHENSIVE,
            execution_strategy=UnifiedExecutionStrategy.INTEGRATED,
            target_config={
                "primary_target": "https://demo.testfire.net",
                "api_endpoints": [
                    "https://demo.testfire.net/api/login",
                    "https://demo.testfire.net/api/account",
                    "https://demo.testfire.net/api/transfer"
                ],
                "mobile_apps": ["com.example.bankingapp"]
            },
            test_suites={
                "functional": {
                    "web_tests": ["login", "navigation", "forms", "transactions"],
                    "api_tests": ["authentication", "data_validation", "error_handling"],
                    "mobile_tests": ["ui_elements", "gestures", "performance"]
                }
            },
            security_scans={
                "owasp_zap": {
                    "scan_type": "full",
                    "policy": "comprehensive"
                },
                "snyk": {
                    "scan_dependencies": True,
                    "scan_containers": True
                },
                "trivy": {
                    "scan_filesystem": True,
                    "scan_config": True
                }
            },
            compliance_checks={
                "GDPR": {
                    "level": "comprehensive",
                    "automated_only": False
                },
                "PCI_DSS": {
                    "level": "standard",
                    "network_scanning": True
                },
                "HIPAA": {
                    "level": "basic",
                    "phi_detection": True
                }
            }
        )
        
        print(f"🎯 Target: {plan.target_config['primary_target']}")
        print(f"📊 Scope: {plan.scope.value}")
        print(f"⚙️ Strategy: {plan.execution_strategy.value}")
        print(f"🧪 Test Suites: {len(plan.test_suites)}")
        print(f"🔒 Security Scans: {len(plan.security_scans)}")
        print(f"📋 Compliance Checks: {len(plan.compliance_checks)}")
        
        # Execute comprehensive assessment
        print("\n🔄 Executing comprehensive assessment...")
        start_time = datetime.now()
        
        result = await self.unified_orchestrator.execute_unified_plan(plan)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Display comprehensive results
        print(f"\n📊 Comprehensive Results Summary:")
        print(f"   • Execution Time: {execution_time:.2f}s")
        print(f"   • Total Tests: {result.total_tests}")
        print(f"   • Success Rate: {result.success_rate:.2%}")
        
        if hasattr(result, 'functional_results'):
            print(f"   • Functional Score: {result.functional_results.quality_score:.2f}/100")
        
        if hasattr(result, 'security_results'):
            print(f"   • Security Score: {result.security_results.security_score:.2f}/100")
        
        if hasattr(result, 'compliance_results'):
            print(f"   • Compliance Score: {result.compliance_results.compliance_score:.2%}")
        
        # Generate executive dashboard
        print("\n📊 Generating executive dashboard...")
        
        # Prepare data for dashboard
        performance_data = {
            "performance_score": result.functional_results.quality_score if hasattr(result, 'functional_results') else 85,
            "execution_times": [1.2, 2.1, 1.8, 2.5, 1.9, 2.3, 1.7],
            "success_rate": result.success_rate,
            "error_rate": 1 - result.success_rate,
            "average_execution_time": execution_time / result.total_tests if result.total_tests > 0 else 0,
            "median_execution_time": execution_time / result.total_tests * 0.8 if result.total_tests > 0 else 0,
            "p95_execution_time": execution_time / result.total_tests * 1.5 if result.total_tests > 0 else 0
        }
        
        security_data = {
            "vulnerabilities_by_severity": {
                "Critical": 2,
                "High": 5,
                "Medium": 12,
                "Low": 8
            },
            "security_score": result.security_results.security_score if hasattr(result, 'security_results') else 78,
            "vulnerability_trends": {
                "Critical": [3, 2, 1, 2, 1],
                "High": [8, 6, 5, 4, 5],
                "Medium": [15, 13, 12, 10, 12]
            }
        }
        
        compliance_data = {
            "compliance_scores": {
                "GDPR": 85,
                "PCI-DSS": 92,
                "HIPAA": 78
            },
            "overall_compliance": result.compliance_results.compliance_score if hasattr(result, 'compliance_results') else 0.85,
            "status_distribution": {
                "Compliant": 65,
                "Non-Compliant": 15,
                "Partially Compliant": 20
            }
        }
        
        unified_data = {
            "quality_metrics": {
                "Functionality": 88,
                "Security": 78,
                "Compliance": 85,
                "Performance": 82,
                "Reliability": 90
            },
            "domain_scores": {
                "Web Testing": 87,
                "API Testing": 91,
                "Mobile Testing": 83,
                "Security": 78,
                "Compliance": 85
            },
            "risk_distribution": {
                "Low Risk": 60,
                "Medium Risk": 30,
                "High Risk": 10
            }
        }
        
        # Generate dashboard
        dashboard_html = generate_executive_dashboard(
            performance_data=performance_data,
            security_data=security_data,
            compliance_data=compliance_data,
            unified_data=unified_data
        )
        
        # Save dashboard
        dashboard_path = f"reports/executive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        print(f"✅ Executive dashboard saved to: {dashboard_path}")
        
        # Generate comprehensive report
        print("\n📄 Generating comprehensive report...")
        comprehensive_report = await self.report_generator.generate_comprehensive_report(
            functional_results=result.functional_results if hasattr(result, 'functional_results') else None,
            security_results=result.security_results if hasattr(result, 'security_results') else None,
            compliance_results=result.compliance_results if hasattr(result, 'compliance_results') else None
        )
        
        # Save comprehensive report
        report_path = f"reports/comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_report.html_content)
        
        print(f"✅ Comprehensive report saved to: {report_path}")
        
        return result
    
    async def example_5_custom_workflow(self):
        """
        Example 5: Custom workflow with specific requirements
        """
        print("\n⚙️ Example 5: Custom Workflow")
        print("=" * 50)
        
        # Step 1: Run functional tests first
        print("🧪 Step 1: Running functional tests...")
        functional_plan = create_comprehensive_test_plan(
            target_url="https://demo.testfire.net",
            execution_strategy=UnifiedExecutionStrategy.SEQUENTIAL,
            include_security=False,
            include_compliance=False
        )
        
        functional_result = await self.unified_orchestrator.execute_unified_plan(functional_plan)
        print(f"   ✅ Functional tests completed: {functional_result.success_rate:.2%} success rate")
        
        # Step 2: Run security scans only if functional tests pass
        if functional_result.success_rate >= 0.8:  # 80% success threshold
            print("🔒 Step 2: Running security scans...")
            security_plan = create_security_focused_plan(
                target_url="https://demo.testfire.net",
                security_tools=["owasp_zap", "snyk"]
            )
            
            security_result = await self.unified_orchestrator.execute_unified_plan(security_plan)
            print(f"   ✅ Security scans completed")
            
            # Step 3: Run compliance checks only if security is acceptable
            if hasattr(security_result, 'security_results') and security_result.security_results.security_score >= 70:
                print("📋 Step 3: Running compliance checks...")
                compliance_plan = create_compliance_focused_plan(
                    target_url="https://demo.testfire.net",
                    compliance_standards=["GDPR", "PCI_DSS"]
                )
                
                compliance_result = await self.unified_orchestrator.execute_unified_plan(compliance_plan)
                print(f"   ✅ Compliance checks completed")
                
                # Generate final report
                print("📄 Generating final workflow report...")
                final_report = await self.report_generator.generate_comprehensive_report(
                    functional_results=functional_result.functional_results if hasattr(functional_result, 'functional_results') else None,
                    security_results=security_result.security_results if hasattr(security_result, 'security_results') else None,
                    compliance_results=compliance_result.compliance_results if hasattr(compliance_result, 'compliance_results') else None
                )
                
                report_path = f"reports/custom_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(final_report.html_content)
                
                print(f"✅ Custom workflow report saved to: {report_path}")
            else:
                print("❌ Security score too low, skipping compliance checks")
        else:
            print("❌ Functional tests failed, skipping security and compliance")
        
        print("🎉 Custom workflow completed!")


async def main():
    """
    Main function to run all examples
    """
    print("🌟 Unified Testing Framework - Example Usage")
    print("=" * 60)
    print("This example demonstrates comprehensive testing capabilities")
    print("including functional, security, and compliance testing.\n")
    
    # Initialize example class
    example = UnifiedTestingExample()
    
    try:
        # Run examples
        print("Starting example demonstrations...\n")
        
        # Example 1: Basic unified testing
        await example.example_1_basic_unified_testing()
        
        # Example 2: Security-focused testing
        await example.example_2_security_focused_testing()
        
        # Example 3: Compliance assessment
        await example.example_3_compliance_assessment()
        
        # Example 4: Comprehensive assessment
        await example.example_4_comprehensive_assessment()
        
        # Example 5: Custom workflow
        await example.example_5_custom_workflow()
        
        print("\n🎉 All examples completed successfully!")
        print("📁 Check the 'reports' directory for generated reports and dashboards.")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    # Set up environment
    os.makedirs("reports", exist_ok=True)
    
    # Run examples
    asyncio.run(main())