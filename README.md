# Software Testing AI Framework

A comprehensive, AI-powered testing framework built with Playwright, featuring advanced tagging, containerized testing, security scanning, and intelligent reporting capabilities.

## 🚀 Features

### Core Testing Capabilities
- **Multi-browser Testing**: Chrome, Firefox, Safari, Edge support
- **Cross-platform**: Windows, macOS, Linux compatibility
- **Mobile Testing**: iOS and Android device simulation with Appium
- **API Testing**: REST API validation and integration testing
- **Visual Testing**: Screenshot comparison and visual regression testing

### Advanced Framework Features
- **AI-Powered Test Generation**: Intelligent test case creation
- **Smart Tagging System**: Organize tests with `@smoke`, `@regression`, `@critical`, `@auth`, `@performance`, `@security`, `@accessibility`
- **Containerized Testing**: Full Docker support with service orchestration
- **Security Integration**: OWASP ZAP security scanning
- **Performance Monitoring**: Grafana and Prometheus integration
- **Allure Reporting**: Beautiful, interactive test reports
- **Notification System**: Email and webhook notifications
- **Test Data Management**: Dynamic test data loading and management

### Infrastructure & DevOps
- **Docker Compose**: Multi-service test environment
- **Selenium Grid**: Distributed test execution
- **MinIO Storage**: Artifact and report storage
- **PostgreSQL**: Test data persistence
- **Redis**: Caching and session management
- **Nginx**: Report server and reverse proxy

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd software-testing-ai
```

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd software-testing-ai
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Install Playwright Browsers
```bash
npx playwright install
```

### 4. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 5. Start Docker Services
```bash
# Start all services
docker-compose up -d

# Or start specific profiles
docker-compose --profile testing up -d
docker-compose --profile monitoring up -d
```

## 🏃‍♂️ Quick Start

### Run Basic Tests
```bash
# Run all tests
npm test

# Run smoke tests
npm run test:smoke

# Run tests by tag
npm run test:tag -- --grep "@critical"
```

### Run Tests in Docker
```bash
# Run containerized tests
npm run docker:test

# Run smoke tests in Docker
npm run docker:smoke

# Run regression tests in Docker
npm run docker:regression
```

### Generate Reports
```bash
# Generate Allure report
npm run report:generate

# Open report in browser
npm run report:open

# View reports dashboard
open http://localhost:8081
```

## 📁 Project Structure

```
software-testing-ai/
├── src/
│   ├── tests/
│   │   ├── auth/                 # Authentication tests
│   │   ├── home/                 # Home page tests
│   │   ├── integration/          # Integration tests
│   │   └── web/                  # Web UI tests
│   ├── pages/                    # Page Object Models
│   ├── utils/                    # Utility classes
│   │   ├── TagManager.ts         # Test tagging system
│   │   ├── NotificationService.ts # Notification handling
│   │   ├── ReportGenerator.ts    # Custom reporting
│   │   └── AllureReporter.ts     # Allure integration
│   ├── ai/                       # AI test generation
│   └── web/                      # Web utilities
├── docker/                       # Docker configurations
│   ├── nginx-reports.conf        # Report server config
│   ├── nginx-app.conf           # Mock app config
│   └── reports-index.html       # Report dashboard
├── tests/                        # Additional test files
├── docker-compose.yml            # Service orchestration
├── playwright.config.ts          # Playwright configuration
└── package.json                  # Dependencies and scripts
```

## 🏷️ Tagging System

The framework uses a comprehensive tagging system to organize and filter tests:

### Available Tags
- `@smoke` - Critical functionality tests
- `@regression` - Full regression test suite
- `@critical` - High-priority tests
- `@auth` - Authentication and authorization tests
- `@performance` - Performance and load tests
- `@security` - Security vulnerability tests
- `@accessibility` - Accessibility compliance tests
- `@flaky` - Tests that may be unstable
- `@api` - API integration tests
- `@ui` - User interface tests
- `@e2e` - End-to-end workflow tests

### Using Tags
```bash
# Run specific tag groups
npm run test:smoke      # @smoke tests
npm run test:regression # @regression tests
npm run test:critical   # @critical tests
npm run test:auth       # @auth tests
npm run test:performance # @performance tests
npm run test:security   # @security tests
npm run test:accessibility # @accessibility tests

# Custom tag filtering
npx playwright test --grep "@api.*@critical"
```

## 🐳 Docker Services

### Core Services
- **PostgreSQL** (5432): Test data storage
- **Redis** (6379): Caching and sessions
- **MinIO** (9000/9001): Object storage for artifacts

### Testing Services
- **Selenium Hub** (4444): Grid coordination
- **Chrome Node** (5900): Chrome browser instances
- **Firefox Node** (5901): Firefox browser instances
- **OWASP ZAP** (8080): Security scanning
- **Appium** (4723): Mobile testing

### Monitoring & Reporting
- **Grafana** (3000): Metrics dashboard
- **Prometheus** (9090): Metrics collection
- **Report Server** (8081): Test report hosting
- **Allure** (5050): Advanced reporting

### Mock Services
- **Mock App** (3000): Application under test

### Uploading Results
```bash
# Upload test results to database
python scripts/upload_test_results.py --input results.json --framework playwright --environment staging

# Upload with artifacts
python scripts/upload_test_results.py --input results.json --framework pytest --artifacts test-results/ --build-number 123
```

## 📁 Project Structure

```
software-testing-ai/
├── src/                          # Source code
│   ├── ai/                       # AI modules
│   │   ├── test_generator.py     # AI test generation
│   │   ├── element_detector.py   # Computer vision for UI
│   │   └── maintenance.py        # Self-healing tests
│   ├── web/                      # Web testing
│   │   ├── playwright_runner.py  # Playwright integration
│   │   └── page_objects/         # Page object models
│   ├── mobile/                   # Mobile testing
│   │   ├── appium_runner.py      # Appium integration
│   │   └── device_manager.py     # Device management
│   ├── api/                      # API testing
│   │   ├── rest_client.py        # REST API client
│   │   └── validators.py         # Response validation
│   ├── security/                 # Security testing
│   │   ├── zap_scanner.py        # OWASP ZAP integration
│   │   └── vulnerability_db.py   # Vulnerability database
│   ├── database/                 # Database layer
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── connection.py         # Database connection
│   │   └── migrations/           # Alembic migrations
│   ├── storage/                  # Artifact storage
│   │   ├── minio_client.py       # MinIO integration
│   │   └── storage_manager.py    # Storage management
│   ├── reports/                  # Report generation
│   │   ├── html_generator.py     # HTML reports
│   │   ├── pdf_generator.py      # PDF reports
│   │   └── json_parser.py        # Result parsing
│   └── utils/                    # Utilities
├── tests/                        # Test suites
│   ├── web/                      # Web tests
│   ├── mobile/                   # Mobile tests
│   ├── api/                      # API tests
│   └── security/                 # Security tests
├── scripts/                      # Utility scripts
├── .github/workflows/            # CI/CD pipelines
├── docker-compose.yml            # Docker services
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js dependencies
└── alembic.ini                   # Database migration config
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testdb
DATABASE_USER=testuser
DATABASE_PASSWORD=testpass

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Security Configuration
ZAP_PROXY_HOST=localhost
ZAP_PROXY_PORT=8080

# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=admin123
PROMETHEUS_PORT=9090
```

### Docker Services Configuration

The `docker-compose.yml` includes:
- **PostgreSQL**: Database for test results
- **Redis**: Caching and session management
- **MinIO**: Artifact storage
- **Selenium Grid**: Web testing infrastructure
- **OWASP ZAP**: Security testing
- **Appium**: Mobile testing server
- **Grafana**: Monitoring dashboards
- **Prometheus**: Metrics collection

## 🧪 Testing

### Running All Tests
```bash
# Run complete test suite
pytest tests/ -v --html=reports/full-report.html

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Test Categories
```bash
# Web tests only
pytest tests/web/ -m "web"

# API tests only
pytest tests/api/ -m "api"

# Mobile tests only
pytest tests/mobile/ -m "mobile"

# Security tests only
pytest tests/security/ -m "security"

# Smoke tests
pytest tests/ -m "smoke"

# Integration tests
pytest tests/ -m "integration"
```

### Parallel Execution
```bash
# Run tests in parallel
pytest tests/ -n auto

# Specify number of workers
pytest tests/ -n 4
```

## 📊 Monitoring & Analytics

### Grafana Dashboards
Access Grafana at `http://localhost:3000` (admin/admin123)

Available dashboards:
- **Test Execution Overview**: Real-time test metrics
- **Performance Trends**: Historical performance data
- **Failure Analysis**: Test failure patterns
- **Resource Utilization**: System resource usage

### Prometheus Metrics
Access Prometheus at `http://localhost:9090`

Key metrics:
- `test_execution_duration_seconds`: Test execution time
- `test_failure_rate`: Test failure percentage
- `test_coverage_percentage`: Code coverage metrics
- `artifact_storage_usage_bytes`: Storage utilization

## 🔄 CI/CD Integration

### GitHub Actions Workflows

#### Web Testing (`test-web.yml`)
- Runs on push/PR to main branches
- Supports multiple browsers (Chrome, Firefox, Safari)
- Uploads test artifacts and reports

#### API Testing (`test-api.yml`)
- Comprehensive API test suite
- Security scanning with OWASP ZAP
- Coverage reporting to Codecov

#### Mobile Testing (`test-mobile.yml`)
- Android and iOS testing
- Emulator/simulator management
- Device-specific test execution

#### Security Testing (`test-security.yml`)
- Automated security scans
- Vulnerability reporting
- Integration with security databases

### Manual Workflow Triggers
All workflows support manual execution with parameters:
```bash
# Trigger web tests
gh workflow run test-web.yml -f environment=staging -f browser=chrome

# Trigger API tests
gh workflow run test-api.yml -f environment=production -f test_suite=smoke

# Trigger mobile tests
gh workflow run test-mobile.yml -f platform=android -f device_type=emulator
```

## 🤖 AI Features

### Test Generation
```python
from src.ai.test_generator import AITestGenerator

generator = AITestGenerator()

# Generate tests from user story
tests = generator.generate_from_story(
    story="As a user, I want to login to access my dashboard",
    framework="playwright"
)

# Generate tests from API specification
api_tests = generator.generate_from_openapi(
    spec_file="api-spec.yaml",
    framework="pytest"
)
```

### Element Detection
```python
from src.ai.element_detector import ComputerVisionDetector

detector = ComputerVisionDetector()

# Find elements by description
element = detector.find_element(
    screenshot="page.png",
    description="blue login button"
)

# Detect UI changes
changes = detector.detect_changes(
    before="old_page.png",
    after="new_page.png"
)
```

### Self-Healing Tests
```python
from src.ai.maintenance import TestMaintainer

maintainer = TestMaintainer()

# Auto-fix broken selectors
fixed_test = maintainer.fix_selector(
    test_file="test_login.py",
    failed_selector="#login-btn",
    page_screenshot="current_page.png"
)
```

## 📈 Performance Optimization

### Test Execution Optimization
- **Parallel Execution**: Run tests concurrently
- **Smart Retry**: AI-powered retry logic
- **Resource Management**: Efficient browser/device allocation
- **Caching**: Intelligent test data caching

### Infrastructure Scaling
- **Docker Swarm**: Multi-node test execution
- **Kubernetes**: Container orchestration
- **Load Balancing**: Distribute test workload
- **Auto-scaling**: Dynamic resource allocation

## 🔒 Security

### Security Best Practices
- **Secrets Management**: Environment-based configuration
- **Access Control**: Role-based permissions
- **Audit Logging**: Comprehensive activity logs
- **Vulnerability Scanning**: Regular security assessments

### Data Protection
- **Encryption**: Data encryption at rest and in transit
- **Backup**: Automated database backups
- **Retention**: Configurable data retention policies
- **Compliance**: GDPR and SOC2 compliance features

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker-compose ps postgresql

# View database logs
docker-compose logs postgresql

# Reset database
docker-compose down -v
docker-compose up -d postgresql
alembic upgrade head
```

#### Selenium Grid Issues
```bash
# Check grid status
curl http://localhost:4444/grid/api/hub/status

# Restart grid
docker-compose restart selenium-hub selenium-chrome selenium-firefox
```

#### MinIO Storage Issues
```bash
# Check MinIO status
curl http://localhost:9000/minio/health/live

# Access MinIO console
# http://localhost:9001 (minioadmin/minioadmin)
```

#### Test Execution Issues
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
pytest tests/ -v -s

# Check test dependencies
pip check

# Verify browser installation
npx playwright install --dry-run
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check test execution times
pytest tests/ --durations=10

# Profile test execution
pytest tests/ --profile
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code quality checks
flake8 src/ tests/
black src/ tests/
isort src/ tests/
```

### Testing Guidelines
- Write tests for all new features
- Maintain minimum 80% code coverage
- Follow PEP 8 style guidelines
- Use type hints for all functions

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit pull request with description

## 📚 Documentation

### API Documentation
- **FastAPI Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Additional Resources
- [Playwright Documentation](https://playwright.dev/)
- [Appium Documentation](https://appium.io/docs/)
- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

### Community
- **Discord**: [Join our Discord](https://discord.gg/your-server)
- **Slack**: [Slack Workspace](https://your-workspace.slack.com)
- **Twitter**: [@YourProject](https://twitter.com/yourproject)

---

## 🎯 Roadmap

### Upcoming Features
- [ ] Machine Learning test optimization
- [ ] Visual regression testing
- [ ] Performance testing integration
- [ ] Multi-cloud deployment support
- [ ] Advanced AI test maintenance
- [ ] Real-time collaboration features

### Version History
- **v1.0.0**: Initial release with core testing capabilities
- **v1.1.0**: AI-powered test generation
- **v1.2.0**: Enhanced reporting and analytics
- **v1.3.0**: Mobile testing improvements
- **v1.4.0**: Security testing enhancements

---

**Built with ❤️ by the Testing AI Team**