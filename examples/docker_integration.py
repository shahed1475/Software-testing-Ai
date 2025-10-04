#!/usr/bin/env python3
"""
Docker Integration Example for Unified Testing Framework

This example demonstrates how to run the unified testing framework
in Docker containers and integrate with containerized applications.
"""

import asyncio
import json
import os
import subprocess
import time
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


class DockerIntegration:
    """
    Docker Integration class for unified testing framework
    """
    
    def __init__(self):
        """Initialize Docker integration"""
        self.orchestrator = UnifiedTestingOrchestrator()
        self.report_generator = ReportGenerator()
        self.docker_network = "testing-network"
        self.containers = {}
        
    async def setup_test_environment(self) -> Dict[str, Any]:
        """
        Set up containerized test environment
        """
        print("🐳 Setting up Docker test environment")
        print("=" * 50)
        
        try:
            # Create Docker network
            print("🌐 Creating Docker network...")
            subprocess.run([
                "docker", "network", "create", 
                "--driver", "bridge", 
                self.docker_network
            ], check=False, capture_output=True)
            
            # Start test application containers
            await self._start_application_containers()
            
            # Start testing infrastructure containers
            await self._start_testing_containers()
            
            # Wait for services to be ready
            await self._wait_for_services()
            
            print("✅ Docker test environment ready!")
            
            return {
                "status": "ready",
                "network": self.docker_network,
                "containers": self.containers
            }
            
        except Exception as e:
            print(f"❌ Failed to setup Docker environment: {e}")
            await self.cleanup_environment()
            raise
    
    async def _start_application_containers(self):
        """Start application containers for testing"""
        
        # Start web application container
        print("🌐 Starting web application container...")
        web_result = subprocess.run([
            "docker", "run", "-d",
            "--name", "test-web-app",
            "--network", self.docker_network,
            "-p", "8080:80",
            "-e", "NODE_ENV=test",
            "nginx:alpine"
        ], capture_output=True, text=True)
        
        if web_result.returncode == 0:
            self.containers["web_app"] = {
                "container_id": web_result.stdout.strip(),
                "name": "test-web-app",
                "port": 8080,
                "url": "http://localhost:8080"
            }
            print("   ✅ Web application started")
        else:
            print(f"   ❌ Failed to start web app: {web_result.stderr}")
        
        # Start API container
        print("🔌 Starting API container...")
        api_result = subprocess.run([
            "docker", "run", "-d",
            "--name", "test-api",
            "--network", self.docker_network,
            "-p", "3000:3000",
            "-e", "NODE_ENV=test",
            "-e", "PORT=3000",
            "node:alpine",
            "sh", "-c", "echo 'const express = require(\"express\"); const app = express(); app.get(\"/health\", (req, res) => res.json({status: \"ok\"})); app.listen(3000);' > app.js && npm init -y && npm install express && node app.js"
        ], capture_output=True, text=True)
        
        if api_result.returncode == 0:
            self.containers["api"] = {
                "container_id": api_result.stdout.strip(),
                "name": "test-api",
                "port": 3000,
                "url": "http://localhost:3000"
            }
            print("   ✅ API container started")
        else:
            print(f"   ❌ Failed to start API: {api_result.stderr}")
        
        # Start database container
        print("🗄️ Starting database container...")
        db_result = subprocess.run([
            "docker", "run", "-d",
            "--name", "test-database",
            "--network", self.docker_network,
            "-p", "5432:5432",
            "-e", "POSTGRES_DB=testdb",
            "-e", "POSTGRES_USER=testuser",
            "-e", "POSTGRES_PASSWORD=testpass",
            "postgres:13-alpine"
        ], capture_output=True, text=True)
        
        if db_result.returncode == 0:
            self.containers["database"] = {
                "container_id": db_result.stdout.strip(),
                "name": "test-database",
                "port": 5432,
                "url": "postgresql://testuser:testpass@localhost:5432/testdb"
            }
            print("   ✅ Database container started")
        else:
            print(f"   ❌ Failed to start database: {db_result.stderr}")
    
    async def _start_testing_containers(self):
        """Start testing infrastructure containers"""
        
        # Start Selenium Grid Hub
        print("🕷️ Starting Selenium Grid...")
        hub_result = subprocess.run([
            "docker", "run", "-d",
            "--name", "selenium-hub",
            "--network", self.docker_network,
            "-p", "4444:4444",
            "selenium/hub:4.15.0"
        ], capture_output=True, text=True)
        
        if hub_result.returncode == 0:
            self.containers["selenium_hub"] = {
                "container_id": hub_result.stdout.strip(),
                "name": "selenium-hub",
                "port": 4444,
                "url": "http://localhost:4444"
            }
            print("   ✅ Selenium Hub started")
            
            # Start Chrome node
            chrome_result = subprocess.run([
                "docker", "run", "-d",
                "--name", "selenium-chrome",
                "--network", self.docker_network,
                "-e", "HUB_HOST=selenium-hub",
                "-e", "HUB_PORT=4444",
                "--shm-size=2g",
                "selenium/node-chrome:4.15.0"
            ], capture_output=True, text=True)
            
            if chrome_result.returncode == 0:
                self.containers["selenium_chrome"] = {
                    "container_id": chrome_result.stdout.strip(),
                    "name": "selenium-chrome"
                }
                print("   ✅ Chrome node started")
        
        # Start OWASP ZAP container
        print("🛡️ Starting OWASP ZAP...")
        zap_result = subprocess.run([
            "docker", "run", "-d",
            "--name", "owasp-zap",
            "--network", self.docker_network,
            "-p", "8090:8080",
            "-i", "owasp/zap2docker-stable",
            "zap.sh", "-daemon", "-host", "0.0.0.0", "-port", "8080",
            "-config", "api.addrs.addr.name=.*", "-config", "api.addrs.addr.regex=true"
        ], capture_output=True, text=True)
        
        if zap_result.returncode == 0:
            self.containers["owasp_zap"] = {
                "container_id": zap_result.stdout.strip(),
                "name": "owasp-zap",
                "port": 8090,
                "url": "http://localhost:8090"
            }
            print("   ✅ OWASP ZAP started")
    
    async def _wait_for_services(self):
        """Wait for all services to be ready"""
        print("⏳ Waiting for services to be ready...")
        
        max_retries = 30
        retry_interval = 2
        
        services_to_check = [
            ("Web App", "http://localhost:8080"),
            ("API", "http://localhost:3000/health"),
            ("Selenium Hub", "http://localhost:4444/status"),
            ("OWASP ZAP", "http://localhost:8090")
        ]
        
        for service_name, url in services_to_check:
            print(f"   🔍 Checking {service_name}...")
            
            for attempt in range(max_retries):
                try:
                    import requests
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"   ✅ {service_name} is ready")
                        break
                except:
                    if attempt < max_retries - 1:
                        time.sleep(retry_interval)
                    else:
                        print(f"   ⚠️ {service_name} not responding, continuing anyway")
    
    async def run_containerized_tests(self) -> Dict[str, Any]:
        """
        Run unified tests in containerized environment
        """
        print("\n🧪 Running containerized tests")
        print("=" * 50)
        
        # Create test plan for containerized environment
        plan = self._create_containerized_test_plan()
        
        print(f"📋 Test plan created:")
        print(f"   • Target: {plan.target_config.get('primary_target')}")
        print(f"   • API endpoints: {len(plan.target_config.get('api_endpoints', []))}")
        print(f"   • Security scans: {len(plan.security_scans)}")
        print(f"   • Compliance checks: {len(plan.compliance_checks)}")
        
        # Execute tests
        print("\n🔄 Executing containerized tests...")
        start_time = datetime.now()
        
        try:
            result = await self.orchestrator.execute_unified_plan(plan)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Display results
            print(f"\n📊 Test Results:")
            print(f"   • Total Tests: {result.total_tests}")
            print(f"   • Passed: {result.passed_tests}")
            print(f"   • Failed: {result.failed_tests}")
            print(f"   • Success Rate: {result.success_rate:.2%}")
            print(f"   • Execution Time: {execution_time:.2f}s")
            
            # Generate container-specific report
            await self._generate_containerized_report(result, execution_time)
            
            return {
                "status": "completed",
                "result": result,
                "execution_time": execution_time,
                "containers_used": list(self.containers.keys())
            }
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _create_containerized_test_plan(self) -> UnifiedTestPlan:
        """Create test plan optimized for containerized environment"""
        
        # Use container URLs
        target_url = self.containers.get("web_app", {}).get("url", "http://localhost:8080")
        api_url = self.containers.get("api", {}).get("url", "http://localhost:3000")
        
        plan = create_comprehensive_test_plan(
            target_url=target_url,
            api_endpoints=[f"{api_url}/health", f"{api_url}/api/test"],
            execution_strategy=UnifiedExecutionStrategy.PARALLEL,
            include_security=True,
            include_compliance=True
        )
        
        # Customize for containerized environment
        plan.name = f"Containerized Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan.description = "Unified testing in Docker containers"
        
        # Configure Selenium to use containerized grid
        if "selenium_hub" in self.containers:
            plan.target_config["selenium_grid_url"] = self.containers["selenium_hub"]["url"]
        
        # Configure security tools for container environment
        plan.security_scans = {
            "owasp_zap": {
                "proxy_url": self.containers.get("owasp_zap", {}).get("url", "http://localhost:8090"),
                "target_url": target_url,
                "scan_type": "baseline"
            },
            "container_scan": {
                "scan_images": True,
                "scan_running_containers": True
            }
        }
        
        # Add container-specific compliance checks
        plan.compliance_checks = {
            "GDPR": {
                "level": "basic",
                "container_data_protection": True
            },
            "Container_Security": {
                "image_vulnerabilities": True,
                "runtime_security": True,
                "network_policies": True
            }
        }
        
        return plan
    
    async def _generate_containerized_report(self, result, execution_time: float):
        """Generate report specific to containerized testing"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Container information
        container_info = {
            "environment": "Docker",
            "network": self.docker_network,
            "containers": self.containers,
            "execution_time": execution_time
        }
        
        # Generate comprehensive report with container context
        try:
            report = await self.report_generator.generate_comprehensive_report(
                functional_results=getattr(result, 'functional_results', None),
                security_results=getattr(result, 'security_results', None),
                compliance_results=getattr(result, 'compliance_results', None)
            )
            
            # Add container information to report
            enhanced_html = self._enhance_report_with_container_info(report.html_content, container_info)
            
            # Save enhanced report
            report_path = Path("reports") / f"containerized-test-{timestamp}.html"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            print(f"📄 Containerized report saved: {report_path}")
            
            # Generate container logs report
            await self._generate_container_logs_report(timestamp)
            
        except Exception as e:
            print(f"⚠️ Failed to generate containerized report: {e}")
    
    def _enhance_report_with_container_info(self, html_content: str, container_info: Dict[str, Any]) -> str:
        """Enhance HTML report with container information"""
        
        container_section = f"""
        <div class="container-info" style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff;">
            <h3>🐳 Container Environment</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px;">
                <div>
                    <strong>Network:</strong> {container_info['network']}<br>
                    <strong>Execution Time:</strong> {container_info['execution_time']:.2f}s
                </div>
                <div>
                    <strong>Containers Used:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
        """
        
        for name, info in container_info['containers'].items():
            container_section += f"""
                        <li>{name}: {info.get('name', 'N/A')} (Port: {info.get('port', 'N/A')})</li>
            """
        
        container_section += """
                    </ul>
                </div>
            </div>
        </div>
        """
        
        # Insert container info after the header
        if "<body>" in html_content:
            html_content = html_content.replace(
                "<body>", 
                f"<body>{container_section}"
            )
        
        return html_content
    
    async def _generate_container_logs_report(self, timestamp: str):
        """Generate report with container logs"""
        
        logs_report = {
            "timestamp": datetime.now().isoformat(),
            "containers": {}
        }
        
        for name, info in self.containers.items():
            try:
                # Get container logs
                logs_result = subprocess.run([
                    "docker", "logs", "--tail", "100", info["name"]
                ], capture_output=True, text=True)
                
                logs_report["containers"][name] = {
                    "container_name": info["name"],
                    "container_id": info.get("container_id", ""),
                    "logs": logs_result.stdout if logs_result.returncode == 0 else "Failed to retrieve logs",
                    "errors": logs_result.stderr if logs_result.stderr else None
                }
                
            except Exception as e:
                logs_report["containers"][name] = {
                    "error": f"Failed to get logs: {e}"
                }
        
        # Save logs report
        logs_path = Path("reports") / f"container-logs-{timestamp}.json"
        
        with open(logs_path, 'w', encoding='utf-8') as f:
            json.dump(logs_report, f, indent=2, default=str)
        
        print(f"📄 Container logs saved: {logs_path}")
    
    async def cleanup_environment(self):
        """Clean up Docker test environment"""
        print("\n🧹 Cleaning up Docker environment...")
        
        # Stop and remove containers
        for name, info in self.containers.items():
            try:
                print(f"   🛑 Stopping {name}...")
                subprocess.run([
                    "docker", "stop", info["name"]
                ], check=False, capture_output=True)
                
                subprocess.run([
                    "docker", "rm", info["name"]
                ], check=False, capture_output=True)
                
            except Exception as e:
                print(f"   ⚠️ Failed to cleanup {name}: {e}")
        
        # Remove network
        try:
            print(f"   🌐 Removing network {self.docker_network}...")
            subprocess.run([
                "docker", "network", "rm", self.docker_network
            ], check=False, capture_output=True)
        except Exception as e:
            print(f"   ⚠️ Failed to remove network: {e}")
        
        print("✅ Cleanup completed")
    
    async def run_docker_compose_tests(self, compose_file: str = "docker-compose.test.yml"):
        """
        Run tests using Docker Compose
        """
        print(f"\n🐳 Running Docker Compose tests with {compose_file}")
        print("=" * 50)
        
        try:
            # Start services with Docker Compose
            print("🚀 Starting services with Docker Compose...")
            subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], check=True)
            
            # Wait for services
            print("⏳ Waiting for services to be ready...")
            time.sleep(10)
            
            # Run tests
            result = await self.run_containerized_tests()
            
            # Stop services
            print("🛑 Stopping Docker Compose services...")
            subprocess.run([
                "docker-compose", "-f", compose_file, "down"
            ], check=False)
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker Compose failed: {e}")
            return {"status": "failed", "error": str(e)}


async def main():
    """
    Main function for Docker integration example
    """
    print("🐳 Docker Integration - Unified Testing Framework")
    print("=" * 60)
    
    docker_integration = DockerIntegration()
    
    try:
        # Setup containerized environment
        setup_result = await docker_integration.setup_test_environment()
        
        if setup_result["status"] == "ready":
            # Run containerized tests
            test_result = await docker_integration.run_containerized_tests()
            
            # Display final results
            print(f"\n🏁 Final Results:")
            print(f"   • Status: {test_result['status']}")
            
            if test_result["status"] == "completed":
                print(f"   • Success Rate: {test_result['result'].success_rate:.2%}")
                print(f"   • Execution Time: {test_result['execution_time']:.2f}s")
                print(f"   • Containers Used: {', '.join(test_result['containers_used'])}")
                print("✅ Containerized testing completed successfully!")
            else:
                print(f"   • Error: {test_result.get('error', 'Unknown error')}")
                print("❌ Containerized testing failed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        # Always cleanup
        await docker_integration.cleanup_environment()


if __name__ == "__main__":
    asyncio.run(main())