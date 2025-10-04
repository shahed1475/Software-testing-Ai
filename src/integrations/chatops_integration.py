"""
ChatOps Integration - Slack/Teams integration with voice summaries
Enables collaborative QA insights and real-time notifications
"""

import asyncio
import json
import logging
import aiohttp
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import io
from urllib.parse import urlencode

from ..agents.executive_summary_agent import ExecutiveSummaryAgent, StakeholderLevel
from ..agents.trend_reporter_agent import TrendReporterAgent
from ..analytics.historical_analyzer import HistoricalAnalyzer
from ..database.database import DatabaseManager

class PlatformType(Enum):
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"

class MessageType(Enum):
    ALERT = "alert"
    SUMMARY = "summary"
    REPORT = "report"
    NOTIFICATION = "notification"
    INTERACTIVE = "interactive"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ChatMessage:
    """Chat message structure"""
    platform: PlatformType
    channel: str
    message_type: MessageType
    title: str
    content: str
    priority: Priority
    attachments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class VoiceSummary:
    """Voice summary structure"""
    text: str
    audio_url: Optional[str]
    duration: float
    language: str
    voice_type: str
    generated_at: datetime

@dataclass
class ChatOpsConfig:
    """ChatOps configuration"""
    slack_token: Optional[str]
    slack_channels: List[str]
    teams_webhook: Optional[str]
    teams_channels: List[str]
    voice_enabled: bool
    voice_service: str  # "azure", "aws", "google"
    notification_rules: Dict[str, Any]
    interactive_commands: bool

class ChatOpsIntegration:
    """
    ChatOps integration for collaborative QA insights
    Supports Slack, Teams, and voice summaries
    """
    
    def __init__(self, config: ChatOpsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        
        # Initialize agents
        self.executive_agent = ExecutiveSummaryAgent({})
        self.trend_reporter = TrendReporterAgent({})
        self.historical_analyzer = HistoricalAnalyzer({})
        
        # Platform clients
        self.slack_client = None
        self.teams_client = None
        
        # Command handlers
        self.command_handlers = {
            "status": self._handle_status_command,
            "summary": self._handle_summary_command,
            "trends": self._handle_trends_command,
            "alerts": self._handle_alerts_command,
            "voice": self._handle_voice_command,
            "help": self._handle_help_command
        }
        
        # Initialize clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize platform clients"""
        if self.config.slack_token:
            self.slack_client = SlackClient(self.config.slack_token)
        
        if self.config.teams_webhook:
            self.teams_client = TeamsClient(self.config.teams_webhook)
    
    async def start(self):
        """Start ChatOps integration"""
        self.logger.info("Starting ChatOps integration")
        
        # Start agents
        await self.executive_agent.start()
        await self.trend_reporter.start()
        
        # Setup periodic notifications
        asyncio.create_task(self._periodic_notifications())
        
        # Setup interactive command listening
        if self.config.interactive_commands:
            asyncio.create_task(self._listen_for_commands())
    
    async def stop(self):
        """Stop ChatOps integration"""
        self.logger.info("Stopping ChatOps integration")
        
        await self.executive_agent.stop()
        await self.trend_reporter.stop()
    
    async def send_alert(
        self,
        title: str,
        message: str,
        priority: Priority = Priority.MEDIUM,
        platforms: Optional[List[PlatformType]] = None,
        include_voice: bool = False
    ):
        """Send alert to configured platforms"""
        
        if platforms is None:
            platforms = [PlatformType.SLACK, PlatformType.TEAMS]
        
        chat_message = ChatMessage(
            platform=PlatformType.SLACK,  # Will be overridden per platform
            channel="",
            message_type=MessageType.ALERT,
            title=title,
            content=message,
            priority=priority,
            attachments=[],
            metadata={"include_voice": include_voice},
            timestamp=datetime.now()
        )
        
        # Send to each platform
        for platform in platforms:
            await self._send_to_platform(platform, chat_message)
        
        # Generate voice summary if requested
        if include_voice and self.config.voice_enabled:
            voice_summary = await self._generate_voice_summary(f"{title}. {message}")
            await self._send_voice_summary(voice_summary, platforms)
    
    async def send_daily_summary(self, stakeholder_level: StakeholderLevel = StakeholderLevel.MANAGEMENT):
        """Send daily executive summary"""
        
        try:
            # Generate executive summary
            dashboard = await self.executive_agent.generate_executive_summary(
                stakeholder_level=stakeholder_level
            )
            
            # Format message
            title = f"Daily QA Summary - Health Score: {dashboard.overall_health_score:.1f}%"
            
            content = self._format_executive_summary(dashboard)
            
            # Create attachments with charts
            attachments = await self._create_summary_attachments(dashboard)
            
            chat_message = ChatMessage(
                platform=PlatformType.SLACK,
                channel="",
                message_type=MessageType.SUMMARY,
                title=title,
                content=content,
                priority=Priority.MEDIUM,
                attachments=attachments,
                metadata={"dashboard": asdict(dashboard)},
                timestamp=datetime.now()
            )
            
            # Send to all platforms
            await self._send_to_platform(PlatformType.SLACK, chat_message)
            await self._send_to_platform(PlatformType.TEAMS, chat_message)
            
            # Generate voice summary
            if self.config.voice_enabled:
                voice_text = self._create_voice_summary_text(dashboard)
                voice_summary = await self._generate_voice_summary(voice_text)
                await self._send_voice_summary(voice_summary, [PlatformType.SLACK, PlatformType.TEAMS])
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {str(e)}")
    
    async def send_trend_report(self, period: str = "weekly"):
        """Send trend analysis report"""
        
        try:
            from ..agents.trend_reporter_agent import TrendPeriod
            
            period_mapping = {
                "daily": TrendPeriod.DAILY,
                "weekly": TrendPeriod.WEEKLY,
                "monthly": TrendPeriod.MONTHLY
            }
            
            # Generate trend report
            trend_report = await self.trend_reporter.generate_trend_report(
                period=period_mapping.get(period, TrendPeriod.WEEKLY),
                include_charts=True
            )
            
            title = f"{period.title()} Trend Report"
            content = self._format_trend_report(trend_report)
            
            # Create chart attachments
            attachments = await self._create_trend_attachments(trend_report)
            
            chat_message = ChatMessage(
                platform=PlatformType.SLACK,
                channel="",
                message_type=MessageType.REPORT,
                title=title,
                content=content,
                priority=Priority.MEDIUM,
                attachments=attachments,
                metadata={"trend_report": trend_report},
                timestamp=datetime.now()
            )
            
            # Send to platforms
            await self._send_to_platform(PlatformType.SLACK, chat_message)
            await self._send_to_platform(PlatformType.TEAMS, chat_message)
            
        except Exception as e:
            self.logger.error(f"Error sending trend report: {str(e)}")
    
    async def _send_to_platform(self, platform: PlatformType, message: ChatMessage):
        """Send message to specific platform"""
        
        try:
            if platform == PlatformType.SLACK and self.slack_client:
                await self._send_to_slack(message)
            elif platform == PlatformType.TEAMS and self.teams_client:
                await self._send_to_teams(message)
            
        except Exception as e:
            self.logger.error(f"Error sending to {platform.value}: {str(e)}")
    
    async def _send_to_slack(self, message: ChatMessage):
        """Send message to Slack"""
        
        for channel in self.config.slack_channels:
            slack_message = {
                "channel": channel,
                "text": message.title,
                "blocks": self._create_slack_blocks(message),
                "attachments": self._format_slack_attachments(message.attachments)
            }
            
            await self.slack_client.send_message(slack_message)
    
    async def _send_to_teams(self, message: ChatMessage):
        """Send message to Teams"""
        
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self._get_priority_color(message.priority),
            "summary": message.title,
            "sections": self._create_teams_sections(message)
        }
        
        await self.teams_client.send_message(teams_message)
    
    def _create_slack_blocks(self, message: ChatMessage) -> List[Dict[str, Any]]:
        """Create Slack blocks for message"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": message.title
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message.content
                }
            }
        ]
        
        # Add priority indicator
        priority_emoji = {
            Priority.LOW: "🟢",
            Priority.MEDIUM: "🟡",
            Priority.HIGH: "🟠",
            Priority.CRITICAL: "🔴"
        }
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{priority_emoji.get(message.priority, '⚪')} Priority: {message.priority.value.title()}"
                }
            ]
        })
        
        # Add interactive buttons for certain message types
        if message.message_type in [MessageType.ALERT, MessageType.SUMMARY]:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "action_id": "view_details",
                        "value": json.dumps(message.metadata)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Get Voice Summary"
                        },
                        "action_id": "voice_summary",
                        "value": "generate_voice"
                    }
                ]
            })
        
        return blocks
    
    def _create_teams_sections(self, message: ChatMessage) -> List[Dict[str, Any]]:
        """Create Teams sections for message"""
        
        sections = [
            {
                "activityTitle": message.title,
                "activitySubtitle": f"Priority: {message.priority.value.title()}",
                "text": message.content,
                "facts": [
                    {
                        "name": "Type",
                        "value": message.message_type.value.title()
                    },
                    {
                        "name": "Timestamp",
                        "value": message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    }
                ]
            }
        ]
        
        return sections
    
    def _format_slack_attachments(self, attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format attachments for Slack"""
        
        slack_attachments = []
        
        for attachment in attachments:
            if attachment.get("type") == "chart":
                slack_attachments.append({
                    "title": attachment.get("title", "Chart"),
                    "image_url": attachment.get("url"),
                    "color": "good"
                })
            elif attachment.get("type") == "data":
                slack_attachments.append({
                    "title": attachment.get("title", "Data"),
                    "text": attachment.get("content"),
                    "color": "warning"
                })
        
        return slack_attachments
    
    def _get_priority_color(self, priority: Priority) -> str:
        """Get color for priority level"""
        
        colors = {
            Priority.LOW: "28a745",      # Green
            Priority.MEDIUM: "ffc107",   # Yellow
            Priority.HIGH: "fd7e14",     # Orange
            Priority.CRITICAL: "dc3545"  # Red
        }
        
        return colors.get(priority, "6c757d")  # Gray default
    
    def _format_executive_summary(self, dashboard) -> str:
        """Format executive summary for chat"""
        
        content = f"""
**System Health Overview**
• Overall Health Score: {dashboard.overall_health_score:.1f}%
• System Uptime: {dashboard.stability_metrics.uptime_percentage:.1f}%
• Risk Level: {dashboard.risk_assessment.risk_level.value.title()}

**Key Insights:**
"""
        
        for insight in dashboard.key_insights[:3]:
            content += f"• {insight.headline}\n"
        
        if dashboard.alerts:
            content += f"\n**Active Alerts:** {len(dashboard.alerts)}"
        
        if dashboard.recommendations:
            content += f"\n**Top Recommendation:** {dashboard.recommendations[0]}"
        
        return content
    
    def _format_trend_report(self, trend_report: Dict[str, Any]) -> str:
        """Format trend report for chat"""
        
        content = f"""
**Trend Analysis Summary**
• Analysis Period: {trend_report.get('period', 'Unknown')}
• Data Points Analyzed: {len(trend_report.get('detailed_metrics', []))}

**Key Trends:**
"""
        
        insights = trend_report.get('business_insights', [])
        for insight in insights[:3]:
            content += f"• {insight.get('summary', 'No summary available')}\n"
        
        return content
    
    async def _create_summary_attachments(self, dashboard) -> List[Dict[str, Any]]:
        """Create attachments for summary"""
        
        attachments = []
        
        # Health score chart (mock)
        attachments.append({
            "type": "chart",
            "title": "Health Score Trend",
            "url": "https://example.com/health-chart.png",  # Would be actual chart URL
            "description": f"Current health score: {dashboard.overall_health_score:.1f}%"
        })
        
        # Key metrics data
        metrics_text = f"""
Uptime: {dashboard.stability_metrics.uptime_percentage:.1f}%
Incidents: {dashboard.stability_metrics.incident_count}
MTTR: {dashboard.stability_metrics.mean_time_to_recovery:.1f} min
"""
        
        attachments.append({
            "type": "data",
            "title": "Key Metrics",
            "content": metrics_text
        })
        
        return attachments
    
    async def _create_trend_attachments(self, trend_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create attachments for trend report"""
        
        attachments = []
        
        # Trend charts (mock URLs)
        chart_types = ["success_rate", "performance", "flakiness"]
        
        for chart_type in chart_types:
            attachments.append({
                "type": "chart",
                "title": f"{chart_type.replace('_', ' ').title()} Trend",
                "url": f"https://example.com/{chart_type}-trend.png",
                "description": f"Historical {chart_type} analysis"
            })
        
        return attachments
    
    async def _generate_voice_summary(self, text: str) -> VoiceSummary:
        """Generate voice summary from text"""
        
        if not self.config.voice_enabled:
            return VoiceSummary(
                text=text,
                audio_url=None,
                duration=0.0,
                language="en-US",
                voice_type="neural",
                generated_at=datetime.now()
            )
        
        try:
            # Mock voice generation (would integrate with actual TTS service)
            audio_url = await self._synthesize_speech(text)
            
            return VoiceSummary(
                text=text,
                audio_url=audio_url,
                duration=len(text) * 0.1,  # Rough estimate
                language="en-US",
                voice_type="neural",
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error generating voice summary: {str(e)}")
            return VoiceSummary(
                text=text,
                audio_url=None,
                duration=0.0,
                language="en-US",
                voice_type="neural",
                generated_at=datetime.now()
            )
    
    async def _synthesize_speech(self, text: str) -> Optional[str]:
        """Synthesize speech from text"""
        
        # Mock implementation - would integrate with Azure Cognitive Services, AWS Polly, etc.
        if self.config.voice_service == "azure":
            return await self._azure_tts(text)
        elif self.config.voice_service == "aws":
            return await self._aws_polly(text)
        elif self.config.voice_service == "google":
            return await self._google_tts(text)
        
        return None
    
    async def _azure_tts(self, text: str) -> Optional[str]:
        """Azure Text-to-Speech integration"""
        # Mock implementation
        return f"https://example.com/audio/{hash(text)}.mp3"
    
    async def _aws_polly(self, text: str) -> Optional[str]:
        """AWS Polly integration"""
        # Mock implementation
        return f"https://s3.amazonaws.com/audio/{hash(text)}.mp3"
    
    async def _google_tts(self, text: str) -> Optional[str]:
        """Google Text-to-Speech integration"""
        # Mock implementation
        return f"https://storage.googleapis.com/audio/{hash(text)}.mp3"
    
    async def _send_voice_summary(self, voice_summary: VoiceSummary, platforms: List[PlatformType]):
        """Send voice summary to platforms"""
        
        if not voice_summary.audio_url:
            return
        
        voice_message = ChatMessage(
            platform=PlatformType.SLACK,
            channel="",
            message_type=MessageType.NOTIFICATION,
            title="🎵 Voice Summary Available",
            content=f"Duration: {voice_summary.duration:.1f}s\nLanguage: {voice_summary.language}",
            priority=Priority.LOW,
            attachments=[{
                "type": "audio",
                "title": "Voice Summary",
                "url": voice_summary.audio_url,
                "duration": voice_summary.duration
            }],
            metadata={"voice_summary": asdict(voice_summary)},
            timestamp=datetime.now()
        )
        
        for platform in platforms:
            await self._send_to_platform(platform, voice_message)
    
    def _create_voice_summary_text(self, dashboard) -> str:
        """Create text for voice summary"""
        
        text = f"""
Quality Assurance Daily Summary.
        
Overall system health score is {dashboard.overall_health_score:.0f} percent.
System uptime is {dashboard.stability_metrics.uptime_percentage:.1f} percent.
Risk level is {dashboard.risk_assessment.risk_level.value}.

Key insights include:
"""
        
        for insight in dashboard.key_insights[:2]:
            text += f"{insight.headline}. "
        
        if dashboard.alerts:
            text += f"There are {len(dashboard.alerts)} active alerts requiring attention. "
        
        if dashboard.recommendations:
            text += f"Top recommendation: {dashboard.recommendations[0]}"
        
        return text
    
    async def _periodic_notifications(self):
        """Send periodic notifications"""
        
        while True:
            try:
                current_time = datetime.now()
                
                # Daily summary at 9 AM
                if current_time.hour == 9 and current_time.minute == 0:
                    await self.send_daily_summary()
                
                # Weekly trend report on Mondays at 10 AM
                if current_time.weekday() == 0 and current_time.hour == 10 and current_time.minute == 0:
                    await self.send_trend_report("weekly")
                
                # Check for critical alerts every 5 minutes
                if current_time.minute % 5 == 0:
                    await self._check_critical_alerts()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in periodic notifications: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _check_critical_alerts(self):
        """Check for critical alerts"""
        
        try:
            # Get recent dashboard data
            dashboard = await self.executive_agent.generate_executive_summary()
            
            # Check for critical conditions
            critical_alerts = [alert for alert in dashboard.alerts if alert.get("type") == "critical"]
            
            for alert in critical_alerts:
                await self.send_alert(
                    title=f"🚨 Critical Alert: {alert.get('title')}",
                    message=alert.get('message', ''),
                    priority=Priority.CRITICAL,
                    include_voice=True
                )
            
        except Exception as e:
            self.logger.error(f"Error checking critical alerts: {str(e)}")
    
    async def _listen_for_commands(self):
        """Listen for interactive commands"""
        
        # Mock implementation - would integrate with platform webhooks
        self.logger.info("Interactive command listening started")
        
        # In a real implementation, this would:
        # 1. Set up webhook endpoints for Slack/Teams
        # 2. Parse incoming commands
        # 3. Route to appropriate handlers
        # 4. Send responses back to the platform
    
    async def _handle_status_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status command"""
        
        dashboard = await self.executive_agent.generate_executive_summary()
        
        return {
            "response_type": "in_channel",
            "text": f"System Health: {dashboard.overall_health_score:.1f}%",
            "attachments": [
                {
                    "color": "good" if dashboard.overall_health_score > 80 else "warning",
                    "fields": [
                        {
                            "title": "Uptime",
                            "value": f"{dashboard.stability_metrics.uptime_percentage:.1f}%",
                            "short": True
                        },
                        {
                            "title": "Risk Level",
                            "value": dashboard.risk_assessment.risk_level.value.title(),
                            "short": True
                        }
                    ]
                }
            ]
        }
    
    async def _handle_summary_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle summary command"""
        
        await self.send_daily_summary()
        
        return {
            "response_type": "ephemeral",
            "text": "Executive summary has been sent to the channel."
        }
    
    async def _handle_trends_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trends command"""
        
        period = command_data.get("text", "weekly").strip().lower()
        if period not in ["daily", "weekly", "monthly"]:
            period = "weekly"
        
        await self.send_trend_report(period)
        
        return {
            "response_type": "ephemeral",
            "text": f"{period.title()} trend report has been sent to the channel."
        }
    
    async def _handle_alerts_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alerts command"""
        
        dashboard = await self.executive_agent.generate_executive_summary()
        
        if not dashboard.alerts:
            return {
                "response_type": "ephemeral",
                "text": "No active alerts. System is operating normally."
            }
        
        alert_text = "Active Alerts:\n"
        for alert in dashboard.alerts[:5]:
            alert_text += f"• {alert.get('title', 'Unknown')}: {alert.get('message', '')}\n"
        
        return {
            "response_type": "in_channel",
            "text": alert_text
        }
    
    async def _handle_voice_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice command"""
        
        dashboard = await self.executive_agent.generate_executive_summary()
        voice_text = self._create_voice_summary_text(dashboard)
        voice_summary = await self._generate_voice_summary(voice_text)
        
        if voice_summary.audio_url:
            return {
                "response_type": "in_channel",
                "text": "🎵 Voice summary generated",
                "attachments": [
                    {
                        "title": "Voice Summary",
                        "title_link": voice_summary.audio_url,
                        "text": f"Duration: {voice_summary.duration:.1f}s"
                    }
                ]
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": "Voice summary generation failed. Please try again later."
            }
    
    async def _handle_help_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help command"""
        
        help_text = """
Available QA Bot Commands:
• `/qa status` - Get current system health status
• `/qa summary` - Generate and send executive summary
• `/qa trends [daily|weekly|monthly]` - Send trend analysis report
• `/qa alerts` - Show active alerts
• `/qa voice` - Generate voice summary
• `/qa help` - Show this help message

The bot also sends automatic notifications:
• Daily summaries at 9 AM
• Weekly trend reports on Mondays at 10 AM
• Critical alerts as they occur
"""
        
        return {
            "response_type": "ephemeral",
            "text": help_text
        }


class SlackClient:
    """Slack API client"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://slack.com/api"
        self.logger = logging.getLogger(__name__)
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to Slack"""
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat.postMessage",
                headers=headers,
                json=message
            ) as response:
                if response.status != 200:
                    self.logger.error(f"Slack API error: {response.status}")
                    return None
                
                return await response.json()


class TeamsClient:
    """Microsoft Teams webhook client"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to Teams"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                headers=headers,
                json=message
            ) as response:
                if response.status != 200:
                    self.logger.error(f"Teams webhook error: {response.status}")
                    return None
                
                return await response.text()