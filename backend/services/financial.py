import asyncio
from functools import lru_cache
from typing import Dict, Any, List, Optional

from backend.data.repository import FileRepository
from backend.models import Asset, Liability, IncomeSource, SpendingCategory
from backend.primitives import (
    get_net_worth,
    simulate_debt_payoff,
    project_compound_growth,
    assess_affordability,
    generate_insights,
)
from backend.primitives.metrics import calculate_metrics

class FinancialService:
    def __init__(self, repository: FileRepository):
        self.repo = repository

    async def get_dashboard_view(self, monthly_payment: float = 500.0, filter_tag: str = "All") -> Dict[str, Any]:
        # Fetch data concurrently
        assets, liabilities, income, spending = await asyncio.gather(
            self.repo.get_assets(),
            self.repo.get_liabilities(),
            self.repo.get_income(),
            self.repo.get_spending_plan()
        )

        # Calculate Metrics
        metrics = calculate_metrics(income, spending, liabilities)
        
        total_monthly_income = metrics["monthly_gross_income"]
        total_monthly_spending = metrics["monthly_expenses"]
        total_min_debt_payments = metrics["monthly_debt_payments"]
        
        free_cash_flow = total_monthly_income - total_monthly_spending - total_min_debt_payments
        
        # Filter liabilities
        filtered_liabilities = liabilities
        if filter_tag != "All":
            filtered_liabilities = [l for l in liabilities if filter_tag in l.tags]
        
        # Calculations
        nw_context = get_net_worth(assets, filtered_liabilities)
        
        # Projection (hardcoded params as per original)
        projection = project_compound_growth(
            principal=nw_context.total, 
            rate=0.07, 
            years=10, 
            monthly_contribution=1000.0
        )
        
        # Debt Payoff Simulations
        # We can cache these if needed, but for now let's run them.
        # To use lru_cache effectively, we'd need hashable arguments (lists aren't).
        # Since the dataset is small, re-running might be fine. 
        # If we wanted to use lru_cache, we'd wrap this in a helper that takes tuples.
        snowball = simulate_debt_payoff(filtered_liabilities, "snowball", extra_monthly_payment=monthly_payment)
        avalanche = simulate_debt_payoff(filtered_liabilities, "avalanche", extra_monthly_payment=monthly_payment)
        
        affordability = assess_affordability(cost=5000, liquidity=nw_context.liquid, monthly_burn=3000)
        
        insights = generate_insights(assets, liabilities, income, spending)

        return {
            "financial_health": {
                "savings_rate": metrics["savings_rate"],
                "debt_to_income_ratio": metrics["debt_to_income_ratio"],
                "savings_rate_change": 0.02  # Mock
            },
            "insights": [i.dict() for i in insights],
            "cash_flow": {
                "income": total_monthly_income,
                "spending": total_monthly_spending,
                "debt_min": total_min_debt_payments,
                "free": free_cash_flow
            },
            "net_worth": nw_context.dict(),
            "liabilities": [l.dict() for l in filtered_liabilities],
            "projection": projection.dict(),
            "debt_payoff": {
                "snowball": snowball.dict(),
                "avalanche": avalanche.dict(),
                "comparison": [
                    f"Switching to Avalanche saves you ${(snowball.interest_paid - avalanche.interest_paid):,.0f} in interest.",
                    f"Avalanche: Debt-free by {avalanche.date_free}",
                    f"Snowball: Debt-free by {snowball.date_free}"
                ]
            },
            "affordability_check": affordability.dict()
        }

    async def get_spending_plan(self) -> List[SpendingCategory]:
        return await self.repo.get_spending_plan()

    async def update_spending_plan(self, plan: List[SpendingCategory]):
        await self.repo.save_spending_plan(plan)

    async def get_insights(self) -> List[Any]:
        assets, liabilities, income, spending = await asyncio.gather(
            self.repo.get_assets(),
            self.repo.get_liabilities(),
            self.repo.get_income(),
            self.repo.get_spending_plan()
        )
        return generate_insights(assets, liabilities, income, spending)
