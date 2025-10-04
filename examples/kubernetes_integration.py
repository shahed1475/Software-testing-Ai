#!/usr/bin/env python3
"""
Kubernetes Integration Example for Unified Testing Framework

This example demonstrates how to deploy and test applications
in Kubernetes environments using the unified testing framework.
"""

import asyncio
import json
import os
import subprocess
import time
import yaml
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


class KubernetesIntegration:
    """
    Kubernetes Integration class for unified testing framework
    """
    
    def __init__(self, namespace: str = "testing"):
        """Initialize Kubernetes integration"""
        self.namespace = namespace
        self.orchestrator = UnifiedTestingOrchestrator()
        self.report_generator = ReportGenerator()
        self.deployed_resources = []
        self.services = {}
        
    async def setup_k8s_environment(self) -> Dict[str, Any]:
        """
        Set up Kubernetes testing environment
        """
        print("☸️ Setting up Kubernetes test environment")
        print("=" * 50)
        
        try:
            # Check kubectl availability
            await self._check_kubectl()
            
            # Create namespace
            await self._create_namespace()
            
            # Deploy test applications
            await self._deploy_test_applications()
            
            # Deploy testing infrastructure
            await self._deploy_testing_infrastructure()
            
            # Wait for deployments to be ready
            await self._wait_for_deployments()
            
            # Get service endpoints
            await self._get_service_endpoints()
            
            print("✅ Kubernetes test environment ready!")
            
            return {
                "status": "ready",
                "namespace": self.namespace,
                "services": self.services,
                "deployed_resources": self.deployed_resources
            }
            
        except Exception as e:
            print(f"❌ Failed to setup Kubernetes environment: {e}")
            await self.cleanup_k8s_environment()
            raise
    
    async def _check_kubectl(self):
        """Check if kubectl is available and configured"""
        print("🔍 Checking kubectl availability...")
        
        try:
            result = subprocess.run([
                "kubectl", "version", "--client", "--short"
            ], capture_output=True, text=True, check=True)
            print("   ✅ kubectl is available")
            
            # Check cluster connection
            cluster_result = subprocess.run([
                "kubectl", "cluster-info"
            ], capture_output=True, text=True, check=True)
            print("   ✅ Connected to Kubernetes cluster")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"kubectl not available or not configured: {e}")
    
    async def _create_namespace(self):
        """Create testing namespace"""
        print(f"📁 Creating namespace '{self.namespace}'...")
        
        try:
            # Check if namespace exists
            result = subprocess.run([
                "kubectl", "get", "namespace", self.namespace
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                # Create namespace
                subprocess.run([
                    "kubectl", "create", "namespace", self.namespace
                ], check=True, capture_output=True)
                print(f"   ✅ Namespace '{self.namespace}' created")
            else:
                print(f"   ✅ Namespace '{self.namespace}' already exists")
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create namespace: {e}")
    
    async def _deploy_test_applications(self):
        """Deploy test applications to Kubernetes"""
        print("🚀 Deploying test applications...")
        
        # Web application deployment
        web_app_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-web-app",
                "namespace": self.namespace,
                "labels": {"app": "test-web-app"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "test-web-app"}},
                "template": {
                    "metadata": {"labels": {"app": "test-web-app"}},
                    "spec": {
                        "containers": [{
                            "name": "web-app",
                            "image": "nginx:alpine",
                            "ports": [{"containerPort": 80}],
                            "env": [{"name": "NODE_ENV", "value": "test"}],
                            "resources": {
                                "requests": {"memory": "64Mi", "cpu": "50m"},
                                "limits": {"memory": "128Mi", "cpu": "100m"}
                            }
                        }]
                    }
                }
            }
        }
        
        # Web service
        web_service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "test-web-service",
                "namespace": self.namespace
            },
            "spec": {
                "selector": {"app": "test-web-app"},
                "ports": [{"port": 80, "targetPort": 80, "nodePort": 30080}],
                "type": "NodePort"
            }
        }
        
        # API application deployment
        api_app_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-api-app",
                "namespace": self.namespace,
                "labels": {"app": "test-api-app"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "test-api-app"}},
                "template": {
                    "metadata": {"labels": {"app": "test-api-app"}},
                    "spec": {
                        "containers": [{
                            "name": "api-app",
                            "image": "node:alpine",
                            "ports": [{"containerPort": 3000}],
                            "command": ["sh", "-c"],
                            "args": [
                                "echo 'const express = require(\"express\"); const app = express(); app.get(\"/health\", (req, res) => res.json({status: \"ok\", timestamp: new Date().toISOString()})); app.get(\"/api/test\", (req, res) => res.json({message: \"Hello from Kubernetes!\"})); app.listen(3000, () => console.log(\"API running on port 3000\"));' > app.js && npm init -y && npm install express && node app.js"
                            ],
                            "env": [{"name": "NODE_ENV", "value": "test"}],
                            "resources": {
                                "requests": {"memory": "128Mi", "cpu": "100m"},
                                "limits": {"memory": "256Mi", "cpu": "200m"}
                            }
                        }]
                    }
                }
            }
        }
        
        # API service
        api_service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "test-api-service",
                "namespace": self.namespace
            },
            "spec": {
                "selector": {"app": "test-api-app"},
                "ports": [{"port": 3000, "targetPort": 3000, "nodePort": 30300}],
                "type": "NodePort"
            }
        }
        
        # Database deployment
        db_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-database",
                "namespace": self.namespace,
                "labels": {"app": "test-database"}
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "test-database"}},
                "template": {
                    "metadata": {"labels": {"app": "test-database"}},
                    "spec": {
                        "containers": [{
                            "name": "postgres",
                            "image": "postgres:13-alpine",
                            "ports": [{"containerPort": 5432}],
                            "env": [
                                {"name": "POSTGRES_DB", "value": "testdb"},
                                {"name": "POSTGRES_USER", "value": "testuser"},
                                {"name": "POSTGRES_PASSWORD", "value": "testpass"}
                            ],
                            "resources": {
                                "requests": {"memory": "256Mi", "cpu": "100m"},
                                "limits": {"memory": "512Mi", "cpu": "200m"}
                            }
                        }]
                    }
                }
            }
        }
        
        # Database service
        db_service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "test-database-service",
                "namespace": self.namespace
            },
            "spec": {
                "selector": {"app": "test-database"},
                "ports": [{"port": 5432, "targetPort": 5432}],
                "type": "ClusterIP"
            }
        }
        
        # Deploy all manifests
        manifests = [
            ("web-app-deployment", web_app_manifest),
            ("web-service", web_service_manifest),
            ("api-app-deployment", api_app_manifest),
            ("api-service", api_service_manifest),
            ("database-deployment", db_manifest),
            ("database-service", db_service_manifest)
        ]
        
        for name, manifest in manifests:
            await self._apply_manifest(name, manifest)
    
    async def _deploy_testing_infrastructure(self):
        """Deploy testing infrastructure to Kubernetes"""
        print("🧪 Deploying testing infrastructure...")
        
        # Selenium Grid Hub
        selenium_hub_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "selenium-hub",
                "namespace": self.namespace,
                "labels": {"app": "selenium-hub"}
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "selenium-hub"}},
                "template": {
                    "metadata": {"labels": {"app": "selenium-hub"}},
                    "spec": {
                        "containers": [{
                            "name": "selenium-hub",
                            "image": "selenium/hub:4.15.0",
                            "ports": [{"containerPort": 4444}],
                            "resources": {
                                "requests": {"memory": "512Mi", "cpu": "200m"},
                                "limits": {"memory": "1Gi", "cpu": "500m"}
                            }
                        }]
                    }
                }
            }
        }
        
        # Selenium Hub Service
        selenium_hub_service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "selenium-hub-service",
                "namespace": self.namespace
            },
            "spec": {
                "selector": {"app": "selenium-hub"},
                "ports": [{"port": 4444, "targetPort": 4444, "nodePort": 30444}],
                "type": "NodePort"
            }
        }
        
        # Chrome Node
        chrome_node_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "selenium-chrome",
                "namespace": self.namespace,
                "labels": {"app": "selenium-chrome"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "selenium-chrome"}},
                "template": {
                    "metadata": {"labels": {"app": "selenium-chrome"}},
                    "spec": {
                        "containers": [{
                            "name": "selenium-chrome",
                            "image": "selenium/node-chrome:4.15.0",
                            "env": [
                                {"name": "HUB_HOST", "value": "selenium-hub-service"},
                                {"name": "HUB_PORT", "value": "4444"}
                            ],
                            "resources": {
                                "requests": {"memory": "1Gi", "cpu": "500m"},
                                "limits": {"memory": "2Gi", "cpu": "1000m"}
                            },
                            "volumeMounts": [{
                                "name": "dshm",
                                "mountPath": "/dev/shm"
                            }]
                        }],
                        "volumes": [{
                            "name": "dshm",
                            "emptyDir": {"medium": "Memory", "sizeLimit": "2Gi"}
                        }]
                    }
                }
            }
        }
        
        # OWASP ZAP
        zap_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "owasp-zap",
                "namespace": self.namespace,
                "labels": {"app": "owasp-zap"}
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "owasp-zap"}},
                "template": {
                    "metadata": {"labels": {"app": "owasp-zap"}},
                    "spec": {
                        "containers": [{
                            "name": "owasp-zap",
                            "image": "owasp/zap2docker-stable",
                            "ports": [{"containerPort": 8080}],
                            "command": ["zap.sh"],
                            "args": [
                                "-daemon", "-host", "0.0.0.0", "-port", "8080",
                                "-config", "api.addrs.addr.name=.*",
                                "-config", "api.addrs.addr.regex=true"
                            ],
                            "resources": {
                                "requests": {"memory": "512Mi", "cpu": "200m"},
                                "limits": {"memory": "1Gi", "cpu": "500m"}
                            }
                        }]
                    }
                }
            }
        }
        
        # ZAP Service
        zap_service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "owasp-zap-service",
                "namespace": self.namespace
            },
            "spec": {
                "selector": {"app": "owasp-zap"},
                "ports": [{"port": 8080, "targetPort": 8080, "nodePort": 30808}],
                "type": "NodePort"
            }
        }
        
        # Deploy testing infrastructure
        testing_manifests = [
            ("selenium-hub-deployment", selenium_hub_manifest),
            ("selenium-hub-service", selenium_hub_service_manifest),
            ("selenium-chrome-deployment", chrome_node_manifest),
            ("owasp-zap-deployment", zap_manifest),
            ("owasp-zap-service", zap_service_manifest)
        ]
        
        for name, manifest in testing_manifests:
            await self._apply_manifest(name, manifest)
    
    async def _apply_manifest(self, name: str, manifest: Dict[str, Any]):
        """Apply Kubernetes manifest"""
        try:
            # Create temporary file for manifest
            manifest_file = f"/tmp/{name}-{int(time.time())}.yaml"
            
            with open(manifest_file, 'w') as f:
                yaml.dump(manifest, f)
            
            # Apply manifest
            result = subprocess.run([
                "kubectl", "apply", "-f", manifest_file
            ], capture_output=True, text=True, check=True)
            
            self.deployed_resources.append({
                "name": name,
                "kind": manifest.get("kind"),
                "manifest_file": manifest_file
            })
            
            print(f"   ✅ Applied {name}")
            
            # Clean up temporary file
            os.unlink(manifest_file)
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to apply {name}: {e}")
            raise
    
    async def _wait_for_deployments(self):
        """Wait for all deployments to be ready"""
        print("⏳ Waiting for deployments to be ready...")
        
        deployments = [
            "test-web-app",
            "test-api-app", 
            "test-database",
            "selenium-hub",
            "selenium-chrome",
            "owasp-zap"
        ]
        
        for deployment in deployments:
            print(f"   🔍 Waiting for {deployment}...")
            
            try:
                subprocess.run([
                    "kubectl", "rollout", "status", 
                    f"deployment/{deployment}",
                    "-n", self.namespace,
                    "--timeout=300s"
                ], check=True, capture_output=True)
                
                print(f"   ✅ {deployment} is ready")
                
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️ {deployment} not ready within timeout")
    
    async def _get_service_endpoints(self):
        """Get service endpoints for testing"""
        print("🔗 Getting service endpoints...")
        
        try:
            # Get node IP
            node_result = subprocess.run([
                "kubectl", "get", "nodes", 
                "-o", "jsonpath={.items[0].status.addresses[?(@.type=='InternalIP')].address}"
            ], capture_output=True, text=True, check=True)
            
            node_ip = node_result.stdout.strip()
            if not node_ip:
                node_ip = "localhost"
            
            # Define service endpoints
            self.services = {
                "web_app": {
                    "url": f"http://{node_ip}:30080",
                    "internal_url": f"http://test-web-service.{self.namespace}.svc.cluster.local"
                },
                "api": {
                    "url": f"http://{node_ip}:30300",
                    "internal_url": f"http://test-api-service.{self.namespace}.svc.cluster.local:3000"
                },
                "selenium_hub": {
                    "url": f"http://{node_ip}:30444",
                    "internal_url": f"http://selenium-hub-service.{self.namespace}.svc.cluster.local:4444"
                },
                "owasp_zap": {
                    "url": f"http://{node_ip}:30808",
                    "internal_url": f"http://owasp-zap-service.{self.namespace}.svc.cluster.local:8080"
                }
            }
            
            print("   ✅ Service endpoints configured:")
            for name, service in self.services.items():
                print(f"      • {name}: {service['url']}")
                
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Failed to get service endpoints: {e}")
            # Use default localhost endpoints
            self.services = {
                "web_app": {"url": "http://localhost:30080"},
                "api": {"url": "http://localhost:30300"},
                "selenium_hub": {"url": "http://localhost:30444"},
                "owasp_zap": {"url": "http://localhost:30808"}
            }
    
    async def run_k8s_tests(self) -> Dict[str, Any]:
        """
        Run unified tests in Kubernetes environment
        """
        print("\n☸️ Running Kubernetes tests")
        print("=" * 50)
        
        # Create test plan for Kubernetes environment
        plan = self._create_k8s_test_plan()
        
        print(f"📋 Test plan created:")
        print(f"   • Target: {plan.target_config.get('primary_target')}")
        print(f"   • API endpoints: {len(plan.target_config.get('api_endpoints', []))}")
        print(f"   • Security scans: {len(plan.security_scans)}")
        print(f"   • Compliance checks: {len(plan.compliance_checks)}")
        
        # Execute tests
        print("\n🔄 Executing Kubernetes tests...")
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
            
            # Generate Kubernetes-specific report
            await self._generate_k8s_report(result, execution_time)
            
            return {
                "status": "completed",
                "result": result,
                "execution_time": execution_time,
                "namespace": self.namespace,
                "services_tested": list(self.services.keys())
            }
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _create_k8s_test_plan(self) -> UnifiedTestPlan:
        """Create test plan optimized for Kubernetes environment"""
        
        # Use Kubernetes service URLs
        target_url = self.services.get("web_app", {}).get("url", "http://localhost:30080")
        api_base = self.services.get("api", {}).get("url", "http://localhost:30300")
        
        plan = create_comprehensive_test_plan(
            target_url=target_url,
            api_endpoints=[f"{api_base}/health", f"{api_base}/api/test"],
            execution_strategy=UnifiedExecutionStrategy.PARALLEL,
            include_security=True,
            include_compliance=True
        )
        
        # Customize for Kubernetes environment
        plan.name = f"Kubernetes Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan.description = "Unified testing in Kubernetes cluster"
        
        # Configure Selenium to use Kubernetes grid
        plan.target_config["selenium_grid_url"] = self.services.get("selenium_hub", {}).get("url")
        plan.target_config["kubernetes_namespace"] = self.namespace
        
        # Configure security tools for Kubernetes environment
        plan.security_scans = {
            "owasp_zap": {
                "proxy_url": self.services.get("owasp_zap", {}).get("url"),
                "target_url": target_url,
                "scan_type": "baseline"
            },
            "kubernetes_security": {
                "pod_security": True,
                "network_policies": True,
                "rbac_analysis": True,
                "resource_limits": True
            }
        }
        
        # Add Kubernetes-specific compliance checks
        plan.compliance_checks = {
            "GDPR": {
                "level": "basic",
                "data_protection": True
            },
            "Kubernetes_Security": {
                "pod_security_standards": True,
                "network_segmentation": True,
                "secrets_management": True,
                "resource_quotas": True
            },
            "CIS_Kubernetes": {
                "master_node_security": True,
                "worker_node_security": True,
                "policies": True
            }
        }
        
        return plan
    
    async def _generate_k8s_report(self, result, execution_time: float):
        """Generate report specific to Kubernetes testing"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Kubernetes environment information
        k8s_info = {
            "environment": "Kubernetes",
            "namespace": self.namespace,
            "services": self.services,
            "deployed_resources": self.deployed_resources,
            "execution_time": execution_time
        }
        
        # Get cluster information
        try:
            cluster_info = await self._get_cluster_info()
            k8s_info["cluster_info"] = cluster_info
        except Exception as e:
            k8s_info["cluster_info"] = {"error": str(e)}
        
        # Generate comprehensive report with Kubernetes context
        try:
            report = await self.report_generator.generate_comprehensive_report(
                functional_results=getattr(result, 'functional_results', None),
                security_results=getattr(result, 'security_results', None),
                compliance_results=getattr(result, 'compliance_results', None)
            )
            
            # Add Kubernetes information to report
            enhanced_html = self._enhance_report_with_k8s_info(report.html_content, k8s_info)
            
            # Save enhanced report
            report_path = Path("reports") / f"kubernetes-test-{timestamp}.html"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            print(f"📄 Kubernetes report saved: {report_path}")
            
            # Generate pod logs report
            await self._generate_pod_logs_report(timestamp)
            
            # Generate resource usage report
            await self._generate_resource_usage_report(timestamp)
            
        except Exception as e:
            print(f"⚠️ Failed to generate Kubernetes report: {e}")
    
    async def _get_cluster_info(self) -> Dict[str, Any]:
        """Get Kubernetes cluster information"""
        
        cluster_info = {}
        
        try:
            # Get cluster version
            version_result = subprocess.run([
                "kubectl", "version", "--short"
            ], capture_output=True, text=True, check=True)
            cluster_info["version"] = version_result.stdout.strip()
            
            # Get node information
            nodes_result = subprocess.run([
                "kubectl", "get", "nodes", "-o", "json"
            ], capture_output=True, text=True, check=True)
            
            nodes_data = json.loads(nodes_result.stdout)
            cluster_info["nodes"] = len(nodes_data.get("items", []))
            
            # Get namespace resources
            resources_result = subprocess.run([
                "kubectl", "get", "all", "-n", self.namespace, "-o", "json"
            ], capture_output=True, text=True, check=True)
            
            resources_data = json.loads(resources_result.stdout)
            cluster_info["resources_in_namespace"] = len(resources_data.get("items", []))
            
        except Exception as e:
            cluster_info["error"] = str(e)
        
        return cluster_info
    
    def _enhance_report_with_k8s_info(self, html_content: str, k8s_info: Dict[str, Any]) -> str:
        """Enhance HTML report with Kubernetes information"""
        
        k8s_section = f"""
        <div class="k8s-info" style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #326ce5;">
            <h3>☸️ Kubernetes Environment</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px;">
                <div>
                    <strong>Namespace:</strong> {k8s_info['namespace']}<br>
                    <strong>Execution Time:</strong> {k8s_info['execution_time']:.2f}s<br>
                    <strong>Resources Deployed:</strong> {len(k8s_info['deployed_resources'])}
                </div>
                <div>
                    <strong>Services Tested:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
        """
        
        for name, service in k8s_info['services'].items():
            k8s_section += f"""
                        <li>{name}: {service.get('url', 'N/A')}</li>
            """
        
        k8s_section += """
                    </ul>
                </div>
        """
        
        if "cluster_info" in k8s_info and "error" not in k8s_info["cluster_info"]:
            cluster = k8s_info["cluster_info"]
            k8s_section += f"""
                <div>
                    <strong>Cluster Info:</strong><br>
                    Nodes: {cluster.get('nodes', 'N/A')}<br>
                    Resources in Namespace: {cluster.get('resources_in_namespace', 'N/A')}
                </div>
            """
        
        k8s_section += """
            </div>
        </div>
        """
        
        # Insert Kubernetes info after the header
        if "<body>" in html_content:
            html_content = html_content.replace(
                "<body>", 
                f"<body>{k8s_section}"
            )
        
        return html_content
    
    async def _generate_pod_logs_report(self, timestamp: str):
        """Generate report with pod logs"""
        
        logs_report = {
            "timestamp": datetime.now().isoformat(),
            "namespace": self.namespace,
            "pods": {}
        }
        
        try:
            # Get all pods in namespace
            pods_result = subprocess.run([
                "kubectl", "get", "pods", "-n", self.namespace, "-o", "json"
            ], capture_output=True, text=True, check=True)
            
            pods_data = json.loads(pods_result.stdout)
            
            for pod in pods_data.get("items", []):
                pod_name = pod["metadata"]["name"]
                
                try:
                    # Get pod logs
                    logs_result = subprocess.run([
                        "kubectl", "logs", pod_name, "-n", self.namespace, "--tail=100"
                    ], capture_output=True, text=True)
                    
                    logs_report["pods"][pod_name] = {
                        "status": pod["status"]["phase"],
                        "logs": logs_result.stdout if logs_result.returncode == 0 else "Failed to retrieve logs",
                        "errors": logs_result.stderr if logs_result.stderr else None
                    }
                    
                except Exception as e:
                    logs_report["pods"][pod_name] = {
                        "error": f"Failed to get logs: {e}"
                    }
        
        except Exception as e:
            logs_report["error"] = f"Failed to get pods: {e}"
        
        # Save logs report
        logs_path = Path("reports") / f"k8s-pod-logs-{timestamp}.json"
        
        with open(logs_path, 'w', encoding='utf-8') as f:
            json.dump(logs_report, f, indent=2, default=str)
        
        print(f"📄 Pod logs saved: {logs_path}")
    
    async def _generate_resource_usage_report(self, timestamp: str):
        """Generate resource usage report"""
        
        usage_report = {
            "timestamp": datetime.now().isoformat(),
            "namespace": self.namespace,
            "resource_usage": {}
        }
        
        try:
            # Get resource usage
            usage_result = subprocess.run([
                "kubectl", "top", "pods", "-n", self.namespace
            ], capture_output=True, text=True)
            
            if usage_result.returncode == 0:
                usage_report["resource_usage"]["pods"] = usage_result.stdout
            else:
                usage_report["resource_usage"]["error"] = "Metrics server not available"
            
        except Exception as e:
            usage_report["resource_usage"]["error"] = str(e)
        
        # Save usage report
        usage_path = Path("reports") / f"k8s-resource-usage-{timestamp}.json"
        
        with open(usage_path, 'w', encoding='utf-8') as f:
            json.dump(usage_report, f, indent=2, default=str)
        
        print(f"📄 Resource usage saved: {usage_path}")
    
    async def cleanup_k8s_environment(self):
        """Clean up Kubernetes test environment"""
        print("\n🧹 Cleaning up Kubernetes environment...")
        
        try:
            # Delete all resources in namespace
            print(f"   🗑️ Deleting resources in namespace {self.namespace}...")
            subprocess.run([
                "kubectl", "delete", "all", "--all", "-n", self.namespace
            ], check=False, capture_output=True)
            
            # Delete namespace
            print(f"   📁 Deleting namespace {self.namespace}...")
            subprocess.run([
                "kubectl", "delete", "namespace", self.namespace
            ], check=False, capture_output=True)
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"   ⚠️ Cleanup failed: {e}")


async def main():
    """
    Main function for Kubernetes integration example
    """
    print("☸️ Kubernetes Integration - Unified Testing Framework")
    print("=" * 60)
    
    k8s_integration = KubernetesIntegration()
    
    try:
        # Setup Kubernetes environment
        setup_result = await k8s_integration.setup_k8s_environment()
        
        if setup_result["status"] == "ready":
            # Run Kubernetes tests
            test_result = await k8s_integration.run_k8s_tests()
            
            # Display final results
            print(f"\n🏁 Final Results:")
            print(f"   • Status: {test_result['status']}")
            
            if test_result["status"] == "completed":
                print(f"   • Success Rate: {test_result['result'].success_rate:.2%}")
                print(f"   • Execution Time: {test_result['execution_time']:.2f}s")
                print(f"   • Namespace: {test_result['namespace']}")
                print(f"   • Services Tested: {', '.join(test_result['services_tested'])}")
                print("✅ Kubernetes testing completed successfully!")
            else:
                print(f"   • Error: {test_result.get('error', 'Unknown error')}")
                print("❌ Kubernetes testing failed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        # Always cleanup
        await k8s_integration.cleanup_k8s_environment()


if __name__ == "__main__":
    asyncio.run(main())