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
from app.services.simulation import SimulationService, SimulationParams
from app.views.simulation_partials import render_simulation_partial
from app.domain.debt import simulate_debt_payoff
from app.domain.svg_charts import generate_simple_line_chart_svg
from app.core.logging import get_logger
from app.core.config import FINANCIAL, RATE_LIMIT, APP
from app.core.state_machine import get_onboarding_fsm, OnboardingSession

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

def get_simulation_service(repo: FileRepository = Depends(get_repository)) -> SimulationService:
    return SimulationService(repo)

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
    
    # Level-up detection
    level_up_detected = False
    previous_level = user.previous_level
    new_level = user.current_level
    unlocked_feature = None
    
    if previous_level is not None and user.current_level > previous_level:
        level_up_detected = True
        # Determine unlocked feature based on new level
        feature_unlocks = {
            1: "Debt Strategy Simulator",
            2: "Emergency Fund Tracker",
            3: "Investment Portfolio",
            4: "Withdrawal Calculator",
            5: "Legacy Planning Tools",
        }
        unlocked_feature = feature_unlocks.get(user.current_level)
        
        # Update previous_level to current (so we don't show again)
        user.previous_level = user.current_level
        await repo.save_user_profile(user)
    
    # Select dashboard based on level
    template_name = "pages/dashboard.html"
    if user.current_level == 0:
        template_name = "pages/dashboard.html"  # Crisis mode
    elif user.current_level == 1:
        template_name = "pages/dashboard_level_1.html"  # Debt war room
    elif user.current_level == 2:
        template_name = "pages/dashboard_level_2.html"  # Stability
    elif user.current_level == 3:
        template_name = "pages/dashboard_level_3.html"  # Growth
    elif user.current_level >= 4:
        template_name = "pages/dashboard_level_5.html"  # FI/RE

    return templates.TemplateResponse(
        template_name, 
        {
            "request": request, 
            "user": user,
            "level_up_detected": level_up_detected,
            "previous_level": previous_level,
            "new_level": new_level,
            "unlocked_feature": unlocked_feature,
        }
    )

@app.get("/simulator", response_class=HTMLResponse)
async def simulator(request: Request, repo: FileRepository = Depends(get_repository)):
    user = await repo.get_user_profile()
    return templates.TemplateResponse("pages/simulator.html", {"request": request, "user": user})

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
# ONBOARDING ENDPOINTS (FSM-Based)
# =============================================================================

def _get_session_from_request(request: Request) -> OnboardingSession:
    """
    Get or create an onboarding session from the request.
    
    Uses session_id cookie if present, otherwise creates a new session.
    """
    fsm = get_onboarding_fsm()
    session_id = request.cookies.get("onboard_session")
    return fsm.get_or_create_session(session_id)


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request):
    """Render the onboarding page with a new session."""
    session = _get_session_from_request(request)
    response = templates.TemplateResponse(
        "onboarding.html", 
        {"request": request, **session.get_context()}
    )
    # Set session cookie for subsequent requests
    response.set_cookie(key="onboard_session", value=session.id, max_age=3600)
    return response


@app.post("/api/onboarding/step-1-income", response_class=HTMLResponse)
async def onboarding_step_1(request: Request, income: float = Form(...)):
    """Step 1: Capture monthly income and proceed to burn rate."""
    session = _get_session_from_request(request)
    session.set_income(income)
    
    fsm = get_onboarding_fsm()
    fsm.update_session(session)
    
    response = templates.TemplateResponse(
        "partials/onboarding_step_2.html", 
        {"request": request, **session.get_context()}
    )
    response.set_cookie(key="onboard_session", value=session.id, max_age=3600)
    return response


@app.post("/api/onboarding/step-2-burn", response_class=HTMLResponse)
async def onboarding_step_2(request: Request, burn: float = Form(...)):
    """Step 2: Capture monthly spending and proceed to debt check."""
    session = _get_session_from_request(request)
    session.set_burn(burn)
    
    fsm = get_onboarding_fsm()
    fsm.update_session(session)
    
    response = templates.TemplateResponse(
        "partials/onboarding_step_3.html", 
        {"request": request, **session.get_context()}
    )
    response.set_cookie(key="onboard_session", value=session.id, max_age=3600)
    return response


@app.post("/api/onboarding/step-3-debt", response_class=HTMLResponse)
async def onboarding_step_3(
    request: Request, 
    has_debt: str = Form(...),
    debt_amount: float = Form(0)
):
    """Step 3: Capture debt status and route accordingly."""
    session = _get_session_from_request(request)
    
    # Process debt response using FSM
    session.set_debt_response(
        has_debt=has_debt == "yes",
        debt_amount=debt_amount if has_debt == "yes" else 0.0
    )
    
    fsm = get_onboarding_fsm()
    fsm.update_session(session)
    
    context = {"request": request, **session.get_context()}
    
    # FSM determines next template based on state
    if session.data.has_debt and session.data.debt_amount > 0:
        template_name = "partials/onboarding_result.html"
        context["level"] = session.data.calculated_level
    else:
        template_name = "partials/onboarding_step_4_assets.html"
    
    response = templates.TemplateResponse(template_name, context)
    response.set_cookie(key="onboard_session", value=session.id, max_age=3600)
    return response


@app.post("/api/onboarding/step-4-assets", response_class=HTMLResponse)
async def onboarding_step_4(request: Request, liquid_assets: float = Form(...)):
    """Step 4: Capture liquid assets and calculate final level."""
    session = _get_session_from_request(request)
    session.set_assets(liquid_assets)
    
    fsm = get_onboarding_fsm()
    fsm.update_session(session)
    
    response = templates.TemplateResponse(
        "partials/onboarding_result.html",
        {"request": request, "level": session.data.calculated_level, **session.get_context()}
    )
    response.set_cookie(key="onboard_session", value=session.id, max_age=3600)
    return response


@app.post("/api/onboarding/complete")
async def onboarding_complete(request: Request, repo: FileRepository = Depends(get_repository)):
    """Complete onboarding: create user profile and redirect to dashboard."""
    session = _get_session_from_request(request)
    
    # Extract data from FSM session
    data = session.data
    income = data.income or 0.0
    burn = data.burn or 0.0
    debt = data.debt_amount
    assets = data.liquid_assets
    level = data.calculated_level or 0
    
    # Create/update user profile
    profile = UserProfile(
        name="User",
        current_level=level,
        previous_level=None,  # First time, no previous level
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
        asset_list = [Asset(
            name="Cash & Savings",
            type=AssetType.CASH,
            value=assets,
            apy=FINANCIAL.DEFAULT_HYSA_APY
        )]
        await repo.save_assets(asset_list)
    
    # Mark session as completed and clean up
    session.complete()
    fsm = get_onboarding_fsm()
    fsm.delete_session(session.id)
    
    # Redirect with proper cookies
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="demo_user", value="onboarded")
    response.delete_cookie(key="onboard_session")
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
    
    # Clean up any existing session
    session_id = request.cookies.get("onboard_session")
    if session_id:
        fsm = get_onboarding_fsm()
        fsm.delete_session(session_id)
    
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="demo_user", value="default")
    response.delete_cookie(key="onboard_session")
    return response

# =============================================================================
# SIMULATION ENDPOINTS
# =============================================================================

@app.get("/partials/calculate", response_class=HTMLResponse)
async def calculate_partial(
    request: Request, 
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Calculate and render debt payoff simulation results.
    
    This endpoint handles HTMX requests from the simulator page,
    returning HTML fragments for out-of-band swaps.
    """
    try:
        # Parse and validate parameters
        params = SimulationParams.from_query_params(dict(request.query_params))
        
        # Run simulation
        result = await simulation_service.run_simulation(params)
        
        # Render HTML response
        return render_simulation_partial(result)
        
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run simulation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP.DEFAULT_HOST, port=APP.DEFAULT_PORT)
