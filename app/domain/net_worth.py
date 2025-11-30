from typing import List
from pydantic import BaseModel
from app.models import Asset, Liability, LiquidityStatus

class NetWorthContext(BaseModel):
    total: float
    liquid: float
    illiquid: float
    assets_total: float
    liabilities_total: float
    reasoning: List[str]

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

