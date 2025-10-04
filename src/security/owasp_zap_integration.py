"""
OWASP ZAP Integration

Integrates OWASP ZAP (Zed Attack Proxy) for comprehensive web application
security testing, including active and passive scanning capabilities.
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

try:
    from zapv2 import ZAPv2
    ZAP_AVAILABLE = True
except ImportError:
    ZAP_AVAILABLE = False

from .security_scanner import (
    SecurityScanner, ScanConfiguration, SecurityScanResult,
    SecurityVulnerability, VulnerabilityLevel, ScanType, ScanStatus
)

logger = logging.getLogger(__name__)


@dataclass
class ZAPScanConfig(ScanConfiguration):
    """Configuration for OWASP ZAP scans"""
    
    # ZAP connection
    zap_proxy_host: str = "127.0.0.1"
    zap_proxy_port: int = 8080
    zap_api_key: Optional[str] = None
    
    # Scan types
    passive_scan: bool = True
    active_scan: bool = True
    spider_scan: bool = True
    ajax_spider: bool = False
    
    # Spider configuration
    spider_max_depth: int = 5
    spider_max_children: int = 10
    spider_recurse: bool = True
    
    # Active scan configuration
    active_scan_policy: Optional[str] = None
    scan_strength: str = "Medium"  # Low, Medium, High, Insane
    alert_threshold: str = "Medium"  # Off, Low, Medium, High
    
    # Authentication
    auth_method: Optional[str] = None  # form, script, manual
    login_url: Optional[str] = None
    username_field: Optional[str] = None
    password_field: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Context and session management
    context_name: str = "Default Context"
    session_management: str = "cookie"
    
    # Exclusions and inclusions
    include_in_context: List[str] = field(default_factory=list)
    exclude_from_context: List[str] = field(default_factory=list)
    exclude_from_scan: List[str] = field(default_factory=list)
    
    # Reporting
    generate_html_report: bool = True
    generate_xml_report: bool = True
    generate_json_report: bool = True


@dataclass
class ZAPScanResult(SecurityScanResult):
    """Extended scan result for ZAP-specific data"""
    
    # ZAP-specific metrics
    spider_urls_found: int = 0
    active_scan_progress: int = 0
    passive_scan_rules: int = 0
    active_scan_rules: int = 0
    
    # ZAP session data
    session_file: Optional[str] = None
    context_id: Optional[int] = None


class ZAPScanner(SecurityScanner):
    """OWASP ZAP security scanner implementation"""
    
    def __init__(self, zap_path: Optional[str] = None):
        super().__init__("OWASP-ZAP", "2.12.0")
        self.zap_path = zap_path or self._find_zap_executable()
        self.zap_process: Optional[subprocess.Popen] = None
        self.zap_client: Optional[ZAPv2] = None
        self.is_zap_started = False
    
    def _find_zap_executable(self) -> Optional[str]:
        """Find ZAP executable in common locations"""
        common_paths = [
            "C:\\Program Files\\OWASP\\Zed Attack Proxy\\ZAP.exe",
            "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\ZAP.exe",
            "/usr/share/zaproxy/zap.sh",
            "/opt/zaproxy/zap.sh",
            "zap.sh",
            "zap"
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def is_available(self) -> bool:
        """Check if ZAP is available"""
        return ZAP_AVAILABLE and self.zap_path is not None
    
    def get_supported_scan_types(self) -> List[ScanType]:
        """ZAP supports web application and API scanning"""
        return [ScanType.WEB_APPLICATION, ScanType.API]
    
    async def start_zap_daemon(self, config: ZAPScanConfig) -> bool:
        """Start ZAP in daemon mode"""
        if self.is_zap_started:
            return True
        
        if not self.zap_path:
            raise RuntimeError("ZAP executable not found")
        
        try:
            # Start ZAP in daemon mode
            cmd = [
                self.zap_path,
                "-daemon",
                "-host", config.zap_proxy_host,
                "-port", str(config.zap_proxy_port),
                "-config", "api.disablekey=true"
            ]
            
            if config.zap_api_key:
                cmd.extend(["-config", f"api.key={config.zap_api_key}"])
            
            self.logger.info(f"Starting ZAP daemon: {' '.join(cmd)}")
            self.zap_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ZAP to start
            await self._wait_for_zap_startup(config)
            
            # Initialize ZAP client
            self.zap_client = ZAPv2(
                proxies={
                    'http': f'http://{config.zap_proxy_host}:{config.zap_proxy_port}',
                    'https': f'http://{config.zap_proxy_host}:{config.zap_proxy_port}'
                },
                apikey=config.zap_api_key
            )
            
            self.is_zap_started = True
            self.logger.info("ZAP daemon started successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start ZAP daemon: {e}")
            return False
    
    async def _wait_for_zap_startup(self, config: ZAPScanConfig, timeout: int = 60):
        """Wait for ZAP to fully start up"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect to ZAP API
                import requests
                response = requests.get(
                    f"http://{config.zap_proxy_host}:{config.zap_proxy_port}/JSON/core/view/version/",
                    timeout=5
                )
                if response.status_code == 200:
                    return
            except:
                pass
            
            await asyncio.sleep(2)
        
        raise TimeoutError("ZAP failed to start within timeout period")
    
    async def scan(self, config: ZAPScanConfig) -> ZAPScanResult:
        """Perform comprehensive ZAP security scan"""
        self.validate_config(config)
        
        if not await self.start_zap_daemon(config):
            raise RuntimeError("Failed to start ZAP daemon")
        
        result = ZAPScanResult(
            scan_id=self.create_scan_result(config).scan_id,
            scan_type=config.scan_type,
            scanner_name=self.name,
            target=config.target,
            start_time=datetime.now(),
            scan_config=config.scan_options
        )
        
        try:
            result.status = ScanStatus.RUNNING
            
            # Setup context and authentication
            await self._setup_context(config, result)
            
            # Perform spider scan
            if config.spider_scan:
                await self._spider_scan(config, result)
            
            # Perform AJAX spider scan
            if config.ajax_spider:
                await self._ajax_spider_scan(config, result)
            
            # Perform passive scan
            if config.passive_scan:
                await self._passive_scan(config, result)
            
            # Perform active scan
            if config.active_scan:
                await self._active_scan(config, result)
            
            # Generate reports
            await self._generate_reports(config, result)
            
            # Parse results
            await self._parse_scan_results(config, result)
            
            result.status = ScanStatus.COMPLETED
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            self.logger.info(f"ZAP scan completed: {result.total_vulnerabilities} vulnerabilities found")
            
        except Exception as e:
            self.logger.error(f"ZAP scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _setup_context(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Setup ZAP context and authentication"""
        try:
            # Create context
            context_id = self.zap_client.context.new_context(config.context_name)
            result.context_id = int(context_id)
            
            # Include URLs in context
            if config.include_in_context:
                for url_pattern in config.include_in_context:
                    self.zap_client.context.include_in_context(config.context_name, url_pattern)
            else:
                # Include target URL by default
                self.zap_client.context.include_in_context(config.context_name, f"{config.target}.*")
            
            # Exclude URLs from context
            for url_pattern in config.exclude_from_context:
                self.zap_client.context.exclude_from_context(config.context_name, url_pattern)
            
            # Setup authentication if configured
            if config.auth_method == "form" and config.login_url:
                await self._setup_form_authentication(config)
            
            self.logger.info(f"ZAP context setup completed: {config.context_name}")
        
        except Exception as e:
            self.logger.warning(f"Context setup failed: {e}")
    
    async def _setup_form_authentication(self, config: ZAPScanConfig):
        """Setup form-based authentication"""
        try:
            # Configure form-based authentication
            login_request_data = f"{config.username_field}={config.username}&{config.password_field}={config.password}"
            
            self.zap_client.authentication.set_authentication_method(
                contextid=config.context_name,
                authmethodname="formBasedAuthentication",
                authmethodconfigparams=f"loginUrl={config.login_url}&loginRequestData={login_request_data}"
            )
            
            # Set up user
            user_id = self.zap_client.users.new_user(config.context_name, config.username)
            self.zap_client.users.set_authentication_credentials(
                config.context_name,
                user_id,
                f"username={config.username}&password={config.password}"
            )
            self.zap_client.users.set_user_enabled(config.context_name, user_id, True)
            
            self.logger.info("Form-based authentication configured")
        
        except Exception as e:
            self.logger.warning(f"Authentication setup failed: {e}")
    
    async def _spider_scan(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Perform spider scan to discover URLs"""
        try:
            self.logger.info("Starting spider scan")
            
            # Configure spider
            self.zap_client.spider.set_option_max_depth(config.spider_max_depth)
            self.zap_client.spider.set_option_max_children(config.spider_max_children)
            
            # Start spider
            scan_id = self.zap_client.spider.scan(config.target, recurse=config.spider_recurse)
            
            # Wait for spider to complete
            while int(self.zap_client.spider.status(scan_id)) < 100:
                await asyncio.sleep(2)
                progress = int(self.zap_client.spider.status(scan_id))
                self.logger.debug(f"Spider progress: {progress}%")
            
            # Get spider results
            urls = self.zap_client.spider.results(scan_id)
            result.spider_urls_found = len(urls)
            
            self.logger.info(f"Spider scan completed: {result.spider_urls_found} URLs found")
        
        except Exception as e:
            self.logger.warning(f"Spider scan failed: {e}")
    
    async def _ajax_spider_scan(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Perform AJAX spider scan for JavaScript-heavy applications"""
        try:
            self.logger.info("Starting AJAX spider scan")
            
            # Start AJAX spider
            self.zap_client.ajaxSpider.scan(config.target)
            
            # Wait for AJAX spider to complete
            while self.zap_client.ajaxSpider.status == "running":
                await asyncio.sleep(5)
                self.logger.debug("AJAX spider running...")
            
            # Get AJAX spider results
            urls = self.zap_client.ajaxSpider.results("start", "count")
            self.logger.info(f"AJAX spider completed: {len(urls)} additional URLs found")
        
        except Exception as e:
            self.logger.warning(f"AJAX spider scan failed: {e}")
    
    async def _passive_scan(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Perform passive scan on discovered URLs"""
        try:
            self.logger.info("Starting passive scan")
            
            # Enable all passive scan rules
            self.zap_client.pscan.enable_all_scanners()
            
            # Wait for passive scan to complete
            while int(self.zap_client.pscan.records_to_scan) > 0:
                await asyncio.sleep(2)
                remaining = int(self.zap_client.pscan.records_to_scan)
                self.logger.debug(f"Passive scan remaining: {remaining} records")
            
            self.logger.info("Passive scan completed")
        
        except Exception as e:
            self.logger.warning(f"Passive scan failed: {e}")
    
    async def _active_scan(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Perform active scan with attack payloads"""
        try:
            self.logger.info("Starting active scan")
            
            # Configure active scan policy
            if config.active_scan_policy:
                self.zap_client.ascan.set_option_default_policy(config.active_scan_policy)
            
            # Set scan strength and threshold
            policy_id = self.zap_client.ascan.add_scan_policy("CustomPolicy")
            
            # Start active scan
            scan_id = self.zap_client.ascan.scan(config.target)
            
            # Wait for active scan to complete
            while int(self.zap_client.ascan.status(scan_id)) < 100:
                await asyncio.sleep(5)
                progress = int(self.zap_client.ascan.status(scan_id))
                result.active_scan_progress = progress
                self.logger.debug(f"Active scan progress: {progress}%")
            
            self.logger.info("Active scan completed")
        
        except Exception as e:
            self.logger.warning(f"Active scan failed: {e}")
    
    async def _generate_reports(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Generate scan reports in various formats"""
        try:
            output_dir = Path(config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            base_filename = f"zap_scan_{result.scan_id}"
            
            # Generate HTML report
            if config.generate_html_report:
                html_report = self.zap_client.core.htmlreport()
                html_path = output_dir / f"{base_filename}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_report)
                result.report_files.append(str(html_path))
            
            # Generate XML report
            if config.generate_xml_report:
                xml_report = self.zap_client.core.xmlreport()
                xml_path = output_dir / f"{base_filename}.xml"
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_report)
                result.report_files.append(str(xml_path))
            
            # Generate JSON report
            if config.generate_json_report:
                json_report = self.zap_client.core.jsonreport()
                json_path = output_dir / f"{base_filename}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    f.write(json_report)
                result.report_files.append(str(json_path))
            
            self.logger.info(f"Reports generated: {len(result.report_files)} files")
        
        except Exception as e:
            self.logger.warning(f"Report generation failed: {e}")
    
    async def _parse_scan_results(self, config: ZAPScanConfig, result: ZAPScanResult):
        """Parse ZAP scan results and extract vulnerabilities"""
        try:
            # Get alerts from ZAP
            alerts = self.zap_client.core.alerts()
            
            for alert in alerts:
                vulnerability = self._create_vulnerability_from_alert(alert)
                result.add_vulnerability(vulnerability)
            
            self.logger.info(f"Parsed {len(result.vulnerabilities)} vulnerabilities")
        
        except Exception as e:
            self.logger.error(f"Failed to parse scan results: {e}")
    
    def _create_vulnerability_from_alert(self, alert: Dict[str, Any]) -> SecurityVulnerability:
        """Create SecurityVulnerability from ZAP alert"""
        # Map ZAP risk levels to our severity levels
        risk_mapping = {
            "High": VulnerabilityLevel.HIGH,
            "Medium": VulnerabilityLevel.MEDIUM,
            "Low": VulnerabilityLevel.LOW,
            "Informational": VulnerabilityLevel.INFO
        }
        
        severity = risk_mapping.get(alert.get("risk", "Medium"), VulnerabilityLevel.MEDIUM)
        
        return SecurityVulnerability(
            id=f"ZAP-{alert.get('pluginId', 'UNKNOWN')}",
            title=alert.get("name", "Unknown Vulnerability"),
            description=alert.get("description", ""),
            severity=severity,
            category=alert.get("category", "Unknown"),
            cwe_id=alert.get("cweid"),
            url=alert.get("url"),
            parameter=alert.get("param"),
            recommendation=alert.get("solution", ""),
            evidence={
                "attack": alert.get("attack", ""),
                "evidence": alert.get("evidence", ""),
                "other_info": alert.get("otherinfo", "")
            },
            references=alert.get("reference", "").split("\n") if alert.get("reference") else [],
            scanner=self.name
        )
    
    def stop_zap_daemon(self):
        """Stop ZAP daemon"""
        try:
            if self.zap_client:
                self.zap_client.core.shutdown()
            
            if self.zap_process:
                self.zap_process.terminate()
                self.zap_process.wait(timeout=10)
            
            self.is_zap_started = False
            self.logger.info("ZAP daemon stopped")
        
        except Exception as e:
            self.logger.warning(f"Error stopping ZAP daemon: {e}")
    
    def __del__(self):
        """Cleanup when scanner is destroyed"""
        if self.is_zap_started:
            self.stop_zap_daemon()


# Example usage
def create_example_zap_config(target_url: str) -> ZAPScanConfig:
    """Create example ZAP scan configuration"""
    return ZAPScanConfig(
        scan_type=ScanType.WEB_APPLICATION,
        target=target_url,
        timeout_minutes=60,
        
        # Enable all scan types
        passive_scan=True,
        active_scan=True,
        spider_scan=True,
        ajax_spider=False,
        
        # Spider configuration
        spider_max_depth=3,
        spider_max_children=10,
        
        # Active scan configuration
        scan_strength="Medium",
        alert_threshold="Medium",
        
        # Authentication (if needed)
        auth_method="form",
        login_url=f"{target_url}/login",
        username_field="username",
        password_field="password",
        username="testuser",
        password="testpass",
        
        # Reporting
        generate_html_report=True,
        generate_xml_report=True,
        generate_json_report=True,
        
        # Exclusions
        exclude_from_scan=[
            f"{target_url}/logout",
            f"{target_url}/admin/delete.*"
        ]
    )