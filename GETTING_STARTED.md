# Getting Started with AI-Powered Testing Framework

This guide will help you get the testing framework running on your Windows system.

## Current Status

✅ **What's Working:**
- Python environment is set up
- Dependencies are installed
- Project structure is complete
- All code files are created

❌ **What Needs Attention:**
- Docker Desktop is not running
- Services need to be started

## Step-by-Step Setup

### Step 1: Start Docker Desktop

**The most important step right now is to start Docker Desktop:**

1. **Find Docker Desktop:**
   - Press `Windows + S` and search for "Docker Desktop"
   - Or look for the Docker whale icon in your system tray
   - Or check your Start menu under "Docker"

2. **Start Docker Desktop:**
   - Click on Docker Desktop to launch it
   - Wait for it to start (this can take 2-3 minutes)
   - You'll see a whale icon in your system tray when it's ready
   - The icon should be steady (not animated) when Docker is ready

3. **Verify Docker is Running:**
   ```powershell
   docker --version
   docker ps
   ```
   - The first command should show Docker version
   - The second should show running containers (may be empty, that's OK)

### Step 2: Start the Services

Once Docker Desktop is running, start the testing services:

```powershell
# Option 1: Use our simple script
python scripts/simple_docker_start.py

# Option 2: Use docker-compose directly
docker-compose up -d
```

### Step 3: Verify Everything is Working

```powershell
# Check service status
python scripts/simple_docker_start.py --action status

# Or verify the complete setup
python scripts/verify_setup.py
```

### Step 4: Run Your First Tests

```powershell
# Run unit tests (no external dependencies needed)
python -m pytest tests/unit/ -v

# Run API tests (requires services to be running)
python -m pytest tests/api/ -v

# Run all tests
python scripts/run_tests.py --test-types unit api
```

## What Each Service Does

When you start the services, you'll get:

| Service | Purpose | URL |
|---------|---------|-----|
| **PostgreSQL** | Database for test results | localhost:5432 |
| **Redis** | Caching and session storage | localhost:6379 |
| **MinIO** | File storage for test artifacts | http://localhost:9001 |
| **Selenium Grid** | Web browser automation | http://localhost:4444 |
| **OWASP ZAP** | Security testing | http://localhost:8080 |
| **Grafana** | Monitoring dashboard | http://localhost:3000 |
| **Prometheus** | Metrics collection | http://localhost:9090 |

## Troubleshooting Common Issues

### Docker Desktop Won't Start

**Problem:** Docker Desktop fails to start or shows errors

**Solutions:**
1. **Restart as Administrator:**
   - Right-click Docker Desktop
   - Select "Run as administrator"

2. **Check System Requirements:**
   - Windows 10/11 with WSL 2
   - Hyper-V enabled (for older versions)
   - At least 4GB RAM available

3. **Reset Docker Desktop:**
   - Open Docker Desktop
   - Go to Settings → Troubleshoot
   - Click "Reset to factory defaults"

4. **Enable WSL 2:**
   ```powershell
   # Run as Administrator
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```
   - Restart your computer
   - Install WSL 2 kernel update from Microsoft

### Port Conflicts

**Problem:** Services can't start because ports are in use

**Solution:**
```powershell
# Check what's using a port
netstat -an | findstr :5432

# Kill process if needed (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Permission Issues

**Problem:** Permission denied errors

**Solutions:**
1. Run PowerShell as Administrator
2. Check if antivirus is blocking Docker
3. Ensure project folder is not in a restricted location

### Memory Issues

**Problem:** Services fail due to insufficient memory

**Solutions:**
1. Close unnecessary applications
2. Increase Docker Desktop memory:
   - Docker Desktop → Settings → Resources
   - Increase Memory to at least 4GB

## Quick Commands Reference

```powershell
# Start Docker services
python scripts/simple_docker_start.py

# Check service status
python scripts/simple_docker_start.py --action status

# View service logs
python scripts/simple_docker_start.py --action logs

# Stop services
python scripts/simple_docker_start.py --action stop

# Restart services
python scripts/simple_docker_start.py --action restart

# Run tests
python scripts/run_tests.py --test-types unit api

# Generate reports
python scripts/generate_report.py --input test_results/

# Verify complete setup
python scripts/verify_setup.py
```

## Next Steps After Setup

1. **Explore the Dashboard:**
   - Open http://localhost:3000 (Grafana)
   - Login: admin/admin123
   - Explore the testing metrics

2. **Run Sample Tests:**
   - Check the `tests/` directory for examples
   - Modify tests for your applications

3. **Configure for Your Needs:**
   - Edit `.env` file for your settings
   - Modify `test_config.json` for test parameters

4. **Set Up CI/CD:**
   - Use GitHub Actions workflows in `.github/workflows/`
   - Configure for your repository

## Getting Help

If you're still having issues:

1. **Check the logs:**
   ```powershell
   docker-compose logs -f
   ```

2. **Review detailed guides:**
   - `DOCKER_SETUP.md` - Docker-specific help
   - `SETUP.md` - Complete setup guide
   - `README.md` - Full documentation

3. **Common solutions:**
   - Restart Docker Desktop
   - Run as Administrator
   - Check Windows updates
   - Disable antivirus temporarily

## Success Indicators

You'll know everything is working when:

✅ Docker Desktop shows green whale icon
✅ `docker ps` shows running containers
✅ Services respond at their URLs
✅ Tests run without connection errors
✅ Reports are generated successfully

---

**🎯 Your Next Action:** Start Docker Desktop, then run `python scripts/simple_docker_start.py`