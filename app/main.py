import asyncio
from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from typing import List

from app.models import Scenario, SpendingCategory, LiabilityTag
from app.data.repository import FileRepository
from app.services.financial import FinancialService
from app.services.docs_service import DocsService
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Dependencies
def get_repository(request: Request) -> FileRepository:
    user_slug = request.cookies.get("demo_user")
    if user_slug == "bill":
        return FileRepository(root_dir=Path("data/bill"))
    return FileRepository(root_dir=Path("data"))

def get_service(repo: FileRepository = Depends(get_repository)) -> FinancialService:
    return FinancialService(repo)

docs_service = DocsService()

@app.get("/docs", response_class=HTMLResponse)
async def docs_index(request: Request):
    menu = docs_service.get_flat_menu()
    # Default to first item if available, or index
    return templates.TemplateResponse("docs/index.html", {
        "request": request, 
        "menu": menu,
        "title": "Documentation"
    })

@app.get("/docs/{path:path}", response_class=HTMLResponse)
async def docs_page(path: str, request: Request):
    menu = docs_service.get_flat_menu()
    page_data = docs_service.get_page_content(path)
    
    if not page_data:
        return templates.TemplateResponse("docs/index.html", {
            "request": request,
            "menu": menu,
            "title": "Not Found"
        }, status_code=404)

    # Mark active item
    for item in menu:
        if item.get("url") == f"/docs/{path}":
            item["active"] = True
            
    return templates.TemplateResponse("docs/page.html", {
        "request": request,
        "menu": menu,
        "title": page_data["title"],
        "content": page_data["content"]
    })


@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    return templates.TemplateResponse("select_user.html", {"request": request})

@app.get("/demo/burn-rate", response_class=HTMLResponse)
async def demo_burn_rate(request: Request):
    return templates.TemplateResponse("demo/burn-rate.html", {"request": request})

@app.get("/demo-select")
async def select_user(user: str, response: Response):
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(key="demo_user", value=user)
    return redirect

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, repo: FileRepository = Depends(get_repository)):
    if not request.cookies.get("demo_user"):
        return RedirectResponse(url="/demo")

    user = await repo.get_user_profile()
    
    template_name = "templates/dashboard.html"
    if user.current_level == 2:
        template_name = "templates/dashboard_level_2.html"
    elif user.current_level == 3:
         template_name = "templates/dashboard_level_3.html"
    elif user.current_level == 5:
         template_name = "templates/dashboard_level_5.html"

    return templates.TemplateResponse(template_name, {"request": request, "user": user})

@app.get("/simulator", response_class=HTMLResponse)
async def simulator(request: Request, repo: FileRepository = Depends(get_repository)):
    user = await repo.get_user_profile()
    return templates.TemplateResponse("templates/simulator.html", {"request": request, "user": user})

@app.get("/spending-editor", response_class=HTMLResponse)
async def spending_editor(request: Request, repo: FileRepository = Depends(get_repository)):
    user = await repo.get_user_profile()
    return templates.TemplateResponse("spending_editor.html", {"request": request, "user": user})

@app.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request, repo: FileRepository = Depends(get_repository), service: FinancialService = Depends(get_service)):
    user = await repo.get_user_profile()
    data = await service.get_assets_view()
    return templates.TemplateResponse("assets.html", {"request": request, "data": data, "user": user})

@app.get("/api/spending-plan", response_model=List[SpendingCategory])
async def get_spending_plan(repo: FileRepository = Depends(get_repository)):
    return await repo.get_spending_plan()

@app.post("/api/spending-plan")
async def save_spending_plan(plan: List[SpendingCategory], repo: FileRepository = Depends(get_repository)):
    await repo.save_spending_plan(plan)
    return {"status": "success"}

@app.get("/api/view")
async def get_dashboard_data(service: FinancialService = Depends(get_service)):
    data = await service.get_dashboard_data()
    return JSONResponse(content=jsonable_encoder(data))

@app.post("/api/commit-scenario")
async def commit_scenario_endpoint(monthly_payment: float = Form(...), strategy: str = Form("avalanche"), service: FinancialService = Depends(get_service)):
    result = await service.commit_scenario(monthly_payment)
    # Return a redirect or success message
    # HTMX can handle the redirect if we set HX-Redirect header
    response =  {"status": "success", "new_payment": monthly_payment}
    return response

@app.post("/api/save-scenario")
async def save_scenario(scenario: Scenario):
    # Placeholder for saving logic
    return {"status": "success", "scenario": scenario}

@app.get("/partials/calculate", response_class=HTMLResponse)
async def calculate_partial(request: Request, repo: FileRepository = Depends(get_repository)):
    # Get params
    params = request.query_params
    try:
        monthly_payment = float(params.get("monthly_payment", 500))
    except ValueError:
        monthly_payment = 500.0
        
    strategy = params.get("strategy", "avalanche")
    filter_tag = params.get("filter_tag", "All")
    
    # Load Data
    liabilities = await repo.get_liabilities()
    income_list = await repo.get_income()
    spending_list = await repo.get_spending_plan()
    
    # Calculate FCF
    monthly_income = 0
    for i in income_list:
        if i.frequency == "monthly": monthly_income += i.amount
        elif i.frequency == "bi-weekly": monthly_income += i.amount * 26 / 12
        elif i.frequency == "weekly": monthly_income += i.amount * 52 / 12
        elif i.frequency == "annually": monthly_income += i.amount / 12

    # Exclude existing 'Debt Repayment' from spending to avoid double counting
    monthly_spending = sum(s.amount for s in spending_list if s.category != "Debt Repayment")
    
    fcf = monthly_income - monthly_spending - monthly_payment
    
    # Run Simulation
    # 1. Baseline (Minimum Payments Only)
    context_baseline = simulate_debt_payoff(
        liabilities=liabilities,
        strategy=strategy,
        extra_monthly_payment=0
    )
    
    # 2. Current Scenario
    context = simulate_debt_payoff(
        liabilities=liabilities,
        strategy=strategy,
        extra_monthly_payment=monthly_payment
    )
    
    # Format Results
    payoff_date_str = context.date_free.strftime("%b %Y")
    
    # Calculate Savings (Baseline Interest - Scenario Interest)
    interest_saved = context_baseline.interest_paid - context.interest_paid
    
    # Generate Chart
    # We need two series for comparison. For now, generate both strategies
    context_snowball = simulate_debt_payoff(liabilities, "snowball", monthly_payment)
    context_avalanche = simulate_debt_payoff(liabilities, "avalanche", monthly_payment)
    
    chart_svg = generate_simple_line_chart_svg(
        snowball_series=context_snowball.series,
        avalanche_series=context_avalanche.series
    )

    # Extract payoff dates per debt
    payoff_dates = {}
    for log in context.log:
        if log.event == "PAID OFF":
            payoff_dates[log.debt_name] = log.date
            
    # Apply Filter
    if filter_tag and filter_tag != "All":
        filtered_liabilities = [l for l in liabilities if filter_tag in l.tags]
    else:
        filtered_liabilities = liabilities

    # Sort liabilities by payoff date
    sorted_debts = sorted(filtered_liabilities, key=lambda x: payoff_dates.get(x.name, context.date_free))
    
    # Available tags: All, plus standard ones
    tags = ["All"] + [t.value for t in LiabilityTag]

    return templates.TemplateResponse("partials/dashboard_update.html", {
        "request": request,
        "fcf": fcf,
        "payoff_date_str": payoff_date_str,
        "interest_saved": interest_saved,
        "chart_svg": chart_svg,
        "sorted_debts": sorted_debts,
        "payoff_dates": payoff_dates,
        "date_free": context.date_free,
        "filter_tag": filter_tag,
        "tags": tags
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
