"""
Application configuration constants.
Centralizes all magic numbers and configurable values for easy maintenance.
"""
import os
from typing import Optional


class FinancialConfig:
    """Financial calculation constants and thresholds."""
    
    # ==========================================================================
    # DEBT CONFIGURATION
    # ==========================================================================
    
    # Default interest rate for unknown debt (typical credit card rate)
    DEFAULT_DEBT_INTEREST_RATE: float = 0.22  # 22% APR
    
    # Default minimum payment as percentage of balance
    DEFAULT_MIN_PAYMENT_PERCENT: float = 0.02  # 2% of balance
    
    # Minimum dollar amount for minimum payment
    MIN_PAYMENT_FLOOR: float = 25.0  # $25 minimum
    
    # Threshold for "high interest" debt warnings
    HIGH_INTEREST_THRESHOLD: float = 0.07  # 7% APR
    
    # Threshold for "danger" interest rate (shown in red)
    DANGER_INTEREST_THRESHOLD: float = 0.20  # 20% APR
    
    # ==========================================================================
    # SAVINGS & INVESTMENT CONFIGURATION
    # ==========================================================================
    
    # Default investment return rate (market average)
    DEFAULT_INVESTMENT_RETURN: float = 0.07  # 7% annually
    
    # Default high-yield savings account APY
    DEFAULT_HYSA_APY: float = 0.045  # 4.5% APY
    
    # Low yield threshold (suggest moving to HYSA)
    LOW_YIELD_THRESHOLD: float = 0.03  # 3% APY
    
    # Minimum balance to suggest HYSA optimization
    HYSA_OPTIMIZATION_MIN_BALANCE: float = 1000.0  # $1000
    
    # Safe withdrawal rate for FIRE calculations
    SAFE_WITHDRAWAL_RATE: float = 0.04  # 4% rule
    
    # ==========================================================================
    # ALLOCATION CONFIGURATION  
    # ==========================================================================
    
    # Default surplus allocation to investments
    SURPLUS_INVESTMENT_ALLOCATION: float = 0.50  # 50% of surplus
    
    # Default surplus allocation to debt payoff
    SURPLUS_DEBT_ALLOCATION: float = 0.50  # 50% of surplus
    
    # Minimum free cash flow as percentage of income (warning threshold)
    MIN_FREE_CASH_FLOW_PERCENT: float = 0.10  # 10% of income
    
    # Asset concentration warning threshold
    CONCENTRATION_WARNING_THRESHOLD: float = 0.50  # 50% of portfolio
    
    # ==========================================================================
    # EMERGENCY FUND CONFIGURATION
    # ==========================================================================
    
    # Target emergency fund in months of expenses
    EMERGENCY_FUND_TARGET_MONTHS: int = 6
    
    # Warning threshold (low emergency fund)
    EMERGENCY_FUND_WARNING_MONTHS: int = 3
    
    # Excess cash threshold (cash drag warning)
    EXCESS_CASH_MONTHS: int = 12
    
    # ==========================================================================
    # FIRE (Financial Independence) CONFIGURATION
    # ==========================================================================
    
    # Standard FI multiple (25x annual expenses)
    FI_EXPENSE_MULTIPLE: int = 25  # 25x = 4% withdrawal rate
    
    # Fat FIRE multiple (50x annual expenses)
    FAT_FIRE_EXPENSE_MULTIPLE: int = 50  # 50x = 2% withdrawal rate
    
    # ==========================================================================
    # SIMULATION DEFAULTS
    # ==========================================================================
    
    # Default monthly payment in simulator
    DEFAULT_MONTHLY_PAYMENT: float = 500.0
    
    # Maximum simulation duration (months)
    MAX_SIMULATION_MONTHS: int = 1200  # 100 years
    
    # Days per month for simulation
    DAYS_PER_MONTH: int = 30


class RateLimitConfig:
    """Rate limiting configuration."""
    
    # Maximum requests per window
    REQUESTS_PER_WINDOW: int = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))
    
    # Window size in seconds
    WINDOW_SECONDS: int = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))


class AppConfig:
    """General application configuration."""
    
    # Application name
    APP_NAME: str = "Radiant Money Manager"
    
    # Application version
    VERSION: str = "1.0.0"
    
    # API documentation paths
    DOCS_URL: str = "/api/docs"
    REDOC_URL: str = "/api/redoc"
    
    # Default server configuration
    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 8000
    
    # Cookie configuration
    COOKIE_MAX_AGE: int = 3600  # 1 hour for onboarding cookies


class LogConfig:
    """Logging configuration."""
    
    # Log level (from environment or default)
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Log format
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    # Date format
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

# Financial constants (most commonly used)
FINANCIAL = FinancialConfig()
RATE_LIMIT = RateLimitConfig()
APP = AppConfig()
LOG = LogConfig()
