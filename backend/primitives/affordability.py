from pydantic import BaseModel
from .financial_formulas import calculate_runway

class AffordabilityContext(BaseModel):
    is_safe: bool
    impact_days: int
    new_liquidity: float
    message: str
    risk_level: str # Low, Medium, High

def assess_affordability(
    cost: float, 
    liquidity: float, 
    monthly_burn: float,
    critical_runway_days: int = 90,
    caution_runway_days: int = 180
) -> AffordabilityContext:
    new_liquidity = liquidity - cost
    impact_days = calculate_runway(new_liquidity, monthly_burn)
    
    is_safe = True
    risk_level = "Low"
    message = "Purchase is within safe limits."
    
    if new_liquidity < 0:
        is_safe = False
        risk_level = "Critical"
        message = "You cannot afford this. It would put you in debt."
    elif impact_days < critical_runway_days: # Less than critical threshold (e.g. 3 months)
        is_safe = False
        risk_level = "High"
        message = f"High Risk: Reduces runway to {impact_days/30:.1f} months (Target: {caution_runway_days/30:.0f}mo)."
    elif impact_days < caution_runway_days:
        risk_level = "Medium"
        message = f"Caution: Runway reduces to {impact_days/30:.1f} months."
        
    return AffordabilityContext(
        is_safe=is_safe,
        impact_days=impact_days,
        new_liquidity=new_liquidity,
        message=message,
        risk_level=risk_level
    )
