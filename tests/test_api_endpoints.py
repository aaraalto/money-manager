"""
Tests for API endpoints.
Critical path tests to ensure API contracts are maintained.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test basic health and routing."""

    def test_demo_page_accessible(self, client):
        """Demo selection page should be accessible."""
        response = client.get("/demo")
        assert response.status_code == 200
        assert "Select Demo" in response.text or "Select" in response.text

    def test_root_redirects_to_demo_without_cookie(self, client):
        """Root should redirect to demo when no user selected."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302 or response.status_code == 307
        assert "/demo" in response.headers.get("location", "")

    def test_onboarding_page_accessible(self, client):
        """Onboarding page should be accessible."""
        response = client.get("/onboarding")
        assert response.status_code == 200
        assert "Radiant" in response.text


class TestOnboardingAPI:
    """Test onboarding flow endpoints."""

    def test_step_1_income_valid(self, client):
        """Step 1 should accept valid income and return step 2."""
        response = client.post(
            "/api/onboarding/step-1-income",
            data={"income": "5000"}
        )
        assert response.status_code == 200
        assert "Burn" in response.text or "spend" in response.text.lower()
        assert "onboard_income" in response.cookies

    def test_step_2_burn_valid(self, client):
        """Step 2 should accept valid burn rate and return step 3."""
        # First complete step 1
        client.post("/api/onboarding/step-1-income", data={"income": "5000"})
        
        response = client.post(
            "/api/onboarding/step-2-burn",
            data={"burn": "3000"}
        )
        assert response.status_code == 200
        assert "debt" in response.text.lower() or "Anchor" in response.text
        assert "onboard_burn" in response.cookies

    def test_step_3_debt_with_debt(self, client):
        """Step 3 with debt should calculate level and show result."""
        # Complete steps 1-2
        client.post("/api/onboarding/step-1-income", data={"income": "5000"})
        client.post("/api/onboarding/step-2-burn", data={"burn": "3000"})
        
        response = client.post(
            "/api/onboarding/step-3-debt",
            data={"has_debt": "yes", "debt_amount": "10000"},
            cookies={"onboard_income": "5000", "onboard_burn": "3000"}
        )
        assert response.status_code == 200
        # Should show level result (Level 1 because has debt)
        assert "Level" in response.text or "LEVEL" in response.text

    def test_step_3_debt_no_debt(self, client):
        """Step 3 without debt should proceed to assets step."""
        client.post("/api/onboarding/step-1-income", data={"income": "5000"})
        client.post("/api/onboarding/step-2-burn", data={"burn": "3000"})
        
        response = client.post(
            "/api/onboarding/step-3-debt",
            data={"has_debt": "no", "debt_amount": "0"},
            cookies={"onboard_income": "5000", "onboard_burn": "3000"}
        )
        assert response.status_code == 200
        # Should ask about assets
        assert "asset" in response.text.lower() or "Safety" in response.text or "cash" in response.text.lower()

    def test_step_4_assets(self, client):
        """Step 4 should calculate level based on assets."""
        response = client.post(
            "/api/onboarding/step-4-assets",
            data={"liquid_assets": "20000"},
            cookies={
                "onboard_income": "5000",
                "onboard_burn": "3000",
                "onboard_debt": "0"
            }
        )
        assert response.status_code == 200
        # Should show level result
        assert "Level" in response.text or "LEVEL" in response.text


class TestSimulatorAPI:
    """Test debt simulation endpoints."""

    def test_calculate_partial_returns_html(self, client):
        """Calculate partial should return valid HTML."""
        # Set up demo user cookie
        response = client.get(
            "/partials/calculate",
            params={
                "monthly_payment": "500",
                "strategy": "avalanche",
                "filter_tag": "All"
            },
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_calculate_partial_invalid_payment(self, client):
        """Negative payment should be handled gracefully."""
        response = client.get(
            "/partials/calculate",
            params={
                "monthly_payment": "-100",
                "strategy": "avalanche"
            },
            cookies={"demo_user": "euclid"}
        )
        # Should either return 200 with default value or handle gracefully
        assert response.status_code in [200, 400]

    def test_calculate_partial_invalid_strategy(self, client):
        """Invalid strategy should default to avalanche."""
        response = client.get(
            "/partials/calculate",
            params={
                "monthly_payment": "500",
                "strategy": "invalid_strategy"
            },
            cookies={"demo_user": "euclid"}
        )
        # Should handle gracefully with default
        assert response.status_code == 200

    def test_commit_scenario_valid(self, client):
        """Committing a valid scenario should succeed."""
        response = client.post(
            "/api/commit-scenario",
            data={
                "monthly_payment": "500",
                "strategy": "avalanche"
            },
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
        assert "success" in response.text.lower() or "committed" in response.text.lower()

    def test_commit_scenario_negative_payment(self, client):
        """Committing negative payment should return error."""
        response = client.post(
            "/api/commit-scenario",
            data={
                "monthly_payment": "-100",
                "strategy": "avalanche"
            },
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 400

    def test_commit_scenario_invalid_strategy(self, client):
        """Committing invalid strategy should return error."""
        response = client.post(
            "/api/commit-scenario",
            data={
                "monthly_payment": "500",
                "strategy": "invalid"
            },
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 400


class TestSpendingPlanAPI:
    """Test spending plan endpoints."""

    def test_get_spending_plan(self, client):
        """Get spending plan should return JSON array."""
        response = client.get(
            "/api/spending-plan",
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDashboardAPI:
    """Test dashboard data endpoint."""

    def test_get_view_returns_json(self, client):
        """Dashboard view endpoint should return JSON."""
        response = client.get(
            "/api/view",
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check expected keys
        assert "net_worth" in data
        assert "financial_health" in data
        assert "debt_payoff" in data


class TestDemoUserSelection:
    """Test demo user selection flow."""

    def test_select_euclid_user(self, client):
        """Selecting Euclid should set cookie and redirect."""
        response = client.get(
            "/demo-select",
            params={"user": "euclid"},
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "demo_user" in response.cookies

    def test_select_bill_user(self, client):
        """Selecting Bill should set cookie and redirect."""
        response = client.get(
            "/demo-select",
            params={"user": "bill"},
            follow_redirects=False
        )
        assert response.status_code == 302
        assert response.cookies.get("demo_user") == "bill"


class TestPageRoutes:
    """Test that page routes render correctly."""

    def test_simulator_page(self, client):
        """Simulator page should render."""
        response = client.get(
            "/simulator",
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
        assert "Radiant" in response.text or "simulator" in response.text.lower()

    def test_spending_editor_page(self, client):
        """Spending editor page should render."""
        response = client.get(
            "/spending-editor",
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200

    def test_assets_page(self, client):
        """Assets page should render."""
        response = client.get(
            "/assets",
            cookies={"demo_user": "euclid"}
        )
        assert response.status_code == 200
