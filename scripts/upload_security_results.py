#!/usr/bin/env python3
"""
Script to upload OWASP ZAP security scan results to the database.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import (
    DatabaseManager, TestRun, TestCase, TestArtifact, TestEnvironment,
    TestStatus, TestType, EnvironmentType
)


class SecurityResultsUploader:
    """Handles uploading OWASP ZAP security scan results to database."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def parse_zap_report(self, report_file: str) -> Dict:
        """Parse OWASP ZAP JSON report."""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing ZAP report {report_file}: {e}")
            return {}
    
    def create_test_run(self, scan_type: str, target_url: str, branch: str, 
                       commit: str, triggered_by: str) -> TestRun:
        """Create a test run record for the security scan."""
        with self.db_manager.get_session() as session:
            # Get or create test environment
            environment = session.query(TestEnvironment).filter_by(
                name=f"security-{scan_type}",
                type=EnvironmentType.STAGING
            ).first()
            
            if not environment:
                environment = TestEnvironment(
                    name=f"security-{scan_type}",
                    type=EnvironmentType.STAGING,
                    description=f"OWASP ZAP {scan_type} scan environment",
                    config={
                        "target_url": target_url,
                        "scan_type": scan_type,
                        "tool": "OWASP ZAP"
                    }
                )
                session.add(environment)
                session.flush()
            
            # Create test run
            test_run = TestRun(
                name=f"Security Scan - {scan_type.title()}",
                type=TestType.SECURITY,
                status=TestStatus.RUNNING,
                environment_id=environment.id,
                branch=branch,
                commit_hash=commit,
                triggered_by=triggered_by,
                config={
                    "target_url": target_url,
                    "scan_type": scan_type,
                    "tool": "OWASP ZAP",
                    "tool_version": "latest"
                }
            )
            
            session.add(test_run)
            session.commit()
            session.refresh(test_run)
            
            return test_run
    
    def process_zap_alerts(self, zap_data: Dict, test_run: TestRun) -> List[TestCase]:
        """Process ZAP alerts and create test cases."""
        test_cases = []
        
        if not zap_data.get('site'):
            return test_cases
        
        with self.db_manager.get_session() as session:
            for site in zap_data['site']:
                if not site.get('alerts'):
                    continue
                
                for alert in site['alerts']:
                    # Determine test status based on risk level
                    risk_level = alert.get('riskdesc', '').lower()
                    if 'high' in risk_level:
                        status = TestStatus.FAILED
                    elif 'medium' in risk_level:
                        status = TestStatus.FAILED
                    elif 'low' in risk_level:
                        status = TestStatus.WARNING
                    else:
                        status = TestStatus.PASSED
                    
                    # Create test case for each alert
                    test_case = TestCase(
                        test_run_id=test_run.id,
                        name=alert.get('name', 'Unknown Alert'),
                        status=status,
                        duration=0.0,  # ZAP doesn't provide individual alert duration
                        error_message=alert.get('desc', '') if status == TestStatus.FAILED else None,
                        metadata={
                            'alert_id': alert.get('pluginid'),
                            'risk_level': alert.get('riskdesc'),
                            'confidence': alert.get('confidence'),
                            'description': alert.get('desc'),
                            'solution': alert.get('solution'),
                            'reference': alert.get('reference'),
                            'cweid': alert.get('cweid'),
                            'wascid': alert.get('wascid'),
                            'sourceid': alert.get('sourceid'),
                            'instances': alert.get('instances', [])
                        }
                    )
                    
                    session.add(test_case)
                    test_cases.append(test_case)
            
            session.commit()
        
        return test_cases
    
    def create_artifacts(self, test_run: TestRun, results_file: str, 
                        scan_type: str) -> List[TestArtifact]:
        """Create test artifacts for the security scan."""
        artifacts = []
        
        with self.db_manager.get_session() as session:
            # Main results file
            if os.path.exists(results_file):
                artifact = TestArtifact(
                    test_run_id=test_run.id,
                    name=f"zap-{scan_type}-report.json",
                    type="security_report",
                    file_path=results_file,
                    file_size=os.path.getsize(results_file),
                    metadata={
                        "format": "json",
                        "tool": "OWASP ZAP",
                        "scan_type": scan_type
                    }
                )
                session.add(artifact)
                artifacts.append(artifact)
            
            # Look for additional report formats
            report_dir = Path(results_file).parent
            base_name = f"zap-{scan_type}-report"
            
            for ext in ['.html', '.xml', '.md']:
                report_file = report_dir / f"{base_name}{ext}"
                if report_file.exists():
                    artifact = TestArtifact(
                        test_run_id=test_run.id,
                        name=report_file.name,
                        type="security_report",
                        file_path=str(report_file),
                        file_size=report_file.stat().st_size,
                        metadata={
                            "format": ext[1:],  # Remove the dot
                            "tool": "OWASP ZAP",
                            "scan_type": scan_type
                        }
                    )
                    session.add(artifact)
                    artifacts.append(artifact)
            
            session.commit()
        
        return artifacts
    
    def update_test_run_status(self, test_run: TestRun, test_cases: List[TestCase]):
        """Update test run status based on test cases."""
        with self.db_manager.get_session() as session:
            # Refresh test_run from database
            test_run = session.merge(test_run)
            
            # Calculate summary statistics
            total_cases = len(test_cases)
            failed_cases = sum(1 for tc in test_cases if tc.status == TestStatus.FAILED)
            warning_cases = sum(1 for tc in test_cases if tc.status == TestStatus.WARNING)
            passed_cases = sum(1 for tc in test_cases if tc.status == TestStatus.PASSED)
            
            # Determine overall status
            if failed_cases > 0:
                overall_status = TestStatus.FAILED
            elif warning_cases > 0:
                overall_status = TestStatus.WARNING
            else:
                overall_status = TestStatus.PASSED
            
            # Update test run
            test_run.status = overall_status
            test_run.end_time = datetime.utcnow()
            test_run.total_tests = total_cases
            test_run.passed_tests = passed_cases
            test_run.failed_tests = failed_cases
            test_run.skipped_tests = 0
            
            # Update metadata with security-specific info
            if test_run.metadata is None:
                test_run.metadata = {}
            
            test_run.metadata.update({
                'warning_tests': warning_cases,
                'high_risk_alerts': sum(1 for tc in test_cases 
                                      if tc.metadata and 'high' in tc.metadata.get('risk_level', '').lower()),
                'medium_risk_alerts': sum(1 for tc in test_cases 
                                        if tc.metadata and 'medium' in tc.metadata.get('risk_level', '').lower()),
                'low_risk_alerts': sum(1 for tc in test_cases 
                                     if tc.metadata and 'low' in tc.metadata.get('risk_level', '').lower()),
                'info_alerts': sum(1 for tc in test_cases 
                                 if tc.metadata and 'informational' in tc.metadata.get('risk_level', '').lower())
            })
            
            session.commit()
    
    def upload_results(self, scan_type: str, results_file: str, target_url: str,
                      branch: str, commit: str, triggered_by: str) -> bool:
        """Upload security scan results to database."""
        try:
            print(f"Uploading {scan_type} security scan results...")
            
            # Parse ZAP report
            zap_data = self.parse_zap_report(results_file)
            if not zap_data:
                print("No data found in ZAP report")
                return False
            
            # Create test run
            test_run = self.create_test_run(scan_type, target_url, branch, commit, triggered_by)
            print(f"Created test run: {test_run.id}")
            
            # Process alerts as test cases
            test_cases = self.process_zap_alerts(zap_data, test_run)
            print(f"Processed {len(test_cases)} security alerts")
            
            # Create artifacts
            artifacts = self.create_artifacts(test_run, results_file, scan_type)
            print(f"Created {len(artifacts)} artifacts")
            
            # Update test run status
            self.update_test_run_status(test_run, test_cases)
            print(f"Updated test run status to: {test_run.status}")
            
            print("Security scan results uploaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error uploading security results: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Upload OWASP ZAP security scan results to database")
    parser.add_argument("--type", required=True, choices=["baseline", "full", "api", "ajax"],
                       help="Type of security scan")
    parser.add_argument("--results-file", required=True, help="Path to ZAP JSON results file")
    parser.add_argument("--target-url", required=True, help="Target URL that was scanned")
    parser.add_argument("--branch", required=True, help="Git branch")
    parser.add_argument("--commit", required=True, help="Git commit hash")
    parser.add_argument("--triggered-by", required=True, help="Who/what triggered the scan")
    
    args = parser.parse_args()
    
    # Validate results file exists
    if not os.path.exists(args.results_file):
        print(f"Results file not found: {args.results_file}")
        sys.exit(1)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Upload results
    uploader = SecurityResultsUploader(db_manager)
    success = uploader.upload_results(
        scan_type=args.type,
        results_file=args.results_file,
        target_url=args.target_url,
        branch=args.branch,
        commit=args.commit,
        triggered_by=args.triggered_by
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()