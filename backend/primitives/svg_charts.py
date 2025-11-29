from backend.primitives.types import TimeSeriesPoint
from typing import List
import math

def generate_simple_line_chart_svg(
    snowball_series: List[TimeSeriesPoint],
    avalanche_series: List[TimeSeriesPoint],
    width: int = 800,
    height: int = 300,
    padding: int = 40
) -> str:
    """
    Generates a simple SVG line chart comparing Snowball vs Avalanche strategies.
    Returns the SVG string.
    """
    if not snowball_series or not avalanche_series:
        return "<svg></svg>"

    # Combine series to find extents
    all_points = snowball_series + avalanche_series
    
    # Helper to get attributes whether obj or dict
    def get_val(item, key):
        return item.get(key) if isinstance(item, dict) else getattr(item, key)

    dates = [get_val(p, 'date') for p in all_points]
    values = [get_val(p, 'value') for p in all_points]

    if not dates or not values:
        return "<svg></svg>"

    min_date = min(dates)
    max_date = max(dates)
    min_val = 0 # Always start Y at 0
    max_val = max(values) * 1.1 # Add 10% headroom

    # Time span in seconds/ticks for X scaling
    total_time = (max_date - min_date).total_seconds()
    if total_time == 0: total_time = 1 # Avoid div/0

    def scale_x(date_obj):
        ratio = (date_obj - min_date).total_seconds() / total_time
        return padding + ratio * (width - 2 * padding)

    def scale_y(val):
        ratio = (val - min_val) / (max_val - min_val) if max_val > min_val else 0
        return height - padding - (ratio * (height - 2 * padding))

    # Generate Path Data
    def get_path_d(series):
        path = []
        for i, p in enumerate(series):
            x = scale_x(get_val(p, 'date'))
            y = scale_y(get_val(p, 'value'))
            cmd = "M" if i == 0 else "L"
            path.append(f"{cmd} {x:.1f} {y:.1f}")
        return "".join(path)

    path_snowball = get_path_d(snowball_series)
    path_avalanche = get_path_d(avalanche_series)

    # Format max value for label
    y_max_label = f"${max_val/1000:.0f}k"
    
    # Start/End Year Labels
    start_year = min_date.year
    end_year = max_date.year

    svg = f"""
    <svg width="100%" height="100%" viewBox="0 0 {width} {height}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Axes -->
        <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#333" stroke-width="1" />
        <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#333" stroke-width="1" />
        
        <!-- Labels -->
        <text x="{padding - 5}" y="{padding}" fill="#666" font-size="12" text-anchor="end" alignment-baseline="middle">{y_max_label}</text>
        <text x="{padding}" y="{height-padding+15}" fill="#666" font-size="12" text-anchor="middle">{start_year}</text>
        <text x="{width-padding}" y="{height-padding+15}" fill="#666" font-size="12" text-anchor="middle">{end_year}</text>

        <!-- Snowball Line (Red) -->
        <path d="{path_snowball}" fill="none" stroke="#ff453a" stroke-width="3" />
        
        <!-- Avalanche Line (Green, Dashed) -->
        <path d="{path_avalanche}" fill="none" stroke="#30d158" stroke-width="3" stroke-dasharray="5,5" />
        
        <!-- Legend -->
        <g transform="translate({width-150}, 20)">
            <rect width="10" height="10" fill="#ff453a" />
            <text x="15" y="10" fill="#ff453a" font-size="12">Snowball</text>
            
            <rect y="20" width="10" height="10" fill="#30d158" />
            <text x="15" y="30" fill="#30d158" font-size="12">Avalanche</text>
        </g>
    </svg>
    """
    return svg

