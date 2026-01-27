"""
Simulation service for debt payoff calculations.

This service encapsulates the business logic for running debt payoff simulations,
separating it from the view layer (HTML generation).
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.models import Liability, IncomeSource, SpendingCategory, LiabilityTag
from app.domain.debt import simulate_debt_payoff, PayoffContext
from app.domain.financial_formulas import calculate_total_monthly_income
from app.domain.svg_charts import generate_simple_line_chart_svg
from app.data.repository import FileRepository
from app.core.config import FINANCIAL


class SimulationParams(BaseModel):
    """Parameters for a debt simulation."""
    monthly_payment: float = FINANCIAL.DEFAULT_MONTHLY_PAYMENT
    strategy: str = "avalanche"
    filter_tag: str = "All"
    
    @classmethod
    def from_query_params(cls, params: Dict[str, str]) -> "SimulationParams":
        """
        Create SimulationParams from query parameters with validation.
        
        Args:
            params: Dictionary of query parameters
            
        Returns:
            Validated SimulationParams
        """
        # Parse monthly_payment with validation
        try:
            monthly_payment = float(params.get("monthly_payment", FINANCIAL.DEFAULT_MONTHLY_PAYMENT))
            if monthly_payment < 0:
                monthly_payment = 0.0
        except (ValueError, TypeError):
            monthly_payment = FINANCIAL.DEFAULT_MONTHLY_PAYMENT
        
        # Validate strategy
        strategy = params.get("strategy", "avalanche")
        if strategy not in ["avalanche", "snowball"]:
            strategy = "avalanche"
        
        # Validate filter_tag
        filter_tag = params.get("filter_tag", "All")
        valid_tags = ["All"] + [t.value for t in LiabilityTag]
        if filter_tag not in valid_tags:
            filter_tag = "All"
            
        return cls(
            monthly_payment=monthly_payment,
            strategy=strategy,
            filter_tag=filter_tag
        )


@dataclass
class SimulationResult:
    """Result of a debt simulation."""
    # Free Cash Flow
    fcf: float
    fcf_is_positive: bool
    
    # Payoff metrics
    payoff_date: date
    payoff_date_str: str
    interest_saved: float
    
    # Strategy contexts
    baseline_context: PayoffContext
    scenario_context: PayoffContext
    snowball_context: PayoffContext
    avalanche_context: PayoffContext
    
    # Chart SVG
    chart_svg: str
    
    # Liabilities with payoff dates
    liabilities: List[Liability]
    filtered_liabilities: List[Liability]
    payoff_dates: Dict[str, date]
    
    # Filter metadata
    filter_tag: str
    available_tags: List[str]


class SimulationService:
    """
    Service for running debt payoff simulations.
    
    Handles all business logic for calculating debt payoff scenarios,
    including baseline vs scenario comparisons, chart generation,
    and filtering.
    """
    
    def __init__(self, repo: FileRepository):
        self.repo = repo
    
    async def run_simulation(self, params: SimulationParams) -> SimulationResult:
        """
        Run a full debt payoff simulation.
        
        Args:
            params: Simulation parameters (payment, strategy, filter)
            
        Returns:
            SimulationResult with all calculated data
        """
        # Load data
        liabilities = await self.repo.get_liabilities()
        income_list = await self.repo.get_income()
        spending_list = await self.repo.get_spending_plan()
        
        # Calculate FCF
        monthly_income = calculate_total_monthly_income(income_list)
        
        # Exclude existing 'Debt Repayment' from spending to avoid double counting
        monthly_spending = sum(s.amount for s in spending_list if s.category != "Debt Repayment")
        
        fcf = monthly_income - monthly_spending - params.monthly_payment
        
        # Run simulations
        # 1. Baseline (Minimum Payments Only)
        baseline_context = simulate_debt_payoff(
            liabilities=liabilities,
            strategy=params.strategy,
            extra_monthly_payment=0
        )
        
        # 2. Current Scenario
        scenario_context = simulate_debt_payoff(
            liabilities=liabilities,
            strategy=params.strategy,
            extra_monthly_payment=params.monthly_payment
        )
        
        # 3. Both strategies for chart comparison
        snowball_context = simulate_debt_payoff(liabilities, "snowball", params.monthly_payment)
        avalanche_context = simulate_debt_payoff(liabilities, "avalanche", params.monthly_payment)
        
        # Calculate interest saved
        interest_saved = baseline_context.interest_paid - scenario_context.interest_paid
        
        # Generate chart SVG
        chart_svg = generate_simple_line_chart_svg(
            snowball_series=snowball_context.series,
            avalanche_series=avalanche_context.series
        )
        
        # Extract payoff dates per debt
        payoff_dates = {}
        for log in scenario_context.log:
            if log.event == "PAID OFF":
                payoff_dates[log.debt_name] = log.date
        
        # Apply filter
        if params.filter_tag and params.filter_tag != "All":
            filtered_liabilities = [
                l for l in liabilities 
                if any(
                    t.value == params.filter_tag if hasattr(t, 'value') else t == params.filter_tag 
                    for t in l.tags
                )
            ]
        else:
            filtered_liabilities = liabilities
        
        # Sort filtered liabilities by payoff date
        filtered_liabilities = sorted(
            filtered_liabilities, 
            key=lambda x: payoff_dates.get(x.name, scenario_context.date_free)
        )
        
        # Available tags for filter dropdown
        available_tags = ["All"] + [t.value for t in LiabilityTag]
        
        return SimulationResult(
            fcf=fcf,
            fcf_is_positive=fcf >= 0,
            payoff_date=scenario_context.date_free,
            payoff_date_str=scenario_context.date_free.strftime("%b %Y"),
            interest_saved=interest_saved,
            baseline_context=baseline_context,
            scenario_context=scenario_context,
            snowball_context=snowball_context,
            avalanche_context=avalanche_context,
            chart_svg=chart_svg,
            liabilities=liabilities,
            filtered_liabilities=filtered_liabilities,
            payoff_dates=payoff_dates,
            filter_tag=params.filter_tag,
            available_tags=available_tags,
        )
