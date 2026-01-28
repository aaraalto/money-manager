from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

class AssetType(str, Enum):
    CASH = "cash"
    EQUITY = "equity"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    VEHICLE = "vehicle"
    RETIREMENT = "401k"
    OTHER = "other"

class LiquidityStatus(str, Enum):
    LIQUID = "liquid"
    ILLIQUID = "illiquid"

class LiabilityTag(str, Enum):
    CREDIT_CARD = "Credit Card"
    PERSONAL_LOANS = "Personal Loans"
    STUDENT_LOANS = "Student Loans"
    FAMILY_LOAN = "Family Loan"
    TAXES = "Taxes"
    SHORT_FAMILY_LOAN = "Short Family Loan"

class Asset(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: AssetType
    value: float = Field(..., ge=0)
    apy: float = Field(0.0, ge=0, description="Annual Percentage Yield (e.g., 0.05 for 5%)")
    liquidity: LiquidityStatus = LiquidityStatus.LIQUID

class Liability(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    balance: float = Field(..., ge=0)
    interest_rate: float = Field(..., ge=0, description="Annual Interest Rate (e.g., 0.24 for 24%)")
    min_payment: float = Field(..., ge=0)
    payment_url: Optional[str] = None
    credit_limit: Optional[float] = Field(None, ge=0, description="Total credit limit for the account")
    tags: list[LiabilityTag] = []

class IncomeSource(BaseModel):
    source: str
    amount: float = Field(..., ge=0)
    frequency: str = "monthly"  # monthly, bi-weekly, etc.
    
    class Config:
        extra = "ignore"  # Ignore extra fields like 'tags' if present

class SpendingCategory(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: str
    amount: float = Field(..., ge=0)
    type: str  # Need, Want, Savings
    owner: str = "Me"
    description: Optional[str] = None
    notes: Optional[str] = None
    roi_potential: Optional[str] = None

class Transaction(BaseModel):
    date: date
    amount: float = Field(..., description="Positive for income, negative for expense")
    category: str
    merchant: str
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

class UserProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = "Euclid"
    current_level: int = Field(0, ge=0, le=6)
    previous_level: Optional[int] = Field(None, ge=0, le=6, description="Previous level for level-up detection")
    onboarding_completed: bool = False
    monthly_income: float = 0.0
    monthly_burn: float = 0.0
    total_debt: float = 0.0
    liquid_assets: float = 0.0


class FinancialSnapshot(BaseModel):
    """Represents the user's financial state at a point in time."""
    assets: list[Asset] = []
    liabilities: list[Liability] = []
    transactions: list[Transaction] = []
    user: Optional[UserProfile] = None


class Scenario(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = "New Scenario"
    monthly_payment: float = Field(..., ge=0)
    strategy: str = "avalanche"
    created_at: date = Field(default_factory=date.today)


# =============================================================================
# FINANCIAL TASKS & EXPENSES (for mnm CLI)
# =============================================================================

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCategory(str, Enum):
    PAYMENT = "payment"
    REVIEW = "review"
    INVESTMENT = "investment"
    TAX = "tax"
    OTHER = "other"


class RecurrenceType(str, Enum):
    NONE = "none"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class FinancialTask(BaseModel):
    """A financial task, reminder, or scheduled action."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.OTHER
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0, description="Associated amount if applicable")
    linked_liability_id: Optional[UUID] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class UpcomingExpense(BaseModel):
    """A scheduled or recurring expense."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    amount: float = Field(..., ge=0)
    due_date: date
    recurrence: RecurrenceType = RecurrenceType.NONE
    category: str
    auto_pay: bool = False
    notes: Optional[str] = None


# =============================================================================
# TYPED RESPONSE MODELS
# =============================================================================

class FinancialHealthMetrics(BaseModel):
    """Metrics about the user's financial health."""
    savings_rate: float = Field(..., description="Percentage of income saved (0.0-1.0)")
    debt_to_income_ratio: float = Field(..., description="DTI ratio (0.0-1.0+)")
    savings_rate_change: float = Field(0.0, description="Change vs previous period")
    monthly_surplus: float = Field(..., description="Income minus expenses")


class SpendingBreakdownItem(BaseModel):
    """A single item in the spending breakdown."""
    label: str
    value: float
    type: str  # Need, Want, Savings


class SystemStatus(BaseModel):
    """Status indicators for the user's financial system."""
    fixed_costs_covered: bool = Field(..., description="Whether income covers fixed costs")
    debt_strategy_active: bool = Field(..., description="Whether a debt payoff strategy is active")
    savings_automated: bool = Field(..., description="Whether savings are automated")
    obligations_monthly: float = Field(..., description="Total monthly obligations")
    income_monthly: float = Field(..., description="Total monthly income")


class DebtPayoffStrategy(BaseModel):
    """Results for a single debt payoff strategy."""
    date_free: date
    interest_paid: float
    strategy: str
    series: list = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    
    class Config:
        # Allow arbitrary types for the series (TimeSeriesPoint objects)
        arbitrary_types_allowed = True


class DebtPayoffSummary(BaseModel):
    """Summary of debt payoff projections."""
    snowball: DebtPayoffStrategy
    avalanche: DebtPayoffStrategy
    comparison: list[str] = Field(default_factory=list)


class ProjectionSummary(BaseModel):
    """Summary of wealth projection."""
    final_value: float
    total_contributions: float
    total_interest: float
    inflation_adjusted_final_value: Optional[float] = None
    context: str
    crossover_date: Optional[date] = None


class NetWorthSummary(BaseModel):
    """Summary of net worth calculation."""
    total: float
    liquid: float
    illiquid: float
    assets_total: float
    liabilities_total: float
    reasoning: list[str] = Field(default_factory=list)


class DashboardData(BaseModel):
    """Complete dashboard data response - fully typed for IDE support."""
    net_worth: NetWorthSummary
    financial_health: FinancialHealthMetrics
    projection: ProjectionSummary
    debt_payoff: DebtPayoffSummary
    spending_breakdown: list[SpendingBreakdownItem]
    daily_allowance: float
    system_status: SystemStatus
