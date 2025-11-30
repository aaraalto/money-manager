# New UX Flows: Implementing the Wealth Ladder

**Principle:** Use existing backend primitives (`manager.py`, `server.py`) but re-orchestrate the frontend journey using HTMX to create a "Game Loop."

---

## Flow 1: The "Level 0" Assessment (Onboarding)
**Goal:** Replace the static data load with an interactive initialization that assigns a User Level.

### Technical Flow
1.  **Entry Point (`/`):**
    *   Backend checks if `data/user_meta.json` exists and has a `level`.
    *   **IF Missing:** Redirect to `/onboarding`.
    *   **IF Present:** Render `dashboard.html` with Level-specific partials.

2.  **Onboarding View (`/onboarding`):**
    *   **Step 1 (Income):** Simple form. "What hits your bank account monthly?"
    *   **Step 2 (Burn Rate):** "Roughly how much do you spend?" -> Calculates `Solvency Ratio`.
    *   **Step 3 (Debt Check):** "Do you have consumer debt?" (Y/N). If Y, quick input of Total Balance.
    *   **Calculation:** Backend runs `metrics.calculate_level()`.
    *   **Result:** Returns a "Card" showing the user's starting Level (e.g., "Level 1: Solvency Seeker").

3.  **Transition:**
    *   User clicks "Start My Journey".
    *   Backend initializes empty `assets.json` / `liabilities.json` templates appropriate for that level.
    *   Redirect to Dashboard.

---

## Flow 2: The "Commit" Loop (Simulator -> Reality)
**Goal:** Make the "Future Simulator" actionable by writing results back to the Spending Plan.

### User Story
"I see that paying \$500 more gets me debt-free 2 years earlier. I want to make that my actual plan."

### Technical Flow
1.  **Simulator Interaction (`/generative`):**
    *   User adjusts Rotary Knob to `+$500`.
    *   Chart updates via HTMX (existing functionality).
    *   **NEW:** A "Commit to this Plan" button appears when the value != current plan.

2.  **Action (`POST /api/commit-scenario`):**
    *   **Payload:** `{ "target_monthly_payment": 500, "strategy": "avalanche" }`.
    *   **Backend Logic:**
        *   Reads `spending_plan.csv`.
        *   Finds "Debt Repayment" category.
        *   Updates amount: `current_amount + 500`.
        *   Adjusts "Unallocated Cash" or prompts user to cut from "Wants" if budget is negative.
        *   Saves `spending_plan.csv`.
    
3.  **Feedback:**
    *   Toast Message: "Plan Updated. New Debt Free Date: March 2026."
    *   Redirect to Dashboard (`/`).

---

## Flow 3: The "Level Up" Moment
**Goal:** Celebrate progression and unlock new features.

### Technical Flow
1.  **Trigger:**
    *   Occurs on `GET /` (Dashboard load) OR after a `POST` that changes financial state (e.g., updating a liability balance to 0).

2.  **Backend Logic (`server.py`):**
    *   `current_level = metrics.calculate_level(data)`
    *   `stored_level = user_meta.get("level")`
    *   **IF `current_level > stored_level`:**
        *   Update `user_meta.json`.
        *   Inject a specialized `trigger="load"` HTMX partial: `partials/level_up_modal.html`.

3.  **Frontend Experience:**
    *   **Modal Overlay:** "Congratulations! You reached Level 2: The Stabilizer."
    *   **Unlock Animation:** "Emergency Fund Tracker Unlocked!" (Icon turns from Grey to Color).
    *   **Call to Action:** "Set your Safety Net Goal." (Deep link to the new feature).

---

## Flow 4: The Gamified Dashboard (Level-Adaptive)
**Goal:** Show only what matters for the current Level.

### Architecture
Refactor `dashboard.html` to use Jinja2 conditionals based on `user_level`.

```html
<!-- Pseudo-code for dashboard.html -->
{% if level == 0 %}
    {% include "partials/levels/level_0_crisis.html" %}
    <!-- Shows: Burn Rate, Immediate Cuts needed -->
{% elif level == 1 %}
    {% include "partials/levels/level_1_debt.html" %}
    <!-- Shows: Debt Mountain, Avalanche Progress -->
{% elif level >= 2 %}
    {% include "partials/levels/level_2_stability.html" %}
    <!-- Shows: Emergency Fund Tank, Investment Seed -->
{% endif %}
```

### Component Visibility
| Feature | Level 0 | Level 1 | Level 2 | Level 3+ |
| :--- | :---: | :---: | :---: | :---: |
| **Debt Charts** | **Hero** | **Hero** | Secondary | Hidden |
| **Net Worth** | Hidden | Secondary | Secondary | **Hero** |
| **Investments** | Locked | Locked | Unlocked | **Hero** |
| **Spending Editor**| "Crisis Mode" | "Slasher" | "Optimizer" | "Allocator" |

---

## Implementation Priority
1.  **Backend:** Add `level` logic to `metrics.py`.
2.  **Views:** Create the `onboarding` HTML template.
3.  **Dashboard:** Break `dashboard.html` into `partials/levels/`.

