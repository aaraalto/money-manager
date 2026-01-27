from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import IncomeSource, SpendingCategory

# =============================================================================
# FREQUENCY NORMALIZATION
# =============================================================================

# Multipliers to convert various frequencies to monthly amounts
FREQUENCY_TO_MONTHLY: dict[str, float] = {
    "monthly": 1.0,
    "bi-weekly": 26 / 12,  # 26 pay periods / 12 months
    "weekly": 52 / 12,      # 52 weeks / 12 months
    "annually": 1 / 12,
    "yearly": 1 / 12,
    "quarterly": 1 / 3,
    "semi-annually": 1 / 6,
}


def normalize_to_monthly(amount: float, frequency: str) -> float:
    """
    Converts an amount from any frequency to its monthly equivalent.
    
    Args:
        amount: The amount in the given frequency.
        frequency: One of 'monthly', 'bi-weekly', 'weekly', 'annually', etc.
        
    Returns:
        The monthly equivalent amount.
    """
    multiplier = FREQUENCY_TO_MONTHLY.get(frequency.lower(), 1.0)
    return amount * multiplier


def calculate_total_monthly_income(sources: List["IncomeSource"]) -> float:
    """
    Calculates total monthly income from a list of income sources.
    
    Args:
        sources: List of IncomeSource objects with amount and frequency.
        
    Returns:
        Total monthly income across all sources.
    """
    return sum(normalize_to_monthly(s.amount, s.frequency) for s in sources)


def calculate_total_monthly_spending(categories: List["SpendingCategory"]) -> float:
    """
    Calculates total monthly spending from a list of spending categories.
    
    Args:
        categories: List of SpendingCategory objects.
        
    Returns:
        Total monthly spending.
    """
    return sum(c.amount for c in categories)


# =============================================================================
# INTEREST & COMPOUND GROWTH
# =============================================================================

def calculate_monthly_interest(principal: float, annual_rate: float, periods_per_year: int = 12) -> float:
    """
    Calculates the interest accrued over one period (default: month) based on an annual interest rate.
    
    Args:
        principal: The current balance or value.
        annual_rate: The annual interest rate (decimal, e.g., 0.05 for 5%).
        periods_per_year: Number of compounding periods per year. Default is 12 (monthly).
        
    Returns:
        The interest amount for one period.
    """
    periodic_rate = annual_rate / periods_per_year
    return principal * periodic_rate

def calculate_compound_step(current_value: float, annual_rate: float, contribution: float, periods_per_year: int = 12) -> float:
    """
    Calculates the new value after one period of interest and contribution.
    
    Args:
        current_value: The starting value for the period.
        annual_rate: The annual interest rate (decimal).
        contribution: The amount added this period.
        periods_per_year: Number of compounding periods per year. Default is 12 (monthly).
        
    Returns:
        The new total value.
    """
    interest = calculate_monthly_interest(current_value, annual_rate, periods_per_year)
    return current_value + interest + contribution

def calculate_runway(liquidity: float, monthly_burn: float, days_in_period: int = 30) -> int:
    """
    Calculates how many days the liquidity will last given the monthly burn rate.
    
    Args:
        liquidity: Total available liquid assets.
        monthly_burn: Monthly expenses/burn rate.
        days_in_period: Number of days in the period (default 30 for a month).
        
    Returns:
        Number of days (capped at 9999 for infinite/long runways).
    """
    if monthly_burn <= 0:
        return 9999
    return int((liquidity / monthly_burn) * days_in_period)

def calculate_amortization_payment(principal: float, annual_rate: float, years: int, periods_per_year: int = 12) -> float:
    """
    Calculates the fixed periodic payment required to pay off a loan over a set term.
    
    Args:
        principal: The loan amount.
        annual_rate: The annual interest rate (decimal).
        years: The term of the loan in years.
        periods_per_year: Number of payments per year. Default is 12 (monthly).
        
    Returns:
        The periodic payment amount.
    """
    if annual_rate <= 0:
        return principal / (years * periods_per_year)
        
    periodic_rate = annual_rate / periods_per_year
    num_payments = years * periods_per_year
    
    # Formula: P = (r * PV) / (1 - (1 + r)^-n)
    payment = (periodic_rate * principal) / (1 - (1 + periodic_rate) ** -num_payments)
    return payment

def calculate_future_value(principal: float, annual_rate: float, years: int, periods_per_year: int = 12) -> float:
    """
    Calculates the future value of a lump sum investment.
    
    Args:
        principal: Present value.
        annual_rate: Annual interest rate (decimal).
        years: Number of years.
        periods_per_year: Number of compounding periods per year.
    """
    rate_per_period = annual_rate / periods_per_year
    total_periods = years * periods_per_year
    return principal * ((1 + rate_per_period) ** total_periods)

def calculate_present_value(future_value: float, annual_rate: float, years: int, periods_per_year: int = 12) -> float:
    """
    Calculates the present value needed to reach a future target.
    
    Args:
        future_value: Target amount.
        annual_rate: Annual interest rate (decimal).
        years: Number of years.
        periods_per_year: Number of compounding periods per year.
    """
    rate_per_period = annual_rate / periods_per_year
    total_periods = years * periods_per_year
    return future_value / ((1 + rate_per_period) ** total_periods)

def calculate_real_return_rate(nominal_rate: float, inflation_rate: float) -> float:
    """
    Calculates the real rate of return adjusting for inflation using the Fisher equation.
    
    Args:
        nominal_rate: The nominal interest rate (decimal).
        inflation_rate: The inflation rate (decimal).
        
    Returns:
        The real interest rate.
    """
    # Fisher equation: (1 + nominal) = (1 + real) * (1 + inflation)
    # real = ((1 + nominal) / (1 + inflation)) - 1
    return ((1 + nominal_rate) / (1 + inflation_rate)) - 1
