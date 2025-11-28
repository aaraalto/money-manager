from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel
from .types import TimeSeriesPoint
from .financial_formulas import calculate_compound_step

class ProjectionContext(BaseModel):
    series: List[TimeSeriesPoint]
    final_value: float
    context: str

def project_compound_growth(
    principal: float, 
    rate: float, 
    years: int, 
    monthly_contribution: float,
    start_date: Optional[date] = None,
    periods_per_year: int = 12,
    days_per_period: int = 30
) -> ProjectionContext:
    series = []
    current_value = principal
    current_start_date = start_date or date.today()
    
    context_str = f"Starting with ${principal:,.2f}, contributing ${monthly_contribution:,.2f}/period at {rate:.1%} APY."
    
    total_periods = years * periods_per_year
    
    for period in range(total_periods + 1):
        current_date = current_start_date + timedelta(days=period*days_per_period) # Approx
        
        if period > 0:
            current_value = calculate_compound_step(current_value, rate, monthly_contribution, periods_per_year)
        
        series.append(TimeSeriesPoint(date=current_date, value=current_value))
        
    return ProjectionContext(
        series=series,
        final_value=current_value,
        context=context_str
    )
