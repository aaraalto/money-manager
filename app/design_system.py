from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ComponentStatus(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"

class ComponentVariant(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GHOST = "ghost"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"
    INFO = "info"

class UIComponent(BaseModel):
    """
    Base model for any backend-driven UI component.
    Allows the backend to dictate which component should be rendered.
    """
    component_name: str = Field(..., description="The key from the Component Registry")
    variant: Optional[str] = None
    props: Dict[str, Any] = Field(default_factory=dict, description="Props to pass to the frontend component")

class KPI(UIComponent):
    component_name: str = "KPI"
    
    @classmethod
    def create(cls, label: str, value: str | float, trend: Optional[str] = None):
        return cls(
            props={
                "label": label,
                "value": value,
                "trend": trend
            }
        )

class Insight(UIComponent):
    component_name: str = "InsightCard"
    
    @classmethod
    def from_advisor_insight(cls, insight: Any):
        """
        Converts a backend FinancialInsight object into a UI Component definition.
        """
        return cls(
            variant=insight.severity,
            props={
                "title": insight.title,
                "description": insight.description,
                "action_item": insight.action_item
            }
        )

# Registry helper to load the JSON (optional, for validation)
import json
import os

def load_registry(path: str = "design_system/registry.json") -> Dict:
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

