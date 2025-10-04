#!/usr/bin/env python3
"""
Docker Services Startup Script

This script helps start and verify Docker services for the AI-powered testing framework.
It provides better error handling and status reporting than raw docker-compose commands.
"""

import subprocess
import time
import sys
import json
import requests
import psycopg2
import redis
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerServiceManager:
    """Manages Docker services for the testing framework."""
    
    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self.compose_file = self.project_dir / "docker-compose.yml"
        
        # Service configurations
        self.services = {
            'postgres': {
                'port': 5432,
                'health_check': self._check_postgres,
                'wait_time': 30
            },
            'redis': {
                'port': 6379,
                'health_check': self._check_redis,
                'wait_time': 10
            },
            'minio': {
                'port': 9000,
                'health_check': self._check_minio,
                'wait_time': 20
            },
            'selenium-hub': {
                'port': 4444,
                'health_check': self._check_selenium,
                'wait_time': 30
            },
            'owasp-zap': {
                'port': 8080,
                'health_check': self._check_zap,
                'wait_time': 45
            },
            'grafana': {
                'port': 3000,
                'health_check': self._check_grafana,
                'wait_time': 30
            },
            'prometheus': {
                'port': 9090,
                'health_check': self._check_prometheus,
                'wait_time': 20
            }
        }
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Docker version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.error("Docker is not available or not running")
        return False
    
    def check_docker_compose_available(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(
                ['docker-compose', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Docker Compose version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.error("Docker Compose is not available")
        return False
    
    def check_compose_file(self) -> bool:
        """Check if docker-compose.yml exists."""
        if self.compose_file.exists():
            logger.info(f"Found docker-compose.yml at {self.compose_file}")
            return True
        
        logger.error(f"docker-compose.yml not found at {self.compose_file}")
        return False
    
    def start_services(self, services: list = None) -> bool:
        """Start Docker services."""
        logger.info("Starting Docker services...")
        
        cmd = ['docker-compose', 'up', '-d']
        if services:
            cmd.extend(services)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Docker services started successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout while starting services")
            return False
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop Docker services."""
        logger.info("Stopping Docker services...")
        
        try:
            result = subprocess.run(
                ['docker-compose', 'down'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Docker services stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return False
    
    def get_service_status(self) -> dict:
        """Get status of all services."""
        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            services.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return {'status': 'success', 'services': services}
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def wait_for_services(self, timeout: int = 300) -> dict:
        """Wait for all services to be healthy."""
        logger.info("Waiting for services to be ready...")
        
        start_time = time.time()
        service_status = {}
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_name, config in self.services.items():
                if service_name not in service_status:
                    service_status[service_name] = {'ready': False, 'error': None}
                
                if not service_status[service_name]['ready']:
                    try:
                        if config['health_check']():
                            service_status[service_name]['ready'] = True
                            logger.info(f"✅ {service_name} is ready")
                        else:
                            all_ready = False
                    except Exception as e:
                        service_status[service_name]['error'] = str(e)
                        all_ready = False
            
            if all_ready:
                logger.info("🎉 All services are ready!")
                return {'status': 'success', 'services': service_status}
            
            time.sleep(5)
        
        logger.warning("Timeout waiting for services")
        return {'status': 'timeout', 'services': service_status}
    
    def _check_postgres(self) -> bool:
        """Check PostgreSQL health."""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='testdb',
                user='testuser',
                password='testpass',
                connect_timeout=5
            )
            conn.close()
            return True
        except:
            return False
    
    def _check_redis(self) -> bool:
        """Check Redis health."""
        try:
            r = redis.Redis(host='localhost', port=6379, socket_timeout=5)
            return r.ping()
        except:
            return False
    
    def _check_minio(self) -> bool:
        """Check MinIO health."""
        try:
            response = requests.get(
                'http://localhost:9000/minio/health/live',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _check_selenium(self) -> bool:
        """Check Selenium Grid health."""
        try:
            response = requests.get(
                'http://localhost:4444/wd/hub/status',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _check_zap(self) -> bool:
        """Check OWASP ZAP health."""
        try:
            response = requests.get(
                'http://localhost:8080/JSON/core/view/version/',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _check_grafana(self) -> bool:
        """Check Grafana health."""
        try:
            response = requests.get(
                'http://localhost:3000/api/health',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _check_prometheus(self) -> bool:
        """Check Prometheus health."""
        try:
            response = requests.get(
                'http://localhost:9090/-/healthy',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def print_service_urls(self):
        """Print URLs for accessing services."""
        urls = {
            'Grafana Dashboard': 'http://localhost:3000 (admin/admin123)',
            'Prometheus': 'http://localhost:9090',
            'MinIO Console': 'http://localhost:9001 (minioadmin/minioadmin)',
            'Selenium Grid': 'http://localhost:4444',
            'OWASP ZAP': 'http://localhost:8080'
        }
        
        print("\n🌐 Service URLs:")
        print("=" * 50)
        for name, url in urls.items():
            print(f"{name:20}: {url}")
        print("=" * 50)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Start and manage Docker services for AI testing framework'
    )
    parser.add_argument(
        '--action',
        choices=['start', 'stop', 'status', 'restart'],
        default='start',
        help='Action to perform'
    )
    parser.add_argument(
        '--services',
        nargs='*',
        help='Specific services to start (default: all)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout for waiting for services (seconds)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Don\'t wait for services to be ready'
    )
    
    args = parser.parse_args()
    
    # Initialize service manager
    manager = DockerServiceManager()
    
    # Check prerequisites
    if not manager.check_docker_available():
        print("❌ Docker is not available. Please install and start Docker Desktop.")
        print("See DOCKER_SETUP.md for installation instructions.")
        sys.exit(1)
    
    if not manager.check_docker_compose_available():
        print("❌ Docker Compose is not available.")
        sys.exit(1)
    
    if not manager.check_compose_file():
        print("❌ docker-compose.yml not found.")
        sys.exit(1)
    
    # Perform requested action
    if args.action == 'start':
        if not manager.start_services(args.services):
            sys.exit(1)
        
        if not args.no_wait:
            result = manager.wait_for_services(args.timeout)
            if result['status'] != 'success':
                print("⚠️  Some services may not be ready. Check logs with:")
                print("docker-compose logs -f")
        
        manager.print_service_urls()
    
    elif args.action == 'stop':
        if not manager.stop_services():
            sys.exit(1)
    
    elif args.action == 'restart':
        manager.stop_services()
        time.sleep(5)
        if not manager.start_services(args.services):
            sys.exit(1)
        
        if not args.no_wait:
            manager.wait_for_services(args.timeout)
        
        manager.print_service_urls()
    
    elif args.action == 'status':
        status = manager.get_service_status()
        if status['status'] == 'success':
            print("\n📊 Service Status:")
            print("=" * 60)
            for service in status['services']:
                name = service.get('Name', 'Unknown')
                state = service.get('State', 'Unknown')
                status_text = service.get('Status', 'Unknown')
                print(f"{name:20}: {state:10} - {status_text}")
            print("=" * 60)
        else:
            print(f"❌ Error getting status: {status['message']}")

if __name__ == '__main__':
    main()