# Quick Start Guide

This guide will help you get the AI-powered testing framework up and running quickly.

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.9+ installed
- ✅ Node.js 16+ installed
- ✅ Docker Desktop installed and running
- ✅ Git installed

## Quick Setup (5 minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd software-testing-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional for local development)
# The default values work for local testing
```

### 3. Start Services

```bash
# Start Docker services
docker-compose up -d

# Wait for services to be ready (about 2-3 minutes)
# Check status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
python -m alembic upgrade head

# Verify setup
python scripts/verify_setup.py
```

## Quick Test Run

### Run Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### Run Web Tests
```bash
# Install Playwright browsers
npx playwright install

# Run web tests
python -m pytest tests/web/ -v --browser chromium
```

### Run API Tests
```bash
python -m pytest tests/api/ -v
```

### Run All Tests
```bash
python scripts/run_tests.py --test-types unit web api
```

## Access Services

Once everything is running, you can access:

- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **OWASP ZAP**: http://localhost:8080
- **Selenium Grid**: http://localhost:4444

## Troubleshooting

### Docker Issues

If Docker services fail to start:

1. **Check Docker Desktop is running**
   ```bash
   docker --version
   docker ps
   ```

2. **Start Docker Desktop manually**
   - Windows: Search for "Docker Desktop" and start it
   - macOS: Open Docker Desktop from Applications
   - Linux: `sudo systemctl start docker`

3. **Free up ports** (if services conflict)
   ```bash
   # Check what's using ports
   netstat -an | findstr :5432  # PostgreSQL
   netstat -an | findstr :6379  # Redis
   netstat -an | findstr :9000  # MinIO
   ```

### Python Dependencies

If you get import errors:

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check virtual environment is activated
which python  # Should point to venv/bin/python
```

### Database Connection

If database tests fail:

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
python -c "import psycopg2; print('PostgreSQL connection OK')"
```

### Permission Issues

On Windows, if you get permission errors:

```bash
# Run as administrator or check folder permissions
# Ensure the project folder is not in a restricted location
```

## What's Next?

1. **Explore Examples**: Check the `examples/` directory for sample tests
2. **Read Documentation**: See `README.md` for detailed information
3. **Configure AI Features**: Edit `.env` to enable AI-powered testing
4. **Set up CI/CD**: Use the GitHub Actions workflows in `.github/workflows/`
5. **Customize Tests**: Modify `test_config.json` for your needs

## Getting Help

- **Documentation**: See `README.md` and `SETUP.md`
- **Issues**: Check the troubleshooting section in `SETUP.md`
- **Examples**: Look at test files in `tests/` directories
- **Configuration**: Review `test_config.json` and `.env.example`

## Quick Commands Reference

```bash
# Verify setup
python scripts/verify_setup.py

# Run all tests
python scripts/run_tests.py

# Generate reports
python scripts/generate_report.py --input test_results/

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Reset everything
docker-compose down -v
docker-compose up -d
```

---

**🎉 You're ready to start testing!**

The framework is now set up and ready for use. Start by running some basic tests and exploring the generated reports.