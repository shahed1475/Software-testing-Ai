#!/usr/bin/env python3
"""
Setup Verification Script

Verifies that all components of the AI-powered testing framework
are properly installed and configured.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from sqlalchemy import text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SetupVerifier:
    """Verify setup components"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
    
    def run_all_checks(self) -> Dict:
        """Run all verification checks"""
        logger.info("Starting setup verification...")
        
        checks = [
            ("Python Environment", self.check_python_environment),
            ("Node.js Environment", self.check_nodejs_environment),
            ("Docker Services", self.check_docker_services),
            ("Database Connection", self.check_database_connection),
            ("Redis Connection", self.check_redis_connection),
            ("MinIO Storage", self.check_minio_storage),
            ("Selenium Grid", self.check_selenium_grid),
            ("OWASP ZAP", self.check_owasp_zap),
            ("Appium Server", self.check_appium_server),
            ("Monitoring Services", self.check_monitoring_services),
            ("Environment Variables", self.check_environment_variables),
            ("File Permissions", self.check_file_permissions),
            ("Network Connectivity", self.check_network_connectivity)
        ]
        
        for check_name, check_func in checks:
            try:
                logger.info(f"Checking {check_name}...")
                result = check_func()
                self.results[check_name] = result
                
                if result['status'] == 'pass':
                    logger.info(f"✅ {check_name}: PASSED")
                elif result['status'] == 'warning':
                    logger.warning(f"⚠️  {check_name}: WARNING - {result['message']}")
                else:
                    logger.error(f"❌ {check_name}: FAILED - {result['message']}")
                    self.errors.append(f"{check_name}: {result['message']}")
                    
            except Exception as e:
                error_msg = f"Exception during {check_name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.results[check_name] = {
                    'status': 'fail',
                    'message': str(e)
                }
                self.errors.append(error_msg)
        
        return self.results
    
    def check_python_environment(self) -> Dict:
        """Check Python environment and dependencies"""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 9):
                return {
                    'status': 'fail',
                    'message': f'Python 3.9+ required, found {python_version.major}.{python_version.minor}'
                }
            
            # Check virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (
                hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
            )
            
            # Check key dependencies
            required_packages = [
                'sqlalchemy', 'alembic', 'fastapi', 'pytest',
                'playwright', 'selenium', 'requests', 'minio'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return {
                    'status': 'fail',
                    'message': f'Missing packages: {", ".join(missing_packages)}'
                }
            
            return {
                'status': 'pass',
                'message': f'Python {python_version.major}.{python_version.minor}, Virtual env: {in_venv}'
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_nodejs_environment(self) -> Dict:
        """Check Node.js environment and dependencies"""
        try:
            # Check Node.js version
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'fail', 'message': 'Node.js not found'}
            
            node_version = result.stdout.strip()
            
            # Check npm
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'fail', 'message': 'npm not found'}
            
            npm_version = result.stdout.strip()
            
            # Check Playwright
            result = subprocess.run(['npx', 'playwright', '--version'], capture_output=True, text=True)
            playwright_installed = result.returncode == 0
            
            if not playwright_installed:
                return {'status': 'warning', 'message': 'Playwright not installed'}
            
            return {
                'status': 'pass',
                'message': f'Node.js {node_version}, npm {npm_version}, Playwright installed'
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_docker_services(self) -> Dict:
        """Check Docker services status"""
        try:
            # Check if Docker is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'fail', 'message': 'Docker not running'}
            
            # Check docker-compose services
            result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'warning', 'message': 'docker-compose services not found'}
            
            # Parse service status
            lines = result.stdout.strip().split('\n')[2:]  # Skip header
            services = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0]
                        status = parts[3] if len(parts) > 3 else 'unknown'
                        services.append(f"{service_name}: {status}")
            
            return {
                'status': 'pass',
                'message': f'Docker running, Services: {len(services)}'
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_database_connection(self) -> Dict:
        """Check database connection"""
        try:
            from database.connection import get_database_session
            
            async def test_db():
                async with get_database_session() as session:
                    result = await session.execute(text("SELECT 1"))
                    return result.scalar()
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_db())
            loop.close()
            
            if result == 1:
                return {'status': 'pass', 'message': 'Database connection successful'}
            else:
                return {'status': 'fail', 'message': 'Database query failed'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Database connection failed: {str(e)}'}
    
    def check_redis_connection(self) -> Dict:
        """Check Redis connection"""
        try:
            import redis
            
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            r.ping()
            
            return {'status': 'pass', 'message': 'Redis connection successful'}
            
        except Exception as e:
            return {'status': 'fail', 'message': f'Redis connection failed: {str(e)}'}
    
    def check_minio_storage(self) -> Dict:
        """Check MinIO storage"""
        try:
            from minio import Minio
            
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
            secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            
            client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
            
            # Test connection by listing buckets
            buckets = list(client.list_buckets())
            
            return {
                'status': 'pass',
                'message': f'MinIO connection successful, Buckets: {len(buckets)}'
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': f'MinIO connection failed: {str(e)}'}
    
    def check_selenium_grid(self) -> Dict:
        """Check Selenium Grid status"""
        try:
            grid_url = os.getenv('SELENIUM_HUB_URL', 'http://localhost:4444')
            response = requests.get(f"{grid_url}/grid/api/hub/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                ready = data.get('value', {}).get('ready', False)
                
                if ready:
                    return {'status': 'pass', 'message': 'Selenium Grid ready'}
                else:
                    return {'status': 'warning', 'message': 'Selenium Grid not ready'}
            else:
                return {'status': 'fail', 'message': f'Selenium Grid HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Selenium Grid check failed: {str(e)}'}
    
    def check_owasp_zap(self) -> Dict:
        """Check OWASP ZAP status"""
        try:
            zap_host = os.getenv('ZAP_PROXY_HOST', 'localhost')
            zap_port = os.getenv('ZAP_PROXY_PORT', '8080')
            
            response = requests.get(f"http://{zap_host}:{zap_port}/JSON/core/view/version/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 'unknown')
                return {'status': 'pass', 'message': f'OWASP ZAP running, version: {version}'}
            else:
                return {'status': 'fail', 'message': f'OWASP ZAP HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'OWASP ZAP check failed: {str(e)}'}
    
    def check_appium_server(self) -> Dict:
        """Check Appium server status"""
        try:
            appium_url = os.getenv('APPIUM_SERVER_URL', 'http://localhost:4723')
            response = requests.get(f"{appium_url}/wd/hub/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                ready = data.get('value', {}).get('ready', False)
                
                if ready:
                    return {'status': 'pass', 'message': 'Appium server ready'}
                else:
                    return {'status': 'warning', 'message': 'Appium server not ready'}
            else:
                return {'status': 'fail', 'message': f'Appium server HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'fail', 'message': f'Appium server check failed: {str(e)}'}
    
    def check_monitoring_services(self) -> Dict:
        """Check monitoring services (Grafana, Prometheus)"""
        try:
            services_status = []
            
            # Check Grafana
            try:
                grafana_port = os.getenv('GRAFANA_PORT', '3000')
                response = requests.get(f"http://localhost:{grafana_port}/api/health", timeout=5)
                if response.status_code == 200:
                    services_status.append("Grafana: OK")
                else:
                    services_status.append(f"Grafana: HTTP {response.status_code}")
            except:
                services_status.append("Grafana: Not accessible")
            
            # Check Prometheus
            try:
                prometheus_port = os.getenv('PROMETHEUS_PORT', '9090')
                response = requests.get(f"http://localhost:{prometheus_port}/-/healthy", timeout=5)
                if response.status_code == 200:
                    services_status.append("Prometheus: OK")
                else:
                    services_status.append(f"Prometheus: HTTP {response.status_code}")
            except:
                services_status.append("Prometheus: Not accessible")
            
            # Determine overall status
            ok_count = sum(1 for status in services_status if "OK" in status)
            
            if ok_count == 2:
                status = 'pass'
            elif ok_count > 0:
                status = 'warning'
            else:
                status = 'fail'
            
            return {
                'status': status,
                'message': ', '.join(services_status)
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_environment_variables(self) -> Dict:
        """Check required environment variables"""
        try:
            required_vars = [
                'DATABASE_URL', 'DATABASE_HOST', 'DATABASE_USER',
                'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return {
                    'status': 'warning',
                    'message': f'Missing environment variables: {", ".join(missing_vars)}'
                }
            
            return {'status': 'pass', 'message': 'All required environment variables set'}
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_file_permissions(self) -> Dict:
        """Check file permissions"""
        try:
            issues = []
            
            # Check if logs directory is writable
            logs_dir = Path('logs')
            if not logs_dir.exists():
                logs_dir.mkdir(exist_ok=True)
            
            if not os.access(logs_dir, os.W_OK):
                issues.append('logs directory not writable')
            
            # Check if reports directory is writable
            reports_dir = Path('reports')
            if not reports_dir.exists():
                reports_dir.mkdir(exist_ok=True)
            
            if not os.access(reports_dir, os.W_OK):
                issues.append('reports directory not writable')
            
            # Check if temp directory is writable
            temp_dir = Path('temp')
            if not temp_dir.exists():
                temp_dir.mkdir(exist_ok=True)
            
            if not os.access(temp_dir, os.W_OK):
                issues.append('temp directory not writable')
            
            if issues:
                return {
                    'status': 'warning',
                    'message': f'Permission issues: {", ".join(issues)}'
                }
            
            return {'status': 'pass', 'message': 'File permissions OK'}
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def check_network_connectivity(self) -> Dict:
        """Check network connectivity"""
        try:
            # Test internet connectivity
            try:
                response = requests.get('https://httpbin.org/get', timeout=10)
                internet_ok = response.status_code == 200
            except:
                internet_ok = False
            
            # Test local services connectivity
            local_services = [
                ('localhost:5432', 'PostgreSQL'),
                ('localhost:6379', 'Redis'),
                ('localhost:9000', 'MinIO'),
                ('localhost:4444', 'Selenium'),
                ('localhost:8080', 'ZAP'),
                ('localhost:4723', 'Appium')
            ]
            
            accessible_services = []
            for host_port, service_name in local_services:
                try:
                    host, port = host_port.split(':')
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    
                    if result == 0:
                        accessible_services.append(service_name)
                except:
                    pass
            
            message_parts = []
            if internet_ok:
                message_parts.append("Internet: OK")
            else:
                message_parts.append("Internet: Failed")
            
            message_parts.append(f"Local services: {len(accessible_services)}/{len(local_services)}")
            
            if internet_ok and len(accessible_services) >= len(local_services) // 2:
                status = 'pass'
            elif len(accessible_services) > 0:
                status = 'warning'
            else:
                status = 'fail'
            
            return {
                'status': status,
                'message': ', '.join(message_parts)
            }
            
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def generate_report(self) -> str:
        """Generate verification report"""
        report = []
        report.append("=" * 60)
        report.append("SETUP VERIFICATION REPORT")
        report.append("=" * 60)
        
        passed = sum(1 for r in self.results.values() if r['status'] == 'pass')
        warnings = sum(1 for r in self.results.values() if r['status'] == 'warning')
        failed = sum(1 for r in self.results.values() if r['status'] == 'fail')
        total = len(self.results)
        
        report.append(f"Total Checks: {total}")
        report.append(f"Passed: {passed} ✅")
        report.append(f"Warnings: {warnings} ⚠️")
        report.append(f"Failed: {failed} ❌")
        report.append("")
        
        # Detailed results
        for check_name, result in self.results.items():
            status_icon = {
                'pass': '✅',
                'warning': '⚠️',
                'fail': '❌'
            }.get(result['status'], '❓')
            
            report.append(f"{status_icon} {check_name}: {result['message']}")
        
        if self.errors:
            report.append("")
            report.append("ERRORS TO ADDRESS:")
            report.append("-" * 20)
            for error in self.errors:
                report.append(f"• {error}")
        
        report.append("")
        report.append("=" * 60)
        
        if failed == 0:
            if warnings == 0:
                report.append("🎉 SETUP VERIFICATION PASSED!")
                report.append("All components are properly configured.")
            else:
                report.append("⚠️  SETUP VERIFICATION PASSED WITH WARNINGS")
                report.append("Some components need attention but system is functional.")
        else:
            report.append("❌ SETUP VERIFICATION FAILED")
            report.append("Critical components are not properly configured.")
            report.append("Please address the errors above before proceeding.")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main function"""
    verifier = SetupVerifier()
    
    try:
        # Run all checks
        results = verifier.run_all_checks()
        
        # Generate and display report
        report = verifier.generate_report()
        print(report)
        
        # Save report to file
        report_file = Path('setup_verification_report.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_file}")
        
        # Save JSON results
        json_file = Path('setup_verification_results.json')
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Detailed results saved to: {json_file}")
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results.values() if r['status'] == 'fail')
        sys.exit(1 if failed_count > 0 else 0)
        
    except KeyboardInterrupt:
        print("\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Verification failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()