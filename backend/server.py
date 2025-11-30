import json
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict, Any, List, Optional
import uvicorn
from pydantic import BaseModel

from backend.data.repository import FileRepository
from backend.services.financial import FinancialService
from backend.models import SpendingCategory
from backend.primitives.svg_charts import generate_simple_line_chart_svg
from backend.chat_service import ChatService
from backend.primitives.metrics import calculate_financial_level, calculate_monthly_income

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

# Initialize Services
repo = FileRepository()
service = FinancialService(repo)
chat_service = ChatService(templates)

@app.get("/")
async def read_root(request: Request):
    # Check if user has completed onboarding
    profile = await repo.get_user_profile()
    if not profile.onboarding_completed:
        return RedirectResponse(url="/onboarding")
    
    # Helper for currency formatting in templates
    def format_currency(val):
        return f"${val:,.0f}"

    context = {
        "request": request, 
        "user": profile,
        "format_currency": format_currency
    }

    # Level-Specific Dashboard Routing
    if profile.current_level == 1:
        return templates.TemplateResponse("templates/dashboard_level_1.html", context)
    elif profile.current_level == 2:
        return templates.TemplateResponse("templates/dashboard_level_2.html", context)
    else:
        # Default / Level 0 / Level 3+ uses the standard dashboard for now
        # (Or we can map L0 -> Crisis Dashboard later)
        return templates.TemplateResponse("templates/dashboard.html", context)

@app.get("/generative")
async def read_generative(request: Request):
    return templates.TemplateResponse("generative_example.html", {"request": request})

@app.get("/design-system")
async def read_design_system(request: Request):
    return templates.TemplateResponse("design_system.html", {"request": request})

# --- Onboarding Endpoints ---

@app.get("/onboarding")
async def onboarding_page(request: Request):
    # Reset profile if needed or just load current state
    profile = await repo.get_user_profile()
    # We always start at step 1 for now if they go to /onboarding
    return templates.TemplateResponse("onboarding.html", {"request": request, "step": 1, "user": profile})

@app.post("/api/onboarding/import", response_class=HTMLResponse)
async def onboarding_import(request: Request):
    """
    Imports data from the JSON/CSV files in the data directory and auto-completes onboarding.
    """
    # 1. Fetch all data from repo
    income_sources = await repo.get_income()
    spending_plan = await repo.get_spending_plan()
    liabilities = await repo.get_liabilities()
    assets = await repo.get_assets()
    
    # 2. Calculate aggregates
    # Income
    monthly_income = calculate_monthly_income(income_sources)
    
    # Expenses (Burn) - Sum of spending plan categories
    # We exclude "Savings" type if we want pure burn, but for Level 0 check, 
    # burn usually means "Outflows required to live". 
    # Let's sum everything except explicit savings/investments if possible, 
    # or just sum everything for now as "Expenses".
    # Looking at spending_plan.csv, it has a "type" column.
    # Let's assume all spending plan items count as "burn" except maybe savings?
    # For safety in L0 calculation, let's sum all.
    monthly_burn = sum(s.amount for s in spending_plan)
    
    # Debt
    total_debt = sum(l.balance for l in liabilities)
    
    # Liquid Assets
    # Filter assets by liquidity="liquid"
    liquid_assets = sum(a.value for a in assets if a.liquidity == "liquid" or a.type == "cash")

    # 3. Update Profile
    profile = await repo.get_user_profile()
    profile.monthly_income = monthly_income
    profile.monthly_burn = monthly_burn
    profile.total_debt = total_debt
    profile.liquid_assets = liquid_assets
    
    # 4. Calculate Level
    level = calculate_financial_level(
        monthly_income,
        monthly_burn,
        total_debt,
        liquid_assets
    )
    profile.current_level = level
    
    # Save profile (but don't mark complete yet, let them see the result)
    # actually, if we import, we probably want to show the result card immediately.
    await repo.save_user_profile(profile)
    
    # 5. Return the Result Partial
    return templates.TemplateResponse("partials/onboarding_result.html", {
        "request": request, 
        "level": level, 
        "profile": profile
    })

@app.post("/api/onboarding/step-1-income", response_class=HTMLResponse)
async def onboarding_step_1(request: Request, income: float = Form(...)):
    profile = await repo.get_user_profile()
    profile.monthly_income = income
    await repo.save_user_profile(profile)
    
    # Return Step 2 HTML
    return templates.TemplateResponse("partials/onboarding_step_2.html", {"request": request})

@app.post("/api/onboarding/step-2-burn", response_class=HTMLResponse)
async def onboarding_step_2(request: Request, burn: float = Form(...)):
    profile = await repo.get_user_profile()
    profile.monthly_burn = burn
    await repo.save_user_profile(profile)
    
    # Return Step 3 HTML
    return templates.TemplateResponse("partials/onboarding_step_3.html", {"request": request})

@app.post("/api/onboarding/step-3-debt", response_class=HTMLResponse)
async def onboarding_step_3(request: Request, has_debt: str = Form(...), debt_amount: Optional[float] = Form(0.0)):
    profile = await repo.get_user_profile()
    
    if has_debt == "no":
        profile.total_debt = 0.0
    else:
        profile.total_debt = debt_amount
        
    await repo.save_user_profile(profile)
    
    # Calculate Level Preview
    # Note: We are assuming liquid assets = 0 for now or we ask for it?
    # The plan says: "If No: Skip to Liquid Assets check".
    # Let's stick to the simpler flow in the plan spec:
    # "If No: Skip to Liquid Assets check ('Do you have 6 months of expenses saved?')"
    # But the plan implementation section 2.2 just says: Income -> Expenses -> Debt -> Result.
    # Let's infer liquid assets is 0 for simplicity in this first pass, OR add a step if debt is 0.
    
    # For Euclid phase 1, let's keep it simple. 
    # If debt > 0 -> Level 0 or 1.
    # If debt == 0 -> Level 2 check requires liquid assets.
    # Let's add a quick check for liquid assets if debt is 0, otherwise assume 0.
    
    if profile.total_debt == 0:
         return templates.TemplateResponse("partials/onboarding_step_4_assets.html", {"request": request})
    
    # If we have debt, we go straight to calculation
    level = calculate_financial_level(
        profile.monthly_income,
        profile.monthly_burn,
        profile.total_debt,
        0.0 # liquid assets assumed 0 if in debt usually, or not relevant for L0/L1 distinction
    )
    profile.current_level = level
    await repo.save_user_profile(profile)

    return templates.TemplateResponse("partials/onboarding_result.html", {"request": request, "level": level, "profile": profile})

@app.post("/api/onboarding/step-4-assets", response_class=HTMLResponse)
async def onboarding_step_4(request: Request, liquid_assets: float = Form(...)):
    profile = await repo.get_user_profile()
    profile.liquid_assets = liquid_assets
    await repo.save_user_profile(profile)
    
    level = calculate_financial_level(
        profile.monthly_income,
        profile.monthly_burn,
        profile.total_debt,
        profile.liquid_assets
    )
    profile.current_level = level
    await repo.save_user_profile(profile)
    
    return templates.TemplateResponse("partials/onboarding_result.html", {"request": request, "level": level, "profile": profile})


@app.post("/api/onboarding/complete", response_class=HTMLResponse)
async def onboarding_complete(request: Request):
    profile = await repo.get_user_profile()
    profile.onboarding_completed = True
    await repo.save_user_profile(profile)
    
    # Client-side redirect via HX-Redirect or just return a script
    # HTMX handles redirects if we use hx-target="body" or return a generic response with HX-Redirect header
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = "/"
    return response

class Scenario(BaseModel):
    query: str
    monthly_payment: float
    results: Dict[str, Any]

SCENARIOS_FILE = Path("data/scenarios.json")

@app.get("/spending-editor")
async def spending_editor(request: Request):
    return templates.TemplateResponse("spending_editor.html", {"request": request})

@app.get("/api/spending-plan", response_model=List[SpendingCategory])
async def get_spending_plan():
    return await service.get_spending_plan()

@app.post("/api/spending-plan")
async def update_spending_plan(plan: List[SpendingCategory]):
    await service.update_spending_plan(plan)
    return {"status": "success", "count": len(plan)}

@app.post("/api/chat", response_class=HTMLResponse)
async def chat_endpoint(request: Request):
    # Parse form data for hx-post
    form = await request.form()
    query = form.get("query", "")
    
    # Get current context
    assets = await repo.get_assets()
    liabilities = await repo.get_liabilities()
    
    context_data = {
        "assets": [a.dict() for a in assets],
        "liabilities": [l.dict() for l in liabilities]
    }
    
    # Get response (User message HTML + OOB swaps)
    response_html = await chat_service.process_query(query, context_data)
    
    # Return the user message first (echo) + AI response
    user_bubble = f'<div class="message user">{query}</div>'
    return user_bubble + response_html

@app.post("/api/save-scenario")
async def save_scenario(scenario: Scenario):
    # This logic could be moved to repo, but leaving here as it's simple and tangential
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
    return await service.get_dashboard_view(monthly_payment, filter_tag)

# --- HTMX Partials ---

@app.get("/partials/calculate", response_class=HTMLResponse)
async def calculate_partial(request: Request, monthly_payment: float = 500.0, filter_tag: str = "All"):
    data = await service.get_dashboard_view(monthly_payment, filter_tag)
    
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
    insights = await service.get_insights()
    
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
