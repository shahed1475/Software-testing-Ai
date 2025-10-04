"""
Report Collector Agent

Fetches test results, artifacts, and logs from multiple sources including
CI/CD systems, databases, file systems, and MinIO/S3 storage.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import boto3
import aiofiles
from botocore.exceptions import ClientError, NoCredentialsError

from .base_agent import BaseAgent, AgentConfig


class ReportCollectorAgent(BaseAgent):
    """
    Agent responsible for collecting test reports, artifacts, and logs from various sources.
    
    Supports:
    - S3/MinIO storage
    - Local file systems
    - CI/CD system APIs
    - Database queries
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.storage_config = config.metadata.get('storage_config', {})
        self.ci_config = config.metadata.get('ci_config', {})
        
        # Initialize S3 client
        self.s3_client = self._init_s3_client()
        
        # Default S3 bucket and paths
        self.default_bucket = self.storage_config.get('bucket', 'my-bucket')
        self.artifacts_path_template = self.storage_config.get('artifacts_path', 's3://my-bucket/artifacts/{run_id}')
        
    def _init_s3_client(self):
        """Initialize S3/MinIO client"""
        try:
            # Get credentials from config or environment
            aws_access_key = (
                self.storage_config.get('aws_access_key_id') or 
                os.getenv('AWS_ACCESS_KEY_ID')
            )
            aws_secret_key = (
                self.storage_config.get('aws_secret_access_key') or 
                os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            aws_region = (
                self.storage_config.get('aws_region') or 
                os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            endpoint_url = (
                self.storage_config.get('endpoint_url') or 
                os.getenv('S3_ENDPOINT_URL')
            )
            
            # Create S3 client
            s3_config = {
                'region_name': aws_region
            }
            
            if aws_access_key and aws_secret_key:
                s3_config.update({
                    'aws_access_key_id': aws_access_key,
                    'aws_secret_access_key': aws_secret_key
                })
            
            if endpoint_url:
                s3_config['endpoint_url'] = endpoint_url
            
            return boto3.client('s3', **s3_config)
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize S3 client: {e}")
            return None

    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Execute report collection logic"""
        run_id = kwargs.get('run_id')
        source_type = kwargs.get('source_type', 's3')
        
        if not run_id:
            raise ValueError("run_id is required for report collection")
        
        self.logger.info(f"Collecting reports for run_id: {run_id}")
        
        if source_type == 's3':
            return await self.collect_from_s3(run_id)
        elif source_type == 'local':
            return await self.collect_from_local(run_id, kwargs.get('local_path'))
        elif source_type == 'github':
            return await self.collect_from_github(run_id, kwargs.get('repo'))
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def collect_from_s3(self, run_id: str, bucket: Optional[str] = None, 
                             custom_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch artifacts from S3 storage path and merge results.
        
        Args:
            run_id: Test run identifier
            bucket: S3 bucket name (optional, uses default)
            custom_path: Custom S3 path (optional, uses template)
            
        Returns:
            Dict with summary and download links for artifacts
        """
        if not self.s3_client:
            raise Exception("S3 client not initialized. Check credentials and configuration.")
        
        bucket_name = bucket or self.default_bucket
        
        # Construct S3 path
        if custom_path:
            s3_path = custom_path.replace('s3://', '').replace(f'{bucket_name}/', '')
        else:
            s3_path = f"artifacts/{run_id}"
        
        self.logger.info(f"Fetching artifacts from s3://{bucket_name}/{s3_path}")
        
        try:
            # List objects in the S3 path
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=s3_path
            )
            
            if 'Contents' not in response:
                return {
                    'status': 'no_artifacts',
                    'message': f'No artifacts found in s3://{bucket_name}/{s3_path}',
                    'run_id': run_id,
                    'artifacts': []
                }
            
            # Target files to collect
            target_files = ['results.json', 'screenshots', 'logs']
            collected_files = {}
            download_links = {}
            
            # Download and process each file
            for obj in response['Contents']:
                key = obj['Key']
                filename = Path(key).name
                
                # Check if this is one of our target files or directories
                if any(target in key.lower() for target in target_files):
                    try:
                        # Create temporary file for download
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                            self.s3_client.download_fileobj(bucket_name, key, tmp_file)
                            tmp_path = tmp_file.name
                        
                        # Process the downloaded file
                        if filename.endswith('.json'):
                            async with aiofiles.open(tmp_path, 'r') as f:
                                content = await f.read()
                                collected_files[filename] = json.loads(content)
                        else:
                            # For non-JSON files, store file info
                            collected_files[filename] = {
                                'type': 'file',
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat(),
                                'local_path': tmp_path
                            }
                        
                        # Generate download link (presigned URL)
                        download_url = self.s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket_name, 'Key': key},
                            ExpiresIn=3600  # 1 hour
                        )
                        download_links[filename] = download_url
                        
                        self.logger.info(f"Collected file: {filename}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process file {key}: {e}")
                        continue
            
            # Merge results into a single JSON object with summary
            merged_results = await self._merge_test_results(collected_files, run_id)
            
            return {
                'status': 'success',
                'run_id': run_id,
                'summary': merged_results['summary'],
                'detailed_results': merged_results['results'],
                'artifacts': list(collected_files.keys()),
                'download_links': download_links,
                'collection_timestamp': datetime.utcnow().isoformat(),
                's3_path': f"s3://{bucket_name}/{s3_path}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise Exception(f"S3 bucket '{bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                raise Exception(f"Access denied to S3 bucket '{bucket_name}'")
            else:
                raise Exception(f"S3 error: {e}")
        except Exception as e:
            raise Exception(f"Failed to collect artifacts from S3: {e}")

    async def _merge_test_results(self, collected_files: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """
        Merge collected test results into a single JSON object with summary.
        
        Args:
            collected_files: Dictionary of collected files and their contents
            run_id: Test run identifier
            
        Returns:
            Dict with merged results and summary
        """
        # Initialize summary counters
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        total_duration = 0.0
        
        # Collect all test results
        all_results = []
        test_suites = []
        
        # Process results.json files
        for filename, content in collected_files.items():
            if filename.endswith('.json') and isinstance(content, dict):
                # Handle different result formats
                if 'tests' in content:
                    # Standard test results format
                    tests = content['tests']
                    all_results.extend(tests)
                    
                    # Update counters
                    for test in tests:
                        total_tests += 1
                        status = test.get('status', '').lower()
                        if status in ['passed', 'pass', 'success']:
                            passed_tests += 1
                        elif status in ['failed', 'fail', 'failure', 'error']:
                            failed_tests += 1
                        elif status in ['skipped', 'skip', 'ignored']:
                            skipped_tests += 1
                        
                        # Add duration if available
                        duration = test.get('duration', 0)
                        if isinstance(duration, (int, float)):
                            total_duration += duration
                
                elif 'summary' in content:
                    # Summary format
                    summary = content['summary']
                    total_tests += summary.get('total', 0)
                    passed_tests += summary.get('passed', 0)
                    failed_tests += summary.get('failed', 0)
                    skipped_tests += summary.get('skipped', 0)
                    total_duration += summary.get('duration', 0)
                    
                    if 'results' in content:
                        all_results.extend(content['results'])
                
                elif 'suites' in content:
                    # Test suite format
                    suites = content['suites']
                    test_suites.extend(suites)
                    
                    for suite in suites:
                        suite_tests = suite.get('tests', [])
                        all_results.extend(suite_tests)
                        
                        for test in suite_tests:
                            total_tests += 1
                            status = test.get('status', '').lower()
                            if status in ['passed', 'pass', 'success']:
                                passed_tests += 1
                            elif status in ['failed', 'fail', 'failure', 'error']:
                                failed_tests += 1
                            elif status in ['skipped', 'skip', 'ignored']:
                                skipped_tests += 1
                            
                            duration = test.get('duration', 0)
                            if isinstance(duration, (int, float)):
                                total_duration += duration
        
        # Calculate pass rate
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create comprehensive summary
        summary = {
            'run_id': run_id,
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'pass_rate': round(pass_rate, 2),
            'duration': round(total_duration, 2),
            'status': 'passed' if failed_tests == 0 and total_tests > 0 else 'failed',
            'artifacts_count': len(collected_files),
            'collection_time': datetime.utcnow().isoformat()
        }
        
        # Organize results by category
        results = {
            'summary': summary,
            'passed_tests': [test for test in all_results if test.get('status', '').lower() in ['passed', 'pass', 'success']],
            'failed_tests': [test for test in all_results if test.get('status', '').lower() in ['failed', 'fail', 'failure', 'error']],
            'skipped_tests': [test for test in all_results if test.get('status', '').lower() in ['skipped', 'skip', 'ignored']],
            'test_suites': test_suites,
            'artifacts': {k: v for k, v in collected_files.items() if not k.endswith('.json')}
        }
        
        return {
            'summary': summary,
            'results': results
        }

    async def collect_from_local(self, run_id: str, local_path: str) -> Dict[str, Any]:
        """
        Collect artifacts from local file system.
        
        Args:
            run_id: Test run identifier
            local_path: Local directory path containing artifacts
            
        Returns:
            Dict with collected results and summary
        """
        if not local_path or not Path(local_path).exists():
            raise ValueError(f"Local path does not exist: {local_path}")
        
        self.logger.info(f"Collecting artifacts from local path: {local_path}")
        
        collected_files = {}
        target_files = ['results.json', 'screenshots', 'logs']
        
        # Recursively search for target files
        for target in target_files:
            for file_path in Path(local_path).rglob(f"*{target}*"):
                if file_path.is_file():
                    filename = file_path.name
                    
                    try:
                        if filename.endswith('.json'):
                            async with aiofiles.open(file_path, 'r') as f:
                                content = await f.read()
                                collected_files[filename] = json.loads(content)
                        else:
                            collected_files[filename] = {
                                'type': 'file',
                                'size': file_path.stat().st_size,
                                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                'local_path': str(file_path)
                            }
                    except Exception as e:
                        self.logger.error(f"Failed to process local file {file_path}: {e}")
                        continue
        
        # Merge results
        merged_results = await self._merge_test_results(collected_files, run_id)
        
        return {
            'status': 'success',
            'run_id': run_id,
            'summary': merged_results['summary'],
            'detailed_results': merged_results['results'],
            'artifacts': list(collected_files.keys()),
            'collection_timestamp': datetime.utcnow().isoformat(),
            'local_path': local_path
        }

    async def collect_from_github(self, run_id: str, repo: str) -> Dict[str, Any]:
        """
        Collect artifacts from GitHub Actions run.
        
        Args:
            run_id: GitHub Actions run ID
            repo: Repository in format 'owner/repo'
            
        Returns:
            Dict with collected results and summary
        """
        import aiohttp
        
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        self.logger.info(f"Collecting artifacts from GitHub Actions run: {run_id}")
        
        async with aiohttp.ClientSession() as session:
            # Get artifacts list
            artifacts_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
            
            async with session.get(artifacts_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get GitHub artifacts: {response.status}")
                
                artifacts_data = await response.json()
                artifacts = artifacts_data.get('artifacts', [])
                
                collected_files = {}
                
                # Download each artifact
                for artifact in artifacts:
                    artifact_name = artifact['name']
                    download_url = artifact['archive_download_url']
                    
                    # Download artifact
                    async with session.get(download_url, headers=headers) as download_response:
                        if download_response.status == 200:
                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                                async for chunk in download_response.content.iter_chunked(8192):
                                    tmp_file.write(chunk)
                                
                                collected_files[artifact_name] = {
                                    'type': 'artifact',
                                    'size': artifact['size_in_bytes'],
                                    'created_at': artifact['created_at'],
                                    'local_path': tmp_file.name
                                }
                
                # For GitHub, we'll create a basic summary since we don't have parsed results
                summary = {
                    'run_id': run_id,
                    'total': len(artifacts),
                    'passed': 0,  # Would need to parse artifacts to determine
                    'failed': 0,
                    'skipped': 0,
                    'pass_rate': 0,
                    'duration': 0,
                    'status': 'collected',
                    'artifacts_count': len(artifacts),
                    'collection_time': datetime.utcnow().isoformat()
                }
                
                return {
                    'status': 'success',
                    'run_id': run_id,
                    'summary': summary,
                    'artifacts': list(collected_files.keys()),
                    'github_artifacts': collected_files,
                    'collection_timestamp': datetime.utcnow().isoformat(),
                    'repository': repo
                }

    async def get_artifact_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Get a quick summary of available artifacts for a run ID.
        
        Args:
            run_id: Test run identifier
            
        Returns:
            Dict with artifact summary information
        """
        try:
            # Try S3 first
            bucket_name = self.default_bucket
            s3_path = f"artifacts/{run_id}"
            
            if self.s3_client:
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=s3_path
                )
                
                if 'Contents' in response:
                    artifacts = []
                    total_size = 0
                    
                    for obj in response['Contents']:
                        artifacts.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })
                        total_size += obj['Size']
                    
                    return {
                        'run_id': run_id,
                        'source': 's3',
                        'artifacts_count': len(artifacts),
                        'total_size_bytes': total_size,
                        'artifacts': artifacts,
                        's3_path': f"s3://{bucket_name}/{s3_path}"
                    }
            
            return {
                'run_id': run_id,
                'source': 'none',
                'artifacts_count': 0,
                'message': 'No artifacts found'
            }
            
        except Exception as e:
            return {
                'run_id': run_id,
                'source': 'error',
                'error': str(e)
            }

    async def download_artifact(self, artifact_info: Dict[str, Any], 
                              download_path: Optional[str] = None) -> str:
        """Download an artifact to local filesystem"""
        source = artifact_info.get('source', 'unknown')
        
        if not download_path:
            download_path = tempfile.mkdtemp()
        
        download_dir = Path(download_path)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        if source == 'minio':
            return await self._download_from_minio(artifact_info, download_dir)
        elif source == 'github':
            return await self._download_from_github(artifact_info, download_dir)
        elif source == 'jenkins':
            return await self._download_from_jenkins(artifact_info, download_dir)
        elif source == 'gitlab':
            return await self._download_from_gitlab(artifact_info, download_dir)
        elif source == 'azure':
            return await self._download_from_azure(artifact_info, download_dir)
        elif source == 'filesystem':
            return await self._copy_from_filesystem(artifact_info, download_dir)
        else:
            raise ValueError(f"Unsupported artifact source: {source}")
    
    async def _download_from_minio(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Download artifact from MinIO"""
        if not self.minio_client:
            raise ValueError("MinIO client not initialized")
        
        bucket = artifact_info['bucket']
        object_name = artifact_info['file_path']
        file_name = artifact_info['file_name']
        
        local_path = download_dir / file_name
        await self.minio_client.download_file(bucket, object_name, str(local_path))
        
        return str(local_path)
    
    async def _download_from_github(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Download artifact from GitHub Actions"""
        github_config = self.collection_config.get('github', {})
        token = github_config.get('token') or os.getenv('GITHUB_TOKEN')
        
        if not token:
            raise ValueError("GitHub token not configured")
        
        download_url = artifact_info['download_url']
        file_name = artifact_info['name']
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        local_path = download_dir / f"{file_name}.zip"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, headers=headers) as response:
                if response.status == 200:
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Failed to download from GitHub: {response.status}")
        
        return str(local_path)
    
    async def _download_from_jenkins(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Download artifact from Jenkins"""
        jenkins_config = self.collection_config.get('jenkins', {})
        username = jenkins_config.get('username')
        token = jenkins_config.get('token') or os.getenv('JENKINS_TOKEN')
        
        if not all([username, token]):
            raise ValueError("Jenkins credentials not configured")
        
        download_url = artifact_info['download_url']
        file_name = artifact_info['name']
        
        auth = aiohttp.BasicAuth(username, token)
        local_path = download_dir / file_name
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, auth=auth) as response:
                if response.status == 200:
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Failed to download from Jenkins: {response.status}")
        
        return str(local_path)
    
    async def _download_from_gitlab(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Download artifact from GitLab CI"""
        gitlab_config = self.collection_config.get('gitlab', {})
        token = gitlab_config.get('token') or os.getenv('GITLAB_TOKEN')
        
        if not token:
            raise ValueError("GitLab token not configured")
        
        download_url = artifact_info['download_url']
        file_name = artifact_info['name']
        
        headers = {'PRIVATE-TOKEN': token}
        local_path = download_dir / f"{file_name}.zip"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, headers=headers) as response:
                if response.status == 200:
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Failed to download from GitLab: {response.status}")
        
        return str(local_path)
    
    async def _download_from_azure(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Download artifact from Azure DevOps"""
        azure_config = self.collection_config.get('azure', {})
        token = azure_config.get('token') or os.getenv('AZURE_DEVOPS_TOKEN')
        
        if not token:
            raise ValueError("Azure DevOps token not configured")
        
        download_url = artifact_info['download_url']
        file_name = artifact_info['name']
        
        headers = {'Authorization': f'Basic {token}'}
        local_path = download_dir / f"{file_name}.zip"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, headers=headers) as response:
                if response.status == 200:
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Failed to download from Azure DevOps: {response.status}")
        
        return str(local_path)
    
    async def _copy_from_filesystem(self, artifact_info: Dict[str, Any], download_dir: Path) -> str:
        """Copy artifact from local filesystem"""
        source_path = Path(artifact_info['file_path'])
        file_name = artifact_info['file_name']
        
        local_path = download_dir / file_name
        
        async with aiofiles.open(source_path, 'rb') as src:
            async with aiofiles.open(local_path, 'wb') as dst:
                while chunk := await src.read(8192):
                    await dst.write(chunk)
        
        return str(local_path)