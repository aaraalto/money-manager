import pytest
from app.domain.financial_formulas import (
    calculate_monthly_interest,
    calculate_compound_step,
    calculate_runway,
    calculate_amortization_payment,
    calculate_future_value,
    calculate_present_value,
    calculate_real_return_rate
)

def test_calculate_monthly_interest():
    # 1200 principal, 12% annual rate -> 1% monthly -> 12.0
    assert calculate_monthly_interest(1200, 0.12) == 12.0
    
    # 1000 principal, 6% annual rate -> 0.5% monthly -> 5.0
    assert calculate_monthly_interest(1000, 0.06) == 5.0

def test_calculate_compound_step():
    # 1000 start, 12% annual (1% monthly), 100 contribution
    # Interest = 10, New Balance = 1000 + 10 + 100 = 1110
    assert calculate_compound_step(1000, 0.12, 100) == 1110.0

def test_calculate_runway():
    # 10,000 liquidity, 2,000 burn -> 5 months -> 150 days
    assert calculate_runway(10000, 2000) == 150
    
    # Zero burn -> Infinite runway
    assert calculate_runway(10000, 0) == 9999

def test_calculate_amortization_payment():
    # 100,000 loan, 0% interest, 10 years -> 10,000/yr -> 833.33/mo
    payment = calculate_amortization_payment(100000, 0, 10)
    assert abs(payment - 833.333) < 0.01
    
    # Standard mortgage check: 100k, 5%, 30 years
    # Formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
    # 100,000 * (0.0041666 * 3.4818) / 2.4818 ≈ 536.82
    payment = calculate_amortization_payment(100000, 0.05, 30)
    assert abs(payment - 536.82) < 0.1

def test_calculate_future_value():
    # 1000 principal, 10% annual, 2 years
    # FV = 1000 * (1.00833)^24 ≈ 1220.39
    fv = calculate_future_value(1000, 0.10, 2)
    assert abs(fv - 1220.39) < 0.1

def test_calculate_present_value():
    # Need 1220.39 in 2 years at 10%
    pv = calculate_present_value(1220.39, 0.10, 2)
    assert abs(pv - 1000) < 0.1

def test_calculate_real_return_rate():
    # Nominal 10%, Inflation 3%
    # Real = (1.10 / 1.03) - 1 ≈ 0.06796
    real = calculate_real_return_rate(0.10, 0.03)
    assert abs(real - 0.06796) < 0.0001

