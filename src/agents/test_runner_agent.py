"""
Test Runner Agent

Handles triggering CI/CD pipelines and orchestrating test execution.
Integrates with various CI/CD systems like GitHub Actions, Jenkins, GitLab CI, etc.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import yaml

from .base_agent import BaseAgent, AgentConfig


class TestRunnerAgent(BaseAgent):
    """
    Agent responsible for triggering and managing test execution in CI/CD pipelines.
    
    Supports:
    - GitHub Actions (enhanced with workflow triggering)
    - Jenkins
    - GitLab CI
    - Azure DevOps
    - Local test execution
    - Docker-based testing
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.ci_config = config.metadata.get('ci_config', {})
        self.test_config = config.metadata.get('test_config', {})
        self.supported_platforms = ['github', 'jenkins', 'gitlab', 'azure', 'local', 'docker']
        
        # GitHub configuration
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPOSITORY', self.ci_config.get('github_repo'))
        self.github_owner = os.getenv('GITHUB_OWNER', self.ci_config.get('github_owner'))
    
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Execute test runner logic"""
        platform = kwargs.get('platform', self.ci_config.get('platform', 'local'))
        test_types = kwargs.get('test_types', ['unit', 'integration'])
        environment = kwargs.get('environment', self.config.environment)
        branch = kwargs.get('branch', 'main')
        commit_hash = kwargs.get('commit_hash')
        
        self.logger.info(f"Running tests on platform: {platform}")
        
        if platform == 'github':
            return await self._run_github_actions(test_types, environment, branch, commit_hash)
        elif platform == 'jenkins':
            return await self._run_jenkins_job(test_types, environment, branch, commit_hash)
        elif platform == 'gitlab':
            return await self._run_gitlab_pipeline(test_types, environment, branch, commit_hash)
        elif platform == 'azure':
            return await self._run_azure_pipeline(test_types, environment, branch, commit_hash)
        elif platform == 'docker':
            return await self._run_docker_tests(test_types, environment, branch, commit_hash)
        elif platform == 'local':
            return await self._run_local_tests(test_types, environment, branch, commit_hash)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def trigger_github_workflow(self, workflow_name: str, test_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger a specific GitHub Actions workflow and return run information.
        
        Args:
            workflow_name: Name of the workflow (e.g., 'e2e-tests', 'api-tests', 'ui-tests')
            test_type: Optional test type filter
            
        Returns:
            Dict containing run_id, status, and logs_url
        """
        if not self.github_token or not self.github_repo or not self.github_owner:
            raise ValueError("GitHub configuration missing. Set GITHUB_TOKEN, GITHUB_REPOSITORY, and GITHUB_OWNER")
        
        # Map workflow names to actual workflow files
        workflow_mapping = {
            'e2e-tests': 'e2e-tests.yml',
            'api-tests': 'test-api.yml', 
            'ui-tests': 'test-web.yml',
            'security-tests': 'test-security.yml',
            'mobile-tests': 'test-mobile.yml'
        }
        
        workflow_file = workflow_mapping.get(workflow_name, f"{workflow_name}.yml")
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Trigger workflow
        trigger_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/actions/workflows/{workflow_file}/dispatches"
        
        payload = {
            'ref': 'main',
            'inputs': {}
        }
        
        if test_type:
            payload['inputs']['test_type'] = test_type
        
        async with aiohttp.ClientSession() as session:
            # Trigger the workflow
            async with session.post(trigger_url, headers=headers, json=payload) as response:
                if response.status == 204:
                    self.logger.info(f"Successfully triggered workflow: {workflow_name}")
                    
                    # Wait a moment for the run to be created
                    await asyncio.sleep(2)
                    
                    # Get the latest run
                    run_info = await self._get_latest_workflow_run(session, headers, workflow_file)
                    
                    if run_info:
                        return {
                            'status': 'triggered',
                            'run_id': run_info['id'],
                            'workflow_name': workflow_name,
                            'logs_url': run_info['html_url'],
                            'api_url': run_info['url'],
                            'created_at': run_info['created_at']
                        }
                    else:
                        return {
                            'status': 'triggered',
                            'message': 'Workflow triggered but run info not immediately available',
                            'workflow_name': workflow_name
                        }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger workflow: {response.status} - {error_text}")

    async def monitor_workflow_status(self, run_id: str) -> Dict[str, Any]:
        """
        Monitor the status of a GitHub Actions workflow run.
        
        Args:
            run_id: The workflow run ID
            
        Returns:
            Dict containing current status, conclusion, and logs_url
        """
        if not self.github_token or not self.github_repo or not self.github_owner:
            raise ValueError("GitHub configuration missing")
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/actions/runs/{run_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    run_data = await response.json()
                    
                    return {
                        'run_id': run_id,
                        'status': run_data['status'],  # queued, in_progress, completed
                        'conclusion': run_data.get('conclusion'),  # success, failure, cancelled, etc.
                        'logs_url': run_data['html_url'],
                        'created_at': run_data['created_at'],
                        'updated_at': run_data['updated_at'],
                        'workflow_name': run_data['name'],
                        'head_branch': run_data['head_branch'],
                        'head_sha': run_data['head_sha']
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get run status: {response.status} - {error_text}")

    async def wait_for_completion(self, run_id: str, timeout: int = 1800, poll_interval: int = 30) -> Dict[str, Any]:
        """
        Wait for a workflow run to complete.
        
        Args:
            run_id: The workflow run ID
            timeout: Maximum time to wait in seconds (default 30 minutes)
            poll_interval: How often to check status in seconds (default 30 seconds)
            
        Returns:
            Final status information
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_info = await self.monitor_workflow_status(run_id)
            
            if status_info['status'] == 'completed':
                self.logger.info(f"Workflow {run_id} completed with conclusion: {status_info['conclusion']}")
                return status_info
            
            self.logger.info(f"Workflow {run_id} status: {status_info['status']}")
            await asyncio.sleep(poll_interval)
        
        # Timeout reached
        final_status = await self.monitor_workflow_status(run_id)
        final_status['timeout'] = True
        return final_status

    async def run_tests(self, test_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to run tests as specified in the user requirements.
        
        Args:
            test_type: Optional filter for test type ('api', 'ui', None for all)
            
        Returns:
            Dict with run_id and logs_url
        """
        # Determine workflow based on test type
        if test_type == 'api':
            workflow_name = 'api-tests'
        elif test_type == 'ui':
            workflow_name = 'ui-tests'
        else:
            workflow_name = 'e2e-tests'  # Default to full e2e tests
        
        # Trigger the workflow
        trigger_result = await self.trigger_github_workflow(workflow_name, test_type)
        
        if 'run_id' in trigger_result:
            # Monitor until completion
            final_status = await self.wait_for_completion(trigger_result['run_id'])
            
            return {
                'run_id': trigger_result['run_id'],
                'logs_url': trigger_result['logs_url'],
                'status': final_status['status'],
                'conclusion': final_status.get('conclusion'),
                'workflow_name': workflow_name
            }
        else:
            return trigger_result

    async def _get_latest_workflow_run(self, session: aiohttp.ClientSession, headers: Dict[str, str], 
                                      workflow_file: str) -> Optional[Dict[str, Any]]:
        """Get the latest workflow run information for the specified workflow file"""
        url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/actions/workflows/{workflow_file}/runs"
        
        # Wait a bit for the workflow to appear
        await asyncio.sleep(2)
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                runs = data.get('workflow_runs', [])
                if runs:
                    return runs[0]  # Return the full run object
        return None

    async def _run_github_actions(self, test_types: List[str], environment: str, 
                                 branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Trigger GitHub Actions workflow"""
        github_config = self.ci_config.get('github', {})
        token = github_config.get('token') or os.getenv('GITHUB_TOKEN')
        repo = github_config.get('repository')
        workflow_id = github_config.get('workflow_id', 'test.yml')
        
        if not token or not repo:
            raise ValueError("GitHub token and repository are required")
        
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'ref': branch,
            'inputs': {
                'test_types': ','.join(test_types),
                'environment': environment,
                'commit_hash': commit_hash or ''
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    self.logger.info("GitHub Actions workflow triggered successfully")
                    
                    # Wait for workflow to start and get run ID
                    run_info = await self._get_latest_workflow_run_legacy(session, headers, repo, workflow_id)
                    
                    return {
                        'platform': 'github',
                        'workflow_id': workflow_id,
                        'run_id': run_info,
                        'repository': repo,
                        'branch': branch,
                        'test_types': test_types,
                        'environment': environment,
                        'status': 'triggered',
                        'url': f"https://github.com/{repo}/actions/runs/{run_info}" if run_info else None
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger GitHub Actions: {response.status} - {error_text}")
    
    async def _get_latest_workflow_run_legacy(self, session: aiohttp.ClientSession, headers: Dict[str, str], 
                                      repo: str, workflow_id: str) -> Optional[str]:
        """Get the latest workflow run ID (legacy method for backward compatibility)"""
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/runs"
        
        # Wait a bit for the workflow to appear
        await asyncio.sleep(2)
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                runs = data.get('workflow_runs', [])
                if runs:
                    return str(runs[0]['id'])
        return None
    
    async def _run_jenkins_job(self, test_types: List[str], environment: str, 
                              branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Trigger Jenkins job"""
        jenkins_config = self.ci_config.get('jenkins', {})
        url = jenkins_config.get('url')
        username = jenkins_config.get('username')
        token = jenkins_config.get('token') or os.getenv('JENKINS_TOKEN')
        job_name = jenkins_config.get('job_name', 'test-pipeline')
        
        if not all([url, username, token]):
            raise ValueError("Jenkins URL, username, and token are required")
        
        job_url = f"{url}/job/{job_name}/buildWithParameters"
        auth = aiohttp.BasicAuth(username, token)
        
        params = {
            'TEST_TYPES': ','.join(test_types),
            'ENVIRONMENT': environment,
            'BRANCH': branch,
            'COMMIT_HASH': commit_hash or ''
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(job_url, auth=auth, params=params) as response:
                if response.status in [200, 201]:
                    # Get queue item location
                    location = response.headers.get('Location')
                    build_number = await self._get_jenkins_build_number(session, auth, location)
                    
                    return {
                        'platform': 'jenkins',
                        'job_name': job_name,
                        'build_number': build_number,
                        'jenkins_url': url,
                        'branch': branch,
                        'test_types': test_types,
                        'environment': environment,
                        'status': 'triggered',
                        'url': f"{url}/job/{job_name}/{build_number}" if build_number else None
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger Jenkins job: {response.status} - {error_text}")
    
    async def _get_jenkins_build_number(self, session: aiohttp.ClientSession, 
                                       auth: aiohttp.BasicAuth, location: Optional[str]) -> Optional[str]:
        """Get Jenkins build number from queue"""
        if not location:
            return None
        
        # Wait for build to start
        await asyncio.sleep(3)
        
        queue_url = f"{location}api/json"
        async with session.get(queue_url, auth=auth) as response:
            if response.status == 200:
                data = await response.json()
                executable = data.get('executable')
                if executable:
                    return str(executable.get('number'))
        return None
    
    async def _run_gitlab_pipeline(self, test_types: List[str], environment: str, 
                                  branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Trigger GitLab CI pipeline"""
        gitlab_config = self.ci_config.get('gitlab', {})
        url = gitlab_config.get('url', 'https://gitlab.com')
        token = gitlab_config.get('token') or os.getenv('GITLAB_TOKEN')
        project_id = gitlab_config.get('project_id')
        
        if not token or not project_id:
            raise ValueError("GitLab token and project ID are required")
        
        pipeline_url = f"{url}/api/v4/projects/{project_id}/pipeline"
        headers = {
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'ref': branch,
            'variables': [
                {'key': 'TEST_TYPES', 'value': ','.join(test_types)},
                {'key': 'ENVIRONMENT', 'value': environment},
                {'key': 'COMMIT_HASH', 'value': commit_hash or ''}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(pipeline_url, headers=headers, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    pipeline_id = data.get('id')
                    
                    return {
                        'platform': 'gitlab',
                        'pipeline_id': pipeline_id,
                        'project_id': project_id,
                        'gitlab_url': url,
                        'branch': branch,
                        'test_types': test_types,
                        'environment': environment,
                        'status': 'triggered',
                        'url': f"{url}/{project_id}/-/pipelines/{pipeline_id}"
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger GitLab pipeline: {response.status} - {error_text}")
    
    async def _run_azure_pipeline(self, test_types: List[str], environment: str, 
                                 branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Trigger Azure DevOps pipeline"""
        azure_config = self.ci_config.get('azure', {})
        organization = azure_config.get('organization')
        project = azure_config.get('project')
        pipeline_id = azure_config.get('pipeline_id')
        token = azure_config.get('token') or os.getenv('AZURE_DEVOPS_TOKEN')
        
        if not all([organization, project, pipeline_id, token]):
            raise ValueError("Azure organization, project, pipeline ID, and token are required")
        
        url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipeline_id}/runs"
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'resources': {
                'repositories': {
                    'self': {
                        'refName': f'refs/heads/{branch}'
                    }
                }
            },
            'variables': {
                'TEST_TYPES': {'value': ','.join(test_types)},
                'ENVIRONMENT': {'value': environment},
                'COMMIT_HASH': {'value': commit_hash or ''}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    run_id = data.get('id')
                    
                    return {
                        'platform': 'azure',
                        'run_id': run_id,
                        'pipeline_id': pipeline_id,
                        'organization': organization,
                        'project': project,
                        'branch': branch,
                        'test_types': test_types,
                        'environment': environment,
                        'status': 'triggered',
                        'url': f"https://dev.azure.com/{organization}/{project}/_build/results?buildId={run_id}"
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger Azure pipeline: {response.status} - {error_text}")
    
    async def _run_docker_tests(self, test_types: List[str], environment: str, 
                               branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Run tests in Docker containers"""
        docker_config = self.test_config.get('docker', {})
        image = docker_config.get('image', 'python:3.9')
        dockerfile = docker_config.get('dockerfile', 'Dockerfile.test')
        
        # Build test image if Dockerfile exists
        if Path(dockerfile).exists():
            build_cmd = ['docker', 'build', '-f', dockerfile, '-t', 'test-runner', '.']
            result = await self._run_command(build_cmd)
            if result['returncode'] != 0:
                raise Exception(f"Docker build failed: {result['stderr']}")
            image = 'test-runner'
        
        # Run tests in container
        test_results = {}
        for test_type in test_types:
            container_name = f"test-{test_type}-{int(datetime.now().timestamp())}"
            
            cmd = [
                'docker', 'run', '--rm',
                '--name', container_name,
                '-e', f'TEST_TYPE={test_type}',
                '-e', f'ENVIRONMENT={environment}',
                '-e', f'BRANCH={branch}',
                '-e', f'COMMIT_HASH={commit_hash or ""}',
                '-v', f'{os.getcwd()}:/workspace',
                '-w', '/workspace',
                image,
                'python', 'scripts/run_tests.py', '--type', test_type
            ]
            
            self.logger.info(f"Running {test_type} tests in Docker container")
            result = await self._run_command(cmd)
            
            test_results[test_type] = {
                'returncode': result['returncode'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'success': result['returncode'] == 0
            }
        
        return {
            'platform': 'docker',
            'image': image,
            'test_results': test_results,
            'branch': branch,
            'test_types': test_types,
            'environment': environment,
            'status': 'completed',
            'success': all(r['success'] for r in test_results.values())
        }
    
    async def _run_local_tests(self, test_types: List[str], environment: str, 
                              branch: str, commit_hash: Optional[str]) -> Dict[str, Any]:
        """Run tests locally"""
        test_results = {}
        
        for test_type in test_types:
            self.logger.info(f"Running {test_type} tests locally")
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'TEST_TYPE': test_type,
                'ENVIRONMENT': environment,
                'BRANCH': branch,
                'COMMIT_HASH': commit_hash or ''
            })
            
            # Run test command
            cmd = ['python', 'scripts/run_tests.py', '--type', test_type, '--environment', environment]
            result = await self._run_command(cmd, env=env)
            
            test_results[test_type] = {
                'returncode': result['returncode'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'success': result['returncode'] == 0
            }
        
        return {
            'platform': 'local',
            'test_results': test_results,
            'branch': branch,
            'test_types': test_types,
            'environment': environment,
            'status': 'completed',
            'success': all(r['success'] for r in test_results.values())
        }
    
    async def _run_command(self, cmd: List[str], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Run a command asynchronously"""
        self.logger.info(f"Executing command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            'returncode': process.returncode,
            'stdout': stdout.decode('utf-8') if stdout else '',
            'stderr': stderr.decode('utf-8') if stderr else ''
        }
    
    async def get_run_status(self, platform: str, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of a running test execution"""
        if platform == 'github':
            return await self._get_github_run_status(run_info)
        elif platform == 'jenkins':
            return await self._get_jenkins_run_status(run_info)
        elif platform == 'gitlab':
            return await self._get_gitlab_run_status(run_info)
        elif platform == 'azure':
            return await self._get_azure_run_status(run_info)
        else:
            return {'status': 'unknown', 'message': f'Status checking not supported for platform: {platform}'}
    
    async def _get_github_run_status(self, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get GitHub Actions run status"""
        github_config = self.ci_config.get('github', {})
        token = github_config.get('token') or os.getenv('GITHUB_TOKEN')
        repo = run_info.get('repository')
        run_id = run_info.get('run_id')
        
        if not all([token, repo, run_id]):
            return {'status': 'error', 'message': 'Missing required information'}
        
        url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': data.get('status'),
                        'conclusion': data.get('conclusion'),
                        'url': data.get('html_url'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at')
                    }
                else:
                    return {'status': 'error', 'message': f'API error: {response.status}'}
    
    async def _get_jenkins_run_status(self, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get Jenkins job status"""
        jenkins_config = self.ci_config.get('jenkins', {})
        url = jenkins_config.get('url')
        username = jenkins_config.get('username')
        token = jenkins_config.get('token') or os.getenv('JENKINS_TOKEN')
        job_name = run_info.get('job_name')
        build_number = run_info.get('build_number')
        
        if not all([url, username, token, job_name, build_number]):
            return {'status': 'error', 'message': 'Missing required information'}
        
        build_url = f"{url}/job/{job_name}/{build_number}/api/json"
        auth = aiohttp.BasicAuth(username, token)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(build_url, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': 'completed' if not data.get('building') else 'running',
                        'result': data.get('result'),
                        'duration': data.get('duration'),
                        'url': data.get('url'),
                        'timestamp': data.get('timestamp')
                    }
                else:
                    return {'status': 'error', 'message': f'API error: {response.status}'}
    
    async def _get_gitlab_run_status(self, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get GitLab pipeline status"""
        gitlab_config = self.ci_config.get('gitlab', {})
        url = gitlab_config.get('url', 'https://gitlab.com')
        token = gitlab_config.get('token') or os.getenv('GITLAB_TOKEN')
        project_id = run_info.get('project_id')
        pipeline_id = run_info.get('pipeline_id')
        
        if not all([token, project_id, pipeline_id]):
            return {'status': 'error', 'message': 'Missing required information'}
        
        pipeline_url = f"{url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
        headers = {'PRIVATE-TOKEN': token}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(pipeline_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': data.get('status'),
                        'duration': data.get('duration'),
                        'url': data.get('web_url'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at')
                    }
                else:
                    return {'status': 'error', 'message': f'API error: {response.status}'}
    
    async def _get_azure_run_status(self, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get Azure DevOps pipeline status"""
        azure_config = self.ci_config.get('azure', {})
        organization = run_info.get('organization')
        project = run_info.get('project')
        run_id = run_info.get('run_id')
        token = azure_config.get('token') or os.getenv('AZURE_DEVOPS_TOKEN')
        
        if not all([organization, project, run_id, token]):
            return {'status': 'error', 'message': 'Missing required information'}
        
        url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/runs/{run_id}"
        headers = {'Authorization': f'Basic {token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': data.get('state'),
                        'result': data.get('result'),
                        'url': data.get('_links', {}).get('web', {}).get('href'),
                        'created_date': data.get('createdDate'),
                        'finished_date': data.get('finishedDate')
                    }
                else:
                    return {'status': 'error', 'message': f'API error: {response.status}'}