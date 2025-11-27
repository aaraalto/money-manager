from typing import List, Dict, Any, Tuple
from datetime import date, timedelta
import math
from pydantic import BaseModel
from backend.models import Asset, Liability, LiquidityStatus

# --- Response Models ---

class NetWorthContext(BaseModel):
    total: float
    liquid: float
    illiquid: float
    assets_total: float
    liabilities_total: float
    reasoning: List[str]

class TimeSeriesPoint(BaseModel):
    date: date
    value: float
    context: str = ""

class ProjectionContext(BaseModel):
    series: List[TimeSeriesPoint]
    final_value: float
    context: str

class PayoffLog(BaseModel):
    date: date
    balance: float
    payment: float
    debt_name: str
    event: str = ""

class PayoffContext(BaseModel):
    date_free: date
    interest_paid: float
    strategy: str
    log: List[PayoffLog]
    series: List[TimeSeriesPoint]
    reasoning: List[str]

class AffordabilityContext(BaseModel):
    is_safe: bool
    impact_days: int
    new_liquidity: float
    message: str
    risk_level: str # Low, Medium, High

# --- Primitives ---

def get_net_worth(assets: List[Asset], liabilities: List[Liability]) -> NetWorthContext:
    assets_val = sum(a.value for a in assets)
    liabilities_val = sum(l.balance for l in liabilities)
    total = assets_val - liabilities_val
    
    liquid_assets = sum(a.value for a in assets if a.liquidity == LiquidityStatus.LIQUID)
    illiquid_assets = assets_val - liquid_assets
    
    reasoning = [
        f"Total Assets: ${assets_val:,.2f}",
        f"Total Liabilities: ${liabilities_val:,.2f}",
        f"Net Worth = Assets - Liabilities = ${total:,.2f}",
        f"Liquid Assets: ${liquid_assets:,.2f} ({liquid_assets/assets_val:.1%} of total assets)" if assets_val > 0 else "Liquid Assets: $0.00",
    ]
    
    return NetWorthContext(
        total=total,
        liquid=liquid_assets,
        illiquid=illiquid_assets,
        assets_total=assets_val,
        liabilities_total=liabilities_val,
        reasoning=reasoning
    )

def project_compound_growth(
    principal: float, 
    rate: float, 
    years: int, 
    monthly_contribution: float
) -> ProjectionContext:
    series = []
    current_value = principal
    monthly_rate = rate / 12
    start_date = date.today()
    
    context_str = f"Starting with ${principal:,.2f}, contributing ${monthly_contribution:,.2f}/mo at {rate:.1%} APY."
    
    for month in range(years * 12 + 1):
        current_date = start_date + timedelta(days=month*30) # Approx
        
        if month > 0:
            interest = current_value * monthly_rate
            current_value += interest + monthly_contribution
        
        series.append(TimeSeriesPoint(date=current_date, value=current_value))
        
    return ProjectionContext(
        series=series,
        final_value=current_value,
        context=context_str
    )

def simulate_debt_payoff(
    liabilities: List[Liability], 
    strategy: str, 
    extra_monthly_payment: float
) -> PayoffContext:
    # Deep copy to avoid mutating originals
    # In a real app, we'd use deepcopy or re-instantiate
    current_debts = [l.model_copy() for l in liabilities]
    
    total_interest_paid = 0.0
    current_date = date.today()
    logs = []
    series = []
    
    reasoning = [f"Strategy: {strategy.title()}", f"Extra Payment: ${extra_monthly_payment:,.2f}/mo"]
    
    # Sort debts based on strategy
    if strategy.lower() == "avalanche":
        # Highest rate first
        reasoning.append("Targeting highest interest rate debts first to minimize interest paid.")
        current_debts.sort(key=lambda x: x.interest_rate, reverse=True)
    elif strategy.lower() == "snowball":
        # Lowest balance first
        reasoning.append("Targeting lowest balance debts first to build momentum.")
        current_debts.sort(key=lambda x: x.balance)
    else:
        reasoning.append("No specific sorting strategy applied.")

    months_passed = 0
    
    # Initial state
    series.append(TimeSeriesPoint(date=current_date, value=sum(d.balance for d in current_debts)))

    while any(d.balance > 0 for d in current_debts):
        months_passed += 1
        current_date += timedelta(days=30)
        available_extra = extra_monthly_payment
        
        # Accrue interest and pay minimums
        for debt in current_debts:
            if debt.balance <= 0:
                continue
                
            monthly_rate = debt.interest_rate / 12
            interest = debt.balance * monthly_rate
            total_interest_paid += interest
            debt.balance += interest
            
            # Pay minimum
            payment = min(debt.balance, debt.min_payment)
            debt.balance -= payment
            
            # If minimum payment cleared the debt, add remaining min payment to available extra? 
            # Usually snowball adds the cleared minimum to the snowball. 
            # For simplicity here, we just assume fixed extra payment + sum of minimums is the "budget".
            # But the prompt asks for "extra_payment" parameter. 
            # Standard model: Budget = Sum(Min Payments) + Extra. 
            # When a debt is paid off, its min payment becomes available for others.
            
            if debt.balance <= 0:
                 logs.append(PayoffLog(date=current_date, balance=0, payment=payment, debt_name=debt.name, event="PAID OFF"))
                 # The 'freed up' min payment should technically go to the next debt in a real snowball/avalanche
                 available_extra += payment 
            else:
                 pass
                 
        # Apply extra payment to top priority debt
        for debt in current_debts:
            if debt.balance > 0:
                payment = min(debt.balance, available_extra)
                debt.balance -= payment
                available_extra -= payment
                if debt.balance <= 0:
                    logs.append(PayoffLog(date=current_date, balance=0, payment=payment, debt_name=debt.name, event="PAID OFF"))
                
                if available_extra <= 0:
                    break
        
        series.append(TimeSeriesPoint(date=current_date, value=sum(d.balance for d in current_debts)))

        if months_passed > 1200: # Safety break (100 years)
            reasoning.append("Simulation stopped after 100 years. Debts may be unsustainable.")
            break

    return PayoffContext(
        date_free=current_date,
        interest_paid=total_interest_paid,
        strategy=strategy,
        log=logs,
        series=series,
        reasoning=reasoning
    )

def assess_affordability(
    cost: float, 
    liquidity: float, 
    monthly_burn: float
) -> AffordabilityContext:
    new_liquidity = liquidity - cost
    if monthly_burn <= 0:
        impact_days = 9999 # Infinite runway if no burn
    else:
        impact_days = int((new_liquidity / monthly_burn) * 30)
    
    is_safe = True
    risk_level = "Low"
    message = "Purchase is within safe limits."
    
    if new_liquidity < 0:
        is_safe = False
        risk_level = "Critical"
        message = "You cannot afford this. It would put you in debt."
    elif impact_days < 90: # Less than 3 months runway
        is_safe = False
        risk_level = "High"
        message = f"High Risk: Reduces runway to {impact_days/30:.1f} months (Target: 6mo)."
    elif impact_days < 180:
        risk_level = "Medium"
        message = f"Caution: Runway reduces to {impact_days/30:.1f} months."
        
    return AffordabilityContext(
        is_safe=is_safe,
        impact_days=impact_days,
        new_liquidity=new_liquidity,
        message=message,
        risk_level=risk_level
    )

