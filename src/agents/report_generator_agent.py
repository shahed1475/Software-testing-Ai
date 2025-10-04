"""
Report Generator Agent

Merges test results from multiple sources and generates comprehensive reports
in various formats (JSON, PDF, HTML, Excel).
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, Template
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from .base_agent import BaseAgent, AgentConfig
from .report_collector_agent import ReportCollectorAgent


class ReportGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive test reports from collected data.
    
    Supports:
    - JSON reports with detailed test results
    - PDF reports with charts and visualizations
    - HTML reports with interactive elements
    - Excel reports with multiple sheets
    - Email-friendly summary reports
    - Custom report templates
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.report_config = config.metadata.get('report_config', {})
        self.template_config = config.metadata.get('template_config', {})
        self.output_config = config.metadata.get('output_config', {})
        
        # Initialize Jinja2 environment
        template_dir = self.template_config.get('template_dir', 'templates/reports')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir) if Path(template_dir).exists() else None
        )
        
        # Set up matplotlib for chart generation
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Execute report generation logic"""
        collected_data = kwargs.get('collected_data', {})
        report_types = kwargs.get('report_types', ['json', 'pdf', 'html'])
        output_dir = kwargs.get('output_dir', 'reports')
        report_name = kwargs.get('report_name', f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        include_charts = kwargs.get('include_charts', True)
        include_details = kwargs.get('include_details', True)
        
        self.logger.info(f"Generating reports: {report_types}")
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info(f"Report name: {report_name}")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process and analyze collected data
        processed_data = await self._process_collected_data(collected_data)
        
        # Generate charts if requested
        charts = {}
        if include_charts:
            charts = await self._generate_charts(processed_data)
        
        # Generate reports in requested formats
        generated_reports = {}
        
        for report_type in report_types:
            self.logger.info(f"Generating {report_type.upper()} report")
            
            try:
                if report_type == 'json':
                    report_path = await self._generate_json_report(
                        processed_data, output_path, report_name, include_details
                    )
                elif report_type == 'pdf':
                    report_path = await self._generate_pdf_report(
                        processed_data, charts, output_path, report_name, include_details
                    )
                elif report_type == 'html':
                    report_path = await self._generate_html_report(
                        processed_data, charts, output_path, report_name, include_details
                    )
                elif report_type == 'excel':
                    report_path = await self._generate_excel_report(
                        processed_data, output_path, report_name, include_details
                    )
                elif report_type == 'summary':
                    report_path = await self._generate_summary_report(
                        processed_data, output_path, report_name
                    )
                else:
                    self.logger.warning(f"Unknown report type: {report_type}")
                    continue
                
                generated_reports[report_type] = {
                    'path': str(report_path),
                    'size': report_path.stat().st_size,
                    'created_at': datetime.now().isoformat()
                }
                
                self.logger.info(f"Generated {report_type.upper()} report: {report_path}")
                
            except Exception as e:
                self.logger.error(f"Error generating {report_type} report: {e}")
                generated_reports[report_type] = {
                    'error': str(e),
                    'created_at': datetime.now().isoformat()
                }
        
        return {
            'generated_reports': generated_reports,
            'report_name': report_name,
            'output_directory': str(output_path),
            'charts_generated': list(charts.keys()) if charts else [],
            'summary': processed_data.get('summary', {}),
            'generation_time': datetime.now().isoformat()
        }
    
    async def _process_collected_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and analyze collected test data"""
        processed = {
            'metadata': collected_data.get('metadata', {}),
            'summary': {},
            'test_runs': collected_data.get('test_runs', []),
            'test_results': collected_data.get('test_results', []),
            'artifacts': collected_data.get('artifacts', []),
            'logs': collected_data.get('logs', []),
            'analysis': {},
            'trends': {},
            'recommendations': []
        }
        
        # Calculate summary statistics
        test_runs = processed['test_runs']
        test_results = processed['test_results']
        
        processed['summary'] = {
            'total_test_runs': len(test_runs),
            'total_test_results': len(test_results),
            'total_artifacts': len(processed['artifacts']),
            'total_logs': len(processed['logs']),
            'date_range': self._calculate_date_range(test_runs),
            'sources': list(set(run.get('source', 'unknown') for run in test_runs)),
            'environments': list(set(run.get('environment', 'unknown') for run in test_runs if run.get('environment'))),
            'test_types': list(set(run.get('test_type', 'unknown') for run in test_runs if run.get('test_type')))
        }
        
        # Analyze test results
        if test_results:
            status_counts = {}
            duration_stats = []
            
            for result in test_results:
                status = result.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if result.get('duration'):
                    duration_stats.append(float(result['duration']))
            
            processed['analysis']['status_distribution'] = status_counts
            
            if duration_stats:
                processed['analysis']['duration_stats'] = {
                    'min': min(duration_stats),
                    'max': max(duration_stats),
                    'avg': sum(duration_stats) / len(duration_stats),
                    'total': sum(duration_stats)
                }
        
        # Analyze test runs
        if test_runs:
            run_status_counts = {}
            success_rate_by_type = {}
            
            for run in test_runs:
                status = run.get('status', 'unknown')
                run_status_counts[status] = run_status_counts.get(status, 0) + 1
                
                test_type = run.get('test_type', 'unknown')
                if test_type not in success_rate_by_type:
                    success_rate_by_type[test_type] = {'total': 0, 'passed': 0}
                
                success_rate_by_type[test_type]['total'] += 1
                if status in ['completed', 'success', 'passed']:
                    success_rate_by_type[test_type]['passed'] += 1
            
            processed['analysis']['run_status_distribution'] = run_status_counts
            processed['analysis']['success_rate_by_type'] = {
                test_type: (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
                for test_type, stats in success_rate_by_type.items()
            }
        
        # Generate trends analysis
        processed['trends'] = await self._analyze_trends(test_runs, test_results)
        
        # Generate recommendations
        processed['recommendations'] = await self._generate_recommendations(processed)
        
        return processed
    
    def _calculate_date_range(self, test_runs: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate the date range of test runs"""
        if not test_runs:
            return {'start': None, 'end': None}
        
        dates = []
        for run in test_runs:
            created_at = run.get('created_at') or run.get('timestamp')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        # Try to parse ISO format
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        date = created_at
                    dates.append(date)
                except:
                    continue
        
        if dates:
            return {
                'start': min(dates).isoformat(),
                'end': max(dates).isoformat()
            }
        
        return {'start': None, 'end': None}
    
    async def _analyze_trends(self, test_runs: List[Dict[str, Any]], 
                            test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in test data"""
        trends = {
            'success_rate_trend': [],
            'duration_trend': [],
            'failure_patterns': {},
            'performance_trend': []
        }
        
        # Group test runs by date
        runs_by_date = {}
        for run in test_runs:
            created_at = run.get('created_at') or run.get('timestamp')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    else:
                        date = created_at.date()
                    
                    date_str = date.isoformat()
                    if date_str not in runs_by_date:
                        runs_by_date[date_str] = []
                    runs_by_date[date_str].append(run)
                except:
                    continue
        
        # Calculate daily success rates
        for date_str, runs in sorted(runs_by_date.items()):
            total_runs = len(runs)
            successful_runs = sum(1 for run in runs if run.get('status') in ['completed', 'success', 'passed'])
            success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0
            
            trends['success_rate_trend'].append({
                'date': date_str,
                'success_rate': success_rate,
                'total_runs': total_runs,
                'successful_runs': successful_runs
            })
        
        # Analyze failure patterns
        failure_reasons = {}
        for result in test_results:
            if result.get('status') in ['failed', 'error']:
                error_msg = result.get('error_message', 'Unknown error')
                # Extract common error patterns
                if 'timeout' in error_msg.lower():
                    pattern = 'Timeout'
                elif 'connection' in error_msg.lower():
                    pattern = 'Connection Error'
                elif 'assertion' in error_msg.lower():
                    pattern = 'Assertion Error'
                elif 'not found' in error_msg.lower():
                    pattern = 'Element Not Found'
                else:
                    pattern = 'Other'
                
                failure_reasons[pattern] = failure_reasons.get(pattern, 0) + 1
        
        trends['failure_patterns'] = failure_reasons
        
        return trends
    
    async def _generate_recommendations(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on test data analysis"""
        recommendations = []
        analysis = processed_data.get('analysis', {})
        trends = processed_data.get('trends', {})
        
        # Check success rate
        success_rates = analysis.get('success_rate_by_type', {})
        for test_type, rate in success_rates.items():
            if rate < 80:
                recommendations.append({
                    'type': 'quality',
                    'priority': 'high',
                    'title': f'Low Success Rate for {test_type}',
                    'description': f'Success rate for {test_type} tests is {rate:.1f}%, which is below the recommended 80%.',
                    'action': f'Review and fix failing {test_type} tests to improve reliability.'
                })
        
        # Check for timeout issues
        failure_patterns = trends.get('failure_patterns', {})
        if failure_patterns.get('Timeout', 0) > 0:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': 'Timeout Issues Detected',
                'description': f'{failure_patterns["Timeout"]} tests failed due to timeouts.',
                'action': 'Consider increasing timeout values or optimizing test performance.'
            })
        
        # Check for connection errors
        if failure_patterns.get('Connection Error', 0) > 0:
            recommendations.append({
                'type': 'infrastructure',
                'priority': 'high',
                'title': 'Connection Issues Detected',
                'description': f'{failure_patterns["Connection Error"]} tests failed due to connection errors.',
                'action': 'Check network connectivity and service availability.'
            })
        
        # Check test duration
        duration_stats = analysis.get('duration_stats', {})
        if duration_stats.get('avg', 0) > 300:  # 5 minutes
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': 'Long Test Duration',
                'description': f'Average test duration is {duration_stats["avg"]:.1f} seconds.',
                'action': 'Consider optimizing test execution time or running tests in parallel.'
            })
        
        return recommendations
    
    async def _generate_charts(self, processed_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts and return base64 encoded images"""
        charts = {}
        
        try:
            # Test status distribution pie chart
            status_dist = processed_data.get('analysis', {}).get('status_distribution', {})
            if status_dist:
                charts['status_distribution'] = await self._create_pie_chart(
                    status_dist, 'Test Results Distribution', 'status_distribution'
                )
            
            # Success rate by test type bar chart
            success_rates = processed_data.get('analysis', {}).get('success_rate_by_type', {})
            if success_rates:
                charts['success_rate_by_type'] = await self._create_bar_chart(
                    success_rates, 'Success Rate by Test Type (%)', 'success_rate_by_type'
                )
            
            # Success rate trend line chart
            trend_data = processed_data.get('trends', {}).get('success_rate_trend', [])
            if trend_data:
                charts['success_rate_trend'] = await self._create_line_chart(
                    trend_data, 'Success Rate Trend', 'success_rate_trend'
                )
            
            # Failure patterns pie chart
            failure_patterns = processed_data.get('trends', {}).get('failure_patterns', {})
            if failure_patterns:
                charts['failure_patterns'] = await self._create_pie_chart(
                    failure_patterns, 'Failure Patterns', 'failure_patterns'
                )
        
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
        
        return charts
    
    async def _create_pie_chart(self, data: Dict[str, Any], title: str, filename: str) -> str:
        """Create a pie chart and return base64 encoded image"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        labels = list(data.keys())
        values = list(data.values())
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    async def _create_bar_chart(self, data: Dict[str, Any], title: str, filename: str) -> str:
        """Create a bar chart and return base64 encoded image"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        labels = list(data.keys())
        values = list(data.values())
        
        bars = ax.bar(labels, values, color=sns.color_palette("husl", len(labels)))
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('Success Rate (%)')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}%', ha='center', va='bottom')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    async def _create_line_chart(self, data: List[Dict[str, Any]], title: str, filename: str) -> str:
        """Create a line chart and return base64 encoded image"""
        if not data:
            return ""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = [item['date'] for item in data]
        success_rates = [item['success_rate'] for item in data]
        
        ax.plot(dates, success_rates, marker='o', linewidth=2, markersize=6)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('Success Rate (%)')
        ax.set_xlabel('Date')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.xticks(rotation=45, ha='right')
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    async def _generate_json_report(self, processed_data: Dict[str, Any], 
                                  output_path: Path, report_name: str, 
                                  include_details: bool) -> Path:
        """Generate JSON report"""
        report_path = output_path / f"{report_name}.json"
        
        report_data = {
            'report_metadata': {
                'name': report_name,
                'generated_at': datetime.now().isoformat(),
                'generator': 'ReportGeneratorAgent',
                'version': '1.0.0',
                'include_details': include_details
            },
            'summary': processed_data.get('summary', {}),
            'analysis': processed_data.get('analysis', {}),
            'trends': processed_data.get('trends', {}),
            'recommendations': processed_data.get('recommendations', [])
        }
        
        if include_details:
            report_data.update({
                'test_runs': processed_data.get('test_runs', []),
                'test_results': processed_data.get('test_results', []),
                'artifacts': processed_data.get('artifacts', []),
                'logs': processed_data.get('logs', [])
            })
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        return report_path
    
    async def _generate_pdf_report(self, processed_data: Dict[str, Any], 
                                 charts: Dict[str, str], output_path: Path, 
                                 report_name: str, include_details: bool) -> Path:
        """Generate PDF report"""
        report_path = output_path / f"{report_name}.pdf"
        
        doc = SimpleDocTemplate(str(report_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"Test Report: {report_name}", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        metadata = processed_data.get('summary', {})
        story.append(Paragraph("Report Summary", styles['Heading2']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Test Runs', str(metadata.get('total_test_runs', 0))],
            ['Total Test Results', str(metadata.get('total_test_results', 0))],
            ['Total Artifacts', str(metadata.get('total_artifacts', 0))],
            ['Sources', ', '.join(metadata.get('sources', []))],
            ['Test Types', ', '.join(metadata.get('test_types', []))],
            ['Date Range', f"{metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Charts
        if charts:
            story.append(Paragraph("Visual Analysis", styles['Heading2']))
            
            for chart_name, chart_data in charts.items():
                if chart_data:
                    # Decode base64 image
                    image_data = base64.b64decode(chart_data)
                    image_buffer = BytesIO(image_data)
                    
                    # Create temporary file for image
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_image.write(image_data)
                    temp_image.close()
                    
                    try:
                        img = Image(temp_image.name, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 10))
                    except:
                        story.append(Paragraph(f"Chart: {chart_name} (Unable to render)", styles['Normal']))
                    finally:
                        os.unlink(temp_image.name)
        
        # Analysis
        analysis = processed_data.get('analysis', {})
        if analysis:
            story.append(PageBreak())
            story.append(Paragraph("Detailed Analysis", styles['Heading2']))
            
            # Status distribution
            status_dist = analysis.get('status_distribution', {})
            if status_dist:
                story.append(Paragraph("Test Results Distribution", styles['Heading3']))
                status_data = [['Status', 'Count', 'Percentage']]
                total_results = sum(status_dist.values())
                
                for status, count in status_dist.items():
                    percentage = (count / total_results) * 100 if total_results > 0 else 0
                    status_data.append([status.title(), str(count), f"{percentage:.1f}%"])
                
                status_table = Table(status_data)
                status_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(status_table)
                story.append(Spacer(1, 20))
        
        # Recommendations
        recommendations = processed_data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Recommendations", styles['Heading2']))
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec['title']}", styles['Heading3']))
                story.append(Paragraph(f"Priority: {rec['priority'].title()}", styles['Normal']))
                story.append(Paragraph(f"Description: {rec['description']}", styles['Normal']))
                story.append(Paragraph(f"Action: {rec['action']}", styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Detailed data (if requested)
        if include_details:
            story.append(PageBreak())
            story.append(Paragraph("Detailed Test Results", styles['Heading2']))
            
            test_results = processed_data.get('test_results', [])[:50]  # Limit to first 50
            if test_results:
                results_data = [['Test Name', 'Status', 'Duration (s)', 'Error']]
                
                for result in test_results:
                    error_msg = result.get('error_message', '')
                    if len(error_msg) > 50:
                        error_msg = error_msg[:47] + '...'
                    
                    results_data.append([
                        result.get('test_name', 'N/A'),
                        result.get('status', 'N/A'),
                        str(result.get('duration', 'N/A')),
                        error_msg
                    ])
                
                results_table = Table(results_data)
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(results_table)
        
        # Build PDF
        doc.build(story)
        return report_path
    
    async def _generate_html_report(self, processed_data: Dict[str, Any], 
                                  charts: Dict[str, str], output_path: Path, 
                                  report_name: str, include_details: bool) -> Path:
        """Generate HTML report"""
        report_path = output_path / f"{report_name}.html"
        
        # Try to use custom template if available
        template = None
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template('test_report.html')
            except:
                pass
        
        if not template:
            # Use default template
            template_content = self._get_default_html_template()
            template = Template(template_content)
        
        # Prepare template data
        template_data = {
            'report_name': report_name,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': processed_data.get('summary', {}),
            'analysis': processed_data.get('analysis', {}),
            'trends': processed_data.get('trends', {}),
            'recommendations': processed_data.get('recommendations', []),
            'charts': charts,
            'include_details': include_details
        }
        
        if include_details:
            template_data.update({
                'test_runs': processed_data.get('test_runs', []),
                'test_results': processed_data.get('test_results', []),
                'artifacts': processed_data.get('artifacts', [])
            })
        
        # Render template
        html_content = template.render(**template_data)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    async def _generate_excel_report(self, processed_data: Dict[str, Any], 
                                   output_path: Path, report_name: str, 
                                   include_details: bool) -> Path:
        """Generate Excel report"""
        report_path = output_path / f"{report_name}.xlsx"
        
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = processed_data.get('summary', {})
            summary_df = pd.DataFrame([
                ['Total Test Runs', summary_data.get('total_test_runs', 0)],
                ['Total Test Results', summary_data.get('total_test_results', 0)],
                ['Total Artifacts', summary_data.get('total_artifacts', 0)],
                ['Sources', ', '.join(summary_data.get('sources', []))],
                ['Test Types', ', '.join(summary_data.get('test_types', []))],
                ['Start Date', summary_data.get('date_range', {}).get('start', 'N/A')],
                ['End Date', summary_data.get('date_range', {}).get('end', 'N/A')]
            ], columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Analysis sheet
            analysis = processed_data.get('analysis', {})
            if analysis.get('status_distribution'):
                status_df = pd.DataFrame([
                    [status, count] for status, count in analysis['status_distribution'].items()
                ], columns=['Status', 'Count'])
                status_df.to_excel(writer, sheet_name='Status Distribution', index=False)
            
            if analysis.get('success_rate_by_type'):
                success_df = pd.DataFrame([
                    [test_type, rate] for test_type, rate in analysis['success_rate_by_type'].items()
                ], columns=['Test Type', 'Success Rate (%)'])
                success_df.to_excel(writer, sheet_name='Success Rates', index=False)
            
            # Recommendations sheet
            recommendations = processed_data.get('recommendations', [])
            if recommendations:
                rec_df = pd.DataFrame(recommendations)
                rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
            
            # Detailed data sheets (if requested)
            if include_details:
                test_runs = processed_data.get('test_runs', [])
                if test_runs:
                    runs_df = pd.DataFrame(test_runs)
                    runs_df.to_excel(writer, sheet_name='Test Runs', index=False)
                
                test_results = processed_data.get('test_results', [])
                if test_results:
                    results_df = pd.DataFrame(test_results)
                    results_df.to_excel(writer, sheet_name='Test Results', index=False)
                
                artifacts = processed_data.get('artifacts', [])
                if artifacts:
                    artifacts_df = pd.DataFrame(artifacts)
                    artifacts_df.to_excel(writer, sheet_name='Artifacts', index=False)
        
        return report_path
    
    async def _generate_summary_report(self, processed_data: Dict[str, Any], 
                                     output_path: Path, report_name: str) -> Path:
        """Generate a concise summary report (text format)"""
        report_path = output_path / f"{report_name}_summary.txt"
        
        summary = processed_data.get('summary', {})
        analysis = processed_data.get('analysis', {})
        recommendations = processed_data.get('recommendations', [])
        
        content = []
        content.append(f"TEST REPORT SUMMARY: {report_name}")
        content.append("=" * 50)
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Summary statistics
        content.append("SUMMARY STATISTICS:")
        content.append(f"  Total Test Runs: {summary.get('total_test_runs', 0)}")
        content.append(f"  Total Test Results: {summary.get('total_test_results', 0)}")
        content.append(f"  Total Artifacts: {summary.get('total_artifacts', 0)}")
        content.append(f"  Sources: {', '.join(summary.get('sources', []))}")
        content.append(f"  Test Types: {', '.join(summary.get('test_types', []))}")
        content.append("")
        
        # Status distribution
        status_dist = analysis.get('status_distribution', {})
        if status_dist:
            content.append("TEST RESULTS DISTRIBUTION:")
            total_results = sum(status_dist.values())
            for status, count in status_dist.items():
                percentage = (count / total_results) * 100 if total_results > 0 else 0
                content.append(f"  {status.title()}: {count} ({percentage:.1f}%)")
            content.append("")
        
        # Success rates by type
        success_rates = analysis.get('success_rate_by_type', {})
        if success_rates:
            content.append("SUCCESS RATES BY TEST TYPE:")
            for test_type, rate in success_rates.items():
                content.append(f"  {test_type}: {rate:.1f}%")
            content.append("")
        
        # Top recommendations
        if recommendations:
            content.append("TOP RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:5], 1):
                content.append(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                content.append(f"     {rec['description']}")
                content.append(f"     Action: {rec['action']}")
                content.append("")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return report_path
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template for reports"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }
        h3 {
            color: #7f8c8d;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: white;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .recommendation {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }
        .recommendation.high {
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .recommendation.medium {
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }
        .recommendation.low {
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ report_name }}</h1>
        <p class="footer">Generated on {{ generated_at }}</p>
        
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Test Runs</h3>
                <div class="value">{{ summary.total_test_runs or 0 }}</div>
            </div>
            <div class="summary-card">
                <h3>Test Results</h3>
                <div class="value">{{ summary.total_test_results or 0 }}</div>
            </div>
            <div class="summary-card">
                <h3>Artifacts</h3>
                <div class="value">{{ summary.total_artifacts or 0 }}</div>
            </div>
            <div class="summary-card">
                <h3>Sources</h3>
                <div class="value">{{ summary.sources|length or 0 }}</div>
            </div>
        </div>
        
        {% if charts %}
        <h2>Visual Analysis</h2>
        {% for chart_name, chart_data in charts.items() %}
        {% if chart_data %}
        <div class="chart-container">
            <h3>{{ chart_name.replace('_', ' ').title() }}</h3>
            <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
        </div>
        {% endif %}
        {% endfor %}
        {% endif %}
        
        {% if analysis.status_distribution %}
        <h2>Test Results Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                {% set total = analysis.status_distribution.values() | sum %}
                {% for status, count in analysis.status_distribution.items() %}
                <tr>
                    <td>{{ status.title() }}</td>
                    <td>{{ count }}</td>
                    <td>{{ "%.1f"|format((count / total * 100) if total > 0 else 0) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        {% if recommendations %}
        <h2>Recommendations</h2>
        {% for rec in recommendations %}
        <div class="recommendation {{ rec.priority }}">
            <h3>{{ rec.title }}</h3>
            <p><strong>Priority:</strong> {{ rec.priority.title() }}</p>
            <p><strong>Description:</strong> {{ rec.description }}</p>
            <p><strong>Action:</strong> {{ rec.action }}</p>
        </div>
        {% endfor %}
        {% endif %}
        
        {% if include_details and test_results %}
        <h2>Detailed Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Error Message</th>
                </tr>
            </thead>
            <tbody>
                {% for result in test_results[:50] %}
                <tr>
                    <td>{{ result.test_name or 'N/A' }}</td>
                    <td>{{ result.status or 'N/A' }}</td>
                    <td>{{ result.duration or 'N/A' }}</td>
                    <td>{{ (result.error_message[:50] + '...') if result.error_message and result.error_message|length > 50 else (result.error_message or '') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <div class="footer">
            <p>Report generated by ReportGeneratorAgent</p>
        </div>
    </div>
</body>
</html>
        """