# The Majestic Monolith: Architecture & Design

## Philosophy
This application is built as a **Majestic Monolith**. We reject the premature complexity of microservices and distributed frontends in favor of a single, cohesive, and testable unit.

**Key Principles:**
1.  **Locality of Behavior:** Code that changes together stays together.
2.  **Fat Models, Skinny Controllers:** Business logic lives in the Domain/Service layer, not in HTTP handlers.
3.  **Server-Driven UI:** We use HTMX to deliver dynamic interactivity without the churn of a heavy client-side framework.

## Directory Structure

The `app/` directory is the heart of the system. It is fractal; you can understand the whole by understanding the parts.

```
app/
├── main.py            # The Entry Point (FastAPI App)
├── domain/            # Pure Business Logic (The "Brain")
│   ├── metrics.py     # Financial formulas & calculations
│   ├── debt.py        # Payoff simulations
│   └── ...
├── services/          # Orchestration Layer (The "Nervous System")
│   └── financial.py   # Coordinates data fetching & domain logic
├── data/              # Data Persistence (The "Memory")
│   └── repository.py  # JSON/CSV file handling
├── models.py          # Type Definitions (Pydantic Models)
├── templates/         # UI Structure (Jinja2 HTML)
└── static/            # UI Skin (CSS/JS)
```

## Data Flow

1.  **Request:** A user hits a route in `main.py`.
2.  **Orchestration:** The route handler calls `FinancialService`.
3.  **Retrieval:** `FinancialService` asks `FileRepository` for raw data.
4.  **Logic:** `FinancialService` passes data to `domain/` functions for calculation.
5.  **Response:** `FinancialService` returns a structured object. `main.py` renders it into a Jinja2 template.

## The Game Loop (Level System)

The app is gamified via **Financial Levels** (0-6). This state is calculated dynamically based on the user's financial metrics.

*   **Level 0-2:** Stability (Income > Burn, Debt Payoff)
*   **Level 3:** Growth (Investments)
*   **Level 4+:** Independence (FI/RE)

The logic for these transitions resides in `app/domain/metrics.py`.

## Development & Operations

*   **Run Server:** `python3 manage.py serve`
*   **Audit Data:** `python3 manage.py audit`
*   **Testing:** `pytest` (Coming Soon)

