"""
Tests for financial level calculation.
Critical path tests to ensure users are assigned correct levels.
"""
import pytest
from app.domain.metrics import calculate_financial_level, calculate_monthly_income, calculate_metrics
from app.models import IncomeSource, SpendingCategory, Liability


class TestLevelCalculation:
    """Test suite for financial level assignment."""

    def test_level_0_expenses_exceed_income(self):
        """Level 0: User spending more than they earn (crisis mode)."""
        level = calculate_financial_level(
            monthly_income=3000,
            monthly_burn=4000,  # Spending exceeds income
            total_debt=0,
            liquid_assets=1000
        )
        assert level == 0, "Should be Level 0 when expenses exceed income"

    def test_level_0_exactly_at_break_even(self):
        """Level 0: User exactly at break-even (still okay, but check edge)."""
        level = calculate_financial_level(
            monthly_income=3000,
            monthly_burn=3000,  # Exactly equal
            total_debt=0,
            liquid_assets=1000
        )
        # At break-even, burn is not > income, so should check debt next
        # No debt and some assets, should be Level 2 or higher
        assert level >= 2, "At break-even with no debt should be at least Level 2"

    def test_level_1_has_debt(self):
        """Level 1: User is solvent but has high-interest debt."""
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=3000,
            total_debt=10000,  # Has debt
            liquid_assets=5000
        )
        assert level == 1, "Should be Level 1 when solvent but has debt"

    def test_level_1_even_with_small_debt(self):
        """Level 1 should apply even with small debt amounts."""
        level = calculate_financial_level(
            monthly_income=10000,
            monthly_burn=5000,
            total_debt=100,  # Small debt
            liquid_assets=50000
        )
        assert level == 1, "Any debt > 0 should put user at Level 1"

    def test_level_2_debt_free_building_emergency_fund(self):
        """Level 2: Debt free, building 6-month emergency fund."""
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=3000,
            total_debt=0,  # Debt free
            liquid_assets=10000  # ~3.3 months < 6 months
        )
        assert level == 2, "Should be Level 2 when debt-free but emergency fund < 6 months"

    def test_level_2_almost_full_emergency_fund(self):
        """Level 2 even if emergency fund is close but not quite 6 months."""
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=3000,
            total_debt=0,
            liquid_assets=17999  # Just under 6 months ($18k)
        )
        assert level == 2, "Should still be Level 2 if just under 6 months"

    def test_level_3_full_emergency_fund_growing(self):
        """Level 3: Has 6-month emergency fund, now investing."""
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=3000,
            total_debt=0,
            liquid_assets=20000  # 6+ months, but not FI number
        )
        assert level == 3, "Should be Level 3 with full emergency fund"

    def test_level_3_wealthy_but_not_fi(self):
        """Level 3 for someone wealthy but not yet FI."""
        level = calculate_financial_level(
            monthly_income=10000,
            monthly_burn=5000,
            total_debt=0,
            liquid_assets=500000  # Wealthy but FI number is 5000*300 = 1.5M
        )
        assert level == 3, "Should be Level 3 when wealthy but below FI number"

    def test_level_4_financial_independence(self):
        """Level 4: Has reached basic FI (25x annual expenses)."""
        monthly_burn = 3000
        fi_number = monthly_burn * 300  # $900k
        
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=monthly_burn,
            total_debt=0,
            liquid_assets=fi_number + 1
        )
        assert level == 4, "Should be Level 4 at 25x annual expenses"

    def test_level_5_abundance(self):
        """Level 5: Fat FIRE (50x annual expenses)."""
        monthly_burn = 3000
        fat_fire_number = monthly_burn * 600  # $1.8M
        
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=monthly_burn,
            total_debt=0,
            liquid_assets=fat_fire_number + 1
        )
        assert level == 5, "Should be Level 5 at 50x annual expenses"

    def test_zero_burn_edge_case(self):
        """Handle edge case where monthly burn is 0."""
        level = calculate_financial_level(
            monthly_income=5000,
            monthly_burn=0,
            total_debt=0,
            liquid_assets=1000
        )
        # With 0 burn, emergency fund is technically infinite
        # Should be Level 3+ since 1000 >= 0 * 6
        assert level >= 3, "Zero burn should result in high level"


class TestIncomeCalculation:
    """Test suite for income frequency normalization."""

    def test_monthly_income(self):
        """Monthly income should pass through unchanged."""
        income = [IncomeSource(source="Salary", amount=5000, frequency="monthly")]
        total = calculate_monthly_income(income)
        assert total == 5000

    def test_biweekly_income(self):
        """Bi-weekly income should be converted to monthly."""
        income = [IncomeSource(source="Salary", amount=2000, frequency="bi-weekly")]
        total = calculate_monthly_income(income)
        # 2000 * 26 / 12 = 4333.33
        assert abs(total - 4333.33) < 0.01

    def test_weekly_income(self):
        """Weekly income should be converted to monthly."""
        income = [IncomeSource(source="Side Gig", amount=500, frequency="weekly")]
        total = calculate_monthly_income(income)
        # 500 * 52 / 12 = 2166.67
        assert abs(total - 2166.67) < 0.01

    def test_annual_income(self):
        """Annual income should be converted to monthly."""
        income = [IncomeSource(source="Bonus", amount=12000, frequency="annually")]
        total = calculate_monthly_income(income)
        # 12000 / 12 = 1000
        assert total == 1000

    def test_mixed_frequencies(self):
        """Multiple income sources with different frequencies."""
        income = [
            IncomeSource(source="Salary", amount=4000, frequency="monthly"),
            IncomeSource(source="Side Gig", amount=1000, frequency="bi-weekly"),
            IncomeSource(source="Bonus", amount=6000, frequency="annually"),
        ]
        total = calculate_monthly_income(income)
        # 4000 + (1000 * 26/12) + (6000/12) = 4000 + 2166.67 + 500 = 6666.67
        assert abs(total - 6666.67) < 0.01


class TestMetricsCalculation:
    """Test suite for financial metrics calculation."""

    @pytest.fixture
    def sample_data(self):
        """Sample financial data for metrics tests."""
        income = [IncomeSource(source="Salary", amount=6000, frequency="monthly")]
        spending = [
            SpendingCategory(category="Rent", amount=1500, type="Need"),
            SpendingCategory(category="Food", amount=500, type="Need"),
            SpendingCategory(category="Entertainment", amount=300, type="Want"),
        ]
        liabilities = [
            Liability(
                name="Credit Card",
                balance=5000,
                interest_rate=0.20,
                min_payment=150
            ),
        ]
        return income, spending, liabilities

    def test_savings_rate_calculation(self, sample_data):
        """Test that savings rate is calculated correctly."""
        income, spending, liabilities = sample_data
        metrics = calculate_metrics(income, spending, liabilities)
        
        # Income: $6000
        # Spending: $2300
        # Debt payments: $150
        # Savings: $6000 - $2300 - $150 = $3550
        # Savings rate: $3550 / $6000 = 0.5917
        expected_rate = (6000 - 2300 - 150) / 6000
        assert abs(metrics["savings_rate"] - expected_rate) < 0.01

    def test_debt_to_income_ratio(self, sample_data):
        """Test that DTI is calculated correctly."""
        income, spending, liabilities = sample_data
        metrics = calculate_metrics(income, spending, liabilities)
        
        # DTI = $150 / $6000 = 0.025
        expected_dti = 150 / 6000
        assert abs(metrics["debt_to_income_ratio"] - expected_dti) < 0.01

    def test_zero_income_edge_case(self):
        """Handle zero income without division errors."""
        income = []
        spending = [SpendingCategory(category="Food", amount=500, type="Need")]
        liabilities = []
        
        metrics = calculate_metrics(income, spending, liabilities)
        
        assert metrics["savings_rate"] == 0
        assert metrics["debt_to_income_ratio"] == 0

    def test_negative_savings_rate(self):
        """Savings rate can be negative when spending exceeds income."""
        income = [IncomeSource(source="Salary", amount=2000, frequency="monthly")]
        spending = [
            SpendingCategory(category="Rent", amount=1500, type="Need"),
            SpendingCategory(category="Food", amount=500, type="Need"),
            SpendingCategory(category="Other", amount=500, type="Need"),
        ]
        liabilities = []
        
        metrics = calculate_metrics(income, spending, liabilities)
        
        # Income: $2000, Spending: $2500 = -$500 deficit
        # Savings rate: -500/2000 = -0.25
        assert metrics["savings_rate"] < 0
