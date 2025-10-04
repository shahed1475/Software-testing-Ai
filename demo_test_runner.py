#!/usr/bin/env python3
"""
Live Demo of Test Runner Agent System
=====================================

This demo showcases the complete Test Runner Agent system with:
- Test Runner Agent (GitHub Actions integration)
- Report Collector Agent (S3 artifact collection)
- Enhanced Notifier Agent (Email/Slack notifications)
- Report Generator Agent
- AI Failure Analyzer
- Test Orchestrator

Run this script to see the system in action!
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.test_runner_agent import TestRunnerAgent
from agents.report_collector_agent import ReportCollectorAgent
from agents.notifier_agent import NotifierAgent, EmailChannel, SlackChannel
from agents.report_generator_agent import ReportGeneratorAgent
from config.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('demo_test_runner.log')
    ]
)
logger = logging.getLogger(__name__)

class TestRunnerDemo:
    """Live demo of the Test Runner Agent system"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.demo_data = self._create_demo_data()
        self.agents = {}
        self.results = {}
        
    def _create_demo_data(self) -> Dict[str, Any]:
        """Create mock demo data for testing"""
        return {
            "test_scenarios": [
                {
                    "name": "API Tests",
                    "type": "api",
                    "workflow": "test-api.yml",
                    "expected_duration": 300,
                    "description": "Comprehensive API testing suite"
                },
                {
                    "name": "Web UI Tests",
                    "type": "web",
                    "workflow": "test-web.yml", 
                    "expected_duration": 600,
                    "description": "End-to-end web UI testing"
                },
                {
                    "name": "Security Tests",
                    "type": "security",
                    "workflow": "test-security.yml",
                    "expected_duration": 900,
                    "description": "Security vulnerability scanning"
                },
                {
                    "name": "Mobile Tests",
                    "type": "mobile",
                    "workflow": "test-mobile.yml",
                    "expected_duration": 450,
                    "description": "Mobile app testing suite"
                }
            ],
            "mock_results": {
                "api": {
                    "total_tests": 45,
                    "passed": 42,
                    "failed": 3,
                    "skipped": 0,
                    "duration": 285,
                    "coverage": 87.5,
                    "failures": [
                        {"test": "test_user_authentication", "error": "Connection timeout"},
                        {"test": "test_payment_processing", "error": "Invalid response format"},
                        {"test": "test_data_validation", "error": "Schema validation failed"}
                    ]
                },
                "web": {
                    "total_tests": 32,
                    "passed": 30,
                    "failed": 2,
                    "skipped": 0,
                    "duration": 580,
                    "coverage": 92.3,
                    "failures": [
                        {"test": "test_checkout_flow", "error": "Element not found: #submit-button"},
                        {"test": "test_responsive_design", "error": "Viewport assertion failed"}
                    ]
                },
                "security": {
                    "total_tests": 28,
                    "passed": 25,
                    "failed": 3,
                    "skipped": 0,
                    "duration": 875,
                    "coverage": 89.3,
                    "vulnerabilities": [
                        {"severity": "HIGH", "type": "SQL Injection", "location": "/api/users"},
                        {"severity": "MEDIUM", "type": "XSS", "location": "/dashboard"},
                        {"severity": "LOW", "type": "Information Disclosure", "location": "/health"}
                    ]
                },
                "mobile": {
                    "total_tests": 38,
                    "passed": 36,
                    "failed": 2,
                    "skipped": 0,
                    "duration": 420,
                    "coverage": 85.7,
                    "failures": [
                        {"test": "test_push_notifications", "error": "Permission denied"},
                        {"test": "test_offline_mode", "error": "Network simulation failed"}
                    ]
                }
            }
        }
    
    async def initialize_agents(self):
        """Initialize all agents for the demo"""
        print("\n🚀 Initializing Test Runner Agent System...")
        print("=" * 60)
        
        try:
            # Initialize Test Runner Agent
            print("📋 Initializing Test Runner Agent...")
            self.agents['test_runner'] = TestRunnerAgent({
                'github_token': os.getenv('GITHUB_TOKEN', 'demo_token'),
                'repository': 'demo/test-repo',
                'timeout': 1800
            })
            
            # Initialize Report Collector Agent
            print("📊 Initializing Report Collector Agent...")
            self.agents['report_collector'] = ReportCollectorAgent({
                'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID', 'demo_key'),
                'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY', 'demo_secret'),
                'bucket_name': 'demo-test-artifacts',
                'region': 'us-east-1'
            })
            
            # Initialize Notifier Agent
            print("📧 Initializing Notifier Agent...")
            email_config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('EMAIL_USERNAME', 'demo@example.com'),
                'password': os.getenv('EMAIL_PASSWORD', 'demo_password'),
                'from_email': os.getenv('FROM_EMAIL', 'demo@example.com')
            }
            
            slack_config = {
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/demo'),
                'bot_token': os.getenv('SLACK_BOT_TOKEN', 'xoxb-demo-token'),
                'channel': os.getenv('SLACK_CHANNEL', '#testing')
            }
            
            self.agents['notifier'] = NotifierAgent({
                'channels': [
                    EmailChannel(email_config),
                    SlackChannel(slack_config)
                ],
                'template_dir': 'templates/notifications'
            })
            
            # Initialize Report Generator Agent
            print("📄 Initializing Report Generator Agent...")
            self.agents['report_generator'] = ReportGeneratorAgent({
                'output_dir': 'reports/generated',
                's3_bucket': 'demo-test-reports',
                'template_dir': 'templates/reports'
            })
            
            print("✅ All agents initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def print_banner(self, title: str, char: str = "="):
        """Print a formatted banner"""
        print(f"\n{char * 60}")
        print(f"{title:^60}")
        print(f"{char * 60}")
    
    async def run_demo_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single demo scenario"""
        scenario_name = scenario['name']
        test_type = scenario['type']
        
        self.print_banner(f"Running {scenario_name}", "=")
        
        print(f"📝 Scenario: {scenario['description']}")
        print(f"🔧 Test Type: {test_type}")
        print(f"⏱️  Expected Duration: {scenario['expected_duration']}s")
        print(f"🔄 Workflow: {scenario['workflow']}")
        
        # Simulate test execution
        print(f"\n🏃 Starting test execution...")
        
        # Mock test runner execution
        start_time = time.time()
        
        # Simulate some processing time
        for i in range(5):
            await asyncio.sleep(0.5)
            progress = (i + 1) * 20
            print(f"⏳ Progress: {progress}% - {'█' * (progress // 5)}{'░' * (20 - progress // 5)}")
        
        execution_time = time.time() - start_time
        
        # Get mock results
        mock_result = self.demo_data['mock_results'][test_type]
        
        result = {
            'scenario': scenario_name,
            'test_type': test_type,
            'status': 'completed',
            'execution_time': execution_time,
            'start_time': datetime.now().isoformat(),
            'results': mock_result,
            'artifacts_collected': True,
            'report_generated': True,
            'notifications_sent': True
        }
        
        # Display results
        print(f"\n📊 Test Results Summary:")
        print(f"   ✅ Total Tests: {mock_result['total_tests']}")
        print(f"   🟢 Passed: {mock_result['passed']}")
        print(f"   🔴 Failed: {mock_result['failed']}")
        print(f"   ⏭️  Skipped: {mock_result['skipped']}")
        print(f"   📈 Coverage: {mock_result.get('coverage', 'N/A')}%")
        print(f"   ⏱️  Duration: {mock_result['duration']}s")
        
        if mock_result['failed'] > 0:
            print(f"\n❌ Failures Detected:")
            failures = mock_result.get('failures', mock_result.get('vulnerabilities', []))
            for i, failure in enumerate(failures[:3], 1):
                if 'test' in failure:
                    print(f"   {i}. {failure['test']}: {failure['error']}")
                else:
                    print(f"   {i}. {failure['severity']} - {failure['type']}: {failure['location']}")
        
        # Simulate artifact collection
        print(f"\n📦 Collecting artifacts...")
        await asyncio.sleep(1)
        print(f"   ✅ Screenshots: 12 files")
        print(f"   ✅ Test logs: 4 files")
        print(f"   ✅ Results JSON: 1 file")
        print(f"   ✅ Coverage report: 1 file")
        
        # Simulate report generation
        print(f"\n📄 Generating reports...")
        await asyncio.sleep(1)
        print(f"   ✅ HTML Report: generated")
        print(f"   ✅ PDF Report: generated")
        print(f"   ✅ JSON Summary: generated")
        print(f"   ✅ Uploaded to S3: success")
        
        # Simulate notifications
        print(f"\n📧 Sending notifications...")
        await asyncio.sleep(0.5)
        print(f"   ✅ Email notification: sent")
        print(f"   ✅ Slack notification: sent")
        
        return result
    
    async def run_full_demo(self):
        """Run the complete demo with all scenarios"""
        self.print_banner("🧪 TEST RUNNER AGENT SYSTEM - LIVE DEMO", "🌟")
        
        print("Welcome to the Test Runner Agent System Demo!")
        print("This demo will showcase:")
        print("• Test execution across multiple platforms")
        print("• Artifact collection from S3")
        print("• Intelligent report generation")
        print("• Multi-channel notifications")
        print("• AI-powered failure analysis")
        
        # Initialize agents
        await self.initialize_agents()
        
        # Run all test scenarios
        all_results = []
        
        for i, scenario in enumerate(self.demo_data['test_scenarios'], 1):
            print(f"\n🎯 Running Scenario {i}/{len(self.demo_data['test_scenarios'])}")
            result = await self.run_demo_scenario(scenario)
            all_results.append(result)
            
            # Short pause between scenarios
            if i < len(self.demo_data['test_scenarios']):
                print("\n⏸️  Pausing before next scenario...")
                await asyncio.sleep(2)
        
        # Generate summary report
        await self.generate_summary_report(all_results)
        
        # Show system metrics
        self.show_system_metrics(all_results)
        
        print("\n🎉 Demo completed successfully!")
        print("Check the generated reports and logs for detailed information.")
    
    async def generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generate a comprehensive summary report"""
        self.print_banner("📊 GENERATING SUMMARY REPORT", "📈")
        
        total_tests = sum(r['results']['total_tests'] for r in results)
        total_passed = sum(r['results']['passed'] for r in results)
        total_failed = sum(r['results']['failed'] for r in results)
        total_duration = sum(r['results']['duration'] for r in results)
        avg_coverage = sum(r['results'].get('coverage', 0) for r in results) / len(results)
        
        summary = {
            'execution_summary': {
                'total_scenarios': len(results),
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': total_duration,
                'average_coverage': avg_coverage
            },
            'scenario_results': results,
            'generated_at': datetime.now().isoformat(),
            'system_info': {
                'agents_used': list(self.agents.keys()),
                'demo_version': '1.0.0'
            }
        }
        
        # Save summary to file
        summary_file = Path('demo_summary_report.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Summary Report Generated:")
        print(f"   📊 Total Scenarios: {summary['execution_summary']['total_scenarios']}")
        print(f"   🧪 Total Tests: {summary['execution_summary']['total_tests']}")
        print(f"   ✅ Pass Rate: {summary['execution_summary']['pass_rate']:.1f}%")
        print(f"   ⏱️  Total Duration: {summary['execution_summary']['total_duration']}s")
        print(f"   📈 Average Coverage: {summary['execution_summary']['average_coverage']:.1f}%")
        print(f"   💾 Report saved to: {summary_file}")
        
        await asyncio.sleep(1)
    
    def show_system_metrics(self, results: List[Dict[str, Any]]):
        """Display system performance metrics"""
        self.print_banner("⚡ SYSTEM PERFORMANCE METRICS", "⚙️")
        
        print("🔧 Agent Performance:")
        print(f"   🏃 Test Runner: ✅ Active")
        print(f"   📊 Report Collector: ✅ Active")
        print(f"   📧 Notifier: ✅ Active")
        print(f"   📄 Report Generator: ✅ Active")
        
        print(f"\n📈 Execution Metrics:")
        print(f"   ⚡ Average Response Time: 2.3s")
        print(f"   💾 Memory Usage: 145MB")
        print(f"   🌐 Network Requests: 28")
        print(f"   📦 Artifacts Processed: 68 files")
        print(f"   📧 Notifications Sent: {len(results) * 2}")
        
        print(f"\n🎯 Success Rates:")
        print(f"   ✅ Test Execution: 100%")
        print(f"   📦 Artifact Collection: 100%")
        print(f"   📄 Report Generation: 100%")
        print(f"   📧 Notification Delivery: 100%")

def main():
    """Main demo function"""
    print("🌟" * 30)
    print("  TEST RUNNER AGENT SYSTEM")
    print("       LIVE DEMO")
    print("🌟" * 30)
    
    demo = TestRunnerDemo()
    
    try:
        # Run the demo
        asyncio.run(demo.run_full_demo())
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution failed")
    finally:
        print("\n👋 Thank you for trying the Test Runner Agent System!")

if __name__ == "__main__":
    main()