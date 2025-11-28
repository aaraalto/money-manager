from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any

from backend.manager import load_json, load_transactions, ASSETS_FILE, LIABILITIES_FILE
from backend.models import Asset, Liability
from backend.primitives import (
    get_net_worth, 
    simulate_debt_payoff, 
    project_compound_growth, 
    assess_affordability
)

app = FastAPI(title="Wealth OS API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
FRONTEND_DIR = Path("frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/generative")
async def read_generative():
    return FileResponse(FRONTEND_DIR / "generative_example.html")

from pydantic import BaseModel

class Scenario(BaseModel):
    query: str
    monthly_payment: float
    results: Dict[str, Any]

SCENARIOS_FILE = Path("data/scenarios.json")

@app.post("/api/save-scenario")
async def save_scenario(scenario: Scenario):
    existing = []
    if SCENARIOS_FILE.exists():
        try:
            with open(SCENARIOS_FILE, "r") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            pass
    
    existing.append(scenario.dict())
    
    # Limit to last 50 scenarios
    if len(existing) > 50:
        existing = existing[-50:]
        
    with open(SCENARIOS_FILE, "w") as f:
        json.dump(existing, f, indent=2, default=str)
        
    return {"status": "success", "count": len(existing)}

@app.get("/api/view")
async def get_dashboard_view(monthly_payment: float = 500.0) -> Dict[str, Any]:
    assets = load_json(ASSETS_FILE, Asset)
    liabilities = load_json(LIABILITIES_FILE, Liability)
    
    # 1. Net Worth
    nw_context = get_net_worth(assets, liabilities)
    
    # 2. Projections (Assumption: $1000/mo contribution, 7% return for 10 years)
    # In a real app, these params would come from the user/UI
    projection = project_compound_growth(
        principal=nw_context.total, 
        rate=0.07, 
        years=10, 
        monthly_contribution=1000.0
    )
    
    # 3. Debt Payoff (Snowball vs Avalanche)
    # We simulate both to show comparison
    snowball = simulate_debt_payoff(liabilities, "snowball", extra_monthly_payment=monthly_payment)
    avalanche = simulate_debt_payoff(liabilities, "avalanche", extra_monthly_payment=monthly_payment)
    
    # 4. Affordability (Example check)
    # Just a placeholder check for the dashboard
    affordability = assess_affordability(cost=5000, liquidity=nw_context.liquid, monthly_burn=3000)

    return {
        "net_worth": nw_context.dict(),
        "liabilities": [l.dict() for l in liabilities],
        "projection": projection.dict(),
        "debt_payoff": {
            "snowball": snowball.dict(),
            "avalanche": avalanche.dict(),
            "comparison": [
                f"Avalanche saves ${(snowball.interest_paid - avalanche.interest_paid):,.2f} in interest vs Snowball.",
                f"Avalanche debt free date: {avalanche.date_free}",
                f"Snowball debt free date: {snowball.date_free}"
            ]
        },
        "affordability_check": affordability.dict()
    }

