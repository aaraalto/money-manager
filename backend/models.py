from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from pydantic import BaseModel, Field, validator

class AssetType(str, Enum):
    CASH = "cash"
    EQUITY = "equity"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    VEHICLE = "vehicle"
    OTHER = "other"

class LiquidityStatus(str, Enum):
    LIQUID = "liquid"
    ILLIQUID = "illiquid"

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

class Transaction(BaseModel):
    date: date
    amount: float = Field(..., description="Positive for income, negative for expense")
    category: str
    merchant: str
    
    @validator("date", pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

class FinancialSnapshot(BaseModel):
    """Represents the user's financial state at a point in time."""
    assets: list[Asset] = []
    liabilities: list[Liability] = []
    transactions: list[Transaction] = []

