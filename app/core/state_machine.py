"""
Finite State Machine for onboarding flow.

Provides robust server-side state management for the onboarding process,
replacing the fragile cookie-based approach.
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
import json
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger("state_machine")


class OnboardingState(str, Enum):
    """States in the onboarding flow."""
    WELCOME = "welcome"
    INCOME = "income"
    BURN = "burn"
    DEBT_CHECK = "debt_check"
    DEBT_AMOUNT = "debt_amount"
    ASSETS = "assets"
    RESULT = "result"
    COMPLETED = "completed"


class OnboardingData(BaseModel):
    """Data collected during onboarding."""
    income: Optional[float] = None
    burn: Optional[float] = None
    has_debt: Optional[bool] = None
    debt_amount: float = 0.0
    liquid_assets: float = 0.0
    calculated_level: Optional[int] = None


class OnboardingSession(BaseModel):
    """
    Complete onboarding session state.
    
    Stores both the current state and all collected data.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    state: OnboardingState = OnboardingState.WELCOME
    data: OnboardingData = Field(default_factory=OnboardingData)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def transition(self, new_state: OnboardingState) -> None:
        """Transition to a new state."""
        logger.info(f"Onboarding {self.id}: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.updated_at = datetime.now()
    
    def set_income(self, income: float) -> None:
        """Set income and transition to burn state."""
        self.data.income = income
        self.transition(OnboardingState.BURN)
    
    def set_burn(self, burn: float) -> None:
        """Set burn rate and transition to debt check state."""
        self.data.burn = burn
        self.transition(OnboardingState.DEBT_CHECK)
    
    def set_debt_response(self, has_debt: bool, debt_amount: float = 0.0) -> None:
        """
        Handle debt check response.
        
        If user has debt, transition to result (with calculated level).
        If no debt, transition to assets question.
        """
        self.data.has_debt = has_debt
        self.data.debt_amount = debt_amount
        
        if has_debt and debt_amount > 0:
            # Calculate level and go to result
            self._calculate_level()
            self.transition(OnboardingState.RESULT)
        else:
            # No debt, ask about assets
            self.data.debt_amount = 0.0
            self.transition(OnboardingState.ASSETS)
    
    def set_assets(self, liquid_assets: float) -> None:
        """Set liquid assets and calculate final level."""
        self.data.liquid_assets = liquid_assets
        self._calculate_level()
        self.transition(OnboardingState.RESULT)
    
    def complete(self) -> None:
        """Mark onboarding as completed."""
        self.transition(OnboardingState.COMPLETED)
    
    def _calculate_level(self) -> None:
        """Calculate the user's financial level based on collected data."""
        from app.domain.metrics import calculate_financial_level
        
        self.data.calculated_level = calculate_financial_level(
            monthly_income=self.data.income or 0.0,
            monthly_burn=self.data.burn or 0.0,
            total_debt=self.data.debt_amount,
            liquid_assets=self.data.liquid_assets,
        )
    
    def get_context(self) -> Dict[str, Any]:
        """Get template context for current state."""
        return {
            "session_id": self.id,
            "state": self.state.value,
            "income": self.data.income,
            "burn": self.data.burn,
            "has_debt": self.data.has_debt,
            "debt_amount": self.data.debt_amount,
            "liquid_assets": self.data.liquid_assets,
            "level": self.data.calculated_level,
        }


class OnboardingFSM:
    """
    Finite State Machine manager for onboarding sessions.
    
    Handles session storage and retrieval with in-memory caching
    and optional file persistence.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the FSM manager.
        
        Args:
            storage_dir: Optional directory for persistent storage.
                        If None, sessions are only stored in memory.
        """
        self._sessions: Dict[str, OnboardingSession] = {}
        self._storage_dir = storage_dir
        
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self) -> OnboardingSession:
        """Create a new onboarding session."""
        session = OnboardingSession()
        self._sessions[session.id] = session
        self._persist_session(session)
        logger.info(f"Created new onboarding session: {session.id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """
        Get an existing session by ID.
        
        First checks in-memory cache, then tries file storage.
        """
        # Check memory cache
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Try loading from storage
        session = self._load_session(session_id)
        if session:
            self._sessions[session_id] = session
        
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> OnboardingSession:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Existing or new OnboardingSession
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session()
    
    def update_session(self, session: OnboardingSession) -> None:
        """Update a session in storage."""
        session.updated_at = datetime.now()
        self._sessions[session.id] = session
        self._persist_session(session)
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session from storage."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        if self._storage_dir:
            file_path = self._storage_dir / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
        
        logger.info(f"Deleted onboarding session: {session_id}")
    
    def _persist_session(self, session: OnboardingSession) -> None:
        """Persist session to file storage if configured."""
        if not self._storage_dir:
            return
        
        try:
            file_path = self._storage_dir / f"{session.id}.json"
            with open(file_path, "w") as f:
                json.dump(session.model_dump(mode="json"), f, default=str)
        except Exception as e:
            logger.error(f"Failed to persist session {session.id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Load session from file storage if it exists."""
        if not self._storage_dir:
            return None
        
        try:
            file_path = self._storage_dir / f"{session_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return OnboardingSession(**data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None


# Global FSM instance with in-memory storage
# In production, you might want persistent storage
_onboarding_fsm: Optional[OnboardingFSM] = None


def get_onboarding_fsm() -> OnboardingFSM:
    """Get the global OnboardingFSM instance."""
    global _onboarding_fsm
    if _onboarding_fsm is None:
        # Use in-memory storage for now
        # Could be configured for file persistence: OnboardingFSM(Path("data/sessions"))
        _onboarding_fsm = OnboardingFSM()
    return _onboarding_fsm
