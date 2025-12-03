import asyncio
from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from typing import List

from app.models import Scenario, SpendingCategory, LiabilityTag, AssetType
from app.data.repository import FileRepository
from app.services.financial import FinancialService
from app.services.docs_service import DocsService
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg
from app.domain.growth import project_compound_growth
from app.domain.net_worth import get_net_worth

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add format_currency filter
def format_currency(value) -> str:
    """Format a number as USD currency."""
    try:
        if value is None:
            return "$0"
        num_value = float(value)
        return f"${num_value:,.0f}"
    except (ValueError, TypeError):
        return "$0"

templates.env.filters["format_currency"] = format_currency

# Dependencies
def get_repository(request: Request) -> FileRepository:
    user_slug = request.cookies.get("demo_user")
    if user_slug == "bill":
        return FileRepository(root_dir=Path("data/bill"))
    elif user_slug == "level3":
        return FileRepository(root_dir=Path("data/level3"))
    elif user_slug == "level4":
        return FileRepository(root_dir=Path("data/level4"))
    elif user_slug == "level5":
        return FileRepository(root_dir=Path("data/level5"))
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
async def root(request: Request, repo: FileRepository = Depends(get_repository), service: FinancialService = Depends(get_service)):
    if not request.cookies.get("demo_user"):
        return RedirectResponse(url="/demo")

    user = await repo.get_user_profile()
    
    template_name = "templates/dashboard.html"
    template_vars = {"request": request, "user": user}
    
    # For levels 3+, calculate additional financial metrics
    if user.current_level >= 3:
        try:
            assets, liabilities, income_list, spending_list = await asyncio.gather(
                repo.get_assets(),
                repo.get_liabilities(),
                repo.get_income(),
                repo.get_spending_plan()
            )
            
            # Calculate monthly income
            total_monthly_income = 0
            for i in income_list:
                if i.frequency == "monthly": total_monthly_income += i.amount
                elif i.frequency == "bi-weekly": total_monthly_income += i.amount * 26 / 12
                elif i.frequency == "weekly": total_monthly_income += i.amount * 52 / 12
                elif i.frequency == "annually": total_monthly_income += i.amount / 12
            
            # Calculate monthly expenses
            total_monthly_spending = sum(s.amount for s in spending_list) if spending_list else 0
            
            # Get invested assets (equity, retirement, crypto)
            investable_assets = sum(a.value for a in assets if a.type in [AssetType.EQUITY, AssetType.RETIREMENT, AssetType.CRYPTO]) if assets else 0
            
            # Calculate monthly contribution (surplus + savings category)
            surplus = total_monthly_income - total_monthly_spending
            savings_category = sum(s.amount for s in spending_list if s.type == "Savings") if spending_list else 0
            monthly_contribution = max(0, (surplus * 0.5) + savings_category)
            
            # Calculate passive income (4% rule on invested assets)
            passive_income = investable_assets * 0.04 / 12  # Monthly passive income
            
            # Project growth to find FI crossover date
            projection = project_compound_growth(
                principal=investable_assets,
                rate=0.07,
                years=30,
                monthly_contribution=monthly_contribution,
                monthly_expenses_target=total_monthly_spending if total_monthly_spending > 0 else None
            )
            
            crossover_date = projection.crossover_date
            if crossover_date:
                crossover_date_str = crossover_date.strftime("%b %Y")
            else:
                crossover_date_str = "Calculating..."
            
            # Net worth calculation
            net_worth_context = get_net_worth(assets or [], liabilities or [])
            
            # Base template vars for level 3+
            template_vars.update({
                "passive_income": passive_income,
                "crossover_date": crossover_date_str,
                "monthly_contribution": monthly_contribution,
                "net_worth": net_worth_context.total
            })
            
            # For level 4 and 5, calculate safe withdrawal and lifestyle metrics
            if user.current_level >= 4:
                safe_withdrawal_monthly = investable_assets * 0.04 / 12
                lifestyle_cost = total_monthly_spending
                coverage_ratio = safe_withdrawal_monthly / lifestyle_cost if lifestyle_cost > 0 else 0
                years_of_expenses = investable_assets / (lifestyle_cost * 12) if lifestyle_cost > 0 else 0
                
                template_vars.update({
                    "safe_withdrawal": safe_withdrawal_monthly,
                    "lifestyle_cost": lifestyle_cost,
                    "coverage_ratio": coverage_ratio,
                    "years_expenses": years_of_expenses
                })
        except Exception as e:
            # Log error but don't crash - provide defaults
            import traceback
            print(f"Error calculating financial metrics for level {user.current_level}: {e}")
            traceback.print_exc()
            # Provide safe defaults
            template_vars.update({
                "passive_income": 0,
                "crossover_date": "N/A",
                "monthly_contribution": 0,
                "net_worth": user.liquid_assets or 0
            })
            if user.current_level >= 4:
                template_vars.update({
                    "safe_withdrawal": 0,
                    "lifestyle_cost": 0,
                    "coverage_ratio": 0,
                    "years_expenses": 0
                })
    
    if user.current_level == 1:
        template_name = "templates/dashboard_level_1.html"
    elif user.current_level == 2:
        template_name = "templates/dashboard_level_2.html"
    elif user.current_level == 3:
        template_name = "templates/dashboard_level_3.html"
    elif user.current_level == 4:
        template_name = "templates/dashboard_level_4.html"
    elif user.current_level == 5:
        template_name = "templates/dashboard_level_5.html"

    return templates.TemplateResponse(template_name, template_vars)

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
