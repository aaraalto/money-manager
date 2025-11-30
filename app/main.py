from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.models import Scenario, SpendingCategory
from app.data.repository import FileRepository
from app.services.financial import FinancialService
from app.chat_service import ChatService
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg
from typing import List

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Services
repo = FileRepository()
service = FinancialService(repo)
chat_service = ChatService(templates)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = await repo.get_user_profile()
    return templates.TemplateResponse("templates/dashboard.html", {"request": request, "user": user})

@app.get("/simulator", response_class=HTMLResponse)
async def simulator(request: Request):
    return templates.TemplateResponse("templates/simulator.html", {"request": request})

@app.get("/spending-editor", response_class=HTMLResponse)
async def spending_editor(request: Request):
    return templates.TemplateResponse("spending_editor.html", {"request": request})

@app.get("/api/spending-plan", response_model=List[SpendingCategory])
async def get_spending_plan():
    return await repo.get_spending_plan()

@app.post("/api/spending-plan")
async def save_spending_plan(plan: List[SpendingCategory]):
    await repo.save_spending_plan(plan)
    return {"status": "success"}

@app.get("/api/view")
async def get_dashboard_data():
    data = await service.get_dashboard_data()
    return JSONResponse(content=jsonable_encoder(data))

@app.post("/api/chat", response_class=HTMLResponse)
async def chat_endpoint(request: Request):
    form = await request.form()
    query = str(form.get("query", ""))
    
    assets = await repo.get_assets()
    liabilities = await repo.get_liabilities()
    
    context_data = {
        "assets": [a.dict() for a in assets],
        "liabilities": [l.dict() for l in liabilities]
    }
    
    response_html = await chat_service.process_query(query, context_data)
    user_bubble = f'<div class="message user">{query}</div>'
    return user_bubble + response_html

@app.post("/api/commit-scenario")
async def commit_scenario_endpoint(monthly_payment: float = Form(...), strategy: str = Form("avalanche")):
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
async def calculate_partial(request: Request):
    # Get params
    params = request.query_params
    try:
        monthly_payment = float(params.get("monthly_payment", 500))
    except ValueError:
        monthly_payment = 500.0
        
    strategy = params.get("strategy", "avalanche")
    
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

    monthly_spending = sum(s.amount for s in spending_list)
    # Don't double count debt payment if it's in spending plan
    # Usually debt payment in spending plan is the committed amount
    # We are simulating a NEW amount 'monthly_payment'
    
    fcf = monthly_income - monthly_spending - monthly_payment
    
    # Run Simulation
    context = simulate_debt_payoff(
        liabilities=liabilities,
        strategy=strategy,
        extra_monthly_payment=monthly_payment
    )
    
    # Format Results
    payoff_date_str = context.date_free.strftime("%b %Y")
    interest_paid = context.interest_paid
    
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
    # Maybe compare to minimums only? For now just show interest paid
    html += f'<div class="value negative" id="metric-savings" hx-swap-oob="true">-${interest_paid:,.0f} <span style="font-size: 0.6em; opacity: 0.7;">Interest</span></div>'
    
    # 4. Chart
    html += f'<div id="chart-container" hx-swap-oob="true">{chart_svg}</div>'
    
    # 5. Table (Simplified)
    # Just showing list of debts and their order/payoff date from log
    # Extract payoff dates per debt
    payoff_dates = {}
    for log in context.log:
        if log.event == "PAID OFF":
            payoff_dates[log.debt_name] = log.date
            
    table_rows = ""
    # Sort liabilities by payoff date
    sorted_debts = sorted(liabilities, key=lambda x: payoff_dates.get(x.name, context.date_free))
    
    for l in sorted_debts:
        p_date = payoff_dates.get(l.name, context.date_free).strftime("%b %Y")
        table_rows += f"""
        <tr>
            <td class="cell-name">{l.name}</td>
            <td class="cell-mono">${l.balance:,.0f}</td>
            <td class="cell-mono text-right">{p_date}</td>
        </tr>
        """
        
    html += f"""
    <div id="payment-table-container" hx-swap-oob="true">
        <div class="sim-table-container">
            <table class="sim-table">
                <thead>
                    <tr>
                        <th class="text-left">Debt Name</th>
                        <th class="text-left">Balance</th>
                        <th class="text-right">Payoff Date</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
