from typing import List, Dict
from app.models import Asset, Liability, IncomeSource, SpendingCategory, AssetType

class FinancialInsight:
    def __init__(self, title: str, description: str, severity: str = "info", action_item: str = None):
        self.title = title
        self.description = description
        self.severity = severity  # info, opportunity, priority, success
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
            title="Cash Flow Opportunity",
            description=f"There's a ${abs(free_cash_flow):,.0f} gap between income and spending. Let's close it together.",
            severity="priority",
            action_item="Check your 'Wants' category—small tweaks can make a big difference."
        ))
    elif free_cash_flow < (total_monthly_income * 0.1):
        insights.append(FinancialInsight(
            title="Room to Grow",
            description="You're saving about 10% of your income—there's room to grow.",
            severity="opportunity",
            action_item="One small cut could boost your savings rate."
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
            title="Safety Net Check",
            description=f"You're building toward 1 month of expenses covered (currently ${cash_assets:,.0f}). Let's strengthen this.",
            severity="priority",
            action_item="Consider prioritizing cash savings—even $500 helps."
        ))
    elif months_runway < 3:
        insights.append(FinancialInsight(
            title="Growing Your Safety Net",
            description=f"You're at {months_runway:.1f} months of expenses saved—next milestone is 3 months.",
            severity="opportunity",
            action_item="Keep building! Consider automating a small monthly transfer."
        ))

    # 3. High Interest Debt Focus
    high_interest_debts = [l for l in liabilities if l.interest_rate > 0.07]
    if high_interest_debts:
        avg_rate = sum(d.interest_rate for d in high_interest_debts) / len(high_interest_debts)
        insights.append(FinancialInsight(
            title="High-Interest Focus",
            description=f"You have {len(high_interest_debts)} higher-rate loans (Avg: {avg_rate*100:.1f}%)—let's prioritize these.",
            severity="opportunity",
            action_item="The Avalanche method works great here—it saves you the most over time."
        ))

    return insights

