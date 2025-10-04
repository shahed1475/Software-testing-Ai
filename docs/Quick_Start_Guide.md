# Quick Start Guide - Unified Testing Framework

Get up and running with the Unified Testing Framework in minutes! This guide provides the fastest path to start testing your applications with integrated functional, security, and compliance testing.

## 🚀 5-Minute Quick Start

### Step 1: Installation

```bash
# Clone or download the framework
git clone <repository-url>
cd unified-testing-framework

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Basic Configuration

Create a simple configuration file or set environment variables:

```bash
# Set your application URL
export TARGET_URL="https://your-application.com"

# Optional: Set API endpoints for testing
export API_ENDPOINTS="https://your-app.com/api/health,https://your-app.com/api/status"
```

### Step 3: Run Your First Test

```bash
# Run the basic unified testing example
python examples/unified_testing_example.py
```

### Step 4: View Results

Open the generated HTML report:
```bash
# The report will be saved as:
# reports/unified-test-YYYYMMDD_HHMMSS.html
```

**🎉 Congratulations!** You've just run your first unified test with functional, security, and compliance checks!

---

## 📋 What You Get Out of the Box

### ✅ Functional Testing
- **UI Testing**: Automated browser testing with Selenium
- **API Testing**: REST API endpoint validation
- **Integration Testing**: Cross-component functionality
- **Performance Testing**: Response time and load analysis

### 🔒 Security Testing
- **Vulnerability Scanning**: OWASP ZAP integration
- **SSL/TLS Analysis**: Certificate and encryption validation
- **Authentication Testing**: Login and session security
- **Input Validation**: XSS, SQL injection, and other attacks

### 📊 Compliance Testing
- **GDPR**: Data protection and privacy compliance
- **SOC 2**: Security and availability controls
- **Custom Policies**: Organization-specific requirements
- **Industry Standards**: Healthcare, finance, and other sectors

### 📈 Comprehensive Reporting
- **Executive Dashboard**: High-level metrics and KPIs
- **Detailed Results**: Test-by-test breakdown
- **Security Findings**: Vulnerability details and remediation
- **Compliance Status**: Gap analysis and recommendations

---

## 🎯 Choose Your Use Case

### For Web Applications
```python
# Quick web app testing
from examples.unified_testing_example import run_basic_unified_testing

result = await run_basic_unified_testing(
    target_url="https://your-web-app.com"
)
```

### For APIs
```python
# API-focused testing
from examples.unified_testing_example import run_security_focused_testing

result = await run_security_focused_testing(
    api_endpoints=[
        "https://api.your-app.com/v1/health",
        "https://api.your-app.com/v1/users"
    ]
)
```

### For CI/CD Pipelines
```bash
# Set thresholds for pass/fail
export SUCCESS_RATE_THRESHOLD="0.95"
export SECURITY_SCORE_THRESHOLD="80"
export MAX_CRITICAL_VULNERABILITIES="0"

# Run CI/CD optimized testing
python examples/ci_cd_integration.py
```

### For Containerized Apps
```bash
# Test Docker applications
python examples/docker_integration.py
```

### For Kubernetes Deployments
```bash
# Test Kubernetes applications
python examples/kubernetes_integration.py
```

---

## ⚙️ Essential Configuration

### Environment Variables

```bash
# Application Configuration
export TARGET_URL="https://your-app.com"                    # Required
export API_ENDPOINTS="https://your-app.com/api/health"      # Optional

# Testing Preferences
export EXECUTION_STRATEGY="parallel"                        # parallel, sequential, layered
export INCLUDE_SECURITY="true"                             # Enable security testing
export INCLUDE_COMPLIANCE="true"                           # Enable compliance testing

# Browser Configuration
export BROWSER="chrome"                                     # chrome, firefox, edge
export HEADLESS="true"                                      # Run browsers in headless mode

# Timeouts
export TEST_TIMEOUT="300"                                   # Test timeout in seconds
export PAGE_LOAD_TIMEOUT="30"                              # Page load timeout
```

### Configuration File (Optional)

Create `config/test_config.yaml`:

```yaml
# Application Under Test
application:
  primary_url: "https://your-application.com"
  api_endpoints:
    - "https://your-app.com/api/health"
    - "https://your-app.com/api/status"
  
# Testing Configuration
testing:
  execution_strategy: "parallel"
  include_security: true
  include_compliance: true
  browser: "chrome"
  headless: true
  
# Thresholds
thresholds:
  success_rate: 0.95
  security_score: 80
  compliance_score: 85
  max_critical_vulnerabilities: 0
```

---

## 🔧 Common Customizations

### 1. Custom Test Plan

```python
from src.unified.unified_orchestrator import (
    UnifiedTestPlan, 
    UnifiedTestingScope,
    UnifiedExecutionStrategy
)

# Create a focused test plan
plan = UnifiedTestPlan(
    name="My Custom Test",
    scope=UnifiedTestingScope.FOCUSED,
    execution_strategy=UnifiedExecutionStrategy.PARALLEL,
    target_config={
        "primary_target": "https://my-app.com",
        "api_endpoints": ["https://my-app.com/api/health"]
    },
    functional_tests={
        "ui_tests": {"enabled": True, "browser": "chrome"},
        "api_tests": {"enabled": True}
    },
    security_scans={
        "owasp_zap": {"scan_type": "baseline"}
    },
    compliance_checks={
        "GDPR": {"level": "basic"}
    }
)
```

### 2. Custom Reporting

```python
from src.reporting.report_generator import ReportGenerator

# Generate custom report
generator = ReportGenerator()
report = await generator.generate_comprehensive_report(
    functional_results=functional_results,
    security_results=security_results,
    compliance_results=compliance_results
)

# Save with custom name
with open("my-custom-report.html", "w") as f:
    f.write(report.html_content)
```

### 3. Integration with Existing Tools

```python
# Export results to your existing tools
import json

# Export to JSON for external processing
with open("results.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2)

# Generate JUnit XML for CI/CD
from src.reporting.junit_exporter import export_to_junit
export_to_junit(result, "junit-results.xml")
```

---

## 🐛 Quick Troubleshooting

### Issue: "Module not found" errors
**Solution**: Ensure you're in the project root directory and have installed dependencies:
```bash
cd unified-testing-framework
pip install -r requirements.txt
```

### Issue: Browser/WebDriver errors
**Solution**: Install browser drivers or use containerized testing:
```bash
# Install ChromeDriver
pip install webdriver-manager

# Or use Docker integration
python examples/docker_integration.py
```

### Issue: Connection refused errors
**Solution**: Check if your application is running and accessible:
```bash
# Test connectivity
curl -I https://your-application.com

# Check firewall/network settings
```

### Issue: Permission denied (Docker/Kubernetes)
**Solution**: Ensure proper permissions:
```bash
# Docker
sudo usermod -aG docker $USER
newgrp docker

# Kubernetes
kubectl auth can-i create pods --namespace=testing
```

---

## 📚 Next Steps

### Learn More
1. **Read the Full Documentation**: `docs/Phase4_Unified_Testing_Security_Integration.md`
2. **Explore Examples**: Check out all examples in the `examples/` directory
3. **Customize for Your Needs**: Modify test plans and configurations

### Advanced Features
1. **Custom Security Policies**: Define organization-specific security rules
2. **Multi-Environment Testing**: Test across dev, staging, and production
3. **Continuous Monitoring**: Set up automated testing schedules
4. **Integration APIs**: Build custom integrations with your tools

### Get Help
1. **Documentation**: Comprehensive guides in the `docs/` directory
2. **Examples**: Working code samples in the `examples/` directory
3. **Configuration**: Detailed configuration options and best practices

---

## 🎯 Success Metrics

After running your first tests, you should see:

### ✅ Functional Testing Results
- Test execution summary (passed/failed/skipped)
- Performance metrics (response times, load times)
- Coverage analysis (code, line, branch coverage)

### 🔒 Security Assessment
- Vulnerability scan results
- Security score (0-100)
- Risk assessment and recommendations

### 📊 Compliance Status
- Compliance score by standard (GDPR, SOC 2, etc.)
- Gap analysis and remediation roadmap
- Policy adherence metrics

### 📈 Unified Dashboard
- Executive summary with key metrics
- Trend analysis and insights
- Actionable recommendations

---

## 🚀 Ready to Scale?

Once you're comfortable with the basics:

1. **Integrate with CI/CD**: Automate testing in your deployment pipeline
2. **Set up Monitoring**: Continuous testing and alerting
3. **Customize Policies**: Define organization-specific requirements
4. **Scale Infrastructure**: Use Kubernetes for large-scale testing

**Happy Testing!** 🎉

The Unified Testing Framework is designed to grow with your needs, from simple smoke tests to comprehensive enterprise-grade testing suites.