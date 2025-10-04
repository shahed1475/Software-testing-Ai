# Setup Guide - AI-Powered Testing Framework

This guide provides step-by-step instructions for setting up the AI-powered testing framework on your local machine or server environment.

## 📋 Prerequisites Checklist

Before starting the installation, ensure you have the following prerequisites installed:

### Required Software
- [ ] **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- [ ] **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- [ ] **Docker Desktop** - [Download Docker](https://www.docker.com/products/docker-desktop/)
- [ ] **Git** - [Download Git](https://git-scm.com/downloads)

### System Requirements
- [ ] **RAM**: 8GB minimum, 16GB recommended
- [ ] **Storage**: 10GB free space minimum
- [ ] **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- [ ] **Network**: Internet connection for downloading dependencies

### Optional Tools
- [ ] **Visual Studio Code** - Recommended IDE
- [ ] **Postman** - For API testing
- [ ] **Android Studio** - For mobile testing (Android)
- [ ] **Xcode** - For mobile testing (iOS, macOS only)

## 🚀 Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd software-testing-ai

# Verify the project structure
ls -la
```

### Step 2: Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit the environment file (use your preferred editor)
# Windows
notepad .env
# macOS/Linux
nano .env
# VS Code
code .env
```

**Important Environment Variables to Configure:**

```env
# Database Configuration
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb
DATABASE_USER=testuser
DATABASE_PASSWORD=testpass

# AI API Keys (obtain from respective providers)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# MinIO Storage
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Security
SECRET_KEY=your_secret_key_here
```

### Step 3: Python Environment Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Node.js Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install

# Verify Playwright installation
npx playwright --version
```

### Step 5: Docker Services Setup

```bash
# Start all Docker services
docker-compose up -d

# Verify all services are running
docker-compose ps

# Check service logs if needed
docker-compose logs [service-name]
```

**Expected Services:**
- PostgreSQL (Database)
- Redis (Cache)
- MinIO (Object Storage)
- Selenium Hub & Nodes (Web Testing)
- OWASP ZAP (Security Testing)
- Appium (Mobile Testing)
- Grafana (Monitoring)
- Prometheus (Metrics)

### Step 6: Database Initialization

```bash
# Run database migrations
alembic upgrade head

# Verify database connection
python -c "from src.database.connection import test_connection; test_connection()"

# Optional: Seed test data
python scripts/seed_database.py
```

### Step 7: Verification Tests

```bash
# Run basic connectivity tests
python scripts/verify_setup.py

# Run a simple test suite
pytest tests/smoke/ -v

# Generate a test report
python scripts/generate_report.py --input test-results.json --framework pytest
```

## 🔧 Platform-Specific Setup

### Windows Setup

#### Additional Requirements
```powershell
# Install Windows Build Tools (if needed)
npm install -g windows-build-tools

# Install Visual C++ Redistributable
# Download from Microsoft website
```

#### PowerShell Configuration
```powershell
# Set execution policy (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Enable long path support
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### macOS Setup

#### Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install Additional Tools
```bash
# Install required tools
brew install postgresql redis

# Install Java (for Appium)
brew install openjdk@11

# Set JAVA_HOME
echo 'export JAVA_HOME=$(/usr/libexec/java_home)' >> ~/.zshrc
source ~/.zshrc
```

### Linux (Ubuntu) Setup

#### Install System Dependencies
```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y python3-dev python3-venv nodejs npm postgresql-client redis-tools

# Install Java (for Appium)
sudo apt install -y openjdk-11-jdk

# Set JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc
```

## 📱 Mobile Testing Setup

### Android Setup

#### Install Android SDK
```bash
# Download Android Studio or SDK tools
# Set ANDROID_HOME environment variable

# Windows
setx ANDROID_HOME "C:\Users\%USERNAME%\AppData\Local\Android\Sdk"

# macOS/Linux
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

#### Create Android Emulator
```bash
# List available system images
sdkmanager --list | grep system-images

# Install system image
sdkmanager "system-images;android-30;google_apis;x86_64"

# Create AVD
avdmanager create avd -n test_device -k "system-images;android-30;google_apis;x86_64"

# Start emulator
emulator -avd test_device
```

### iOS Setup (macOS only)

#### Install Xcode
```bash
# Install Xcode from App Store
# Install Xcode Command Line Tools
xcode-select --install

# Install iOS Simulator
# (Included with Xcode)
```

#### Configure iOS Simulator
```bash
# List available simulators
xcrun simctl list devices

# Boot a simulator
xcrun simctl boot "iPhone 14"
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate self-signed certificates (for development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Move certificates to appropriate directory
mkdir -p certs/
mv key.pem cert.pem certs/
```

### API Key Management
```bash
# Create secure directory for API keys
mkdir -p ~/.config/testing-ai/

# Set proper permissions
chmod 700 ~/.config/testing-ai/

# Store API keys securely (example)
echo "OPENAI_API_KEY=your_key_here" > ~/.config/testing-ai/api_keys
chmod 600 ~/.config/testing-ai/api_keys
```

## 📊 Monitoring Setup

### Grafana Configuration
1. Access Grafana at `http://localhost:3000`
2. Login with `admin/admin123`
3. Import dashboards from `monitoring/grafana/dashboards/`
4. Configure data sources:
   - Prometheus: `http://prometheus:9090`
   - PostgreSQL: Connection details from `.env`

### Prometheus Configuration
1. Access Prometheus at `http://localhost:9090`
2. Verify targets are up: Status > Targets
3. Configure alerting rules if needed

## 🧪 Test Configuration

### Browser Configuration
```bash
# Install additional browsers (optional)
npx playwright install chromium firefox webkit

# Configure browser preferences
# Edit tests/config/browser_config.json
```

### Mobile Device Configuration
```bash
# Configure device capabilities
# Edit tests/config/mobile_config.json

# Test device connectivity
adb devices  # For Android
xcrun simctl list devices  # For iOS
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Docker Issues
```bash
# Docker daemon not running
sudo systemctl start docker  # Linux
# Start Docker Desktop on Windows/macOS

# Port conflicts
docker-compose down
# Change ports in docker-compose.yml if needed
docker-compose up -d
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose logs postgresql

# Reset database
docker-compose down -v
docker-compose up -d postgresql
sleep 10
alembic upgrade head
```

#### Python Dependencies Issues
```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

#### Node.js Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### Playwright Issues
```bash
# Reinstall browsers
npx playwright uninstall
npx playwright install

# Check browser installation
npx playwright install --dry-run
```

### Performance Optimization

#### System Optimization
```bash
# Increase file descriptor limits (Linux/macOS)
ulimit -n 65536

# Increase memory limits for Docker
# Edit Docker Desktop settings: Resources > Memory > 8GB+
```

#### Test Execution Optimization
```bash
# Configure parallel execution
export PYTEST_WORKERS=4

# Enable test result caching
export PYTEST_CACHE_DIR=.pytest_cache
```

## 📝 Verification Checklist

After completing the setup, verify everything is working:

- [ ] All Docker services are running (`docker-compose ps`)
- [ ] Database connection is successful
- [ ] Python dependencies are installed
- [ ] Node.js dependencies are installed
- [ ] Playwright browsers are installed
- [ ] Environment variables are configured
- [ ] Basic tests pass (`pytest tests/smoke/`)
- [ ] Web UI is accessible (if applicable)
- [ ] Monitoring dashboards are accessible
- [ ] Mobile devices/emulators are detected (if using mobile testing)

## 🆘 Getting Help

If you encounter issues during setup:

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Review the troubleshooting section** above
3. **Search existing issues**: Check GitHub issues
4. **Create a new issue**: Include setup logs and error messages
5. **Join the community**: Discord/Slack channels for real-time help

## 📚 Next Steps

After successful setup:

1. **Read the main README.md** for usage instructions
2. **Explore example tests** in the `tests/` directory
3. **Configure your first test suite**
4. **Set up CI/CD pipelines** using the provided GitHub Actions workflows
5. **Customize the framework** for your specific needs

---

**Setup Complete! 🎉**

You're now ready to start using the AI-powered testing framework. Check out the main README.md for usage examples and advanced features.