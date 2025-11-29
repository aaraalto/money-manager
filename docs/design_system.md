# Design System Architecture

This project uses a centralized design system to ensure visual consistency across frontend and backend.

## Core Components

### 1. Design Tokens (`design_system/tokens.json`)
The single source of truth for all visual primitives:
- Colors (Notion-inspired dark palette)
- Spacing (8px grid)
- Typography
- Radius & Shadows

**To update tokens:**
1. Edit `design_system/tokens.json`
2. Run `python scripts/build_tokens.py`
3. The file `frontend/css/variables.css` will be regenerated.

### 2. Component Registry (`design_system/registry.json`)
A manifest of all UI components tracked in the system. This ensures we know exactly what UI elements exist, their status (stable/beta), and where they are defined.

**To track a new component:**
Run the tracking script:
```bash
python scripts/track_component.py
```

### 3. Backend Integration (`backend/design_system.py`)
The backend is aware of the design system. It uses `UIComponent` Pydantic models to define how data should be presented.

**Example Usage (Python):**
```python
from backend.design_system import KPI, Insight

# Create a KPI component definition
kpi = KPI.create(label="Net Worth", value=100000)

# Convert an advisor insight to a UI component
ui_insight = Insight.from_advisor_insight(advisor_insight)
```

## Workflow for New Features

1. **Define**: If it needs new colors/spacing, add to `tokens.json`.
2. **Build**: Create the HTML/CSS/JS implementation.
3. **Track**: Run `python scripts/track_component.py` to register the new component.
4. **Integrate**: Use `backend/design_system.py` if the backend needs to drive this component.

