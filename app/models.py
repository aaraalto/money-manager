from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
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
