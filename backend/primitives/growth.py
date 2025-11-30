from typing import List, Optional
import random
import math
from datetime import date, timedelta
from pydantic import BaseModel
from .types import TimeSeriesPoint
from .financial_formulas import calculate_compound_step, calculate_real_return_rate

class ProjectionContext(BaseModel):
    series: List[TimeSeriesPoint]
    final_value: float
    total_contributions: float
    total_interest: float
    inflation_adjusted_final_value: Optional[float] = None
    context: str
    crossover_date: Optional[date] = None

class MonteCarloResult(BaseModel):
    p10_value: float
    p50_value: float
    p90_value: float
    worst_case: float
    best_case: float
    iterations: int
    context: str

def add_months(start_date: date, months: int) -> date:
    """Adds months to a date accurately."""
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, [31, 29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return date(year, month, day)

def calculate_crossover_point(
    monthly_expenses: float, 
    current_portfolio: float, 
    growth_rate: float, 
    monthly_contribution: float,
    safe_withdrawal_rate: float = 0.04
) -> Optional[date]:
    """
    Calculates the date when safe withdrawal amount exceeds monthly expenses.
    
    Args:
        monthly_expenses: Target monthly income needed.
        current_portfolio: Starting invested assets.
        growth_rate: Annual growth rate (nominal or real).
        monthly_contribution: Monthly addition to portfolio.
        safe_withdrawal_rate: Annual withdrawal rate (default 4%).
        
    Returns:
        Date when crossover occurs, or None if not found within realistic timeframe (e.g. 50 years).
    """
    if monthly_expenses <= 0:
        return date.today()
        
    target_portfolio = (monthly_expenses * 12) / safe_withdrawal_rate
    
    if current_portfolio >= target_portfolio:
        return date.today()
        
    # Simple iterative check (monthly)
    portfolio = current_portfolio
    current_date = date.today()
    monthly_rate = growth_rate / 12
    
    for month in range(1, 600): # Max 50 years check
        portfolio = portfolio * (1 + monthly_rate) + monthly_contribution
        if portfolio >= target_portfolio:
            return add_months(current_date, month)
            
    return None

def project_compound_growth(
    principal: float, 
    rate: float, 
    years: int, 
    monthly_contribution: float,
    start_date: Optional[date] = None,
    inflation_rate: float = 0.0,
    periods_per_year: int = 12,
    monthly_expenses_target: Optional[float] = None
) -> ProjectionContext:
    series = []
    current_value = principal
    current_date = start_date or date.today()
    
    real_rate = calculate_real_return_rate(rate, inflation_rate) if inflation_rate else rate
    
    # Track both nominal and real if inflation is present
    nominal_value = principal
    real_value = principal
    total_contributed = principal
    
    context_str = f"Starting with ${principal:,.2f}, contributing ${monthly_contribution:,.2f}/mo at {rate:.1%} APY"
    if inflation_rate > 0:
        context_str += f" (Inflation: {inflation_rate:.1%}, Real Rate: {real_rate:.1%})"
    
    total_periods = years * periods_per_year
    
    # Initial point
    series.append(TimeSeriesPoint(date=current_date, value=nominal_value))
    
    # Crossover calculation prep
    crossover_date = None
    safe_withdrawal_rate = 0.04
    target_portfolio_nominal = 0
    if monthly_expenses_target:
        # In nominal terms, expenses grow with inflation, so target grows.
        # But simplified: if we use Real Rate for projection, we use constant Real Dollars for target.
        # OR if we use Nominal Rate, we inflate the target every year.
        # Let's use the separate helper for cleaner logic usually, but we can detect it during the loop.
        pass

    # Check crossover separately or inside loop?
    # Let's use the helper for precise calculation
    if monthly_expenses_target:
        # If using nominal rate, expenses inflate. 
        # If we want "Real" crossover (buying power), we compare Real Value vs Current Expenses.
        # Using 4% rule on Real Value is the standard FIRE approach.
        crossover_date = calculate_crossover_point(
            monthly_expenses_target, 
            principal, 
            real_rate, # Use real rate to keep purchasing power constant
            monthly_contribution
        )

    for period in range(1, total_periods + 1):
        # Step date
        # Assuming monthly periods for date calculation if periods_per_year is 12
        if periods_per_year == 12:
            current_date = add_months(start_date or date.today(), period)
        else:
            # Fallback for non-monthly
            current_date += timedelta(days=365/periods_per_year)
            
        # Calculate steps
        nominal_value = calculate_compound_step(nominal_value, rate, monthly_contribution, periods_per_year)
        
        if inflation_rate > 0:
             # Deflate nominal value to get real value
             years_passed = period / periods_per_year
             deflator = (1 + inflation_rate) ** years_passed
             real_value = nominal_value / deflator
        else:
             real_value = nominal_value

        total_contributed += monthly_contribution
        
        series.append(TimeSeriesPoint(date=current_date, value=nominal_value))
        
    return ProjectionContext(
        series=series,
        final_value=nominal_value,
        total_contributions=total_contributed,
        total_interest=nominal_value - total_contributed,
        inflation_adjusted_final_value=real_value if inflation_rate > 0 else None,
        context=context_str,
        crossover_date=crossover_date
    )

def simulate_monte_carlo_growth(
    principal: float,
    mean_return: float,
    std_dev: float,
    years: int,
    monthly_contribution: float,
    iterations: int = 1000,
    inflation_rate: float = 0.0
) -> MonteCarloResult:
    final_values = []
    
    # Convert annual parameters to monthly
    monthly_mean = mean_return / 12
    monthly_std_dev = std_dev / math.sqrt(12) # Square root of time rule for volatility
    months = years * 12
    
    for _ in range(iterations):
        current_value = principal
        for _ in range(months):
            # Random return for this month
            r = random.gauss(monthly_mean, monthly_std_dev)
            interest = current_value * r
            current_value += interest + monthly_contribution
            
        if inflation_rate > 0:
            # Adjust for inflation at the end
            deflator = (1 + inflation_rate) ** years
            current_value = current_value / deflator
            
        final_values.append(current_value)
        
    final_values.sort()
    n = len(final_values)
    
    return MonteCarloResult(
        p10_value=final_values[int(n * 0.1)],
        p50_value=final_values[int(n * 0.5)],
        p90_value=final_values[int(n * 0.9)],
        worst_case=final_values[0],
        best_case=final_values[-1],
        iterations=iterations,
        context=f"Monte Carlo ({iterations} runs): Mean {mean_return:.1%}, StdDev {std_dev:.1%}"
    )
