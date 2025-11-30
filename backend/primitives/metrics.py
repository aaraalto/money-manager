
from typing import List
from backend.models import IncomeSource, Liability, SpendingCategory

def calculate_monthly_income(income: List[IncomeSource]) -> float:
    total = 0.0
    for i in income:
        if i.frequency == "monthly":
            total += i.amount
        elif i.frequency == "bi-weekly":
            total += i.amount * 26 / 12
        elif i.frequency == "weekly":
            total += i.amount * 52 / 12
        elif i.frequency == "annually":
            total += i.amount / 12
    return total

def calculate_metrics(
    income: List[IncomeSource],
    spending: List[SpendingCategory],
    liabilities: List[Liability]
) -> dict:
    monthly_gross_income = calculate_monthly_income(income)
    
    monthly_spending = sum(s.amount for s in spending)
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
        
    # Default to Level 3 (Growth) if above conditions met
    # (Plan focuses on 0-2, so returning 3 as "Graduated Phase 1")
    return 3
