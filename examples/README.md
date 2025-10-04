# Unified Testing Framework - Examples

This directory contains comprehensive examples demonstrating how to integrate and use the Unified Testing Framework in various environments and scenarios.

## 📁 Available Examples

### 1. Basic Unified Testing (`unified_testing_example.py`)
**Purpose**: Demonstrates the core functionality of the unified testing framework

**Features**:
- Basic unified testing workflow
- Security-focused testing
- Compliance assessment
- Comprehensive assessment with all domains
- Custom workflow creation
- Report generation and visualization

**Usage**:
```bash
python examples/unified_testing_example.py
```

**What it demonstrates**:
- Creating and executing unified test plans
- Integrating functional, security, and compliance testing
- Generating comprehensive HTML reports
- Using different execution strategies (sequential, parallel, layered)

---

### 2. CI/CD Integration (`ci_cd_integration.py`)
**Purpose**: Shows how to integrate the framework into CI/CD pipelines

**Features**:
- Environment-based configuration
- Fast CI/CD optimized testing
- Pass/fail criteria evaluation
- Multiple report formats (JUnit XML, JSON, HTML)
- Pipeline status determination

**Usage**:
```bash
# Set environment variables
export TARGET_URL="https://your-app.com"
export API_ENDPOINTS="https://your-app.com/api/health,https://your-app.com/api/status"
export SUCCESS_RATE_THRESHOLD="0.95"
export SECURITY_SCORE_THRESHOLD="80"
export COMPLIANCE_SCORE_THRESHOLD="85"
export MAX_CRITICAL_VULNERABILITIES="0"

# Run CI/CD integration
python examples/ci_cd_integration.py
```

**Configuration Options**:
- `TARGET_URL`: Primary application URL to test
- `API_ENDPOINTS`: Comma-separated list of API endpoints
- `SUCCESS_RATE_THRESHOLD`: Minimum test success rate (0.0-1.0)
- `SECURITY_SCORE_THRESHOLD`: Minimum security score (0-100)
- `COMPLIANCE_SCORE_THRESHOLD`: Minimum compliance score (0-100)
- `MAX_CRITICAL_VULNERABILITIES`: Maximum allowed critical vulnerabilities

**Pipeline Integration**:
```yaml
# GitHub Actions example
- name: Run Unified Tests
  run: |
    python examples/ci_cd_integration.py
  env:
    TARGET_URL: ${{ secrets.TARGET_URL }}
    API_ENDPOINTS: ${{ secrets.API_ENDPOINTS }}
    SUCCESS_RATE_THRESHOLD: "0.95"
```

---

### 3. Docker Integration (`docker_integration.py`)
**Purpose**: Demonstrates testing applications in containerized environments

**Features**:
- Docker container orchestration
- Multi-service testing (web app, API, database)
- Containerized testing infrastructure (Selenium Grid, OWASP ZAP)
- Docker Compose integration
- Container log collection
- Network isolation testing

**Usage**:
```bash
# Ensure Docker is running
python examples/docker_integration.py
```

**What it sets up**:
- **Application Containers**:
  - Nginx web server (port 8080)
  - Node.js API server (port 3000)
  - PostgreSQL database (port 5432)

- **Testing Infrastructure**:
  - Selenium Grid Hub (port 4444)
  - Chrome browser nodes
  - OWASP ZAP security scanner (port 8081)

**Docker Compose Alternative**:
The example also supports Docker Compose workflows for more complex orchestration.

---

### 4. Kubernetes Integration (`kubernetes_integration.py`)
**Purpose**: Shows how to deploy and test applications in Kubernetes clusters

**Features**:
- Kubernetes deployment automation
- Multi-replica application testing
- Kubernetes-native testing infrastructure
- Pod security and compliance checks
- Resource usage monitoring
- Cluster-wide security assessment
- Service mesh testing capabilities

**Prerequisites**:
- `kubectl` installed and configured
- Access to a Kubernetes cluster (local or remote)
- Sufficient cluster resources

**Usage**:
```bash
# Ensure kubectl is configured
kubectl cluster-info

# Run Kubernetes integration
python examples/kubernetes_integration.py
```

**What it deploys**:
- **Application Workloads**:
  - Web application (2 replicas, NodePort 30080)
  - API application (2 replicas, NodePort 30300)
  - PostgreSQL database (1 replica, ClusterIP)

- **Testing Infrastructure**:
  - Selenium Grid Hub (NodePort 30444)
  - Chrome browser nodes (2 replicas)
  - OWASP ZAP scanner (NodePort 30808)

**Kubernetes-Specific Features**:
- Pod Security Standards compliance
- Network policy validation
- RBAC analysis
- Resource quota enforcement
- CIS Kubernetes Benchmark checks

---

## 🚀 Getting Started

### Prerequisites

1. **Python Environment**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Docker** (for Docker integration):
   - Docker Desktop or Docker Engine
   - Docker Compose (optional)

3. **Kubernetes** (for K8s integration):
   - kubectl configured with cluster access
   - Sufficient cluster resources (4+ CPU, 8GB+ RAM recommended)

4. **Testing Tools**:
   - Selenium WebDriver
   - OWASP ZAP (automatically handled in containerized examples)

### Basic Workflow

1. **Choose an Example**: Start with `unified_testing_example.py` for basic functionality
2. **Configure Environment**: Set required environment variables or configuration files
3. **Run the Example**: Execute the Python script
4. **Review Results**: Check generated reports in the `reports/` directory

### Environment Variables

Common environment variables used across examples:

```bash
# Application Configuration
export TARGET_URL="https://your-application.com"
export API_ENDPOINTS="https://your-app.com/api/health,https://your-app.com/api/status"

# Testing Configuration
export EXECUTION_STRATEGY="parallel"  # sequential, parallel, layered, integrated
export INCLUDE_SECURITY="true"
export INCLUDE_COMPLIANCE="true"

# CI/CD Thresholds
export SUCCESS_RATE_THRESHOLD="0.95"
export SECURITY_SCORE_THRESHOLD="80"
export COMPLIANCE_SCORE_THRESHOLD="85"
export MAX_CRITICAL_VULNERABILITIES="0"

# Infrastructure Configuration
export SELENIUM_GRID_URL="http://localhost:4444"
export ZAP_PROXY_URL="http://localhost:8080"

# Kubernetes Configuration
export KUBE_NAMESPACE="testing"
export KUBE_CONTEXT="your-cluster-context"
```

## 📊 Report Generation

All examples generate comprehensive reports in multiple formats:

### HTML Reports
- **Location**: `reports/unified-test-{timestamp}.html`
- **Features**: Interactive dashboards, charts, detailed results
- **Sections**: Executive summary, functional results, security findings, compliance status

### JSON Reports
- **Location**: `reports/unified-test-{timestamp}.json`
- **Features**: Machine-readable format for integration
- **Usage**: API consumption, data analysis, CI/CD integration

### JUnit XML (CI/CD only)
- **Location**: `reports/junit-results.xml`
- **Features**: Standard CI/CD format
- **Usage**: Jenkins, GitHub Actions, Azure DevOps integration

### Specialized Reports
- **Container Logs**: `reports/container-logs-{timestamp}.json`
- **Pod Logs**: `reports/k8s-pod-logs-{timestamp}.json`
- **Resource Usage**: `reports/k8s-resource-usage-{timestamp}.json`

## 🔧 Customization

### Creating Custom Test Plans

```python
from src.unified.unified_orchestrator import UnifiedTestPlan, UnifiedTestingScope

# Create custom test plan
plan = UnifiedTestPlan(
    name="Custom Test Plan",
    description="Tailored testing for specific requirements",
    scope=UnifiedTestingScope.COMPREHENSIVE,
    target_config={
        "primary_target": "https://your-app.com",
        "api_endpoints": ["https://your-app.com/api/v1/health"],
        "selenium_grid_url": "http://localhost:4444"
    },
    functional_tests={
        "ui_tests": {"enabled": True, "browser": "chrome"},
        "api_tests": {"enabled": True, "timeout": 30},
        "integration_tests": {"enabled": True}
    },
    security_scans={
        "owasp_zap": {"scan_type": "full", "target_url": "https://your-app.com"},
        "ssl_analysis": {"enabled": True},
        "vulnerability_scan": {"enabled": True}
    },
    compliance_checks={
        "GDPR": {"level": "comprehensive"},
        "SOC2": {"level": "basic"},
        "custom_policies": {"enabled": True}
    }
)
```

### Environment-Specific Configurations

#### Development Environment
```python
# Fast feedback, basic security
config = {
    "execution_strategy": "parallel",
    "security_level": "basic",
    "compliance_level": "basic",
    "timeout": 300
}
```

#### Staging Environment
```python
# Comprehensive testing, moderate security
config = {
    "execution_strategy": "layered",
    "security_level": "comprehensive",
    "compliance_level": "comprehensive",
    "timeout": 1800
}
```

#### Production Environment
```python
# Full security and compliance validation
config = {
    "execution_strategy": "integrated",
    "security_level": "comprehensive",
    "compliance_level": "comprehensive",
    "timeout": 3600
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker Connection Issues**:
   ```bash
   # Check Docker status
   docker info
   
   # Restart Docker service
   sudo systemctl restart docker
   ```

2. **Kubernetes Access Issues**:
   ```bash
   # Check cluster connection
   kubectl cluster-info
   
   # Verify permissions
   kubectl auth can-i create pods --namespace=testing
   ```

3. **Selenium Grid Issues**:
   ```bash
   # Check grid status
   curl http://localhost:4444/grid/api/hub/status
   
   # Restart grid containers
   docker restart selenium-hub selenium-chrome
   ```

4. **Port Conflicts**:
   - Modify port mappings in the integration scripts
   - Use `netstat -tulpn` to check port usage
   - Update firewall rules if necessary

### Performance Optimization

1. **Parallel Execution**:
   - Use `UnifiedExecutionStrategy.PARALLEL` for faster execution
   - Adjust thread pool sizes based on available resources

2. **Resource Limits**:
   - Set appropriate memory and CPU limits for containers
   - Monitor resource usage during test execution

3. **Test Scope**:
   - Use `UnifiedTestingScope.FOCUSED` for targeted testing
   - Disable unnecessary security scans in development

## 📚 Additional Resources

- **Framework Documentation**: `docs/Phase4_Unified_Testing_Security_Integration.md`
- **API Reference**: `docs/api/`
- **Configuration Guide**: `docs/configuration.md`
- **Best Practices**: `docs/best_practices.md`

## 🤝 Contributing

To add new examples:

1. Create a new Python file in the `examples/` directory
2. Follow the existing naming convention
3. Include comprehensive documentation and error handling
4. Add configuration examples and troubleshooting tips
5. Update this README with the new example

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.