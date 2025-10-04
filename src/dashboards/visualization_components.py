"""
Visualization Components - Reusable chart components and styling
Provides consistent visualization elements across all dashboards
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

class ChartTheme(Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    DARK = "dark"
    LIGHT = "light"

class ColorPalette(Enum):
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    INFO = "#17a2b8"
    PRIMARY = "#007bff"
    SECONDARY = "#6c757d"

@dataclass
class ChartConfig:
    """Chart configuration settings"""
    theme: ChartTheme
    height: int
    width: Optional[int]
    show_toolbar: bool
    responsive: bool
    animation: bool
    title_font_size: int
    axis_font_size: int

@dataclass
class TooltipConfig:
    """Tooltip configuration"""
    enabled: bool
    format_string: str
    background_color: str
    border_color: str
    font_size: int

class VisualizationComponents:
    """
    Reusable visualization components for consistent styling
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.themes = self._initialize_themes()
        self.default_config = ChartConfig(
            theme=ChartTheme.LIGHT,
            height=400,
            width=None,
            show_toolbar=True,
            responsive=True,
            animation=True,
            title_font_size=16,
            axis_font_size=12
        )
    
    def _initialize_themes(self) -> Dict[ChartTheme, Dict[str, Any]]:
        """Initialize chart themes"""
        
        return {
            ChartTheme.EXECUTIVE: {
                "template": "plotly_white",
                "color_palette": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                "background_color": "#ffffff",
                "grid_color": "#e6e6e6",
                "text_color": "#2c3e50",
                "font_family": "Arial, sans-serif",
                "title_color": "#2c3e50",
                "axis_color": "#7f8c8d"
            },
            ChartTheme.OPERATIONAL: {
                "template": "plotly_white",
                "color_palette": ["#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6f42c1"],
                "background_color": "#f8f9fa",
                "grid_color": "#dee2e6",
                "text_color": "#495057",
                "font_family": "Arial, sans-serif",
                "title_color": "#343a40",
                "axis_color": "#6c757d"
            },
            ChartTheme.TECHNICAL: {
                "template": "plotly_white",
                "color_palette": ["#6c5ce7", "#a29bfe", "#fd79a8", "#fdcb6e", "#6c5ce7"],
                "background_color": "#ffffff",
                "grid_color": "#e9ecef",
                "text_color": "#212529",
                "font_family": "Consolas, monospace",
                "title_color": "#495057",
                "axis_color": "#6c757d"
            },
            ChartTheme.DARK: {
                "template": "plotly_dark",
                "color_palette": ["#00d4ff", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4"],
                "background_color": "#2c3e50",
                "grid_color": "#34495e",
                "text_color": "#ecf0f1",
                "font_family": "Arial, sans-serif",
                "title_color": "#ecf0f1",
                "axis_color": "#bdc3c7"
            },
            ChartTheme.LIGHT: {
                "template": "plotly_white",
                "color_palette": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"],
                "background_color": "#ffffff",
                "grid_color": "#ecf0f1",
                "text_color": "#2c3e50",
                "font_family": "Arial, sans-serif",
                "title_color": "#2c3e50",
                "axis_color": "#7f8c8d"
            }
        }
    
    def create_line_chart(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_columns: Union[str, List[str]],
        title: str,
        config: Optional[ChartConfig] = None,
        tooltip_config: Optional[TooltipConfig] = None
    ) -> go.Figure:
        """Create a line chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        fig = go.Figure()
        
        if isinstance(y_columns, str):
            y_columns = [y_columns]
        
        for i, y_col in enumerate(y_columns):
            color = theme["color_palette"][i % len(theme["color_palette"])]
            
            fig.add_trace(go.Scatter(
                x=data[x_column],
                y=data[y_col],
                mode='lines+markers',
                name=y_col.replace('_', ' ').title(),
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color),
                hovertemplate=f"<b>{y_col}</b><br>" +
                             f"{x_column}: %{{x}}<br>" +
                             f"Value: %{{y}}<br>" +
                             "<extra></extra>"
            ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_bar_chart(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
        color_column: Optional[str] = None,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a bar chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        if color_column:
            # Color by category
            fig = px.bar(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_sequence=theme["color_palette"]
            )
        else:
            # Single color
            fig = go.Figure(data=go.Bar(
                x=data[x_column],
                y=data[y_column],
                marker_color=theme["color_palette"][0],
                hovertemplate=f"<b>{x_column}</b>: %{{x}}<br>" +
                             f"<b>{y_column}</b>: %{{y}}<br>" +
                             "<extra></extra>"
            ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_pie_chart(
        self,
        data: pd.DataFrame,
        labels_column: str,
        values_column: str,
        title: str,
        config: Optional[ChartConfig] = None,
        hole_size: float = 0.0
    ) -> go.Figure:
        """Create a pie chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        fig = go.Figure(data=go.Pie(
            labels=data[labels_column],
            values=data[values_column],
            hole=hole_size,
            marker_colors=theme["color_palette"],
            hovertemplate="<b>%{label}</b><br>" +
                         "Value: %{value}<br>" +
                         "Percentage: %{percent}<br>" +
                         "<extra></extra>",
            textinfo='label+percent',
            textposition='auto'
        ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_gauge_chart(
        self,
        value: float,
        title: str,
        min_value: float = 0,
        max_value: float = 100,
        target_value: Optional[float] = None,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a gauge chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        # Determine color based on value
        if value >= 90:
            bar_color = ColorPalette.SUCCESS.value
        elif value >= 70:
            bar_color = ColorPalette.WARNING.value
        else:
            bar_color = ColorPalette.DANGER.value
        
        gauge_config = {
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': bar_color},
            'steps': [
                {'range': [min_value, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
            ],
            'borderwidth': 2,
            'bordercolor': theme["text_color"]
        }
        
        if target_value:
            gauge_config['threshold'] = {
                'line': {'color': ColorPalette.DANGER.value, 'width': 4},
                'thickness': 0.75,
                'value': target_value
            }
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'color': theme["title_color"]}},
            delta={'reference': target_value} if target_value else None,
            gauge=gauge_config
        ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_heatmap(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        z_column: str,
        title: str,
        config: Optional[ChartConfig] = None,
        colorscale: str = "RdYlGn"
    ) -> go.Figure:
        """Create a heatmap with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        # Pivot data for heatmap
        pivot_data = data.pivot(index=y_column, columns=x_column, values=z_column)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale=colorscale,
            hovertemplate=f"<b>{x_column}</b>: %{{x}}<br>" +
                         f"<b>{y_column}</b>: %{{y}}<br>" +
                         f"<b>{z_column}</b>: %{{z}}<br>" +
                         "<extra></extra>",
            showscale=True
        ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_scatter_plot(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
        size_column: Optional[str] = None,
        color_column: Optional[str] = None,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a scatter plot with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        scatter_config = {
            'x': data[x_column],
            'y': data[y_column],
            'mode': 'markers',
            'marker': {
                'color': theme["color_palette"][0],
                'size': 8
            },
            'hovertemplate': f"<b>{x_column}</b>: %{{x}}<br>" +
                           f"<b>{y_column}</b>: %{{y}}<br>" +
                           "<extra></extra>"
        }
        
        if size_column:
            scatter_config['marker']['size'] = data[size_column]
            scatter_config['marker']['sizemode'] = 'diameter'
            scatter_config['marker']['sizeref'] = 2. * max(data[size_column]) / (40.**2)
        
        if color_column:
            scatter_config['marker']['color'] = data[color_column]
            scatter_config['marker']['colorscale'] = 'Viridis'
            scatter_config['marker']['showscale'] = True
        
        fig = go.Figure(data=go.Scatter(**scatter_config))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_funnel_chart(
        self,
        data: pd.DataFrame,
        stage_column: str,
        value_column: str,
        title: str,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a funnel chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        # Sort data by value (descending)
        data_sorted = data.sort_values(value_column, ascending=False)
        
        fig = go.Figure(data=go.Funnel(
            y=data_sorted[stage_column],
            x=data_sorted[value_column],
            textinfo="value+percent initial",
            marker_color=theme["color_palette"][0],
            connector_line_color=theme["grid_color"],
            hovertemplate="<b>%{y}</b><br>" +
                         "Value: %{x}<br>" +
                         "Percentage: %{percentInitial}<br>" +
                         "<extra></extra>"
        ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_waterfall_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a waterfall chart with consistent styling"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        # Calculate cumulative values
        cumulative = [0]
        for value in values[:-1]:  # Exclude total
            cumulative.append(cumulative[-1] + value)
        
        # Determine colors (positive/negative)
        colors = []
        for value in values:
            if value > 0:
                colors.append(ColorPalette.SUCCESS.value)
            elif value < 0:
                colors.append(ColorPalette.DANGER.value)
            else:
                colors.append(ColorPalette.INFO.value)
        
        fig = go.Figure(data=go.Waterfall(
            name="",
            orientation="v",
            measure=["relative"] * (len(values) - 1) + ["total"],
            x=categories,
            y=values,
            connector={"line": {"color": theme["grid_color"]}},
            increasing={"marker": {"color": ColorPalette.SUCCESS.value}},
            decreasing={"marker": {"color": ColorPalette.DANGER.value}},
            totals={"marker": {"color": ColorPalette.INFO.value}},
            hovertemplate="<b>%{x}</b><br>" +
                         "Value: %{y}<br>" +
                         "<extra></extra>"
        ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_multi_axis_chart(
        self,
        data: pd.DataFrame,
        x_column: str,
        left_y_columns: List[str],
        right_y_columns: List[str],
        title: str,
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a chart with multiple y-axes"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add left y-axis traces
        for i, col in enumerate(left_y_columns):
            color = theme["color_palette"][i % len(theme["color_palette"])]
            fig.add_trace(
                go.Scatter(
                    x=data[x_column],
                    y=data[col],
                    name=col.replace('_', ' ').title(),
                    line=dict(color=color),
                    yaxis="y"
                ),
                secondary_y=False
            )
        
        # Add right y-axis traces
        for i, col in enumerate(right_y_columns):
            color = theme["color_palette"][(i + len(left_y_columns)) % len(theme["color_palette"])]
            fig.add_trace(
                go.Scatter(
                    x=data[x_column],
                    y=data[col],
                    name=col.replace('_', ' ').title(),
                    line=dict(color=color, dash='dash'),
                    yaxis="y2"
                ),
                secondary_y=True
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            template=theme["template"],
            font=dict(family=theme["font_family"], color=theme["text_color"]),
            height=config.height
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Primary Metrics", secondary_y=False)
        fig.update_yaxes(title_text="Secondary Metrics", secondary_y=True)
        
        return fig
    
    def create_comparison_chart(
        self,
        data: pd.DataFrame,
        category_column: str,
        value_columns: List[str],
        title: str,
        chart_type: str = "bar",
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a comparison chart (grouped bar or line)"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        fig = go.Figure()
        
        for i, col in enumerate(value_columns):
            color = theme["color_palette"][i % len(theme["color_palette"])]
            
            if chart_type == "bar":
                fig.add_trace(go.Bar(
                    x=data[category_column],
                    y=data[col],
                    name=col.replace('_', ' ').title(),
                    marker_color=color
                ))
            elif chart_type == "line":
                fig.add_trace(go.Scatter(
                    x=data[category_column],
                    y=data[col],
                    mode='lines+markers',
                    name=col.replace('_', ' ').title(),
                    line=dict(color=color)
                ))
        
        if chart_type == "bar":
            fig.update_layout(barmode='group')
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_distribution_chart(
        self,
        data: pd.DataFrame,
        value_column: str,
        title: str,
        chart_type: str = "histogram",
        config: Optional[ChartConfig] = None
    ) -> go.Figure:
        """Create a distribution chart (histogram or box plot)"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        if chart_type == "histogram":
            fig = go.Figure(data=go.Histogram(
                x=data[value_column],
                nbinsx=30,
                marker_color=theme["color_palette"][0],
                opacity=0.7,
                hovertemplate="Range: %{x}<br>" +
                             "Count: %{y}<br>" +
                             "<extra></extra>"
            ))
        elif chart_type == "box":
            fig = go.Figure(data=go.Box(
                y=data[value_column],
                marker_color=theme["color_palette"][0],
                boxmean='sd',
                hovertemplate="Value: %{y}<br>" +
                             "<extra></extra>"
            ))
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def create_time_series_chart(
        self,
        data: pd.DataFrame,
        time_column: str,
        value_columns: Union[str, List[str]],
        title: str,
        config: Optional[ChartConfig] = None,
        show_range_selector: bool = True
    ) -> go.Figure:
        """Create a time series chart with range selector"""
        
        config = config or self.default_config
        theme = self.themes[config.theme]
        
        if isinstance(value_columns, str):
            value_columns = [value_columns]
        
        fig = go.Figure()
        
        for i, col in enumerate(value_columns):
            color = theme["color_palette"][i % len(theme["color_palette"])]
            fig.add_trace(go.Scatter(
                x=data[time_column],
                y=data[col],
                mode='lines',
                name=col.replace('_', ' ').title(),
                line=dict(color=color, width=2)
            ))
        
        if show_range_selector:
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1h", step="hour", stepmode="backward"),
                            dict(count=6, label="6h", step="hour", stepmode="backward"),
                            dict(count=1, label="1d", step="day", stepmode="backward"),
                            dict(count=7, label="7d", step="day", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )
        
        self._apply_theme_to_figure(fig, theme, config, title)
        return fig
    
    def _apply_theme_to_figure(
        self,
        fig: go.Figure,
        theme: Dict[str, Any],
        config: ChartConfig,
        title: str
    ):
        """Apply theme styling to figure"""
        
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(
                    size=config.title_font_size,
                    color=theme["title_color"],
                    family=theme["font_family"]
                ),
                x=0.5,
                xanchor='center'
            ),
            template=theme["template"],
            font=dict(
                family=theme["font_family"],
                size=config.axis_font_size,
                color=theme["text_color"]
            ),
            plot_bgcolor=theme["background_color"],
            paper_bgcolor=theme["background_color"],
            height=config.height,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Update axes styling
        fig.update_xaxes(
            gridcolor=theme["grid_color"],
            linecolor=theme["axis_color"],
            tickfont=dict(color=theme["text_color"])
        )
        fig.update_yaxes(
            gridcolor=theme["grid_color"],
            linecolor=theme["axis_color"],
            tickfont=dict(color=theme["text_color"])
        )
        
        # Configure interactivity
        if not config.show_toolbar:
            fig.update_layout(
                showlegend=True,
                dragmode=False
            )
        
        if config.responsive:
            fig.update_layout(autosize=True)
        
        if config.width:
            fig.update_layout(width=config.width)
    
    def create_kpi_card(
        self,
        title: str,
        value: float,
        unit: str,
        trend: float,
        target: Optional[float] = None,
        icon: str = "📊",
        theme: ChartTheme = ChartTheme.LIGHT
    ) -> Dict[str, Any]:
        """Create a KPI card configuration"""
        
        # Determine color based on performance
        if target:
            performance = (value / target) * 100
            if performance >= 95:
                color = ColorPalette.SUCCESS.value
            elif performance >= 80:
                color = ColorPalette.WARNING.value
            else:
                color = ColorPalette.DANGER.value
        else:
            color = ColorPalette.INFO.value
        
        return {
            "title": title,
            "value": value,
            "unit": unit,
            "trend": trend,
            "target": target,
            "color": color,
            "icon": icon,
            "theme": theme.value,
            "performance": (value / target * 100) if target else None
        }
    
    def create_alert_badge(
        self,
        message: str,
        severity: str = "info",
        dismissible: bool = True
    ) -> Dict[str, Any]:
        """Create an alert badge configuration"""
        
        severity_colors = {
            "success": ColorPalette.SUCCESS.value,
            "warning": ColorPalette.WARNING.value,
            "danger": ColorPalette.DANGER.value,
            "info": ColorPalette.INFO.value
        }
        
        severity_icons = {
            "success": "✅",
            "warning": "⚠️",
            "danger": "❌",
            "info": "ℹ️"
        }
        
        return {
            "message": message,
            "severity": severity,
            "color": severity_colors.get(severity, ColorPalette.INFO.value),
            "icon": severity_icons.get(severity, "ℹ️"),
            "dismissible": dismissible,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_chart_config(self, fig: go.Figure) -> Dict[str, Any]:
        """Export chart configuration for web rendering"""
        
        return {
            "data": fig.data,
            "layout": fig.layout,
            "config": {
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": [
                    'pan2d', 'lasso2d', 'select2d', 'autoScale2d'
                ],
                "responsive": True
            }
        }


class InteractiveComponents:
    """
    Interactive dashboard components
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_filter_dropdown(
        self,
        options: List[Dict[str, Any]],
        default_value: Any = None,
        multi_select: bool = False
    ) -> Dict[str, Any]:
        """Create a filter dropdown configuration"""
        
        return {
            "type": "dropdown",
            "options": options,
            "value": default_value,
            "multi": multi_select,
            "clearable": True,
            "searchable": True
        }
    
    def create_date_range_picker(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a date range picker configuration"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        return {
            "type": "date_range_picker",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "display_format": "YYYY-MM-DD",
            "clearable": True
        }
    
    def create_slider(
        self,
        min_value: float,
        max_value: float,
        step: float = 1.0,
        default_value: Optional[float] = None,
        marks: Optional[Dict[float, str]] = None
    ) -> Dict[str, Any]:
        """Create a slider configuration"""
        
        return {
            "type": "slider",
            "min": min_value,
            "max": max_value,
            "step": step,
            "value": default_value or min_value,
            "marks": marks or {},
            "tooltip": {"placement": "top", "always_visible": False}
        }
    
    def create_toggle_switch(
        self,
        label: str,
        default_value: bool = False
    ) -> Dict[str, Any]:
        """Create a toggle switch configuration"""
        
        return {
            "type": "toggle",
            "label": label,
            "value": default_value
        }
    
    def create_refresh_button(
        self,
        interval_seconds: int = 300,
        auto_refresh: bool = True
    ) -> Dict[str, Any]:
        """Create a refresh button configuration"""
        
        return {
            "type": "refresh_button",
            "interval": interval_seconds,
            "auto_refresh": auto_refresh,
            "last_updated": datetime.now().isoformat()
        }


# Utility functions for chart data processing
def prepare_time_series_data(
    data: pd.DataFrame,
    time_column: str,
    value_columns: List[str],
    resample_freq: Optional[str] = None
) -> pd.DataFrame:
    """Prepare time series data for visualization"""
    
    # Ensure time column is datetime
    data[time_column] = pd.to_datetime(data[time_column])
    
    # Set time column as index
    data_indexed = data.set_index(time_column)
    
    # Resample if requested
    if resample_freq:
        data_indexed = data_indexed[value_columns].resample(resample_freq).mean()
        data_indexed = data_indexed.reset_index()
    
    return data_indexed

def calculate_trend(values: List[float], periods: int = 2) -> float:
    """Calculate trend percentage change"""
    
    if len(values) < periods:
        return 0.0
    
    recent_avg = sum(values[-periods:]) / periods
    previous_avg = sum(values[-periods*2:-periods]) / periods
    
    if previous_avg == 0:
        return 0.0
    
    return ((recent_avg - previous_avg) / previous_avg) * 100

def format_number(value: float, unit: str = "") -> str:
    """Format numbers for display"""
    
    if abs(value) >= 1e9:
        return f"{value/1e9:.1f}B{unit}"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.1f}M{unit}"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.1f}K{unit}"
    else:
        return f"{value:.1f}{unit}"