#!/usr/bin/env python3
"""
Upload Test Results to Database

Script to upload test results from various testing frameworks to the database
for tracking, analysis, and reporting purposes.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.connection import get_database_session
from database.models import TestRun, TestCase, TestArtifact
from reports.json_parser import TestResultParser, TestFramework, TestStatus
from storage import get_storage_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResultsUploader:
    """Upload test results to database"""
    
    def __init__(self):
        self.parser = TestResultParser()
        self.storage_manager = get_storage_manager()
    
    async def upload_results(
        self,
        results_file: Path,
        framework: TestFramework,
        environment: str = "development",
        branch: str = "main",
        commit_hash: Optional[str] = None,
        build_number: Optional[str] = None,
        artifacts_dir: Optional[Path] = None
    ) -> str:
        """Upload test results to database"""
        
        logger.info(f"Uploading test results from {results_file}")
        logger.info(f"Framework: {framework.value}, Environment: {environment}")
        
        # Parse test results
        test_suite = self.parser.parse_file(results_file, framework)
        
        async with get_database_session() as session:
            # Create test run
            test_run = TestRun(
                framework=framework.value,
                environment=environment,
                branch=branch,
                commit_hash=commit_hash,
                build_number=build_number,
                start_time=test_suite.start_time,
                end_time=test_suite.end_time,
                duration=test_suite.duration,
                total_tests=test_suite.total_tests,
                passed_tests=test_suite.passed_tests,
                failed_tests=test_suite.failed_tests,
                skipped_tests=test_suite.skipped_tests,
                status="completed",
                metadata={
                    "framework_version": getattr(test_suite, 'framework_version', None),
                    "platform": getattr(test_suite, 'platform', None),
                    "browser": getattr(test_suite, 'browser', None),
                    "device": getattr(test_suite, 'device', None)
                }
            )
            
            session.add(test_run)
            await session.flush()  # Get the test_run.id
            
            logger.info(f"Created test run with ID: {test_run.id}")
            
            # Upload test cases
            for test_case in test_suite.test_cases:
                db_test_case = TestCase(
                    test_run_id=test_run.id,
                    name=test_case.name,
                    class_name=test_case.class_name,
                    file_path=test_case.file_path,
                    status=test_case.status.value,
                    duration=test_case.duration,
                    error_message=test_case.error_message,
                    error_type=test_case.error_type,
                    stack_trace=test_case.stack_trace,
                    metadata=test_case.metadata or {}
                )
                session.add(db_test_case)
            
            # Upload artifacts if directory provided
            if artifacts_dir and artifacts_dir.exists():
                await self._upload_artifacts(session, test_run.id, artifacts_dir)
            
            # Upload results file as artifact
            await self._upload_results_file(session, test_run.id, results_file)
            
            await session.commit()
            
            logger.info(f"Successfully uploaded {len(test_suite.test_cases)} test cases")
            return test_run.id
    
    async def _upload_artifacts(self, session, test_run_id: str, artifacts_dir: Path):
        """Upload test artifacts to storage and database"""
        
        logger.info(f"Uploading artifacts from {artifacts_dir}")
        
        artifact_patterns = {
            "screenshot": ["*.png", "*.jpg", "*.jpeg"],
            "video": ["*.mp4", "*.webm", "*.avi"],
            "log": ["*.log", "*.txt"],
            "report": ["*.html", "*.xml", "*.json"]
        }
        
        for artifact_type, patterns in artifact_patterns.items():
            for pattern in patterns:
                for artifact_file in artifacts_dir.rglob(pattern):
                    try:
                        # Upload to storage
                        storage_path = await self.storage_manager.store_file(
                            file_path=artifact_file,
                            artifact_type=artifact_type
                        )
                        
                        # Create database record
                        artifact = TestArtifact(
                            test_run_id=test_run_id,
                            artifact_type=artifact_type,
                            file_name=artifact_file.name,
                            file_path=str(artifact_file),
                            storage_path=storage_path,
                            file_size=artifact_file.stat().st_size,
                            content_type=self._get_content_type(artifact_file),
                            metadata={
                                "original_path": str(artifact_file),
                                "upload_time": datetime.utcnow().isoformat()
                            }
                        )
                        session.add(artifact)
                        
                        logger.debug(f"Uploaded artifact: {artifact_file.name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to upload artifact {artifact_file}: {e}")
    
    async def _upload_results_file(self, session, test_run_id: str, results_file: Path):
        """Upload the results file itself as an artifact"""
        
        try:
            # Upload to storage
            storage_path = await self.storage_manager.store_file(
                file_path=results_file,
                artifact_type="report"
            )
            
            # Create database record
            artifact = TestArtifact(
                test_run_id=test_run_id,
                artifact_type="report",
                file_name=results_file.name,
                file_path=str(results_file),
                storage_path=storage_path,
                file_size=results_file.stat().st_size,
                content_type="application/json",
                metadata={
                    "description": "Original test results file",
                    "upload_time": datetime.utcnow().isoformat()
                }
            )
            session.add(artifact)
            
            logger.debug(f"Uploaded results file: {results_file.name}")
            
        except Exception as e:
            logger.warning(f"Failed to upload results file {results_file}: {e}")
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension"""
        
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.log': 'text/plain',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.xml': 'application/xml',
            '.json': 'application/json'
        }
        
        return content_types.get(file_path.suffix.lower(), 'application/octet-stream')


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Upload test results to database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload Playwright results
  python upload_test_results.py --input results.json --framework playwright --environment staging

  # Upload with artifacts and build info
  python upload_test_results.py --input results.json --framework pytest --artifacts test-results/ --build-number 123

  # Upload with git information
  python upload_test_results.py --input results.json --framework appium --branch feature/mobile --commit abc123
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to test results JSON file'
    )
    
    parser.add_argument(
        '--framework', '-f',
        type=str,
        choices=['playwright', 'pytest', 'appium', 'security'],
        required=True,
        help='Testing framework used'
    )
    
    # Optional arguments
    parser.add_argument(
        '--environment', '-e',
        type=str,
        default='development',
        help='Test environment (default: development)'
    )
    
    parser.add_argument(
        '--branch', '-b',
        type=str,
        default='main',
        help='Git branch (default: main)'
    )
    
    parser.add_argument(
        '--commit',
        type=str,
        help='Git commit hash'
    )
    
    parser.add_argument(
        '--build-number',
        type=str,
        help='Build number or CI job ID'
    )
    
    parser.add_argument(
        '--artifacts', '-a',
        type=str,
        help='Directory containing test artifacts (screenshots, videos, logs)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool):
    """Setup logging based on verbosity flags"""
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


async def main():
    """Main function"""
    args = parse_arguments()
    setup_logging(args.verbose, args.quiet)
    
    try:
        # Validate input file
        input_file = Path(args.input)
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)
        
        # Validate artifacts directory
        artifacts_dir = None
        if args.artifacts:
            artifacts_dir = Path(args.artifacts)
            if not artifacts_dir.exists():
                logger.warning(f"Artifacts directory not found: {artifacts_dir}")
                artifacts_dir = None
        
        # Parse framework
        framework = TestFramework(args.framework.lower())
        
        # Upload results
        uploader = TestResultsUploader()
        test_run_id = await uploader.upload_results(
            results_file=input_file,
            framework=framework,
            environment=args.environment,
            branch=args.branch,
            commit_hash=args.commit,
            build_number=args.build_number,
            artifacts_dir=artifacts_dir
        )
        
        # Report success
        logger.info("Test results uploaded successfully!")
        logger.info(f"Test Run ID: {test_run_id}")
        
        if not args.quiet:
            print("\n" + "="*50)
            print("UPLOAD SUMMARY")
            print("="*50)
            print(f"Test Run ID: {test_run_id}")
            print(f"Framework: {framework.value}")
            print(f"Environment: {args.environment}")
            print(f"Results File: {input_file}")
            if artifacts_dir:
                print(f"Artifacts: {artifacts_dir}")
            print("="*50)
        
    except KeyboardInterrupt:
        logger.info("Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())