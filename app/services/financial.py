import asyncio
from typing import List, Any, Dict
from app.models import (
    SpendingCategory,
    AssetType,
    DashboardData,
    FinancialHealthMetrics,
    SpendingBreakdownItem,
    SystemStatus,
    DebtPayoffSummary,
    DebtPayoffStrategy,
    ProjectionSummary,
    NetWorthSummary,
)
from app.domain.advisor import generate_insights
from app.domain.net_worth import get_net_worth
from app.domain.growth import project_compound_growth
from app.domain.debt import simulate_debt_payoff
from app.domain.financial_formulas import (
    calculate_total_monthly_income,
    calculate_total_monthly_spending,
)
from app.data.repository import FileRepository
from app.core.config import FINANCIAL
from app.core.exceptions import (
    RepositoryError,
    InsufficientDataError,
    DataCorruptionError,
    SimulationOverflowError,
)
from app.core.logging import get_logger

logger = get_logger("financial_service")


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
        
    async def get_dashboard_data(self) -> DashboardData:
        """
        Retrieves and calculates all dashboard data with full type safety.
        
        Returns:
            DashboardData: Fully typed dashboard response model.
            
        Raises:
            RepositoryError: If data cannot be loaded
            InsufficientDataError: If required data is missing
            DataCorruptionError: If data validation fails
        """
        try:
            assets, liabilities, income_list, spending_list = await asyncio.gather(
                self.repo.get_assets(),
                self.repo.get_liabilities(),
                self.repo.get_income(),
                self.repo.get_spending_plan()
            )
        except Exception as e:
            logger.error(f"Failed to load financial data: {e}")
            raise RepositoryError("data loading", str(e))
        
        # Validate we have minimum required data
        if not income_list:
            raise InsufficientDataError("dashboard metrics", "income sources")
        
        # 1. Net Worth
        net_worth_context = get_net_worth(assets, liabilities)
        net_worth_summary = NetWorthSummary(
            total=net_worth_context.total,
            liquid=net_worth_context.liquid,
            illiquid=net_worth_context.illiquid,
            assets_total=net_worth_context.assets_total,
            liabilities_total=net_worth_context.liabilities_total,
            reasoning=net_worth_context.reasoning,
        )
        
        # 2. Financial Health (Savings Rate & DTI)
        total_monthly_income = calculate_total_monthly_income(income_list)
        total_monthly_spending = calculate_total_monthly_spending(spending_list)
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
        
        # DTI (Debt Payments / Gross Income)
        dti = min_debt_payments / total_monthly_income if total_monthly_income > 0 else 0
        
        financial_health = FinancialHealthMetrics(
            savings_rate=savings_rate,
            debt_to_income_ratio=dti,
            savings_rate_change=0.02,  # Mock change for demo
            monthly_surplus=surplus,
        )
        
        # 3. Projection (Wealth Growth)
        investable_assets = sum(a.value for a in assets if a.type in [AssetType.EQUITY, AssetType.RETIREMENT, AssetType.CRYPTO])
        # Assume we invest configured percentage of surplus + any existing "Savings" category
        savings_category = sum(s.amount for s in spending_list if s.type == "Savings")
        monthly_contribution = max(0, (surplus * FINANCIAL.SURPLUS_INVESTMENT_ALLOCATION) + savings_category)
        
        projection_result = project_compound_growth(
            principal=investable_assets,
            rate=FINANCIAL.DEFAULT_INVESTMENT_RETURN,
            years=30,
            monthly_contribution=monthly_contribution
        )
        
        projection = ProjectionSummary(
            final_value=projection_result.final_value,
            total_contributions=projection_result.total_contributions,
            total_interest=projection_result.total_interest,
            inflation_adjusted_final_value=projection_result.inflation_adjusted_final_value,
            context=projection_result.context,
            crossover_date=projection_result.crossover_date,
        )
        
        # 4. Debt Payoff
        # Calculate potential extra payment from surplus
        extra_payment = max(0, surplus * FINANCIAL.SURPLUS_DEBT_ALLOCATION)
        
        try:
            snowball_result = simulate_debt_payoff(liabilities, "snowball", extra_payment)
            avalanche_result = simulate_debt_payoff(liabilities, "avalanche", extra_payment)
        except Exception as e:
            logger.error(f"Debt simulation failed: {e}")
            raise SimulationOverflowError("Debt payoff simulation", "maximum calculation time")
        
        debt_payoff = DebtPayoffSummary(
            snowball=DebtPayoffStrategy(
                date_free=snowball_result.date_free,
                interest_paid=snowball_result.interest_paid,
                strategy=snowball_result.strategy,
                series=[p.dict() for p in snowball_result.series],
                reasoning=snowball_result.reasoning,
            ),
            avalanche=DebtPayoffStrategy(
                date_free=avalanche_result.date_free,
                interest_paid=avalanche_result.interest_paid,
                strategy=avalanche_result.strategy,
                series=[p.dict() for p in avalanche_result.series],
                reasoning=avalanche_result.reasoning,
            ),
            comparison=[
                f"Strategy: paying ${extra_payment:,.0f} extra per month.",
                f"Snowball free by {snowball_result.date_free.strftime('%b %Y')}",
                f"Avalanche free by {avalanche_result.date_free.strftime('%b %Y')}",
                f"Avalanche saves ${(snowball_result.interest_paid - avalanche_result.interest_paid):,.0f} in interest.",
            ],
        )
        
        # 5. Spending Breakdown
        spending_breakdown = [
            SpendingBreakdownItem(label=s.category, value=s.amount, type=s.type)
            for s in spending_list
        ]
        spending_breakdown.sort(key=lambda x: x.value, reverse=True)

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
        
        system_status = SystemStatus(
            fixed_costs_covered=total_monthly_income >= obligations,
            debt_strategy_active=True,  # Implicitly true as we have a strategy
            savings_automated=sum(s.amount for s in spending_list if s.type == "Savings") > 0,
            obligations_monthly=obligations,
            income_monthly=total_monthly_income,
        )
        
        return DashboardData(
            net_worth=net_worth_summary,
            financial_health=financial_health,
            projection=projection,
            debt_payoff=debt_payoff,
            spending_breakdown=spending_breakdown,
            daily_allowance=daily_allowance,
            system_status=system_status,
        )

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
        monthly_burn = calculate_total_monthly_spending(spending)
        months_of_runway = total_cash / monthly_burn if monthly_burn > 0 else 0
        if months_of_runway < FINANCIAL.EMERGENCY_FUND_WARNING_MONTHS:
            ideas.append({
                "title": "Build Emergency Fund",
                "description": f"You have {months_of_runway:.1f} months of liquid runway. Aim for {FINANCIAL.EMERGENCY_FUND_TARGET_MONTHS} months.",
                "impact": "Security",
                "type": "warning"
            })
        elif months_of_runway > FINANCIAL.EXCESS_CASH_MONTHS:
            ideas.append({
                "title": "Excess Cash Drag",
                "description": f"You have {months_of_runway:.1f} months of cash. Inflation is eating it. Invest the excess.",
                "impact": "Growth",
                "type": "opportunity"
            })

        # 3. Concentration Risk
        if total_assets > 0:
            for a in assets:
                if a.value / total_assets > FINANCIAL.CONCENTRATION_WARNING_THRESHOLD and len(assets) > 1:
                    ideas.append({
                        "title": f"Concentration in {a.name}",
                        "description": f"{a.name} makes up {a.value/total_assets*100:.0f}% of your assets. Diversify to reduce risk.",
                        "impact": "Risk Reduction",
                        "type": "warning"
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
