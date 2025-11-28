from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel
from backend.models import Liability
from .types import TimeSeriesPoint
from .financial_formulas import calculate_monthly_interest

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

def simulate_debt_payoff(
    liabilities: List[Liability], 
    strategy: str, 
    extra_monthly_payment: float,
    start_date: Optional[date] = None,
    max_months: int = 1200,
    days_per_month: int = 30
) -> PayoffContext:
    # Deep copy to avoid mutating originals
    current_debts = [l.model_copy() for l in liabilities]
    
    total_interest_paid = 0.0
    current_date = start_date or date.today()
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
        current_date += timedelta(days=days_per_month)
        available_extra = extra_monthly_payment
        
        # Accrue interest and pay minimums
        for debt in current_debts:
            if debt.balance <= 0:
                continue
                
            interest = calculate_monthly_interest(debt.balance, debt.interest_rate)
            total_interest_paid += interest
            debt.balance += interest
            
            # Pay minimum
            effective_min = debt.min_payment
            if effective_min <= 0:
                # If no min payment set, assume interest-only + 1% principal as a heuristic floor
                # to prevent infinite debt spirals in simulation if extra_payment is low.
                # This mimics typical credit card minimums (Interest + 1% or $25).
                effective_min = max(25.0, (interest + (debt.balance * 0.01)))

            payment = min(debt.balance, effective_min)
            debt.balance -= payment
            
            if debt.balance <= 0:
                logs.append(PayoffLog(date=current_date, balance=0, payment=payment, debt_name=debt.name, event="PAID OFF"))
                # If we overpaid (because min_payment > balance), the remainder shouldn't "create" money
                # but effectively it's just paid off.
                # Wait, min(balance, min_payment) ensures we don't overpay.
                
                # IMPORTANT: If we used 'effective_min' which was > actual configured min_payment (0),
                # does this mean we are 'forcing' the user to pay more? 
                # Yes, because paying $0 min payment is impossible on debt.
                pass
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

        if months_passed > max_months: # Safety break
            reasoning.append(f"Simulation stopped after {max_months/12:.0f} years. Debts may be unsustainable.")
            break

    return PayoffContext(
        date_free=current_date,
        interest_paid=total_interest_paid,
        strategy=strategy,
        log=logs,
        series=series,
        reasoning=reasoning
    )
