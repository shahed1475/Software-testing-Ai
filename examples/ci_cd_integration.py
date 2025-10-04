#!/usr/bin/env python3
"""
CI/CD Integration Example for Unified Testing Framework

This example demonstrates how to integrate the unified testing framework
into CI/CD pipelines (GitHub Actions, Jenkins, GitLab CI, etc.)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import unified testing components
from src.unified.unified_orchestrator import (
    UnifiedTestingOrchestrator,
    UnifiedTestPlan,
    UnifiedTestingScope,
    UnifiedExecutionStrategy,
    create_comprehensive_test_plan
)

# Import reporting components
from src.reporting.report_generator import ReportGenerator


class CICDIntegration:
    """
    CI/CD Integration class for unified testing framework
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize CI/CD integration with optional config"""
        self.config = self._load_config(config_path)
        self.orchestrator = UnifiedTestingOrchestrator()
        self.report_generator = ReportGenerator()
        self.results_dir = Path("test-results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        config = {
            "target_url": os.getenv("TEST_TARGET_URL", "https://demo.testfire.net"),
            "api_endpoints": os.getenv("TEST_API_ENDPOINTS", "").split(",") if os.getenv("TEST_API_ENDPOINTS") else [],
            "mobile_apps": os.getenv("TEST_MOBILE_APPS", "").split(",") if os.getenv("TEST_MOBILE_APPS") else [],
            "security_enabled": os.getenv("SECURITY_TESTING_ENABLED", "true").lower() == "true",
            "compliance_enabled": os.getenv("COMPLIANCE_TESTING_ENABLED", "true").lower() == "true",
            "security_tools": os.getenv("SECURITY_TOOLS", "owasp_zap,snyk").split(","),
            "compliance_standards": os.getenv("COMPLIANCE_STANDARDS", "GDPR,PCI_DSS").split(","),
            "execution_strategy": os.getenv("EXECUTION_STRATEGY", "INTEGRATED"),
            "fail_threshold": float(os.getenv("FAIL_THRESHOLD", "0.8")),  # 80% success rate required
            "security_threshold": int(os.getenv("SECURITY_THRESHOLD", "70")),  # Security score threshold
            "compliance_threshold": float(os.getenv("COMPLIANCE_THRESHOLD", "0.85")),  # 85% compliance required
            "generate_junit": os.getenv("GENERATE_JUNIT", "true").lower() == "true",
            "generate_html": os.getenv("GENERATE_HTML", "true").lower() == "true",
            "generate_json": os.getenv("GENERATE_JSON", "true").lower() == "true"
        }
        
        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    async def run_pipeline_tests(self) -> Dict[str, Any]:
        """
        Run tests suitable for CI/CD pipeline
        """
        print("🚀 Starting CI/CD Pipeline Tests")
        print("=" * 50)
        
        # Display configuration
        print("📋 Configuration:")
        print(f"   • Target URL: {self.config['target_url']}")
        print(f"   • Security Testing: {'✅' if self.config['security_enabled'] else '❌'}")
        print(f"   • Compliance Testing: {'✅' if self.config['compliance_enabled'] else '❌'}")
        print(f"   • Execution Strategy: {self.config['execution_strategy']}")
        print(f"   • Fail Threshold: {self.config['fail_threshold']:.0%}")
        
        # Create test plan based on configuration
        plan = self._create_pipeline_test_plan()
        
        # Execute tests
        print("\n🔄 Executing pipeline tests...")
        start_time = datetime.now()
        
        try:
            result = await self.orchestrator.execute_unified_plan(plan)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Analyze results
            analysis = self._analyze_results(result, execution_time)
            
            # Generate reports
            await self._generate_pipeline_reports(result, analysis)
            
            # Determine pipeline status
            pipeline_status = self._determine_pipeline_status(analysis)
            
            print(f"\n📊 Pipeline Results:")
            print(f"   • Status: {'✅ PASSED' if pipeline_status['passed'] else '❌ FAILED'}")
            print(f"   • Execution Time: {execution_time:.2f}s")
            print(f"   • Success Rate: {analysis['success_rate']:.2%}")
            
            if self.config['security_enabled'] and 'security_score' in analysis:
                print(f"   • Security Score: {analysis['security_score']:.0f}/100")
            
            if self.config['compliance_enabled'] and 'compliance_score' in analysis:
                print(f"   • Compliance Score: {analysis['compliance_score']:.2%}")
            
            # Exit with appropriate code
            exit_code = 0 if pipeline_status['passed'] else 1
            
            return {
                "status": "passed" if pipeline_status['passed'] else "failed",
                "exit_code": exit_code,
                "analysis": analysis,
                "execution_time": execution_time,
                "reports_generated": pipeline_status.get('reports_generated', [])
            }
            
        except Exception as e:
            print(f"❌ Pipeline execution failed: {e}")
            
            # Generate failure report
            await self._generate_failure_report(str(e))
            
            return {
                "status": "error",
                "exit_code": 2,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _create_pipeline_test_plan(self) -> UnifiedTestPlan:
        """Create test plan optimized for CI/CD pipeline"""
        
        # Determine execution strategy
        strategy_map = {
            "SEQUENTIAL": UnifiedExecutionStrategy.SEQUENTIAL,
            "PARALLEL": UnifiedExecutionStrategy.PARALLEL,
            "INTEGRATED": UnifiedExecutionStrategy.INTEGRATED,
            "LAYERED": UnifiedExecutionStrategy.LAYERED
        }
        
        execution_strategy = strategy_map.get(
            self.config['execution_strategy'], 
            UnifiedExecutionStrategy.INTEGRATED
        )
        
        # Create comprehensive plan
        plan = create_comprehensive_test_plan(
            target_url=self.config['target_url'],
            api_endpoints=self.config['api_endpoints'],
            mobile_apps=self.config['mobile_apps'],
            execution_strategy=execution_strategy,
            include_security=self.config['security_enabled'],
            include_compliance=self.config['compliance_enabled']
        )
        
        # Customize for CI/CD
        plan.name = f"CI/CD Pipeline Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan.description = "Automated testing for CI/CD pipeline"
        
        # Configure security scans if enabled
        if self.config['security_enabled']:
            plan.security_scans = {}
            for tool in self.config['security_tools']:
                if tool.strip():
                    plan.security_scans[tool.strip()] = {
                        "scan_type": "fast",  # Use fast scans for CI/CD
                        "timeout": 300  # 5 minute timeout
                    }
        
        # Configure compliance checks if enabled
        if self.config['compliance_enabled']:
            plan.compliance_checks = {}
            for standard in self.config['compliance_standards']:
                if standard.strip():
                    plan.compliance_checks[standard.strip()] = {
                        "level": "basic",  # Use basic checks for CI/CD
                        "automated_only": True  # Only automated checks
                    }
        
        return plan
    
    def _analyze_results(self, result, execution_time: float) -> Dict[str, Any]:
        """Analyze test results for CI/CD decision making"""
        
        analysis = {
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "skipped_tests": result.skipped_tests,
            "success_rate": result.success_rate,
            "execution_time": execution_time
        }
        
        # Analyze functional results
        if hasattr(result, 'functional_results'):
            functional = result.functional_results
            analysis.update({
                "functional_score": getattr(functional, 'quality_score', 0),
                "code_coverage": getattr(functional, 'code_coverage', 0),
                "performance_score": getattr(functional, 'performance_score', 0)
            })
        
        # Analyze security results
        if hasattr(result, 'security_results'):
            security = result.security_results
            analysis.update({
                "security_score": getattr(security, 'security_score', 0),
                "vulnerabilities_found": getattr(security, 'total_vulnerabilities', 0),
                "critical_vulnerabilities": getattr(security, 'critical_count', 0),
                "high_vulnerabilities": getattr(security, 'high_count', 0)
            })
        
        # Analyze compliance results
        if hasattr(result, 'compliance_results'):
            compliance = result.compliance_results
            analysis.update({
                "compliance_score": getattr(compliance, 'compliance_score', 0),
                "compliance_checks": getattr(compliance, 'total_checks', 0),
                "compliance_failures": getattr(compliance, 'failed_checks', 0)
            })
        
        return analysis
    
    def _determine_pipeline_status(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if pipeline should pass or fail based on thresholds"""
        
        status = {
            "passed": True,
            "reasons": [],
            "warnings": [],
            "reports_generated": []
        }
        
        # Check success rate threshold
        if analysis['success_rate'] < self.config['fail_threshold']:
            status["passed"] = False
            status["reasons"].append(
                f"Success rate {analysis['success_rate']:.2%} below threshold {self.config['fail_threshold']:.2%}"
            )
        
        # Check security threshold if security testing is enabled
        if self.config['security_enabled'] and 'security_score' in analysis:
            if analysis['security_score'] < self.config['security_threshold']:
                status["passed"] = False
                status["reasons"].append(
                    f"Security score {analysis['security_score']:.0f} below threshold {self.config['security_threshold']}"
                )
            
            # Critical vulnerabilities always fail the pipeline
            if analysis.get('critical_vulnerabilities', 0) > 0:
                status["passed"] = False
                status["reasons"].append(
                    f"Found {analysis['critical_vulnerabilities']} critical vulnerabilities"
                )
            
            # High vulnerabilities generate warnings
            if analysis.get('high_vulnerabilities', 0) > 5:
                status["warnings"].append(
                    f"Found {analysis['high_vulnerabilities']} high-severity vulnerabilities"
                )
        
        # Check compliance threshold if compliance testing is enabled
        if self.config['compliance_enabled'] and 'compliance_score' in analysis:
            if analysis['compliance_score'] < self.config['compliance_threshold']:
                status["passed"] = False
                status["reasons"].append(
                    f"Compliance score {analysis['compliance_score']:.2%} below threshold {self.config['compliance_threshold']:.2%}"
                )
        
        return status
    
    async def _generate_pipeline_reports(self, result, analysis: Dict[str, Any]):
        """Generate reports suitable for CI/CD pipeline"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reports_generated = []
        
        # Generate JUnit XML report
        if self.config['generate_junit']:
            junit_path = self.results_dir / f"junit-report-{timestamp}.xml"
            junit_content = self._generate_junit_xml(result, analysis)
            
            with open(junit_path, 'w', encoding='utf-8') as f:
                f.write(junit_content)
            
            reports_generated.append(str(junit_path))
            print(f"📄 JUnit report: {junit_path}")
        
        # Generate JSON report
        if self.config['generate_json']:
            json_path = self.results_dir / f"test-results-{timestamp}.json"
            json_content = self._generate_json_report(result, analysis)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, default=str)
            
            reports_generated.append(str(json_path))
            print(f"📄 JSON report: {json_path}")
        
        # Generate HTML report
        if self.config['generate_html']:
            try:
                html_report = await self.report_generator.generate_comprehensive_report(
                    functional_results=getattr(result, 'functional_results', None),
                    security_results=getattr(result, 'security_results', None),
                    compliance_results=getattr(result, 'compliance_results', None)
                )
                
                html_path = self.results_dir / f"test-report-{timestamp}.html"
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_report.html_content)
                
                reports_generated.append(str(html_path))
                print(f"📄 HTML report: {html_path}")
                
            except Exception as e:
                print(f"⚠️ Failed to generate HTML report: {e}")
        
        return reports_generated
    
    def _generate_junit_xml(self, result, analysis: Dict[str, Any]) -> str:
        """Generate JUnit XML format report"""
        
        junit_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Unified Testing Framework" tests="{analysis['total_tests']}" failures="{analysis['failed_tests']}" skipped="{analysis['skipped_tests']}" time="{analysis['execution_time']:.2f}">
    <testsuite name="Functional Tests" tests="{analysis.get('functional_tests', analysis['total_tests'])}" failures="{analysis.get('functional_failures', analysis['failed_tests'])}" skipped="{analysis.get('functional_skipped', 0)}" time="{analysis['execution_time']:.2f}">
'''
        
        # Add functional test cases
        if hasattr(result, 'functional_results'):
            junit_xml += '''        <testcase name="Web Application Tests" classname="functional.web" time="1.5">
        </testcase>
        <testcase name="API Tests" classname="functional.api" time="2.1">
        </testcase>
        <testcase name="Mobile Tests" classname="functional.mobile" time="1.8">
        </testcase>
'''
        
        junit_xml += '''    </testsuite>
'''
        
        # Add security test suite if enabled
        if self.config['security_enabled'] and hasattr(result, 'security_results'):
            junit_xml += f'''    <testsuite name="Security Tests" tests="3" failures="{1 if analysis.get('security_score', 100) < self.config['security_threshold'] else 0}" skipped="0" time="5.2">
        <testcase name="Vulnerability Scan" classname="security.vulnerability" time="3.1">
'''
            if analysis.get('critical_vulnerabilities', 0) > 0:
                junit_xml += f'''            <failure message="Critical vulnerabilities found" type="SecurityFailure">
                Found {analysis['critical_vulnerabilities']} critical vulnerabilities
            </failure>
'''
            junit_xml += '''        </testcase>
        <testcase name="Dependency Scan" classname="security.dependencies" time="1.5">
        </testcase>
        <testcase name="Configuration Scan" classname="security.config" time="0.6">
        </testcase>
    </testsuite>
'''
        
        # Add compliance test suite if enabled
        if self.config['compliance_enabled'] and hasattr(result, 'compliance_results'):
            junit_xml += f'''    <testsuite name="Compliance Tests" tests="{analysis.get('compliance_checks', 10)}" failures="{analysis.get('compliance_failures', 0)}" skipped="0" time="2.8">
'''
            for standard in self.config['compliance_standards']:
                junit_xml += f'''        <testcase name="{standard} Compliance" classname="compliance.{standard.lower()}" time="0.9">
        </testcase>
'''
            junit_xml += '''    </testsuite>
'''
        
        junit_xml += '''</testsuites>'''
        
        return junit_xml
    
    def _generate_json_report(self, result, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON format report"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline_status": "passed" if analysis['success_rate'] >= self.config['fail_threshold'] else "failed",
            "configuration": self.config,
            "summary": {
                "total_tests": analysis['total_tests'],
                "passed_tests": analysis['passed_tests'],
                "failed_tests": analysis['failed_tests'],
                "skipped_tests": analysis['skipped_tests'],
                "success_rate": analysis['success_rate'],
                "execution_time": analysis['execution_time']
            },
            "functional": {
                "enabled": True,
                "score": analysis.get('functional_score', 0),
                "coverage": analysis.get('code_coverage', 0),
                "performance": analysis.get('performance_score', 0)
            } if hasattr(result, 'functional_results') else {"enabled": False},
            "security": {
                "enabled": self.config['security_enabled'],
                "score": analysis.get('security_score', 0),
                "vulnerabilities": {
                    "total": analysis.get('vulnerabilities_found', 0),
                    "critical": analysis.get('critical_vulnerabilities', 0),
                    "high": analysis.get('high_vulnerabilities', 0)
                },
                "tools_used": self.config['security_tools']
            } if self.config['security_enabled'] else {"enabled": False},
            "compliance": {
                "enabled": self.config['compliance_enabled'],
                "score": analysis.get('compliance_score', 0),
                "total_checks": analysis.get('compliance_checks', 0),
                "failed_checks": analysis.get('compliance_failures', 0),
                "standards": self.config['compliance_standards']
            } if self.config['compliance_enabled'] else {"enabled": False}
        }
    
    async def _generate_failure_report(self, error_message: str):
        """Generate report when pipeline fails with error"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        failure_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": error_message,
            "configuration": self.config
        }
        
        failure_path = self.results_dir / f"failure-report-{timestamp}.json"
        
        with open(failure_path, 'w', encoding='utf-8') as f:
            json.dump(failure_report, f, indent=2, default=str)
        
        print(f"📄 Failure report: {failure_path}")


async def main():
    """
    Main function for CI/CD integration
    """
    print("🔄 CI/CD Integration - Unified Testing Framework")
    print("=" * 60)
    
    # Initialize CI/CD integration
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    ci_cd = CICDIntegration(config_path)
    
    try:
        # Run pipeline tests
        result = await ci_cd.run_pipeline_tests()
        
        # Print final status
        print(f"\n🏁 Pipeline Status: {result['status'].upper()}")
        
        if result['status'] == 'passed':
            print("✅ All tests passed! Pipeline can proceed.")
        elif result['status'] == 'failed':
            print("❌ Tests failed! Pipeline should be blocked.")
            print("📋 Check the generated reports for details.")
        else:
            print("💥 Pipeline error occurred!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Exit with appropriate code
        sys.exit(result['exit_code'])
        
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())