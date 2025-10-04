"""
Notifier Agent

Handles notifications and alerts for test results, failures, and system events.
Supports multiple notification channels including email, Slack, Microsoft Teams,
Discord, webhooks, and SMS.
"""

import asyncio
import json
import smtplib
import ssl
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiohttp
import requests
from jinja2 import Environment, Template, FileSystemLoader

from .base_agent import BaseAgent, AgentConfig


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 1)
    
    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification message with retry logic"""
        if not self.enabled:
            return {'success': False, 'error': f'Channel {self.name} is disabled'}
        
        for attempt in range(self.retry_count):
            try:
                result = await self._send_impl(message)
                if result.get('success'):
                    return result
                
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    
            except Exception as e:
                if attempt == self.retry_count - 1:
                    return {
                        'success': False,
                        'channel': self.name,
                        'error': f'Failed after {self.retry_count} attempts: {str(e)}',
                        'sent_at': datetime.now().isoformat()
                    }
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        return {'success': False, 'error': 'Max retry attempts exceeded'}
    
    async def _send_impl(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation-specific send method"""
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    """Enhanced email notification channel"""
    
    async def _send_impl(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification"""
        smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = self.config.get('smtp_port', 587)
        username = self.config.get('username')
        password = self.config.get('password')
        from_email = self.config.get('from_email', username)
        to_emails = self.config.get('to_emails', [])
        
        if not username or not password or not to_emails:
            return {'success': False, 'error': 'Missing email configuration'}
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = message.get('subject', 'Test Notification')
        
        # Add priority if specified
        priority = message.get('priority', 'normal')
        if priority == 'high':
            msg['X-Priority'] = '1'
            msg['X-MSMail-Priority'] = 'High'
        elif priority == 'low':
            msg['X-Priority'] = '5'
            msg['X-MSMail-Priority'] = 'Low'
        
        # Add body (both plain text and HTML)
        body_text = message.get('body', message.get('text', ''))
        body_html = message.get('html', '')
        
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))
        
        # Add attachments
        attachments = message.get('attachments', [])
        for attachment_path in attachments:
            if Path(attachment_path).exists():
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment_path).name}'
                )
                msg.attach(part)
        
        # Send email with enhanced error handling
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.sendmail(from_email, to_emails, msg.as_string())
            
            return {
                'success': True,
                'channel': 'email',
                'recipients': to_emails,
                'subject': msg['Subject'],
                'sent_at': datetime.now().isoformat()
            }
            
        except smtplib.SMTPAuthenticationError as e:
            return {'success': False, 'channel': 'email', 'error': f'Authentication failed: {str(e)}'}
        except smtplib.SMTPRecipientsRefused as e:
            return {'success': False, 'channel': 'email', 'error': f'Recipients refused: {str(e)}'}
        except smtplib.SMTPServerDisconnected as e:
            return {'success': False, 'channel': 'email', 'error': f'Server disconnected: {str(e)}'}
        except Exception as e:
            return {'success': False, 'channel': 'email', 'error': str(e)}


class SlackChannel(NotificationChannel):
    """Enhanced Slack notification channel"""
    
    async def _send_impl(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification"""
        webhook_url = self.config.get('webhook_url')
        bot_token = self.config.get('bot_token')
        channel = self.config.get('channel', '#general')
        
        if not webhook_url and not bot_token:
            return {'success': False, 'error': 'Missing Slack webhook URL or bot token'}
        
        # Prepare enhanced Slack message
        slack_message = {
            'channel': channel,
            'username': self.config.get('username', 'TestBot'),
            'icon_emoji': self.config.get('icon_emoji', ':robot_face:'),
            'text': message.get('text', ''),
            'attachments': [],
            'blocks': message.get('blocks', [])  # Support for Block Kit
        }
        
        # Add rich formatting if provided
        if message.get('title') or message.get('color') or message.get('fields'):
            attachment = {
                'color': self._get_color_for_status(message.get('status', 'info')),
                'title': message.get('title', ''),
                'title_link': message.get('title_link', ''),
                'text': message.get('body', ''),
                'fields': self._format_slack_fields(message.get('fields', [])),
                'footer': message.get('footer', 'Test Automation System'),
                'footer_icon': message.get('footer_icon', ''),
                'ts': int(datetime.now().timestamp()),
                'actions': message.get('actions', [])
            }
            
            # Add author info if provided
            if message.get('author_name'):
                attachment['author_name'] = message['author_name']
                attachment['author_link'] = message.get('author_link', '')
                attachment['author_icon'] = message.get('author_icon', '')
            
            slack_message['attachments'].append(attachment)
        
        # Send via webhook or API
        if webhook_url:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, 
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'channel': 'slack',
                            'method': 'webhook',
                            'target_channel': channel,
                            'sent_at': datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'channel': 'slack',
                            'error': f'HTTP {response.status}: {error_text}',
                            'sent_at': datetime.now().isoformat()
                        }
        else:
            # Use bot token API
            headers = {
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://slack.com/api/chat.postMessage',
                    headers=headers,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    if result.get('ok'):
                        return {
                            'success': True,
                            'channel': 'slack',
                            'method': 'api',
                            'target_channel': channel,
                            'message_ts': result.get('ts'),
                            'sent_at': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'channel': 'slack',
                            'error': result.get('error', 'Unknown error'),
                            'sent_at': datetime.now().isoformat()
                        }
    
    def _get_color_for_status(self, status: str) -> str:
        """Get appropriate color for message status"""
        color_map = {
            'success': 'good',
            'passed': 'good',
            'failure': 'danger',
            'failed': 'danger',
            'error': 'danger',
            'warning': 'warning',
            'info': '#36a64f',
            'pending': '#ffcc00'
        }
        return color_map.get(status.lower(), '#36a64f')
    
    def _format_slack_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format fields for Slack attachment"""
        formatted_fields = []
        for field in fields:
            formatted_field = {
                'title': field.get('title', ''),
                'value': field.get('value', ''),
                'short': field.get('short', True)
            }
            formatted_fields.append(formatted_field)
        return formatted_fields


class TeamsChannel(NotificationChannel):
    """Microsoft Teams notification channel"""
    
    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send Teams notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            
            if not webhook_url:
                return {'success': False, 'error': 'Missing Teams webhook URL'}
            
            # Prepare Teams message (Adaptive Card format)
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": message.get('color', '0076D7'),
                "summary": message.get('title', 'Test Notification'),
                "sections": [{
                    "activityTitle": message.get('title', 'Test Notification'),
                    "activitySubtitle": message.get('subtitle', ''),
                    "activityImage": message.get('image_url', ''),
                    "text": message.get('body', message.get('text', '')),
                    "facts": message.get('facts', [])
                }]
            }
            
            # Add potential actions
            actions = message.get('actions', [])
            if actions:
                teams_message['potentialAction'] = actions
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=teams_message) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'channel': 'teams',
                            'sent_at': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'channel': 'teams',
                            'error': f'HTTP {response.status}: {await response.text()}',
                            'sent_at': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'channel': 'teams',
                'error': str(e),
                'sent_at': datetime.now().isoformat()
            }


class DiscordChannel(NotificationChannel):
    """Discord notification channel"""
    
    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send Discord notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            
            if not webhook_url:
                return {'success': False, 'error': 'Missing Discord webhook URL'}
            
            # Prepare Discord message
            discord_message = {
                'username': self.config.get('username', 'TestBot'),
                'avatar_url': self.config.get('avatar_url', ''),
                'content': message.get('text', ''),
                'embeds': []
            }
            
            # Add embed if rich content provided
            if message.get('title') or message.get('body') or message.get('fields'):
                embed = {
                    'title': message.get('title', ''),
                    'description': message.get('body', ''),
                    'color': int(message.get('color', '0076D7').replace('#', ''), 16) if message.get('color') else 123456,
                    'fields': message.get('fields', []),
                    'footer': {
                        'text': message.get('footer', 'Test Automation')
                    },
                    'timestamp': datetime.now().isoformat()
                }
                discord_message['embeds'].append(embed)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=discord_message) as response:
                    if response.status == 204:  # Discord returns 204 for successful webhook
                        return {
                            'success': True,
                            'channel': 'discord',
                            'sent_at': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'channel': 'discord',
                            'error': f'HTTP {response.status}: {await response.text()}',
                            'sent_at': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'channel': 'discord',
                'error': str(e),
                'sent_at': datetime.now().isoformat()
            }


class WebhookChannel(NotificationChannel):
    """Generic webhook notification channel"""
    
    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            url = self.config.get('url')
            method = self.config.get('method', 'POST').upper()
            headers = self.config.get('headers', {})
            
            if not url:
                return {'success': False, 'error': 'Missing webhook URL'}
            
            # Prepare payload
            payload = {
                'timestamp': datetime.now().isoformat(),
                'source': 'test_automation',
                'message': message
            }
            
            # Add custom fields from config
            custom_fields = self.config.get('custom_fields', {})
            payload.update(custom_fields)
            
            async with aiohttp.ClientSession() as session:
                if method == 'POST':
                    async with session.post(url, json=payload, headers=headers) as response:
                        success = 200 <= response.status < 300
                        return {
                            'success': success,
                            'channel': 'webhook',
                            'status_code': response.status,
                            'response': await response.text() if not success else '',
                            'sent_at': datetime.now().isoformat()
                        }
                elif method == 'GET':
                    async with session.get(url, params=payload, headers=headers) as response:
                        success = 200 <= response.status < 300
                        return {
                            'success': success,
                            'channel': 'webhook',
                            'status_code': response.status,
                            'response': await response.text() if not success else '',
                            'sent_at': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'channel': 'webhook',
                'error': str(e),
                'sent_at': datetime.now().isoformat()
            }


class NotifierAgent(BaseAgent):
    """
    Enhanced Notifier Agent for comprehensive notification management
    
    Supports multiple notification channels with retry logic, templating,
    and intelligent message formatting based on test results and system events.
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.channels = {}
        self.templates = {}
        self.template_env = None
        
        # Initialize notification channels
        channels_config = config.config.get('channels', {})
        for name, channel_config in channels_config.items():
            self.channels[name] = self._initialize_channel(name, channel_config)
        
        # Initialize templates
        templates_config = config.config.get('templates', {})
        template_dir = config.config.get('template_directory', 'templates/notifications')
        if Path(template_dir).exists():
            self.template_env = Environment(loader=FileSystemLoader(template_dir))
        
        for name, template_config in templates_config.items():
            self.templates[name] = self._initialize_template(name, template_config)
    
    def _initialize_channel(self, name: str, config: Dict[str, Any]):
        """Initialize notification channel based on type"""
        channel_type = config.get('type', '').lower()
        
        if channel_type == 'email':
            return EmailChannel(name, config)
        elif channel_type == 'slack':
            return SlackChannel(name, config)
        elif channel_type == 'teams':
            return TeamsChannel(name, config)
        elif channel_type == 'discord':
            return DiscordChannel(name, config)
        elif channel_type == 'webhook':
            return WebhookChannel(name, config)
        else:
            self.logger.warning(f"Unknown channel type: {channel_type}")
            return None
    
    def _initialize_template(self, name: str, config: Dict[str, Any]):
        """Initialize message template"""
        template_content = config.get('content', '')
        template_file = config.get('file', '')
        
        if template_file and self.template_env:
            try:
                return self.template_env.get_template(template_file)
            except Exception as e:
                self.logger.error(f"Failed to load template file {template_file}: {e}")
        
        if template_content:
            return Template(template_content)
        
        return None
    
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Execute notification sending"""
        notification_type = kwargs.get('notification_type', 'generic')
        message_data = kwargs.get('message_data', {})
        channels = kwargs.get('channels', list(self.channels.keys()))
        template_name = kwargs.get('template_name')
        
        # Prepare message based on type
        message = await self._prepare_message(notification_type, message_data, template_name)
        
        # Send to specified channels
        results = {}
        tasks = []
        
        for channel_name in channels:
            if channel_name in self.channels and self.channels[channel_name]:
                task = self.channels[channel_name].send(message)
                tasks.append((channel_name, task))
        
        # Execute all notifications concurrently
        for channel_name, task in tasks:
            try:
                result = await task
                results[channel_name] = result
            except Exception as e:
                results[channel_name] = {
                    'success': False,
                    'channel': channel_name,
                    'error': str(e),
                    'sent_at': datetime.now().isoformat()
                }
        
        # Calculate overall success
        successful_channels = [name for name, result in results.items() if result.get('success')]
        
        return {
            'success': len(successful_channels) > 0,
            'total_channels': len(channels),
            'successful_channels': len(successful_channels),
            'failed_channels': len(channels) - len(successful_channels),
            'results': results,
            'message_type': notification_type,
            'sent_at': datetime.now().isoformat()
        }
    
    async def _prepare_message(self, notification_type: str, 
                             message_data: Dict[str, Any], 
                             template_name: Optional[str] = None) -> Dict[str, Any]:
        """Prepare message based on type and template"""
        
        # Use template if specified
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
            try:
                rendered_content = template.render(**message_data)
                return json.loads(rendered_content) if rendered_content.startswith('{') else {'text': rendered_content}
            except Exception as e:
                self.logger.error(f"Template rendering failed: {e}")
        
        # Use type-specific message preparation
        if notification_type == 'test_result':
            return await self._prepare_test_result_message(message_data)
        elif notification_type == 'test_failure':
            return await self._prepare_test_failure_message(message_data)
        elif notification_type == 'test_success':
            return await self._prepare_test_success_message(message_data)
        elif notification_type == 'system_alert':
            return await self._prepare_system_alert_message(message_data)
        elif notification_type == 'report_ready':
            return await self._prepare_report_ready_message(message_data)
        else:
            return await self._prepare_generic_message(message_data)
    
    async def _prepare_test_result_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test result notification message"""
        test_run = data.get('test_run', {})
        summary = data.get('summary', {})
        
        total_tests = summary.get('total', 0)
        passed_tests = summary.get('passed', 0)
        failed_tests = summary.get('failed', 0)
        skipped_tests = summary.get('skipped', 0)
        pass_rate = summary.get('pass_rate', 0)
        duration = summary.get('duration', 0)
        
        status = 'success' if failed_tests == 0 else 'failure'
        
        # Create comprehensive message
        message = {
            'title': f"Test Run Complete: {test_run.get('name', 'Unknown')}",
            'status': status,
            'text': f"Test execution completed with {passed_tests}/{total_tests} tests passing ({pass_rate:.1f}%)",
            'fields': [
                {'title': 'Total Tests', 'value': str(total_tests), 'short': True},
                {'title': 'Passed', 'value': str(passed_tests), 'short': True},
                {'title': 'Failed', 'value': str(failed_tests), 'short': True},
                {'title': 'Skipped', 'value': str(skipped_tests), 'short': True},
                {'title': 'Pass Rate', 'value': f"{pass_rate:.1f}%", 'short': True},
                {'title': 'Duration', 'value': f"{duration:.2f}s", 'short': True}
            ],
            'footer': f"Run ID: {test_run.get('run_id', 'N/A')}",
            'author_name': test_run.get('triggered_by', 'System'),
            'title_link': test_run.get('report_url', ''),
            'priority': 'high' if failed_tests > 0 else 'normal'
        }
        
        # Add environment info if available
        if test_run.get('environment'):
            message['fields'].append({
                'title': 'Environment', 
                'value': test_run['environment'], 
                'short': True
            })
        
        # Add branch info if available
        if test_run.get('branch'):
            message['fields'].append({
                'title': 'Branch', 
                'value': test_run['branch'], 
                'short': True
            })
        
        return message
    
    async def _prepare_test_failure_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test failure notification message"""
        test_run = data.get('test_run', {})
        failed_tests = data.get('failed_tests', [])
        
        failure_count = len(failed_tests)
        
        message = {
            'title': f"🚨 Test Failures Detected: {test_run.get('name', 'Unknown')}",
            'status': 'failure',
            'text': f"{failure_count} test(s) failed in the latest run",
            'fields': [
                {'title': 'Failed Tests', 'value': str(failure_count), 'short': True},
                {'title': 'Run ID', 'value': test_run.get('run_id', 'N/A'), 'short': True}
            ],
            'priority': 'high'
        }
        
        # Add details of first few failures
        if failed_tests:
            failure_details = []
            for i, test in enumerate(failed_tests[:5]):  # Limit to first 5
                failure_details.append(f"• {test.get('name', 'Unknown')}: {test.get('error', 'No details')}")
            
            if len(failed_tests) > 5:
                failure_details.append(f"... and {len(failed_tests) - 5} more")
            
            message['fields'].append({
                'title': 'Failed Tests Details',
                'value': '\n'.join(failure_details),
                'short': False
            })
        
        return message
    
    async def _prepare_test_success_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test success notification message"""
        test_run = data.get('test_run', {})
        summary = data.get('summary', {})
        
        message = {
            'title': f"✅ All Tests Passed: {test_run.get('name', 'Unknown')}",
            'status': 'success',
            'text': f"All {summary.get('total', 0)} tests passed successfully!",
            'fields': [
                {'title': 'Total Tests', 'value': str(summary.get('total', 0)), 'short': True},
                {'title': 'Duration', 'value': f"{summary.get('duration', 0):.2f}s", 'short': True},
                {'title': 'Run ID', 'value': test_run.get('run_id', 'N/A'), 'short': True}
            ],
            'priority': 'normal'
        }
        
        return message
    
    async def _prepare_system_alert_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare system alert notification message"""
        alert_type = data.get('alert_type', 'unknown')
        severity = data.get('severity', 'info')
        description = data.get('description', 'No description provided')
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        
        message = {
            'title': f"{severity_icons.get(severity, '⚠️')} System Alert: {alert_type.title()}",
            'status': 'error' if severity in ['critical', 'high'] else 'warning',
            'text': description,
            'fields': [
                {'title': 'Alert Type', 'value': alert_type, 'short': True},
                {'title': 'Severity', 'value': severity.upper(), 'short': True},
                {'title': 'Timestamp', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
            ],
            'priority': 'high' if severity in ['critical', 'high'] else 'normal'
        }
        
        # Add additional context fields
        for key, value in data.items():
            if key not in ['alert_type', 'severity', 'description'] and value:
                message['fields'].append({
                    'title': key.replace('_', ' ').title(),
                    'value': str(value),
                    'short': True
                })
        
        return message
    
    async def _prepare_report_ready_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare report ready notification message"""
        report_name = data.get('report_name', 'Test Report')
        report_types = data.get('report_types', [])
        report_url = data.get('report_url', '')
        
        message = {
            'title': f"📊 Report Ready: {report_name}",
            'status': 'info',
            'text': f"Your {report_name} has been generated and is ready for review",
            'fields': [
                {'title': 'Report Types', 'value': ', '.join(report_types), 'short': True},
                {'title': 'Generated At', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
            ],
            'title_link': report_url,
            'priority': 'normal'
        }
        
        if report_url:
            message['actions'] = [{
                'type': 'button',
                'text': 'View Report',
                'url': report_url
            }]
        
        return message
    
    async def _prepare_generic_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare generic notification message"""
        return {
            'title': data.get('title', 'Notification'),
            'text': data.get('message', data.get('text', 'No message provided')),
            'status': data.get('status', 'info'),
            'priority': data.get('priority', 'normal')
        }
    
    # Convenience methods for common notification types
    async def send_test_result_notification(self, test_run: Dict[str, Any], 
                                          summary: Dict[str, Any], 
                                          channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send test result notification"""
        return await self._execute_impl(
            notification_type='test_result',
            message_data={'test_run': test_run, 'summary': summary},
            channels=channels or list(self.channels.keys())
        )
    
    async def send_test_failure_notification(self, test_run: Dict[str, Any], 
                                           failed_tests: List[Dict[str, Any]], 
                                           channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send test failure notification"""
        return await self._execute_impl(
            notification_type='test_failure',
            message_data={'test_run': test_run, 'failed_tests': failed_tests},
            channels=channels or list(self.channels.keys())
        )
    
    async def send_system_alert(self, alert_type: str, severity: str, 
                              description: str, **kwargs) -> Dict[str, Any]:
        """Send system alert notification"""
        alert_data = {
            'alert_type': alert_type,
            'severity': severity,
            'description': description,
            **kwargs
        }
        return await self._execute_impl(
            notification_type='system_alert',
            message_data=alert_data,
            channels=kwargs.get('channels', list(self.channels.keys()))
        )
    
    async def send_report_notification(self, report_name: str, report_types: List[str], 
                                     report_url: Optional[str] = None, 
                                     channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send report ready notification"""
        return await self._execute_impl(
            notification_type='report_ready',
            message_data={
                'report_name': report_name,
                'report_types': report_types,
                'report_url': report_url
            },
            channels=channels or list(self.channels.keys())
        )