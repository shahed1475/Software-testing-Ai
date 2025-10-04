# Docker Setup Guide

This guide helps you set up Docker services for the AI-powered testing framework.

## Docker Desktop Installation

### Windows

1. **Download Docker Desktop**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download Docker Desktop for Windows

2. **Install Docker Desktop**
   - Run the installer as Administrator
   - Enable WSL 2 integration if prompted
   - Restart your computer when installation completes

3. **Start Docker Desktop**
   - Search for "Docker Desktop" in Start menu
   - Launch the application
   - Wait for Docker to start (green icon in system tray)

### macOS

1. **Download Docker Desktop**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Choose the right version (Intel or Apple Silicon)

2. **Install Docker Desktop**
   - Open the .dmg file
   - Drag Docker to Applications folder
   - Launch Docker from Applications

### Linux

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Test Docker is running
docker run hello-world
```

## Starting Services

### Method 1: Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd software-testing-ai

# Start all services in background
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Method 2: Start Services Individually

```bash
# PostgreSQL Database
docker run -d --name postgres \
  -e POSTGRES_DB=testdb \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -p 5432:5432 \
  postgres:15

# Redis Cache
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# MinIO Object Storage
docker run -d --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio server /data --console-address ":9001"

# Selenium Grid Hub
docker run -d --name selenium-hub \
  -p 4444:4444 \
  selenium/hub:4.15.0

# Chrome Node
docker run -d --name selenium-chrome \
  --link selenium-hub:hub \
  -e HUB_HOST=hub \
  selenium/node-chrome:4.15.0

# Firefox Node
docker run -d --name selenium-firefox \
  --link selenium-hub:hub \
  -e HUB_HOST=hub \
  selenium/node-firefox:4.15.0
```

## Service Configuration

### PostgreSQL
- **Port**: 5432
- **Database**: testdb
- **Username**: testuser
- **Password**: testpass
- **Connection**: `postgresql://testuser:testpass@localhost:5432/testdb`

### Redis
- **Port**: 6379
- **No authentication** (for local development)
- **Connection**: `redis://localhost:6379`

### MinIO
- **API Port**: 9000
- **Console Port**: 9001
- **Access Key**: minioadmin
- **Secret Key**: minioadmin
- **Console URL**: http://localhost:9001

### Selenium Grid
- **Hub Port**: 4444
- **Grid Console**: http://localhost:4444
- **WebDriver URL**: `http://localhost:4444/wd/hub`

### OWASP ZAP
- **Port**: 8080
- **API URL**: http://localhost:8080
- **Proxy**: localhost:8080

### Grafana
- **Port**: 3000
- **Username**: admin
- **Password**: admin123
- **URL**: http://localhost:3000

### Prometheus
- **Port**: 9090
- **URL**: http://localhost:9090

## Troubleshooting

### Docker Desktop Not Starting

**Windows:**
```bash
# Check if Hyper-V is enabled
dism.exe /Online /Enable-Feature:Microsoft-Hyper-V /All

# Check WSL 2
wsl --list --verbose
wsl --set-default-version 2

# Restart Docker Desktop service
net stop com.docker.service
net start com.docker.service
```

**macOS:**
```bash
# Reset Docker Desktop
# Go to Docker Desktop > Troubleshoot > Reset to factory defaults

# Check system resources
# Ensure you have at least 4GB RAM available
```

### Port Conflicts

```bash
# Check what's using a port (Windows)
netstat -an | findstr :5432

# Check what's using a port (macOS/Linux)
lsof -i :5432

# Kill process using port
# Windows: taskkill /PID <PID> /F
# macOS/Linux: kill -9 <PID>
```

### Service Connection Issues

```bash
# Check if services are running
docker-compose ps

# Check service logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs minio

# Restart specific service
docker-compose restart postgres

# Restart all services
docker-compose restart
```

### Memory/Resource Issues

```bash
# Check Docker resource usage
docker stats

# Clean up unused containers/images
docker system prune -a

# Increase Docker Desktop memory
# Docker Desktop > Settings > Resources > Memory (increase to 4GB+)
```

### Network Issues

```bash
# Check Docker networks
docker network ls

# Inspect network
docker network inspect software-testing-ai_default

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## Service Health Checks

### Quick Health Check Script

```bash
#!/bin/bash
# save as check_services.sh

echo "Checking Docker services..."

# PostgreSQL
if docker-compose exec -T postgres pg_isready -U testuser; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "✅ MinIO is ready"
else
    echo "❌ MinIO is not ready"
fi

# Selenium Grid
if curl -s http://localhost:4444/wd/hub/status > /dev/null; then
    echo "✅ Selenium Grid is ready"
else
    echo "❌ Selenium Grid is not ready"
fi
```

### Manual Health Checks

```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U testuser

# Redis
docker-compose exec redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Selenium Grid
curl http://localhost:4444/wd/hub/status

# OWASP ZAP
curl http://localhost:8080/JSON/core/view/version/

# Grafana
curl http://localhost:3000/api/health

# Prometheus
curl http://localhost:9090/-/healthy
```

## Performance Optimization

### Docker Desktop Settings

1. **Increase Resources**
   - Memory: 4GB minimum, 8GB recommended
   - CPU: 2 cores minimum, 4 cores recommended
   - Disk: 20GB minimum

2. **Enable Features**
   - Use WSL 2 based engine (Windows)
   - Enable VirtioFS (macOS)
   - Use Docker Compose V2

### Service Optimization

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  postgres:
    command: postgres -c shared_preload_libraries=pg_stat_statements -c pg_stat_statements.track=all
    environment:
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
  
  redis:
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Backup and Recovery

### Backup Data

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U testuser testdb > backup.sql

# Backup MinIO data
docker-compose exec minio mc mirror /data ./minio-backup/

# Export Docker volumes
docker run --rm -v software-testing-ai_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Restore Data

```bash
# Restore PostgreSQL
docker-compose exec -T postgres psql -U testuser testdb < backup.sql

# Restore MinIO data
docker-compose exec minio mc mirror ./minio-backup/ /data

# Import Docker volumes
docker run --rm -v software-testing-ai_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Clean Up

### Remove All Services

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean up system
docker system prune -a --volumes
```

### Reset Everything

```bash
# Complete reset
docker-compose down -v
docker system prune -a --volumes
docker-compose up -d
```

---

**Need Help?**

If you're still having issues:

1. Check Docker Desktop logs: Docker Desktop > Troubleshoot > View logs
2. Restart Docker Desktop completely
3. Check system requirements and available resources
4. Try running services individually to isolate issues
5. Check firewall/antivirus settings that might block Docker