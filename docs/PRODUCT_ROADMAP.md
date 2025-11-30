# Product Roadmap: The Wealth Ladder

**Strategy:** Transformation from "Financial Tool" to "Financial RPG" (Role Playing Game).
**Core Metaphor:** Climbing the Ladder.
**Objective:** Guide users from Level 0 (Dependency) to Level 6 (Abundance).

---

## Phase 1: The Foundation (Levels 0-2)
**Focus:** Crisis Management, Solvency, and Stability.
**Target Audience:** Users with high debt or low runway.

### 1.1 Feature: The "Level 0" Audit (Onboarding)
*   **Concept:** A mandatory "check-in" that determines the user's starting Level.
*   **Logic:**
    *   `IF (Debt Payments > Income) -> Level 0`
    *   `IF (Income > Debt Payments) AND (Debt > 0) -> Level 1`
    *   `IF (Debt == 0) AND (Liquid Assets < 6mo Expenses) -> Level 2`
*   **UX:** A dramatic full-screen assessment. "Let's find your footing."

### 1.2 Feature: The "Debt Slayer" (Level 1 Interface)
*   **Redesign:** The Dashboard transforms into a "War Room."
*   **Primary Visualization:** A giant progress bar for "Total Debt."
*   **Action:** "Commit to the Avalanche."
*   **Simulator Unlock:** Only the "Debt Payoff" simulator is available. Investment simulators are locked to prevent distraction.

### 1.3 Feature: The "Safety Net" (Level 2 Interface)
*   **Unlock Condition:** Debt Balance = $0.
*   **Redesign:** Dashboard shifts to blue/green tones.
*   **Primary Visualization:** A "Water Tank" filling up to 6 months of expenses.
*   **Micro-Interaction:** Every savings deposit plays a satisfying "filling" sound/animation.

---

## Phase 2: The Climb (Levels 3-4)
**Focus:** Accumulation and Independence.
**Target Audience:** Debt-free users building wealth.

### 2.1 Feature: The "Growth Engine" (Level 3 Interface)
*   **Unlock Condition:** Emergency Fund = 100%.
*   **Redesign:** The "Wealth Trajectory" chart (currently in `generative_example.html`) becomes the home screen.
*   **New Metric:** "Crossover Point" – The date when Investment Income > Expenses.

### 2.2 Feature: "Expense Slasher" Minigame
*   **Concept:** Gamified Spending Editor.
*   **Interaction:** Dragging an expense category down immediately moves the "Crossover Point" date closer.
*   **Feedback:** "Cutting Netflix saved you 14 days of working!"

### 2.3 Feature: Simulator Expansion
*   **Unlock:** "Real Estate Scenario," "Career Switch Scenario," "Mini-Retirement Scenario."
*   **Goal:** Modeling "Life Goals" (Level 4 requirement).

---

## Phase 3: The Summit (Levels 5-6)
**Focus:** Freedom, Legacy, and Abundance.
**Target Audience:** High Net Worth Individuals.

### 3.1 Feature: The "Legacy Builder"
*   **Concept:** Tools for estate planning and philanthropy.
*   **Visualization:** "Impact Radius" – How your wealth affects others.

### 3.2 Feature: "Infinite Runway" Mode
*   **Visualization:** The charts change scale. Focus shifts from "Monthly Budget" to "Annual Allocation."

---

## Technical Implementation Plan

| Milestone | Task | Tech Stack |
| :--- | :--- | :--- |
| **M1** | **Global State Management** | Backend (`manager.py`) needs to persist "User Level." |
| **M2** | **Gamified UI Components** | Build reusable `LevelProgressBar`, `LockedFeatureOverlay`. |
| **M3** | **Onboarding Flow** | New HTML/HTMX flow for initial assessment. |
| **M4** | **Dynamic Dashboard** | Dashboard logic that serves different HTML partials based on Level. |

---

## Immediate Next Steps (Sprint 1)
1.  Define the **Level Logic** in `backend/primitives/metrics.py`.
2.  Create the **Onboarding Assessment** HTML.
3.  Refactor `dashboard.html` to support **Level-Specific Views**.

