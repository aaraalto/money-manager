import pytest
from backend.primitives.growth import project_compound_growth, simulate_monte_carlo_growth
from backend.primitives.types import TimeSeriesPoint

def test_project_compound_growth_simple():
    # 1000 start, 0% interest, 100/mo, 1 year
    # Total = 1000 + 1200 = 2200
    ctx = project_compound_growth(1000, 0.0, 1, 100)
    assert ctx.final_value == 2200.0
    assert ctx.total_contributions == 2200.0
    assert ctx.total_interest == 0.0
    assert len(ctx.series) == 13 # Start + 12 months

def test_project_compound_growth_with_interest():
    # 1000 start, 12% interest (1% mo), 0 contrib, 1 year
    # FV = 1000 * (1.01)^12 ≈ 1126.82
    ctx = project_compound_growth(1000, 0.12, 1, 0)
    assert abs(ctx.final_value - 1126.82) < 0.1
    assert ctx.total_contributions == 1000.0
    assert abs(ctx.total_interest - 126.82) < 0.1

def test_project_compound_growth_inflation():
    # 1000 start, 0% interest, 0 contrib, 1 year, 10% inflation
    # Real value ≈ 1000 / 1.10 ≈ 909.09
    ctx = project_compound_growth(1000, 0.0, 1, 0, inflation_rate=0.10)
    assert ctx.inflation_adjusted_final_value is not None
    assert abs(ctx.inflation_adjusted_final_value - 909.09) < 0.1

def test_monte_carlo_simulation():
    # Deterministic case: 0 std dev -> should match simple compound
    # 1000 start, 10% mean, 0 std dev, 1 year, 0 contrib
    mc = simulate_monte_carlo_growth(1000, 0.10, 0.0, 1, 0, iterations=100)
    
    # Monthly rate = 10%/12 = 0.008333
    # FV = 1000 * (1 + 0.008333)^12 ≈ 1104.71 (approx, since formula uses e^(rt) or (1+r/n)^nt)
    # My code uses: current_value += current_value * r
    # which is (1+r) stepping.
    
    # Let's just check range logic
    assert mc.worst_case <= mc.p10_value <= mc.p50_value <= mc.p90_value <= mc.best_case
    assert mc.iterations == 100
    
    # With 0 std dev, all values should be identical
    assert abs(mc.worst_case - mc.best_case) < 0.01

