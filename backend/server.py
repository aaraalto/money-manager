import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict, Any, List
import uvicorn
from pydantic import BaseModel

from backend.data.repository import FileRepository
from backend.services.financial import FinancialService
from backend.models import SpendingCategory
from backend.primitives.svg_charts import generate_simple_line_chart_svg
from backend.chat_service import ChatService

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
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/generative")
async def read_generative(request: Request):
    return templates.TemplateResponse("generative_example.html", {"request": request})

@app.get("/design-system")
async def read_design_system(request: Request):
    return templates.TemplateResponse("design_system.html", {"request": request})

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
    uvicorn.run(app, host="0.0.0.0", port=8081)
