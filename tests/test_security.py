"""
Tests for security features.
Ensures security headers and rate limiting work correctly.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestSecurityHeaders:
    """Test that security headers are properly set."""

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options header should be set."""
        response = client.get("/demo")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        """X-Frame-Options header should be set to DENY."""
        response = client.get("/demo")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection(self, client):
        """X-XSS-Protection header should be set."""
        response = client.get("/demo")
        assert "1" in response.headers.get("X-XSS-Protection", "")

    def test_referrer_policy(self, client):
        """Referrer-Policy header should be set."""
        response = client.get("/demo")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_content_security_policy(self, client):
        """Content-Security-Policy header should be set."""
        response = client.get("/demo")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_permissions_policy(self, client):
        """Permissions-Policy header should be set."""
        response = client.get("/demo")
        pp = response.headers.get("Permissions-Policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp

    def test_api_endpoints_no_cache(self, client):
        """API endpoints should have no-cache headers."""
        response = client.get(
            "/api/spending-plan",
            cookies={"demo_user": "euclid"}
        )
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-store" in cache_control or "no-cache" in cache_control


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers_present(self, client):
        """Rate limit headers should be present in responses."""
        response = client.get("/demo")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_decrements(self, client):
        """Rate limit remaining should decrement with each request."""
        response1 = client.get("/demo")
        remaining1 = int(response1.headers.get("X-RateLimit-Remaining", 0))
        
        response2 = client.get("/demo")
        remaining2 = int(response2.headers.get("X-RateLimit-Remaining", 0))
        
        # Remaining should decrease
        assert remaining2 < remaining1

    def test_rate_limit_returns_limit(self, client):
        """X-RateLimit-Limit should return configured limit."""
        response = client.get("/demo")
        limit = response.headers.get("X-RateLimit-Limit")
        assert limit is not None
        assert int(limit) > 0
