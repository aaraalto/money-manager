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
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg

app = FastAPI()

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

@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    return templates.TemplateResponse("select_user.html", {"request": request})

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
    
    # Construct OOB Response
    # 1. FCF
    fcf_class = "positive" if fcf >= 0 else "negative"
    html = f'<span class="value {fcf_class}" id="metric-fcf" hx-swap-oob="true">${fcf:,.0f}</span>'
    
    # 2. Date
    html += f'<div class="value date" id="metric-date" hx-swap-oob="true">{payoff_date_str}</div>'
    
    # 3. Savings/Interest
    # Show positive savings
    html += f'<div class="value positive" id="metric-savings" hx-swap-oob="true">${interest_saved:,.0f}</div>'
    
    # 4. Chart
    html += f'<div id="chart-container" hx-swap-oob="true">{chart_svg}</div>'
    
    # 5. Table (With Filtering)
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

    table_rows = ""
    # Sort liabilities by payoff date
    sorted_debts = sorted(filtered_liabilities, key=lambda x: payoff_dates.get(x.name, context.date_free))
    
    for l in sorted_debts:
        is_paid_off = l.balance <= 0
        row_class = "row-paid-off" if is_paid_off else ""
        
        if is_paid_off:
            p_date = "-"
            pay_action = ""
        else:
            p_date = payoff_dates.get(l.name, context.date_free).strftime("%b %Y")
            # Pay Link (Action) - visible on hover
            if getattr(l, 'payment_url', None):
                pay_action = f'<a href="{l.payment_url}" target="_blank" class="pay-link" title="Pay off {l.name}">Pay</a>'
            else:
                pay_action = f'<a href="/pay/{l.id}" class="pay-link" title="Pay off {l.name}">Pay</a>'
            
        apr = f"{l.interest_rate * 100:.1f}%"
        apr_class = "text-danger" if l.interest_rate > 0.2 else ""
        
        table_rows += f"""
        <tr class="{row_class}">
            <td class="cell-name">{l.name}</td>
            <td class="text-right"><span class="badge badge-soft {apr_class}">{apr}</span></td>
            <td class="cell-mono">${l.balance:,.0f}</td>
            <td class="cell-mono text-right">{p_date}</td>
            <td class="cell-action text-right">{pay_action}</td>
        </tr>
        """
        
    html += f"""
    <div id="payment-table-container" hx-swap-oob="true">
        <div class="sim-table-container">
            <table class="sim-table">
                <thead>
                    <tr>
                        <th class="text-left">Debt Name</th>
                        <th class="text-right">APR</th>
                        <th class="text-left">Balance</th>
                        <th class="text-right">Payoff Date</th>
                        <th class="text-right">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    
    # 6. Filters (Dropdown)
    # Generate filter dropdown dynamically
    # Available tags: All, plus standard ones
    tags = ["All"] + [t.value for t in LiabilityTag]
    
    options = ""
    for tag in tags:
        selected = "selected" if tag == filter_tag else ""
        options += f'<option value="{tag}" {selected}>{tag}</option>'
        
    # Clean styled select component
    filter_dropdown = f"""
    <div class="select-wrapper">
        <select class="filter-select" 
                onchange="document.querySelector('[name=filter_tag]').value=this.value; htmx.trigger('#hidden-payment-input', 'change')">
            {options}
        </select>
        <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
    </div>
    """

    html += f'<div id="filter-container" class="filter-row" hx-swap-oob="true">{filter_dropdown}</div>'
    
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
