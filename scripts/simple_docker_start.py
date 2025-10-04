#!/usr/bin/env python3
"""
Simple Docker Services Startup Script

A lightweight script to start Docker services without external dependencies.
"""

import subprocess
import time
import sys
import json
from pathlib import Path
import argparse

class SimpleDockerManager:
    """Simple Docker service manager without external dependencies."""
    
    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self.compose_file = self.project_dir / "docker-compose.yml"
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Docker version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("❌ Docker is not available or not running")
        return False
    
    def check_docker_compose_available(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(
                ['docker-compose', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Docker Compose version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("❌ Docker Compose is not available")
        return False
    
    def check_compose_file(self) -> bool:
        """Check if docker-compose.yml exists."""
        if self.compose_file.exists():
            print(f"✅ Found docker-compose.yml at {self.compose_file}")
            return True
        
        print(f"❌ docker-compose.yml not found at {self.compose_file}")
        return False
    
    def start_services(self, services: list = None) -> bool:
        """Start Docker services."""
        print("🚀 Starting Docker services...")
        
        cmd = ['docker-compose', 'up', '-d']
        if services:
            cmd.extend(services)
            print(f"Starting specific services: {', '.join(services)}")
        else:
            print("Starting all services...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print("✅ Docker services started successfully")
                return True
            else:
                print(f"❌ Failed to start services (exit code: {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout while starting services")
            return False
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop Docker services."""
        print("🛑 Stopping Docker services...")
        
        try:
            result = subprocess.run(
                ['docker-compose', 'down'],
                cwd=self.project_dir,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Docker services stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop services (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping services: {e}")
            return False
    
    def get_service_status(self) -> bool:
        """Get status of all services."""
        print("📊 Checking service status...")
        
        try:
            result = subprocess.run(
                ['docker-compose', 'ps'],
                cwd=self.project_dir,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("Service Status:")
                print("=" * 60)
                print(result.stdout)
                print("=" * 60)
                return True
            else:
                print(f"❌ Failed to get status (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return False
    
    def show_logs(self, service: str = None, follow: bool = False) -> bool:
        """Show service logs."""
        cmd = ['docker-compose', 'logs']
        if follow:
            cmd.append('-f')
        if service:
            cmd.append(service)
            print(f"📋 Showing logs for {service}...")
        else:
            print("📋 Showing logs for all services...")
        
        try:
            if follow:
                # For follow mode, don't capture output
                result = subprocess.run(cmd, cwd=self.project_dir)
            else:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_dir,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print(result.stdout)
            
            return result.returncode == 0
            
        except KeyboardInterrupt:
            print("\n⏹️  Log viewing interrupted")
            return True
        except Exception as e:
            print(f"❌ Error showing logs: {e}")
            return False
    
    def wait_for_services(self, timeout: int = 60):
        """Simple wait for services to start."""
        print(f"⏳ Waiting {timeout} seconds for services to initialize...")
        
        for i in range(timeout):
            if i % 10 == 0 and i > 0:
                print(f"⏳ Still waiting... ({i}/{timeout} seconds)")
            time.sleep(1)
        
        print("✅ Wait complete. Services should be ready now.")
        print("💡 Use --action status to check service health")
    
    def print_service_urls(self):
        """Print URLs for accessing services."""
        urls = {
            'Grafana Dashboard': 'http://localhost:3000 (admin/admin123)',
            'Prometheus': 'http://localhost:9090',
            'MinIO Console': 'http://localhost:9001 (minioadmin/minioadmin)',
            'Selenium Grid': 'http://localhost:4444',
            'OWASP ZAP': 'http://localhost:8080',
            'PostgreSQL': 'localhost:5432 (testuser/testpass)',
            'Redis': 'localhost:6379'
        }
        
        print("\n🌐 Service URLs:")
        print("=" * 60)
        for name, url in urls.items():
            print(f"{name:20}: {url}")
        print("=" * 60)
        print("\n💡 Tip: Use 'docker-compose logs -f' to view real-time logs")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Simple Docker service manager for AI testing framework'
    )
    parser.add_argument(
        '--action',
        choices=['start', 'stop', 'status', 'restart', 'logs'],
        default='start',
        help='Action to perform'
    )
    parser.add_argument(
        '--services',
        nargs='*',
        help='Specific services to start (default: all)'
    )
    parser.add_argument(
        '--wait',
        type=int,
        default=60,
        help='Seconds to wait after starting services'
    )
    parser.add_argument(
        '--follow-logs',
        action='store_true',
        help='Follow logs in real-time (use with --action logs)'
    )
    parser.add_argument(
        '--service',
        help='Specific service for logs (use with --action logs)'
    )
    
    args = parser.parse_args()
    
    print("🐳 Simple Docker Service Manager")
    print("=" * 40)
    
    # Initialize service manager
    manager = SimpleDockerManager()
    
    # Check prerequisites
    if not manager.check_docker_available():
        print("\n💡 To fix this:")
        print("1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/")
        print("2. Start Docker Desktop")
        print("3. Wait for Docker to be ready (green icon in system tray)")
        print("4. See DOCKER_SETUP.md for detailed instructions")
        sys.exit(1)
    
    if not manager.check_docker_compose_available():
        print("\n💡 Docker Compose should come with Docker Desktop")
        print("If you're on Linux, install docker-compose separately")
        sys.exit(1)
    
    if not manager.check_compose_file():
        print("\n💡 Make sure you're in the project root directory")
        sys.exit(1)
    
    print()  # Empty line for better formatting
    
    # Perform requested action
    success = True
    
    if args.action == 'start':
        success = manager.start_services(args.services)
        if success:
            manager.wait_for_services(args.wait)
            manager.print_service_urls()
    
    elif args.action == 'stop':
        success = manager.stop_services()
    
    elif args.action == 'restart':
        print("🔄 Restarting services...")
        manager.stop_services()
        time.sleep(5)
        success = manager.start_services(args.services)
        if success:
            manager.wait_for_services(args.wait)
            manager.print_service_urls()
    
    elif args.action == 'status':
        success = manager.get_service_status()
    
    elif args.action == 'logs':
        success = manager.show_logs(args.service, args.follow_logs)
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("- Check if Docker Desktop is running")
        print("- Try: docker-compose down && docker-compose up -d")
        print("- Check logs: docker-compose logs -f")
        print("- See DOCKER_SETUP.md for more help")
        sys.exit(1)
    
    print("\n🎉 Operation completed successfully!")

if __name__ == '__main__':
    main()