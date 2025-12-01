import asyncio
from typing import List, Any, Dict
from app.models import SpendingCategory, AssetType
from app.domain.advisor import generate_insights
from app.domain.net_worth import get_net_worth
from app.domain.growth import project_compound_growth
from app.domain.debt import simulate_debt_payoff
from app.data.repository import FileRepository

class FinancialService:
    def __init__(self, repo: FileRepository):
        self.repo = repo

    async def get_insights(self) -> List[Any]:
        assets, liabilities, income, spending = await asyncio.gather(
            self.repo.get_assets(),
            self.repo.get_liabilities(),
            self.repo.get_income(),
            self.repo.get_spending_plan()
        )
        return generate_insights(assets, liabilities, income, spending)
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        assets, liabilities, income_list, spending_list = await asyncio.gather(
            self.repo.get_assets(),
            self.repo.get_liabilities(),
            self.repo.get_income(),
            self.repo.get_spending_plan()
        )
        
        # 1. Net Worth
        net_worth_context = get_net_worth(assets, liabilities)
        
        # 2. Financial Health (Savings Rate & DTI)
        total_monthly_income = 0
        for i in income_list:
            if i.frequency == "monthly": total_monthly_income += i.amount
            elif i.frequency == "bi-weekly": total_monthly_income += i.amount * 26 / 12
            elif i.frequency == "weekly": total_monthly_income += i.amount * 52 / 12
            elif i.frequency == "annually": total_monthly_income += i.amount / 12

        total_monthly_spending = sum(s.amount for s in spending_list)
        min_debt_payments = sum(l.min_payment for l in liabilities)
        
        # Correctly handle Debt Repayment category to avoid double counting
        debt_repayment_category = next((s for s in spending_list if s.category == "Debt Repayment"), None)
        debt_outflow = min_debt_payments
        
        # If user has explicitly budgeted for debt, use that amount if it covers minimums
        spending_for_surplus = total_monthly_spending
        if debt_repayment_category:
            if debt_repayment_category.amount >= min_debt_payments:
                debt_outflow = debt_repayment_category.amount
                # Don't double count debt in spending
                spending_for_surplus -= debt_repayment_category.amount
            else:
                # If budgeted amount is less than min payments, we must use min payments
                # and remove the insufficient budgeted amount from spending to avoid double counting
                 spending_for_surplus -= debt_repayment_category.amount

        # Calculate Surplus / Savings
        surplus = total_monthly_income - spending_for_surplus - debt_outflow
        savings_rate = surplus / total_monthly_income if total_monthly_income > 0 else 0
        
        # DTI (Debt Payments / Gross Income usually, but here using net income proxy or just income)
        dti = min_debt_payments / total_monthly_income if total_monthly_income > 0 else 0
        
        financial_health = {
            "savings_rate": savings_rate,
            "debt_to_income_ratio": dti,
            "savings_rate_change": 0.02 # Mock change for demo
        }
        
        # 3. Projection (Wealth Growth)
        investable_assets = sum(a.value for a in assets if a.type in [AssetType.EQUITY, AssetType.RETIREMENT, AssetType.CRYPTO])
        # Assume we invest 50% of surplus + any existing "Savings" category
        savings_category = sum(s.amount for s in spending_list if s.type == "Savings")
        monthly_contribution = max(0, (surplus * 0.5) + savings_category)
        
        projection = project_compound_growth(
            principal=investable_assets,
            rate=0.07,
            years=30,
            monthly_contribution=monthly_contribution
        )
        
        # 4. Debt Payoff
        # Calculate potential extra payment from surplus
        extra_payment = max(0, surplus * 0.5) # Use other half of surplus for debt
        
        snowball = simulate_debt_payoff(liabilities, "snowball", extra_payment)
        avalanche = simulate_debt_payoff(liabilities, "avalanche", extra_payment)
        
        debt_payoff = {
            "snowball": snowball.dict(),
            "avalanche": avalanche.dict(),
            "comparison": [
                f"Strategy: paying ${extra_payment:,.0f} extra per month.",
                f"Snowball free by {snowball.date_free.strftime('%b %Y')}",
                f"Avalanche free by {avalanche.date_free.strftime('%b %Y')}",
                f"Avalanche saves ${(snowball.interest_paid - avalanche.interest_paid):,.0f} in interest."
            ]
        }
        
        # 5. Spending Breakdown
        spending_breakdown = [
            {"label": s.category, "value": s.amount, "type": s.type}
            for s in spending_list
        ]
        spending_breakdown.sort(key=lambda x: x["value"], reverse=True)

        # 6. Daily Allowance (Safe to Spend)
        # Formula: (Allocated 'Wants' + Unallocated Surplus) / 30
        # This represents money that is NOT for Bills, Debt, or Savings.
        allocated_wants = sum(s.amount for s in spending_list if s.type == "Want")
        safe_to_spend_monthly = allocated_wants + max(0, surplus)
        daily_allowance = safe_to_spend_monthly / 30
        
        # 7. System Status
        # Determine if core obligations are met
        fixed_costs = sum(s.amount for s in spending_list if s.type == "Need")
        obligations = fixed_costs + debt_outflow
        
        system_status = {
            "fixed_costs_covered": total_monthly_income >= obligations,
            "debt_strategy_active": True, # Implicitly true as we have a strategy
            "savings_automated": sum(s.amount for s in spending_list if s.type == "Savings") > 0,
            "obligations_monthly": obligations,
            "income_monthly": total_monthly_income
        }
        
        return {
            "net_worth": net_worth_context.dict(),
            "financial_health": financial_health,
            "projection": projection.dict(),
            "debt_payoff": debt_payoff,
            "spending_breakdown": spending_breakdown,
            "daily_allowance": daily_allowance,
            "system_status": system_status
        }

    async def commit_scenario(self, monthly_payment: float) -> Dict[str, Any]:
        """
        Updates the 'Debt Repayment' spending category with the new committed amount.
        """
        plan = await self.repo.get_spending_plan()
        
        found = False
        for category in plan:
            if category.category == "Debt Repayment":
                category.amount = monthly_payment
                found = True
                break
        
        if not found:
            # If it doesn't exist, add it as a 'Savings' or 'Need' type
            plan.append(SpendingCategory(category="Debt Repayment", amount=monthly_payment, type="Savings"))
            
        await self.repo.save_spending_plan(plan)
        
        return {"status": "success", "new_payment": monthly_payment}
