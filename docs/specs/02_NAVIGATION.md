# Spec 02: Navigation & Dashboard Architecture

**Goal:** A "Living" Interface that changes as the user evolves.
**Concept:** The UI *is* the Ladder.

## 1. Global Navigation

We move away from a traditional hamburger menu to a **Contextual Tab Bar** (Mobile) or **Sidebar** (Desktop).

### Navigation Items (Dynamic)
1.  **Home (The View):** The current Level's dashboard.
2.  **Strategy (The Lab):** The Simulator / Spending Editor.
3.  **Progress (The Ladder):** A view of the overall Level 0-6 map.
    *   *Why?* Users need to see "What's next?" to stay motivated.

---

## 2. Level-Adaptive Dashboard Views

The `dashboard.html` template will act as a router, serving specific partials based on `user.level`.

### Level 0: The Crisis View (Dependent)
*   **Primary KPI:** **Monthly Deficit**. (Red/Amber).
*   **Main Action:** "Find Cash" (Links to Expense Slasher).
*   **Hidden:** Investment Projections (Don't distract).
*   **Tone:** Urgent but supportive. "We need to stop the bleeding."

### Level 1: The War Room (Solvency Seeker)
*   **Primary KPI:** **Debt Payoff Date**.
*   **Visual:** A large progress bar: "Debt Mountain".
*   **Main Action:** "Attack Debt" (Links to Avalanche Simulator).
*   **Secondary:** "Velocity Points" (How fast are you paying it off?).

### Level 2: The Foundation (Stabilizer)
*   **Primary KPI:** **Runway (Months)**.
*   **Visual:** A "Water Tank" filling up.
*   **Main Action:** "Fill the Tank" (Savings Goals).
*   **Unlocked:** High-Yield Savings Calculator.

### Level 3+: The Growth Engine (Builder)
*   **Primary KPI:** **Net Worth** & **Crossover Date** (Financial Independence).
*   **Visual:** Exponential Growth Curve.
*   **Main Action:** "Optimize Portfolio".

---

## 3. Visualizing "The Ladder"
A dedicated page (`/progress`) showing the full game map.
*   **UI:** Vertical timeline/stepper.
*   **States:**
    *   **Completed:** Green Check, dimmed.
    *   **Current:** Bright, pulsating, interactive.
    *   **Locked:** Padlock icon, blurred details.
*   **Interaction:** Tapping a Locked level shows "Unlock Requirements" (e.g., "Pay off $5,000 more to unlock Level 2").

