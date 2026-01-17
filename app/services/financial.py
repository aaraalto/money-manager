import asyncio
from typing import List, Any, Dict
from app.models import SpendingCategory, AssetType
from app.domain.advisor import generate_insights
from app.domain.net_worth import get_net_worth
from app.domain.growth import project_compound_growth
from app.domain.debt import simulate_debt_payoff
from app.data.repository import FileRepository
from app.core.config import FINANCIAL

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
            "savings_rate_change": 0.02, # Mock change for demo
            "monthly_surplus": surplus
        }
        
        # 3. Projection (Wealth Growth)
        investable_assets = sum(a.value for a in assets if a.type in [AssetType.EQUITY, AssetType.RETIREMENT, AssetType.CRYPTO])
        # Assume we invest configured percentage of surplus + any existing "Savings" category
        savings_category = sum(s.amount for s in spending_list if s.type == "Savings")
        monthly_contribution = max(0, (surplus * FINANCIAL.SURPLUS_INVESTMENT_ALLOCATION) + savings_category)
        
        projection = project_compound_growth(
            principal=investable_assets,
            rate=FINANCIAL.DEFAULT_INVESTMENT_RETURN,
            years=30,
            monthly_contribution=monthly_contribution
        )
        
        # 4. Debt Payoff
        # Calculate potential extra payment from surplus
        extra_payment = max(0, surplus * FINANCIAL.SURPLUS_DEBT_ALLOCATION)
        
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

    async def get_assets_view(self) -> Dict[str, Any]:
        assets = await self.repo.get_assets()
        liabilities = await self.repo.get_liabilities()
        spending = await self.repo.get_spending_plan()
        
        # Net Worth Logic
        total_assets = sum(a.value for a in assets)
        total_liabilities = sum(l.balance for l in liabilities)
        net_worth = total_assets - total_liabilities
        
        # Ideas Logic
        ideas = []
        
        # 1. Low Yield Cash
        cash_assets = [a for a in assets if a.type == AssetType.CASH]
        total_cash = sum(a.value for a in cash_assets)
        for a in cash_assets:
            if a.apy < FINANCIAL.LOW_YIELD_THRESHOLD and a.value > FINANCIAL.HYSA_OPTIMIZATION_MIN_BALANCE:
                 ideas.append({
                     "title": f"Optimize {a.name}",
                     "description": f"Your cash in {a.name} is earning only {a.apy*100:.1f}%. Consider a HYSA earning ~{FINANCIAL.DEFAULT_HYSA_APY*100:.1f}%.",
                     "impact": f"+${a.value * (FINANCIAL.DEFAULT_HYSA_APY - a.apy):.0f}/yr",
                     "type": "optimization"
                 })

        # 2. Emergency Fund Check
        monthly_burn = sum(s.amount for s in spending)
        months_of_runway = total_cash / monthly_burn if monthly_burn > 0 else 0
        if months_of_runway < FINANCIAL.EMERGENCY_FUND_WARNING_MONTHS:
             ideas.append({
                 "title": "Strengthen Your Safety Net",
                 "description": f"You've got {months_of_runway:.1f} months covered—building to {FINANCIAL.EMERGENCY_FUND_TARGET_MONTHS} months gives extra security.",
                 "impact": "Security",
                 "type": "opportunity"
             })
        elif months_of_runway > FINANCIAL.EXCESS_CASH_MONTHS:
              ideas.append({
                 "title": "Put Your Cash to Work",
                 "description": f"With {months_of_runway:.1f} months saved, you could invest the extra and let it grow.",
                 "impact": "Growth",
                 "type": "opportunity"
             })

        # 3. Concentration Risk
        if total_assets > 0:
            for a in assets:
                if a.value / total_assets > FINANCIAL.CONCENTRATION_WARNING_THRESHOLD and len(assets) > 1:
                     ideas.append({
                         "title": f"Diversification Opportunity",
                         "description": f"{a.name} makes up {a.value/total_assets*100:.0f}% of your assets. Spreading it out could reduce risk.",
                         "impact": "Risk Reduction",
                         "type": "opportunity"
                     })

        # Group Assets by Type
        grouped_assets = {}
        for a in assets:
            # Use value (string) of enum for template compatibility
            t_val = a.type.value
            if t_val not in grouped_assets:
                grouped_assets[t_val] = []
            # Convert Asset model to dict for template compatibility
            grouped_assets[t_val].append(a.dict())

        return {
            "net_worth": net_worth,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "assets": [a.dict() for a in assets],
            "grouped_assets": grouped_assets,
            "ideas": ideas
        }
