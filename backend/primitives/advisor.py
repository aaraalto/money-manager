from typing import List, Dict
from backend.models import Asset, Liability, IncomeSource, SpendingCategory, AssetType

class FinancialInsight:
    def __init__(self, title: str, description: str, severity: str = "info", action_item: str = None):
        self.title = title
        self.description = description
        self.severity = severity # info, warning, critical, success
        self.action_item = action_item

    def dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "action_item": self.action_item
        }

def generate_insights(
    assets: List[Asset],
    liabilities: List[Liability],
    income: List[IncomeSource],
    spending: List[SpendingCategory]
) -> List[FinancialInsight]:
    insights = []
    
    # 1. Cash Flow Analysis
    total_monthly_income = 0
    for i in income:
        if i.frequency == "monthly":
            total_monthly_income += i.amount
        elif i.frequency == "bi-weekly":
            total_monthly_income += i.amount * 26 / 12
        elif i.frequency == "weekly":
            total_monthly_income += i.amount * 52 / 12
        elif i.frequency == "annually":
            total_monthly_income += i.amount / 12

    total_monthly_spending = sum(s.amount for s in spending)
    min_debt_payments = sum(l.min_payment for l in liabilities)
    total_outflow = total_monthly_spending + min_debt_payments
    
    free_cash_flow = total_monthly_income - total_outflow
    
    if free_cash_flow < 0:
        insights.append(FinancialInsight(
            title="Cash Flow Alert",
            description=f"You're spending ${abs(free_cash_flow):,.0f} more than you make each month.",
            severity="critical",
            action_item="Review 'Wants' in your spending plan immediately."
        ))
    elif free_cash_flow < (total_monthly_income * 0.1):
        insights.append(FinancialInsight(
            title="Savings Check-in",
            description="You're saving less than 10% of your income right now.",
            severity="warning",
            action_item="Small tweaks add up. Try trimming one variable expense."
        ))
    else:
        insights.append(FinancialInsight(
            title="You're crushing it!",
            description=f"You have a ${free_cash_flow:,.0f} monthly surplus to fuel your goals.",
            severity="success"
        ))

    # 2. Emergency Fund Check
    cash_assets = sum(a.value for a in assets if a.type == AssetType.CASH)
    monthly_burn = total_monthly_spending + min_debt_payments
    
    months_runway = cash_assets / monthly_burn if monthly_burn > 0 else float('inf')
    
    if months_runway < 1:
        insights.append(FinancialInsight(
            title="Emergency Alert",
            description=f"You have less than 1 month of expenses (${cash_assets:,.0f}) covered. Let's fix this.",
            severity="critical",
            action_item="Pause extra debt payments. Build $1,000 emergency fund immediately."
        ))
    elif months_runway < 3:
        insights.append(FinancialInsight(
            title="Safety Net Check",
            description=f"You have {months_runway:.1f} months of expenses saved. Goal is 3-6 months.",
            severity="warning",
            action_item="Prioritize cash savings over low-interest debt."
        ))

    # 3. High Interest Debt Alert
    high_interest_debts = [l for l in liabilities if l.interest_rate > 0.07]
    if high_interest_debts:
        avg_rate = sum(d.interest_rate for d in high_interest_debts) / len(high_interest_debts)
        insights.append(FinancialInsight(
            title="Debt Alert",
            description=f"You have {len(high_interest_debts)} high-interest loans slowing you down (Avg: {avg_rate*100:.1f}%).",
            severity="warning",
            action_item="Use the Avalanche method to attack these aggressively."
        ))

    return insights

