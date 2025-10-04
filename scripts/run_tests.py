#!/usr/bin/env python3
"""
Test Runner Script

Comprehensive test runner for the AI-powered testing framework.
Supports web, mobile, API, security, and unit testing.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Comprehensive test runner"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {}
        self.start_time = datetime.now()
        
        # Create output directories
        self.output_dir = Path(config.get('output_dir', 'test_results'))
        self.output_dir.mkdir(exist_ok=True)
        
        self.reports_dir = self.output_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.artifacts_dir = self.output_dir / 'artifacts'
        self.artifacts_dir.mkdir(exist_ok=True)
    
    def run_all_tests(self) -> Dict:
        """Run all configured test types"""
        logger.info("Starting comprehensive test run...")
        
        test_types = self.config.get('test_types', [])
        
        for test_type in test_types:
            try:
                logger.info(f"Running {test_type} tests...")
                
                if test_type == 'unit':
                    result = self.run_unit_tests()
                elif test_type == 'web':
                    result = self.run_web_tests()
                elif test_type == 'mobile':
                    result = self.run_mobile_tests()
                elif test_type == 'api':
                    result = self.run_api_tests()
                elif test_type == 'security':
                    result = self.run_security_tests()
                elif test_type == 'performance':
                    result = self.run_performance_tests()
                elif test_type == 'integration':
                    result = self.run_integration_tests()
                else:
                    logger.warning(f"Unknown test type: {test_type}")
                    continue
                
                self.results[test_type] = result
                
                if result['success']:
                    logger.info(f"✅ {test_type} tests completed successfully")
                else:
                    logger.error(f"❌ {test_type} tests failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Exception during {test_type} tests: {str(e)}")
                self.results[test_type] = {
                    'success': False,
                    'error': str(e),
                    'duration': 0,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0
                }
        
        return self.results
    
    def run_unit_tests(self) -> Dict:
        """Run unit tests with pytest"""
        try:
            start_time = datetime.now()
            
            # Prepare pytest command
            cmd = [
                'python', '-m', 'pytest',
                'tests/unit/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/unit_tests.json',
                '--html', f'{self.reports_dir}/unit_tests.html',
                '--self-contained-html',
                '--cov=src',
                f'--cov-report=html:{self.reports_dir}/coverage_html',
                f'--cov-report=json:{self.reports_dir}/coverage.json'
            ]
            
            # Add markers if specified
            markers = self.config.get('unit_tests', {}).get('markers', [])
            if markers:
                cmd.extend(['-m', ' or '.join(markers)])
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'unit_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'coverage': self._get_coverage_percentage(),
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'unit_tests.html'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_web_tests(self) -> Dict:
        """Run web tests with Playwright"""
        try:
            start_time = datetime.now()
            
            # Prepare Playwright command
            cmd = [
                'python', '-m', 'pytest',
                'tests/web/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/web_tests.json',
                '--html', f'{self.reports_dir}/web_tests.html',
                '--self-contained-html'
            ]
            
            # Add browser configuration
            web_config = self.config.get('web_tests', {})
            browsers = web_config.get('browsers', ['chromium'])
            
            if len(browsers) == 1:
                cmd.extend(['--browser', browsers[0]])
            
            # Add headless mode
            if web_config.get('headless', True):
                cmd.append('--headed')
            
            # Add parallel execution
            workers = web_config.get('workers', 1)
            if workers > 1:
                cmd.extend(['-n', str(workers)])
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'web_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'browsers': browsers,
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'web_tests.html'),
                    'artifacts_dir': str(self.artifacts_dir / 'web'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_mobile_tests(self) -> Dict:
        """Run mobile tests with Appium"""
        try:
            start_time = datetime.now()
            
            # Check if Appium server is running
            appium_url = os.getenv('APPIUM_SERVER_URL', 'http://localhost:4723')
            
            # Prepare mobile test command
            cmd = [
                'python', '-m', 'pytest',
                'tests/mobile/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/mobile_tests.json',
                '--html', f'{self.reports_dir}/mobile_tests.html',
                '--self-contained-html'
            ]
            
            # Add platform configuration
            mobile_config = self.config.get('mobile_tests', {})
            platform = mobile_config.get('platform', 'android')
            cmd.extend(['--platform', platform])
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'mobile_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'platform': platform,
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'mobile_tests.html'),
                    'artifacts_dir': str(self.artifacts_dir / 'mobile'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_api_tests(self) -> Dict:
        """Run API tests"""
        try:
            start_time = datetime.now()
            
            # Prepare API test command
            cmd = [
                'python', '-m', 'pytest',
                'tests/api/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/api_tests.json',
                '--html', f'{self.reports_dir}/api_tests.html',
                '--self-contained-html'
            ]
            
            # Add API configuration
            api_config = self.config.get('api_tests', {})
            base_url = api_config.get('base_url')
            if base_url:
                cmd.extend(['--base-url', base_url])
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'api_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'base_url': base_url,
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'api_tests.html'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_security_tests(self) -> Dict:
        """Run security tests with OWASP ZAP"""
        try:
            start_time = datetime.now()
            
            security_config = self.config.get('security_tests', {})
            target_url = security_config.get('target_url', 'http://localhost:8000')
            scan_type = security_config.get('scan_type', 'baseline')
            
            # Prepare ZAP command
            cmd = [
                'python', 'scripts/run_security_scan.py',
                '--target', target_url,
                '--scan-type', scan_type,
                '--output', str(self.reports_dir / 'security_report.json')
            ]
            
            # Run security scan
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            security_report_file = self.reports_dir / 'security_report.json'
            if security_report_file.exists():
                with open(security_report_file) as f:
                    report_data = json.load(f)
                
                alerts = report_data.get('site', [{}])[0].get('alerts', [])
                high_alerts = [a for a in alerts if a.get('riskdesc', '').startswith('High')]
                medium_alerts = [a for a in alerts if a.get('riskdesc', '').startswith('Medium')]
                low_alerts = [a for a in alerts if a.get('riskdesc', '').startswith('Low')]
                
                return {
                    'success': result.returncode == 0 and len(high_alerts) == 0,
                    'duration': duration,
                    'total_alerts': len(alerts),
                    'high_alerts': len(high_alerts),
                    'medium_alerts': len(medium_alerts),
                    'low_alerts': len(low_alerts),
                    'target_url': target_url,
                    'scan_type': scan_type,
                    'report_file': str(security_report_file),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'total_alerts': 0,
                    'high_alerts': 0,
                    'medium_alerts': 0,
                    'low_alerts': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'total_alerts': 0,
                'high_alerts': 0,
                'medium_alerts': 0,
                'low_alerts': 0
            }
    
    def run_performance_tests(self) -> Dict:
        """Run performance tests"""
        try:
            start_time = datetime.now()
            
            # Prepare performance test command
            cmd = [
                'python', '-m', 'pytest',
                'tests/performance/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/performance_tests.json',
                '--html', f'{self.reports_dir}/performance_tests.html',
                '--self-contained-html'
            ]
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'performance_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'performance_tests.html'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_integration_tests(self) -> Dict:
        """Run integration tests"""
        try:
            start_time = datetime.now()
            
            # Prepare integration test command
            cmd = [
                'python', '-m', 'pytest',
                'tests/integration/',
                '--verbose',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.reports_dir}/integration_tests.json',
                '--html', f'{self.reports_dir}/integration_tests.html',
                '--self-contained-html'
            ]
            
            # Run tests
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            json_report_file = self.reports_dir / 'integration_tests.json'
            if json_report_file.exists():
                with open(json_report_file) as f:
                    report_data = json.load(f)
                
                summary = report_data.get('summary', {})
                
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'report_file': str(json_report_file),
                    'html_report': str(self.reports_dir / 'integration_tests.html'),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'duration': duration,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def _get_coverage_percentage(self) -> Optional[float]:
        """Get code coverage percentage"""
        try:
            coverage_file = self.reports_dir / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                
                totals = coverage_data.get('totals', {})
                percent_covered = totals.get('percent_covered')
                
                return percent_covered
        except:
            pass
        
        return None
    
    def generate_summary_report(self) -> str:
        """Generate summary report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = []
        report.append("=" * 80)
        report.append("TEST EXECUTION SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Duration: {total_duration:.2f} seconds")
        report.append("")
        
        # Overall statistics
        total_tests = sum(r.get('tests_run', 0) for r in self.results.values())
        total_passed = sum(r.get('tests_passed', 0) for r in self.results.values())
        total_failed = sum(r.get('tests_failed', 0) for r in self.results.values())
        total_skipped = sum(r.get('tests_skipped', 0) for r in self.results.values())
        
        successful_suites = sum(1 for r in self.results.values() if r.get('success', False))
        total_suites = len(self.results)
        
        report.append("OVERALL STATISTICS:")
        report.append(f"Test Suites: {successful_suites}/{total_suites} passed")
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {total_passed} ✅")
        report.append(f"Failed: {total_failed} ❌")
        report.append(f"Skipped: {total_skipped} ⏭️")
        
        if total_tests > 0:
            pass_rate = (total_passed / total_tests) * 100
            report.append(f"Pass Rate: {pass_rate:.1f}%")
        
        report.append("")
        
        # Detailed results by test type
        report.append("DETAILED RESULTS BY TEST TYPE:")
        report.append("-" * 40)
        
        for test_type, result in self.results.items():
            status_icon = "✅" if result.get('success', False) else "❌"
            duration = result.get('duration', 0)
            tests_run = result.get('tests_run', 0)
            tests_passed = result.get('tests_passed', 0)
            tests_failed = result.get('tests_failed', 0)
            
            report.append(f"{status_icon} {test_type.upper()} TESTS:")
            report.append(f"   Duration: {duration:.2f}s")
            report.append(f"   Tests: {tests_run} (Passed: {tests_passed}, Failed: {tests_failed})")
            
            # Add specific metrics for different test types
            if test_type == 'unit' and 'coverage' in result:
                coverage = result['coverage']
                if coverage is not None:
                    report.append(f"   Coverage: {coverage:.1f}%")
            
            elif test_type == 'security':
                total_alerts = result.get('total_alerts', 0)
                high_alerts = result.get('high_alerts', 0)
                medium_alerts = result.get('medium_alerts', 0)
                low_alerts = result.get('low_alerts', 0)
                
                report.append(f"   Security Alerts: {total_alerts} (High: {high_alerts}, Medium: {medium_alerts}, Low: {low_alerts})")
            
            elif test_type == 'web' and 'browsers' in result:
                browsers = result['browsers']
                report.append(f"   Browsers: {', '.join(browsers)}")
            
            elif test_type == 'mobile' and 'platform' in result:
                platform = result['platform']
                report.append(f"   Platform: {platform}")
            
            # Add error information if test failed
            if not result.get('success', False) and 'error' in result:
                report.append(f"   Error: {result['error']}")
            
            report.append("")
        
        # Report files
        report.append("GENERATED REPORTS:")
        report.append("-" * 20)
        
        for test_type, result in self.results.items():
            if 'html_report' in result:
                report.append(f"{test_type.capitalize()}: {result['html_report']}")
            elif 'report_file' in result:
                report.append(f"{test_type.capitalize()}: {result['report_file']}")
        
        report.append("")
        
        # Final status
        report.append("=" * 80)
        
        if total_failed == 0 and successful_suites == total_suites:
            report.append("🎉 ALL TESTS PASSED!")
            report.append("The application is ready for deployment.")
        elif total_failed > 0:
            report.append("❌ SOME TESTS FAILED")
            report.append("Please review the failed tests before deployment.")
        else:
            report.append("⚠️  TESTS COMPLETED WITH ISSUES")
            report.append("Some test suites encountered problems.")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def upload_results(self):
        """Upload test results to database and storage"""
        try:
            logger.info("Uploading test results...")
            
            for test_type, result in self.results.items():
                if 'report_file' in result and Path(result['report_file']).exists():
                    # Upload using the upload script
                    cmd = [
                        'python', 'scripts/upload_test_results.py',
                        '--input', result['report_file'],
                        '--framework', test_type,
                        '--environment', self.config.get('environment', 'local'),
                        '--branch', self.config.get('branch', 'main'),
                        '--commit', self.config.get('commit_hash', 'unknown')
                    ]
                    
                    if 'artifacts_dir' in result:
                        cmd.extend(['--artifacts-dir', result['artifacts_dir']])
                    
                    subprocess.run(cmd, cwd=Path.cwd())
            
            logger.info("✅ Test results uploaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to upload test results: {str(e)}")


def load_config(config_file: Optional[str] = None) -> Dict:
    """Load test configuration"""
    default_config = {
        'test_types': ['unit', 'web', 'api'],
        'output_dir': 'test_results',
        'environment': 'local',
        'branch': 'main',
        'unit_tests': {
            'markers': []
        },
        'web_tests': {
            'browsers': ['chromium'],
            'headless': True,
            'workers': 1
        },
        'mobile_tests': {
            'platform': 'android'
        },
        'api_tests': {
            'base_url': 'http://localhost:8000'
        },
        'security_tests': {
            'target_url': 'http://localhost:8000',
            'scan_type': 'baseline'
        }
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
            
            # Merge configurations
            default_config.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    return default_config


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive Test Runner')
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--test-types', '-t',
        nargs='+',
        choices=['unit', 'web', 'mobile', 'api', 'security', 'performance', 'integration'],
        help='Test types to run'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='test_results',
        help='Output directory for test results'
    )
    
    parser.add_argument(
        '--environment', '-e',
        default='local',
        help='Test environment'
    )
    
    parser.add_argument(
        '--branch', '-b',
        default='main',
        help='Git branch'
    )
    
    parser.add_argument(
        '--commit',
        help='Git commit hash'
    )
    
    parser.add_argument(
        '--upload',
        action='store_true',
        help='Upload results to database'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override with command line arguments
        if args.test_types:
            config['test_types'] = args.test_types
        
        if args.output_dir:
            config['output_dir'] = args.output_dir
        
        if args.environment:
            config['environment'] = args.environment
        
        if args.branch:
            config['branch'] = args.branch
        
        if args.commit:
            config['commit_hash'] = args.commit
        
        # Create test runner
        runner = TestRunner(config)
        
        # Run tests
        results = runner.run_all_tests()
        
        # Generate summary report
        summary = runner.generate_summary_report()
        print(summary)
        
        # Save summary report
        summary_file = Path(config['output_dir']) / 'test_summary.txt'
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"\nSummary report saved to: {summary_file}")
        
        # Save detailed results
        results_file = Path(config['output_dir']) / 'test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Detailed results saved to: {results_file}")
        
        # Upload results if requested
        if args.upload:
            runner.upload_results()
        
        # Exit with appropriate code
        failed_suites = sum(1 for r in results.values() if not r.get('success', False))
        sys.exit(1 if failed_suites > 0 else 0)
        
    except KeyboardInterrupt:
        print("\nTest execution cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()