import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict, Any, List

from backend.manager import load_json, load_transactions, load_spending_plan, ASSETS_FILE, LIABILITIES_FILE, INCOME_FILE
from backend.models import Asset, Liability, IncomeSource
from backend.primitives import (
    get_net_worth, 
    simulate_debt_payoff, 
    project_compound_growth, 
    assess_affordability,
    generate_insights
)
from backend.primitives.svg_charts import generate_simple_line_chart_svg

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
templates = Jinja2Templates(directory=FRONTEND_DIR)

@app.get("/")
async def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/generative")
async def read_generative(request: Request):
    return templates.TemplateResponse("generative_example.html", {"request": request})

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
async def get_dashboard_view(monthly_payment: float = 500.0, filter_tag: str = "All") -> Dict[str, Any]:
    assets = load_json(ASSETS_FILE, Asset)
    liabilities = load_json(LIABILITIES_FILE, Liability)
    income = load_json(INCOME_FILE, IncomeSource)
    spending = load_spending_plan()
    
    # Calculate Cash Flow
    total_monthly_income = 0
    for i in income:
        if i.frequency == "monthly":
            total_monthly_income += i.amount
        elif i.frequency == "bi-weekly":
            total_monthly_income += i.amount * 26 / 12
        elif i.frequency == "weekly":
            total_monthly_income += i.amount * 52 / 12
        elif i.frequency == "annually":
            total_monthly_income += i.amount / 12

    total_monthly_spending = sum(s.amount for s in spending)
    total_min_debt_payments = sum(l.min_payment for l in liabilities)
    
    free_cash_flow = total_monthly_income - total_monthly_spending - total_min_debt_payments
    
    # Filter liabilities if a specific tag is requested
    if filter_tag != "All":
        liabilities = [l for l in liabilities if filter_tag in l.tags]
    
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

    # 5. Algorithmic Insights
    insights = generate_insights(assets, liabilities, income, spending)

    return {
        "insights": [i.dict() for i in insights],
        "cash_flow": {
            "income": total_monthly_income,
            "spending": total_monthly_spending,
            "debt_min": total_min_debt_payments,
            "free": free_cash_flow
        },
        "net_worth": nw_context.dict(),
        "liabilities": [l.dict() for l in liabilities],
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

# --- HTMX Partials ---

@app.get("/partials/calculate", response_class=HTMLResponse)
async def calculate_partial(request: Request, monthly_payment: float = 500.0, filter_tag: str = "All"):
    data = await get_dashboard_view(monthly_payment, filter_tag)
    
    # Prepare Chart SVG
    chart_svg = generate_simple_line_chart_svg(
        data["debt_payoff"]["snowball"]["series"],
        data["debt_payoff"]["avalanche"]["series"]
    )

    # Prepare Payment Table Data
    liabilities = data["liabilities"]
    # Re-calculate plan as simple list for template
    # 1. Sort by rate (Avalanche logic)
    sorted_liabs = sorted(liabilities, key=lambda x: x["interest_rate"], reverse=True)
    
    total_min = sum(l["min_payment"] for l in sorted_liabs)
    extra = monthly_payment
    
    plan = []
    for l in sorted_liabs:
        row = l.copy()
        row["pay"] = l["min_payment"]
        row["extraAllocation"] = 0
        if extra > 0 and l["balance"] > 0:
            row["extraAllocation"] = extra
            row["pay"] += extra
            extra = 0
        plan.append(row)

    visible_total = sum(item["pay"] for item in plan)
    
    # Format helpers for Jinja
    def format_currency(val):
        return f"${val:,.0f}"
    
    def format_date(d):
        return d.strftime("%b %Y") if hasattr(d, "strftime") else str(d)

    context = {
        "request": request,
        "data": data,
        "chart_svg": chart_svg,
        "plan": plan,
        "visible_total": visible_total,
        "filter_tag": filter_tag,
        "format_currency": format_currency,
        "format_date": format_date
    }
    
    return templates.TemplateResponse("partials/generative_content.html", context)


@app.get("/partials/insights", response_class=HTMLResponse)
async def insights_partial(request: Request, index: int = 0):
    # In a real scenario, we might cache insights or re-generate them. 
    # For statelessness, let's re-generate them quickly.
    assets = load_json(ASSETS_FILE, Asset)
    liabilities = load_json(LIABILITIES_FILE, Liability)
    income = load_json(INCOME_FILE, IncomeSource)
    spending = load_spending_plan()
    
    insights = generate_insights(assets, liabilities, income, spending)
    
    if not insights:
        return ""
        
    # Cycle index safely
    safe_index = index % len(insights)
    insight = insights[safe_index]
    
    context = {
        "request": request,
        "insight": insight,
        "index": safe_index,
        "total": len(insights)
    }
    return templates.TemplateResponse("partials/insight_card.html", context)
