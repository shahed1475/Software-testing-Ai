"""
Visualization Engine Module

This module provides comprehensive visualization capabilities for
functional testing, security scanning, and compliance assessment results.
It generates charts, graphs, and interactive visualizations.
"""

import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import math


class ChartType(Enum):
    """Types of charts"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    RADAR = "radar"
    TREEMAP = "treemap"
    TIMELINE = "timeline"
    HISTOGRAM = "histogram"


class VisualizationTheme(Enum):
    """Visualization themes"""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    PROFESSIONAL = "professional"
    COLORFUL = "colorful"


class ChartSize(Enum):
    """Chart sizes"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


@dataclass
class ChartConfig:
    """Chart configuration"""
    chart_type: ChartType
    title: str
    width: int = 800
    height: int = 400
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
    show_legend: bool = True
    show_grid: bool = True
    interactive: bool = True
    colors: Optional[List[str]] = None
    font_size: int = 12
    margin: Dict[str, int] = field(default_factory=lambda: {"top": 20, "right": 20, "bottom": 40, "left": 40})


@dataclass
class ChartData:
    """Chart data structure"""
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Visualization:
    """Visualization result"""
    chart_id: str
    chart_type: ChartType
    title: str
    svg_content: str
    html_content: str
    config: ChartConfig
    data: ChartData
    generated_at: datetime = field(default_factory=datetime.now)


class VisualizationEngine:
    """
    Comprehensive visualization engine for test results
    """
    
    def __init__(self, theme: VisualizationTheme = VisualizationTheme.DEFAULT):
        """Initialize the visualization engine"""
        self.theme = theme
        self.color_palettes = self._initialize_color_palettes()
        self.chart_counter = 0
    
    def create_trend_chart(
        self,
        data: Dict[str, List[float]],
        title: str = "Trend Analysis",
        time_labels: Optional[List[str]] = None
    ) -> Visualization:
        """
        Create a line chart for trend analysis
        """
        config = ChartConfig(
            chart_type=ChartType.LINE,
            title=title,
            width=900,
            height=400
        )
        
        # Prepare data
        chart_data = ChartData()
        
        if time_labels:
            chart_data.labels = time_labels
        else:
            # Generate default time labels
            max_length = max(len(values) for values in data.values()) if data else 0
            chart_data.labels = [f"Point {i+1}" for i in range(max_length)]
        
        # Create datasets for each metric
        colors = self._get_color_palette(len(data))
        
        for i, (metric_name, values) in enumerate(data.items()):
            dataset = {
                "label": metric_name,
                "data": values,
                "borderColor": colors[i % len(colors)],
                "backgroundColor": self._add_transparency(colors[i % len(colors)], 0.2),
                "fill": False,
                "tension": 0.1
            }
            chart_data.datasets.append(dataset)
        
        # Generate SVG
        svg_content = self._generate_line_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.LINE,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_performance_dashboard(
        self,
        performance_data: Dict[str, Any]
    ) -> List[Visualization]:
        """
        Create a comprehensive performance dashboard
        """
        visualizations = []
        
        # 1. Performance Score Gauge
        if 'performance_score' in performance_data:
            gauge_viz = self.create_gauge_chart(
                value=performance_data['performance_score'],
                title="Overall Performance Score",
                min_value=0,
                max_value=100,
                thresholds=[30, 60, 80]
            )
            visualizations.append(gauge_viz)
        
        # 2. Execution Time Distribution
        if 'execution_times' in performance_data:
            histogram_viz = self.create_histogram(
                data=performance_data['execution_times'],
                title="Execution Time Distribution",
                bins=20
            )
            visualizations.append(histogram_viz)
        
        # 3. Success Rate Pie Chart
        if 'success_rate' in performance_data and 'error_rate' in performance_data:
            pie_viz = self.create_pie_chart(
                data={
                    "Successful": performance_data['success_rate'] * 100,
                    "Failed": performance_data['error_rate'] * 100
                },
                title="Test Success Rate"
            )
            visualizations.append(pie_viz)
        
        # 4. Performance Metrics Bar Chart
        metrics = {}
        for key in ['average_execution_time', 'median_execution_time', 'p95_execution_time']:
            if key in performance_data:
                metrics[key.replace('_', ' ').title()] = performance_data[key]
        
        if metrics:
            bar_viz = self.create_bar_chart(
                data=metrics,
                title="Performance Metrics Comparison"
            )
            visualizations.append(bar_viz)
        
        return visualizations
    
    def create_security_dashboard(
        self,
        security_data: Dict[str, Any]
    ) -> List[Visualization]:
        """
        Create a comprehensive security dashboard
        """
        visualizations = []
        
        # 1. Vulnerability Severity Distribution
        if 'vulnerabilities_by_severity' in security_data:
            pie_viz = self.create_pie_chart(
                data=security_data['vulnerabilities_by_severity'],
                title="Vulnerabilities by Severity"
            )
            visualizations.append(pie_viz)
        
        # 2. Security Score Gauge
        if 'security_score' in security_data:
            gauge_viz = self.create_gauge_chart(
                value=security_data['security_score'] * 100,
                title="Security Posture Score",
                min_value=0,
                max_value=100,
                thresholds=[40, 70, 90]
            )
            visualizations.append(gauge_viz)
        
        # 3. Vulnerability Trends
        if 'vulnerability_trends' in security_data:
            trend_viz = self.create_trend_chart(
                data=security_data['vulnerability_trends'],
                title="Vulnerability Trends Over Time"
            )
            visualizations.append(trend_viz)
        
        # 4. Risk Assessment Heatmap
        if 'risk_matrix' in security_data:
            heatmap_viz = self.create_heatmap(
                data=security_data['risk_matrix'],
                title="Security Risk Assessment Matrix"
            )
            visualizations.append(heatmap_viz)
        
        return visualizations
    
    def create_compliance_dashboard(
        self,
        compliance_data: Dict[str, Any]
    ) -> List[Visualization]:
        """
        Create a comprehensive compliance dashboard
        """
        visualizations = []
        
        # 1. Compliance Score by Standard
        if 'compliance_scores' in compliance_data:
            bar_viz = self.create_bar_chart(
                data=compliance_data['compliance_scores'],
                title="Compliance Scores by Standard"
            )
            visualizations.append(bar_viz)
        
        # 2. Overall Compliance Gauge
        if 'overall_compliance' in compliance_data:
            gauge_viz = self.create_gauge_chart(
                value=compliance_data['overall_compliance'] * 100,
                title="Overall Compliance Level",
                min_value=0,
                max_value=100,
                thresholds=[60, 80, 95]
            )
            visualizations.append(gauge_viz)
        
        # 3. Compliance Status Distribution
        if 'status_distribution' in compliance_data:
            pie_viz = self.create_pie_chart(
                data=compliance_data['status_distribution'],
                title="Compliance Check Status Distribution"
            )
            visualizations.append(pie_viz)
        
        # 4. Compliance Trends
        if 'compliance_trends' in compliance_data:
            trend_viz = self.create_trend_chart(
                data=compliance_data['compliance_trends'],
                title="Compliance Trends Over Time"
            )
            visualizations.append(trend_viz)
        
        return visualizations
    
    def create_unified_dashboard(
        self,
        unified_data: Dict[str, Any]
    ) -> List[Visualization]:
        """
        Create a unified dashboard combining all domains
        """
        visualizations = []
        
        # 1. Overall Quality Radar Chart
        if 'quality_metrics' in unified_data:
            radar_viz = self.create_radar_chart(
                data=unified_data['quality_metrics'],
                title="Overall Quality Assessment"
            )
            visualizations.append(radar_viz)
        
        # 2. Domain Comparison Bar Chart
        if 'domain_scores' in unified_data:
            bar_viz = self.create_bar_chart(
                data=unified_data['domain_scores'],
                title="Quality Scores by Domain"
            )
            visualizations.append(bar_viz)
        
        # 3. Risk Level Distribution
        if 'risk_distribution' in unified_data:
            pie_viz = self.create_pie_chart(
                data=unified_data['risk_distribution'],
                title="Risk Level Distribution"
            )
            visualizations.append(pie_viz)
        
        # 4. Quality Trends Timeline
        if 'quality_trends' in unified_data:
            timeline_viz = self.create_timeline_chart(
                data=unified_data['quality_trends'],
                title="Quality Metrics Timeline"
            )
            visualizations.append(timeline_viz)
        
        return visualizations
    
    def create_pie_chart(
        self,
        data: Dict[str, float],
        title: str = "Pie Chart"
    ) -> Visualization:
        """
        Create a pie chart
        """
        config = ChartConfig(
            chart_type=ChartType.PIE,
            title=title,
            width=500,
            height=500
        )
        
        chart_data = ChartData()
        chart_data.labels = list(data.keys())
        
        colors = self._get_color_palette(len(data))
        
        dataset = {
            "data": list(data.values()),
            "backgroundColor": colors,
            "borderColor": "#ffffff",
            "borderWidth": 2
        }
        chart_data.datasets.append(dataset)
        
        svg_content = self._generate_pie_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.PIE,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "Bar Chart"
    ) -> Visualization:
        """
        Create a bar chart
        """
        config = ChartConfig(
            chart_type=ChartType.BAR,
            title=title,
            width=800,
            height=400
        )
        
        chart_data = ChartData()
        chart_data.labels = list(data.keys())
        
        colors = self._get_color_palette(len(data))
        
        dataset = {
            "data": list(data.values()),
            "backgroundColor": colors,
            "borderColor": colors,
            "borderWidth": 1
        }
        chart_data.datasets.append(dataset)
        
        svg_content = self._generate_bar_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.BAR,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_gauge_chart(
        self,
        value: float,
        title: str = "Gauge Chart",
        min_value: float = 0,
        max_value: float = 100,
        thresholds: Optional[List[float]] = None
    ) -> Visualization:
        """
        Create a gauge chart
        """
        config = ChartConfig(
            chart_type=ChartType.GAUGE,
            title=title,
            width=400,
            height=300
        )
        
        chart_data = ChartData()
        chart_data.metadata = {
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "thresholds": thresholds or [30, 60, 80]
        }
        
        svg_content = self._generate_gauge_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.GAUGE,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_radar_chart(
        self,
        data: Dict[str, float],
        title: str = "Radar Chart"
    ) -> Visualization:
        """
        Create a radar chart
        """
        config = ChartConfig(
            chart_type=ChartType.RADAR,
            title=title,
            width=500,
            height=500
        )
        
        chart_data = ChartData()
        chart_data.labels = list(data.keys())
        
        dataset = {
            "data": list(data.values()),
            "borderColor": self._get_color_palette(1)[0],
            "backgroundColor": self._add_transparency(self._get_color_palette(1)[0], 0.2),
            "pointBackgroundColor": self._get_color_palette(1)[0],
            "pointBorderColor": "#ffffff",
            "pointHoverBackgroundColor": "#ffffff",
            "pointHoverBorderColor": self._get_color_palette(1)[0]
        }
        chart_data.datasets.append(dataset)
        
        svg_content = self._generate_radar_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.RADAR,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_heatmap(
        self,
        data: List[List[float]],
        title: str = "Heatmap",
        x_labels: Optional[List[str]] = None,
        y_labels: Optional[List[str]] = None
    ) -> Visualization:
        """
        Create a heatmap
        """
        config = ChartConfig(
            chart_type=ChartType.HEATMAP,
            title=title,
            width=600,
            height=400
        )
        
        chart_data = ChartData()
        chart_data.metadata = {
            "data": data,
            "x_labels": x_labels or [f"X{i}" for i in range(len(data[0]) if data else 0)],
            "y_labels": y_labels or [f"Y{i}" for i in range(len(data))]
        }
        
        svg_content = self._generate_heatmap_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.HEATMAP,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_histogram(
        self,
        data: List[float],
        title: str = "Histogram",
        bins: int = 10
    ) -> Visualization:
        """
        Create a histogram
        """
        config = ChartConfig(
            chart_type=ChartType.HISTOGRAM,
            title=title,
            width=800,
            height=400
        )
        
        # Calculate histogram bins
        min_val = min(data) if data else 0
        max_val = max(data) if data else 1
        bin_width = (max_val - min_val) / bins
        
        bin_counts = [0] * bins
        bin_labels = []
        
        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width
            bin_labels.append(f"{bin_start:.2f}-{bin_end:.2f}")
            
            # Count values in this bin
            for value in data:
                if bin_start <= value < bin_end or (i == bins - 1 and value == bin_end):
                    bin_counts[i] += 1
        
        chart_data = ChartData()
        chart_data.labels = bin_labels
        
        dataset = {
            "data": bin_counts,
            "backgroundColor": self._get_color_palette(1)[0],
            "borderColor": self._get_color_palette(1)[0],
            "borderWidth": 1
        }
        chart_data.datasets.append(dataset)
        
        svg_content = self._generate_bar_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.HISTOGRAM,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_timeline_chart(
        self,
        data: Dict[str, List[Tuple[datetime, float]]],
        title: str = "Timeline Chart"
    ) -> Visualization:
        """
        Create a timeline chart
        """
        config = ChartConfig(
            chart_type=ChartType.TIMELINE,
            title=title,
            width=1000,
            height=400
        )
        
        chart_data = ChartData()
        
        # Convert datetime data to chart format
        all_dates = set()
        for series_data in data.values():
            for date, _ in series_data:
                all_dates.add(date)
        
        sorted_dates = sorted(all_dates)
        chart_data.labels = [date.strftime("%Y-%m-%d") for date in sorted_dates]
        
        colors = self._get_color_palette(len(data))
        
        for i, (series_name, series_data) in enumerate(data.items()):
            # Create a mapping of dates to values
            date_value_map = {date: value for date, value in series_data}
            
            # Fill in values for all dates (use None for missing dates)
            values = []
            for date in sorted_dates:
                values.append(date_value_map.get(date))
            
            dataset = {
                "label": series_name,
                "data": values,
                "borderColor": colors[i % len(colors)],
                "backgroundColor": self._add_transparency(colors[i % len(colors)], 0.2),
                "fill": False,
                "tension": 0.1
            }
            chart_data.datasets.append(dataset)
        
        svg_content = self._generate_line_chart_svg(chart_data, config)
        html_content = self._wrap_svg_in_html(svg_content, config)
        
        return Visualization(
            chart_id=self._generate_chart_id(),
            chart_type=ChartType.TIMELINE,
            title=title,
            svg_content=svg_content,
            html_content=html_content,
            config=config,
            data=chart_data
        )
    
    def create_custom_dashboard(
        self,
        visualizations: List[Visualization],
        title: str = "Custom Dashboard",
        layout: str = "grid"
    ) -> str:
        """
        Create a custom dashboard with multiple visualizations
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>{title}</title>",
            "<style>",
            self._get_dashboard_css(layout),
            "</style>",
            "</head>",
            "<body>",
            f"<div class='dashboard-header'><h1>{title}</h1></div>",
            "<div class='dashboard-container'>"
        ]
        
        for viz in visualizations:
            html_parts.append(f"<div class='chart-container'>{viz.html_content}</div>")
        
        html_parts.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    # Helper methods for SVG generation
    
    def _generate_line_chart_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for line chart"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        # Chart area
        chart_left = config.margin["left"]
        chart_top = title_y + 20
        chart_width = config.width - config.margin["left"] - config.margin["right"]
        chart_height = config.height - chart_top - config.margin["bottom"]
        
        if not data.datasets or not data.labels:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Calculate scales
        all_values = []
        for dataset in data.datasets:
            all_values.extend([v for v in dataset["data"] if v is not None])
        
        if not all_values:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        min_val = min(all_values)
        max_val = max(all_values)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Draw grid lines
        if config.show_grid:
            for i in range(5):
                y = chart_top + (i * chart_height / 4)
                svg_parts.append(f'<line x1="{chart_left}" y1="{y}" x2="{chart_left + chart_width}" y2="{y}" stroke="#e0e0e0" stroke-width="1"/>')
        
        # Draw axes
        svg_parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="black" stroke-width="2"/>')
        svg_parts.append(f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="black" stroke-width="2"/>')
        
        # Draw data lines
        for dataset in data.datasets:
            points = []
            for i, value in enumerate(dataset["data"]):
                if value is not None:
                    x = chart_left + (i * chart_width / (len(data.labels) - 1)) if len(data.labels) > 1 else chart_left + chart_width / 2
                    y = chart_top + chart_height - ((value - min_val) / val_range * chart_height)
                    points.append(f"{x},{y}")
            
            if len(points) > 1:
                path = f'M {" L ".join(points)}'
                svg_parts.append(f'<path d="{path}" stroke="{dataset["borderColor"]}" stroke-width="2" fill="none"/>')
                
                # Add data points
                for point in points:
                    x, y = point.split(',')
                    svg_parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{dataset["borderColor"]}"/>')
        
        # Add legend
        if config.show_legend and len(data.datasets) > 1:
            legend_y = chart_top + chart_height + 30
            legend_x = chart_left
            
            for i, dataset in enumerate(data.datasets):
                legend_item_x = legend_x + (i * 150)
                svg_parts.append(f'<rect x="{legend_item_x}" y="{legend_y}" width="15" height="15" fill="{dataset["borderColor"]}"/>')
                svg_parts.append(f'<text x="{legend_item_x + 20}" y="{legend_y + 12}" font-size="12">{dataset["label"]}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_pie_chart_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for pie chart"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        if not data.datasets or not data.datasets[0]["data"]:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Calculate pie chart
        values = data.datasets[0]["data"]
        colors = data.datasets[0]["backgroundColor"]
        total = sum(values)
        
        if total == 0:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        center_x = config.width // 2
        center_y = (config.height + title_y) // 2
        radius = min(config.width, config.height - title_y - 40) // 3
        
        current_angle = -90  # Start at top
        
        for i, (value, color) in enumerate(zip(values, colors)):
            if value == 0:
                continue
                
            angle = (value / total) * 360
            end_angle = current_angle + angle
            
            # Calculate arc path
            start_x = center_x + radius * math.cos(math.radians(current_angle))
            start_y = center_y + radius * math.sin(math.radians(current_angle))
            end_x = center_x + radius * math.cos(math.radians(end_angle))
            end_y = center_y + radius * math.sin(math.radians(end_angle))
            
            large_arc = 1 if angle > 180 else 0
            
            path = f'M {center_x} {center_y} L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y} Z'
            svg_parts.append(f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2"/>')
            
            # Add label
            label_angle = current_angle + angle / 2
            label_x = center_x + (radius + 20) * math.cos(math.radians(label_angle))
            label_y = center_y + (radius + 20) * math.sin(math.radians(label_angle))
            
            percentage = (value / total) * 100
            label_text = f"{data.labels[i]}: {percentage:.1f}%"
            svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="10">{label_text}</text>')
            
            current_angle = end_angle
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_bar_chart_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for bar chart"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        if not data.datasets or not data.datasets[0]["data"] or not data.labels:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Chart area
        chart_left = config.margin["left"]
        chart_top = title_y + 20
        chart_width = config.width - config.margin["left"] - config.margin["right"]
        chart_height = config.height - chart_top - config.margin["bottom"]
        
        values = data.datasets[0]["data"]
        colors = data.datasets[0]["backgroundColor"]
        
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Draw axes
        svg_parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="black" stroke-width="2"/>')
        svg_parts.append(f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="black" stroke-width="2"/>')
        
        # Draw bars
        bar_width = chart_width / len(values) * 0.8
        bar_spacing = chart_width / len(values)
        
        for i, (value, color) in enumerate(zip(values, colors)):
            bar_height = (value - min_val) / val_range * chart_height
            bar_x = chart_left + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_y = chart_top + chart_height - bar_height
            
            svg_parts.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" fill="{color}" stroke="none"/>')
            
            # Add value label on top of bar
            label_x = bar_x + bar_width / 2
            label_y = bar_y - 5
            svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="10">{value:.1f}</text>')
            
            # Add category label below bar
            category_y = chart_top + chart_height + 15
            svg_parts.append(f'<text x="{label_x}" y="{category_y}" text-anchor="middle" font-size="10">{data.labels[i]}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_gauge_chart_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for gauge chart"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        # Gauge parameters
        center_x = config.width // 2
        center_y = config.height - 50
        radius = min(config.width, config.height - title_y - 50) // 3
        
        value = data.metadata["value"]
        min_val = data.metadata["min_value"]
        max_val = data.metadata["max_value"]
        thresholds = data.metadata["thresholds"]
        
        # Draw gauge background arc
        svg_parts.append(f'<path d="M {center_x - radius} {center_y} A {radius} {radius} 0 0 1 {center_x + radius} {center_y}" stroke="#e0e0e0" stroke-width="20" fill="none"/>')
        
        # Draw colored segments based on thresholds
        colors = ["#ff4444", "#ffaa00", "#44ff44", "#00aa44"]  # Red, Orange, Light Green, Dark Green
        
        prev_threshold = min_val
        for i, threshold in enumerate(thresholds + [max_val]):
            if i >= len(colors):
                break
                
            # Calculate angles for this segment
            start_angle = 180 - ((prev_threshold - min_val) / (max_val - min_val)) * 180
            end_angle = 180 - ((threshold - min_val) / (max_val - min_val)) * 180
            
            start_x = center_x + radius * math.cos(math.radians(start_angle))
            start_y = center_y + radius * math.sin(math.radians(start_angle))
            end_x = center_x + radius * math.cos(math.radians(end_angle))
            end_y = center_y + radius * math.sin(math.radians(end_angle))
            
            large_arc = 1 if (start_angle - end_angle) > 180 else 0
            
            svg_parts.append(f'<path d="M {start_x} {start_y} A {radius} {radius} 0 {large_arc} 0 {end_x} {end_y}" stroke="{colors[i]}" stroke-width="20" fill="none"/>')
            
            prev_threshold = threshold
        
        # Draw needle
        needle_angle = 180 - ((value - min_val) / (max_val - min_val)) * 180
        needle_x = center_x + (radius - 10) * math.cos(math.radians(needle_angle))
        needle_y = center_y + (radius - 10) * math.sin(math.radians(needle_angle))
        
        svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{needle_x}" y2="{needle_y}" stroke="black" stroke-width="3"/>')
        svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="8" fill="black"/>')
        
        # Add value text
        svg_parts.append(f'<text x="{center_x}" y="{center_y + 30}" text-anchor="middle" font-size="18" font-weight="bold">{value:.1f}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_radar_chart_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for radar chart"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        if not data.datasets or not data.datasets[0]["data"] or not data.labels:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Radar chart parameters
        center_x = config.width // 2
        center_y = (config.height + title_y) // 2
        radius = min(config.width, config.height - title_y - 40) // 3
        
        values = data.datasets[0]["data"]
        labels = data.labels
        num_axes = len(labels)
        
        if num_axes == 0:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Draw radar grid
        for level in range(1, 6):  # 5 levels
            level_radius = radius * level / 5
            points = []
            
            for i in range(num_axes):
                angle = (i * 360 / num_axes) - 90  # Start from top
                x = center_x + level_radius * math.cos(math.radians(angle))
                y = center_y + level_radius * math.sin(math.radians(angle))
                points.append(f"{x},{y}")
            
            if points:
                polygon_path = " ".join(points)
                svg_parts.append(f'<polygon points="{polygon_path}" stroke="#e0e0e0" stroke-width="1" fill="none"/>')
        
        # Draw axes
        for i in range(num_axes):
            angle = (i * 360 / num_axes) - 90
            end_x = center_x + radius * math.cos(math.radians(angle))
            end_y = center_y + radius * math.sin(math.radians(angle))
            
            svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{end_x}" y2="{end_y}" stroke="#e0e0e0" stroke-width="1"/>')
            
            # Add axis labels
            label_x = center_x + (radius + 20) * math.cos(math.radians(angle))
            label_y = center_y + (radius + 20) * math.sin(math.radians(angle))
            svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="10">{labels[i]}</text>')
        
        # Draw data polygon
        max_val = max(values) if values else 1
        data_points = []
        
        for i, value in enumerate(values):
            angle = (i * 360 / num_axes) - 90
            normalized_value = value / max_val if max_val > 0 else 0
            point_radius = radius * normalized_value
            
            x = center_x + point_radius * math.cos(math.radians(angle))
            y = center_y + point_radius * math.sin(math.radians(angle))
            data_points.append(f"{x},{y}")
        
        if data_points:
            polygon_path = " ".join(data_points)
            dataset = data.datasets[0]
            svg_parts.append(f'<polygon points="{polygon_path}" stroke="{dataset["borderColor"]}" stroke-width="2" fill="{dataset["backgroundColor"]}"/>')
            
            # Add data points
            for point in data_points:
                x, y = point.split(',')
                svg_parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{dataset["borderColor"]}"/>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_heatmap_svg(self, data: ChartData, config: ChartConfig) -> str:
        """Generate SVG for heatmap"""
        
        svg_parts = [
            f'<svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">',
            f'<title>{config.title}</title>'
        ]
        
        # Add background
        svg_parts.append(f'<rect width="{config.width}" height="{config.height}" fill="white" stroke="none"/>')
        
        # Add title
        title_y = 30
        svg_parts.append(f'<text x="{config.width//2}" y="{title_y}" text-anchor="middle" font-size="16" font-weight="bold">{config.title}</text>')
        
        matrix_data = data.metadata["data"]
        x_labels = data.metadata["x_labels"]
        y_labels = data.metadata["y_labels"]
        
        if not matrix_data or not matrix_data[0]:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Calculate cell dimensions
        chart_left = 80
        chart_top = title_y + 40
        chart_width = config.width - chart_left - 40
        chart_height = config.height - chart_top - 60
        
        rows = len(matrix_data)
        cols = len(matrix_data[0])
        
        cell_width = chart_width / cols
        cell_height = chart_height / rows
        
        # Find min/max values for color scaling
        all_values = [val for row in matrix_data for val in row]
        min_val = min(all_values) if all_values else 0
        max_val = max(all_values) if all_values else 1
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Draw heatmap cells
        for i, row in enumerate(matrix_data):
            for j, value in enumerate(row):
                x = chart_left + j * cell_width
                y = chart_top + i * cell_height
                
                # Calculate color intensity
                intensity = (value - min_val) / val_range if val_range > 0 else 0
                color = self._get_heatmap_color(intensity)
                
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_width}" height="{cell_height}" fill="{color}" stroke="white" stroke-width="1"/>')
                
                # Add value text
                text_x = x + cell_width / 2
                text_y = y + cell_height / 2 + 4
                svg_parts.append(f'<text x="{text_x}" y="{text_y}" text-anchor="middle" font-size="10" fill="white">{value:.2f}</text>')
        
        # Add axis labels
        for i, label in enumerate(x_labels):
            x = chart_left + (i + 0.5) * cell_width
            y = chart_top + chart_height + 20
            svg_parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="10">{label}</text>')
        
        for i, label in enumerate(y_labels):
            x = chart_left - 10
            y = chart_top + (i + 0.5) * cell_height + 4
            svg_parts.append(f'<text x="{x}" y="{y}" text-anchor="end" font-size="10">{label}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _wrap_svg_in_html(self, svg_content: str, config: ChartConfig) -> str:
        """Wrap SVG content in HTML"""
        
        return f"""
        <div class="chart-wrapper" style="text-align: center; margin: 20px;">
            {svg_content}
        </div>
        """
    
    def _get_dashboard_css(self, layout: str) -> str:
        """Get CSS for dashboard layout"""
        
        base_css = """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .dashboard-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .dashboard-header h1 {
            margin: 0;
            color: #333;
        }
        
        .chart-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 20px;
        }
        """
        
        if layout == "grid":
            layout_css = """
            .dashboard-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
            }
            """
        elif layout == "vertical":
            layout_css = """
            .dashboard-container {
                display: flex;
                flex-direction: column;
            }
            """
        else:  # horizontal
            layout_css = """
            .dashboard-container {
                display: flex;
                flex-wrap: wrap;
            }
            """
        
        return base_css + layout_css
    
    def _initialize_color_palettes(self) -> Dict[str, List[str]]:
        """Initialize color palettes for different themes"""
        
        return {
            "default": [
                "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                "#1abc9c", "#34495e", "#e67e22", "#95a5a6", "#f1c40f"
            ],
            "dark": [
                "#2980b9", "#c0392b", "#27ae60", "#d68910", "#8e44ad",
                "#16a085", "#2c3e50", "#d35400", "#7f8c8d", "#f4d03f"
            ],
            "light": [
                "#5dade2", "#ec7063", "#58d68d", "#f7dc6f", "#bb8fce",
                "#76d7c4", "#85929e", "#f8c471", "#aeb6bf", "#f9e79f"
            ],
            "professional": [
                "#2c3e50", "#34495e", "#7f8c8d", "#95a5a6", "#bdc3c7",
                "#ecf0f1", "#3498db", "#2980b9", "#1abc9c", "#16a085"
            ],
            "colorful": [
                "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7",
                "#dda0dd", "#98d8c8", "#f7dc6f", "#bb8fce", "#85c1e9"
            ]
        }
    
    def _get_color_palette(self, count: int) -> List[str]:
        """Get color palette for the current theme"""
        
        palette = self.color_palettes.get(self.theme.value, self.color_palettes["default"])
        
        # Repeat colors if we need more than available
        colors = []
        for i in range(count):
            colors.append(palette[i % len(palette)])
        
        return colors
    
    def _add_transparency(self, color: str, alpha: float) -> str:
        """Add transparency to a color"""
        
        if color.startswith('#'):
            # Convert hex to rgba
            hex_color = color.lstrip('#')
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return f"rgba({r}, {g}, {b}, {alpha})"
        
        return color  # Return original if can't convert
    
    def _get_heatmap_color(self, intensity: float) -> str:
        """Get color for heatmap based on intensity (0-1)"""
        
        # Create a gradient from blue (low) to red (high)
        if intensity <= 0.25:
            # Blue to cyan
            r = 0
            g = int(255 * intensity * 4)
            b = 255
        elif intensity <= 0.5:
            # Cyan to green
            r = 0
            g = 255
            b = int(255 * (1 - (intensity - 0.25) * 4))
        elif intensity <= 0.75:
            # Green to yellow
            r = int(255 * (intensity - 0.5) * 4)
            g = 255
            b = 0
        else:
            # Yellow to red
            r = 255
            g = int(255 * (1 - (intensity - 0.75) * 4))
            b = 0
        
        return f"rgb({r}, {g}, {b})"
    
    def _generate_chart_id(self) -> str:
        """Generate unique chart ID"""
        
        self.chart_counter += 1
        return f"chart_{self.chart_counter}_{int(datetime.now().timestamp())}"


# Utility functions for visualization

def create_performance_visualization(
    performance_data: Dict[str, Any],
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
) -> List[Visualization]:
    """Create performance visualizations"""
    
    engine = VisualizationEngine(theme)
    return engine.create_performance_dashboard(performance_data)


def create_security_visualization(
    security_data: Dict[str, Any],
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
) -> List[Visualization]:
    """Create security visualizations"""
    
    engine = VisualizationEngine(theme)
    return engine.create_security_dashboard(security_data)


def create_compliance_visualization(
    compliance_data: Dict[str, Any],
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
) -> List[Visualization]:
    """Create compliance visualizations"""
    
    engine = VisualizationEngine(theme)
    return engine.create_compliance_dashboard(compliance_data)


def create_unified_visualization(
    unified_data: Dict[str, Any],
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
) -> List[Visualization]:
    """Create unified dashboard visualizations"""
    
    engine = VisualizationEngine(theme)
    return engine.create_unified_dashboard(unified_data)


def generate_executive_dashboard(
    performance_data: Optional[Dict[str, Any]] = None,
    security_data: Optional[Dict[str, Any]] = None,
    compliance_data: Optional[Dict[str, Any]] = None,
    unified_data: Optional[Dict[str, Any]] = None,
    theme: VisualizationTheme = VisualizationTheme.PROFESSIONAL
) -> str:
    """Generate executive dashboard HTML"""
    
    engine = VisualizationEngine(theme)
    visualizations = []
    
    if unified_data:
        visualizations.extend(engine.create_unified_dashboard(unified_data))
    
    if performance_data:
        visualizations.extend(engine.create_performance_dashboard(performance_data))
    
    if security_data:
        visualizations.extend(engine.create_security_dashboard(security_data))
    
    if compliance_data:
        visualizations.extend(engine.create_compliance_dashboard(compliance_data))
    
    return engine.create_custom_dashboard(
        visualizations=visualizations,
        title="Executive Testing Dashboard",
        layout="grid"
    )