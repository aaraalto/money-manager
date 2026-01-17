import asyncio
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from typing import List
import html as html_module

from app.models import Scenario, SpendingCategory, LiabilityTag, UserProfile, IncomeSource, Liability, Asset, AssetType
from app.data.repository import FileRepository
from app.services.financial import FinancialService
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg
from app.core.logging import get_logger
from app.core.config import FINANCIAL, RATE_LIMIT, APP

# Module logger
logger = get_logger("main")

# In-memory rate limit storage (use Redis in production)
rate_limit_storage = defaultdict(lambda: {"count": 0, "reset_time": 0})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: Enable XSS filter (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy: Restrict resource loading
        # Note: 'unsafe-inline' is needed for HTMX and inline scripts
        # In production, consider using nonces or hashes
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Permissions-Policy: Restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        # Cache-Control for sensitive endpoints
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or cookie-based user)
        client_ip = request.client.host if request.client else "unknown"
        demo_user = request.cookies.get("demo_user", "")
        client_id = f"{client_ip}:{demo_user}"
        
        current_time = time.time()
        
        # Check rate limit
        client_data = rate_limit_storage[client_id]
        
        # Reset if window expired
        if current_time > client_data["reset_time"]:
            client_data["count"] = 0
            client_data["reset_time"] = current_time + RATE_LIMIT.WINDOW_SECONDS
        
        # Increment counter
        client_data["count"] += 1
        
        # Check if over limit
        if client_data["count"] > RATE_LIMIT.REQUESTS_PER_WINDOW:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": str(int(client_data["reset_time"] - current_time)),
                    "X-RateLimit-Limit": str(RATE_LIMIT.REQUESTS_PER_WINDOW),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(client_data["reset_time"]))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT.REQUESTS_PER_WINDOW)
        response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT.REQUESTS_PER_WINDOW - client_data["count"])
        response.headers["X-RateLimit-Reset"] = str(int(client_data["reset_time"]))
        
        return response


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title=APP.APP_NAME,
    description="Personal finance management application",
    version=APP.VERSION,
    docs_url=APP.DOCS_URL,
    redoc_url=APP.REDOC_URL
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Dependencies
def get_repository(request: Request) -> FileRepository:
    user_slug = request.cookies.get("demo_user")
    if user_slug == "bill":
        return FileRepository(root_dir=Path("data/bill"))
    elif user_slug == "onboarded":
        return FileRepository(root_dir=Path("data/onboarded"))
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
    demo_user = request.cookies.get("demo_user")
    
    # If no user selected, show demo page
    if not demo_user:
        return RedirectResponse(url="/demo")
    
    # For onboarded users, check if onboarding was completed
    if demo_user == "onboarded":
        try:
            user = await repo.get_user_profile()
            if not user.onboarding_completed:
                return RedirectResponse(url="/onboarding")
        except Exception:
            return RedirectResponse(url="/onboarding")
    
    user = await repo.get_user_profile()
    
    # Select dashboard based on level
    template_name = "templates/dashboard.html"
    if user.current_level == 0:
        template_name = "templates/dashboard.html"  # Building Balance
    elif user.current_level == 1:
        template_name = "templates/dashboard_level_1.html"  # Clearing the Path
    elif user.current_level == 2:
        template_name = "templates/dashboard_level_2.html"  # Building Security
    elif user.current_level == 3:
        template_name = "templates/dashboard_level_3.html"  # Building Wealth
    elif user.current_level >= 4:
        template_name = "templates/dashboard_level_5.html"  # Abundance

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
    try:
        data = await service.get_dashboard_data()
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard data: {str(e)}")

@app.post("/api/commit-scenario", response_class=HTMLResponse)
async def commit_scenario_endpoint(monthly_payment: float = Form(...), strategy: str = Form("avalanche"), service: FinancialService = Depends(get_service)):
    # Validate input
    if monthly_payment < 0:
        return HTMLResponse(
            content='<div class="feedback-error">Payment must be non-negative</div>',
            status_code=400
        )
    
    if strategy not in ["avalanche", "snowball"]:
        return HTMLResponse(
            content='<div class="feedback-error">Invalid strategy</div>',
            status_code=400
        )
    
    try:
        result = await service.commit_scenario(monthly_payment)
        # Return success feedback HTML
        return HTMLResponse(
            content=f'''<div class="feedback-success">
                <svg class="success-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <span>Plan committed! Allocating ${monthly_payment:,.0f}/mo to debt payoff.</span>
            </div>''',
            status_code=200
        )
    except Exception as e:
        return HTMLResponse(
            content=f'<div class="feedback-error">Failed to commit: {str(e)}</div>',
            status_code=500
        )

@app.post("/api/save-scenario")
async def save_scenario(scenario: Scenario, repo: FileRepository = Depends(get_repository)):
    # Validate scenario
    if scenario.monthly_payment < 0:
        raise HTTPException(status_code=400, detail="Monthly payment must be non-negative")
    
    if scenario.strategy not in ["avalanche", "snowball"]:
        raise HTTPException(status_code=400, detail="Strategy must be 'avalanche' or 'snowball'")
    
    # TODO: Implement scenario persistence
    # For now, scenarios are calculated on-the-fly, but we could save them to a scenarios.json file
    # await repo.save_scenario(scenario)
    
    return {"status": "success", "scenario": scenario.model_dump()}

# =============================================================================
# ONBOARDING ENDPOINTS
# =============================================================================

@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request):
    """Render the onboarding page."""
    return templates.TemplateResponse("onboarding.html", {"request": request})

@app.post("/api/onboarding/step-1-income", response_class=HTMLResponse)
async def onboarding_step_1(request: Request, income: float = Form(...)):
    """Step 1: Capture monthly income and proceed to burn rate."""
    # Store in session via cookies (stateless approach)
    response = templates.TemplateResponse(
        "partials/onboarding_step_2.html", 
        {"request": request}
    )
    response.set_cookie(key="onboard_income", value=str(income), max_age=3600)
    return response

@app.post("/api/onboarding/step-2-burn", response_class=HTMLResponse)
async def onboarding_step_2(request: Request, burn: float = Form(...)):
    """Step 2: Capture monthly spending and proceed to debt check."""
    response = templates.TemplateResponse(
        "partials/onboarding_step_3.html", 
        {"request": request}
    )
    response.set_cookie(key="onboard_burn", value=str(burn), max_age=3600)
    return response

@app.post("/api/onboarding/step-3-debt", response_class=HTMLResponse)
async def onboarding_step_3(
    request: Request, 
    has_debt: str = Form(...),
    debt_amount: float = Form(0)
):
    """Step 3: Capture debt status and route accordingly."""
    # If user has debt, go to result. If no debt, ask about liquid assets.
    income = float(request.cookies.get("onboard_income", 0))
    burn = float(request.cookies.get("onboard_burn", 0))
    
    if has_debt == "yes" and debt_amount > 0:
        # Calculate level immediately
        from app.domain.metrics import calculate_financial_level
        level = calculate_financial_level(
            monthly_income=income,
            monthly_burn=burn,
            total_debt=debt_amount,
            liquid_assets=0
        )
        response = templates.TemplateResponse(
            "partials/onboarding_result.html",
            {"request": request, "level": level}
        )
        response.set_cookie(key="onboard_debt", value=str(debt_amount), max_age=3600)
        response.set_cookie(key="onboard_level", value=str(level), max_age=3600)
        return response
    else:
        # No debt - ask about liquid assets
        response = templates.TemplateResponse(
            "partials/onboarding_step_4_assets.html",
            {"request": request}
        )
        response.set_cookie(key="onboard_debt", value="0", max_age=3600)
        return response

@app.post("/api/onboarding/step-4-assets", response_class=HTMLResponse)
async def onboarding_step_4(request: Request, liquid_assets: float = Form(...)):
    """Step 4: Capture liquid assets and calculate final level."""
    income = float(request.cookies.get("onboard_income", 0))
    burn = float(request.cookies.get("onboard_burn", 0))
    debt = float(request.cookies.get("onboard_debt", 0))
    
    from app.domain.metrics import calculate_financial_level
    level = calculate_financial_level(
        monthly_income=income,
        monthly_burn=burn,
        total_debt=debt,
        liquid_assets=liquid_assets
    )
    
    response = templates.TemplateResponse(
        "partials/onboarding_result.html",
        {"request": request, "level": level}
    )
    response.set_cookie(key="onboard_assets", value=str(liquid_assets), max_age=3600)
    response.set_cookie(key="onboard_level", value=str(level), max_age=3600)
    return response

@app.post("/api/onboarding/complete")
async def onboarding_complete(request: Request, repo: FileRepository = Depends(get_repository)):
    """Complete onboarding: create user profile and redirect to dashboard."""
    # Retrieve onboarding data from cookies
    income = float(request.cookies.get("onboard_income", 0))
    burn = float(request.cookies.get("onboard_burn", 0))
    debt = float(request.cookies.get("onboard_debt", 0))
    assets = float(request.cookies.get("onboard_assets", 0))
    level = int(request.cookies.get("onboard_level", 0))
    
    # Create/update user profile
    profile = UserProfile(
        name="User",
        current_level=level,
        onboarding_completed=True,
        monthly_income=income,
        monthly_burn=burn,
        total_debt=debt,
        liquid_assets=assets
    )
    await repo.save_user_profile(profile)
    
    # Create initial income source
    if income > 0:
        income_data = [IncomeSource(source="Primary Income", amount=income, frequency="monthly")]
        await repo.save_income(income_data)
    
    # Create initial liability if debt exists
    if debt > 0:
        liabilities = [Liability(
            name="High-Interest Debt",
            balance=debt,
            interest_rate=FINANCIAL.DEFAULT_DEBT_INTEREST_RATE,
            min_payment=max(FINANCIAL.MIN_PAYMENT_FLOOR, debt * FINANCIAL.DEFAULT_MIN_PAYMENT_PERCENT)
        )]
        await repo.save_liabilities(liabilities)
    
    # Create initial asset if liquid assets exist
    if assets > 0:
        from app.models import Asset, AssetType
        asset_list = [Asset(
            name="Cash & Savings",
            type=AssetType.CASH,
            value=assets,
            apy=FINANCIAL.DEFAULT_HYSA_APY
        )]
        await repo.save_assets(asset_list)
    
    # Clear onboarding cookies and redirect
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="demo_user", value="onboarded")
    response.delete_cookie(key="onboard_income")
    response.delete_cookie(key="onboard_burn")
    response.delete_cookie(key="onboard_debt")
    response.delete_cookie(key="onboard_assets")
    response.delete_cookie(key="onboard_level")
    return response

@app.post("/api/onboarding/import", response_class=HTMLResponse)
async def onboarding_import(request: Request, repo: FileRepository = Depends(get_repository)):
    """Import existing data and skip onboarding."""
    # Check if data files exist
    try:
        user = await repo.get_user_profile()
        user.onboarding_completed = True
        await repo.save_user_profile(user)
    except Exception:
        pass
    
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="demo_user", value="default")
    return response

# =============================================================================
# SIMULATION ENDPOINTS
# =============================================================================

@app.get("/partials/calculate", response_class=HTMLResponse)
async def calculate_partial(request: Request, repo: FileRepository = Depends(get_repository)):
    # Get params with validation
    params = request.query_params
    try:
        monthly_payment = float(params.get("monthly_payment", FINANCIAL.DEFAULT_MONTHLY_PAYMENT))
        if monthly_payment < 0:
            monthly_payment = 0.0
    except (ValueError, TypeError):
        monthly_payment = FINANCIAL.DEFAULT_MONTHLY_PAYMENT
        
    strategy = params.get("strategy", "avalanche")
    if strategy not in ["avalanche", "snowball"]:
        strategy = "avalanche"
    
    filter_tag = params.get("filter_tag", "All")
    valid_tags = ["All"] + [t.value for t in LiabilityTag]
    if filter_tag not in valid_tags:
        filter_tag = "All"
    
    try:
        # Load Data
        liabilities = await repo.get_liabilities()
        income_list = await repo.get_income()
        spending_list = await repo.get_spending_plan()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load financial data: {str(e)}")
    
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
        # Compare against tag values (tags are LiabilityTag enums, filter_tag is a string)
        filtered_liabilities = [l for l in liabilities if any(t.value == filter_tag if hasattr(t, 'value') else t == filter_tag for t in l.tags)]
    else:
        filtered_liabilities = liabilities

    table_rows = ""
    # Sort liabilities by payoff date
    sorted_debts = sorted(filtered_liabilities, key=lambda x: payoff_dates.get(x.name, context.date_free))
    
    if not sorted_debts:
        # Empty state - no liabilities to display
        table_rows = """
        <tr>
            <td colspan="5" class="empty-state">
                <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                    <p>No liabilities found.</p>
                    <p style="font-size: 0.85rem;">Add debts to start tracking your payoff journey.</p>
                </div>
            </td>
        </tr>
        """
    else:
        for l in sorted_debts:
            is_paid_off = l.balance <= 0
            row_class = "row-paid-off" if is_paid_off else ""
            
            # Escape user data to prevent XSS
            debt_name_escaped = html_module.escape(l.name)
            
            if is_paid_off:
                p_date = "-"
                pay_action = ""
            else:
                p_date = payoff_dates.get(l.name, context.date_free).strftime("%b %Y")
                # Pay Link (Action) - visible on hover
                # Escape payment_url if present to prevent XSS
                if getattr(l, 'payment_url', None):
                    payment_url_escaped = html_module.escape(l.payment_url)
                    pay_action = f'<a href="{payment_url_escaped}" target="_blank" class="pay-link" title="Pay off {debt_name_escaped}">Pay</a>'
                else:
                    pay_action = f'<a href="/pay/{l.id}" class="pay-link" title="Pay off {debt_name_escaped}">Pay</a>'
                
            apr = f"{l.interest_rate * 100:.1f}%"
            apr_class = "text-danger" if l.interest_rate > FINANCIAL.DANGER_INTEREST_THRESHOLD else ""
            
            table_rows += f"""
            <tr class="{row_class}">
                <td class="cell-name">{debt_name_escaped}</td>
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
    uvicorn.run(app, host=APP.DEFAULT_HOST, port=APP.DEFAULT_PORT)
