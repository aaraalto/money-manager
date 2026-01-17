from typing import List
from app.models import IncomeSource, Liability, SpendingCategory
from app.domain.financial_formulas import (
    calculate_total_monthly_income,
    calculate_total_monthly_spending,
)


def calculate_monthly_income(income: List[IncomeSource]) -> float:
    """
    Calculates total monthly income from all sources.
    
    Deprecated: Use calculate_total_monthly_income() from financial_formulas.py directly.
    This function is kept for backwards compatibility.
    """
    return calculate_total_monthly_income(income)

def calculate_metrics(
    income: List[IncomeSource],
    spending: List[SpendingCategory],
    liabilities: List[Liability]
) -> dict:
    monthly_gross_income = calculate_total_monthly_income(income)
    
    monthly_spending = calculate_total_monthly_spending(spending)
    monthly_debt_payments = sum(l.min_payment for l in liabilities)
    
    # DTI: Debt Payments / Gross Income
    dti = 0.0
    if monthly_gross_income > 0:
        dti = monthly_debt_payments / monthly_gross_income

    # Savings Rate: (Income - Outflows) / Income
    # Outflows = Spending + Debt Payments
    total_outflow = monthly_spending + monthly_debt_payments
    savings_rate = 0.0
    if monthly_gross_income > 0:
        savings = monthly_gross_income - total_outflow
        savings_rate = savings / monthly_gross_income

    return {
        "monthly_gross_income": monthly_gross_income,
        "monthly_expenses": monthly_spending,
        "monthly_debt_payments": monthly_debt_payments,
        "savings_rate": savings_rate,
        "debt_to_income_ratio": dti
    }

def calculate_financial_level(
    monthly_income: float,
    monthly_burn: float,
    total_debt: float,
    liquid_assets: float
) -> int:
    """
    Calculates the user's financial level based on inputs.
    """
    
    # Level 0: Insolvency
    if monthly_burn > monthly_income:
        return 0
        
    # Level 1: Solvency but Indebted
    if total_debt > 0:
        return 1
        
    # Level 2: Stability Building (Debt free, building emergency fund)
    six_months_expenses = monthly_burn * 6
    if liquid_assets < six_months_expenses:
        return 2
    
    # Level 3: Growth (Emergency fund full, investing < 25x expenses)
    # Note: This logic assumes a standard "FIRE" number of 25x annual expenses for Level 4.
    # Annual Burn = monthly_burn * 12
    # FI Number = Annual Burn * 25 = monthly_burn * 300
    fi_number = monthly_burn * 300
    
    # We check if liquid/invested assets are less than FI Number for Level 3.
    # Assuming liquid_assets roughly tracks total invested assets for this check, 
    # or we might need a separate 'net_worth' or 'invested_assets' param.
    # For now, reusing liquid_assets as the main asset metric.
    if liquid_assets < fi_number:
        return 3
        
    # Level 4: Independence (Assets >= 25x Annual Expenses)
    # Basic FI achieved.
    # Level 5 (Abundance) and 6 (Legacy) require significantly higher multiples or specific goals.
    # Let's say Level 5 is 50x expenses (Fat FIRE).
    fat_fire_number = monthly_burn * 600
    if liquid_assets < fat_fire_number:
        return 4
        
    # Level 5: Abundance
    return 5
