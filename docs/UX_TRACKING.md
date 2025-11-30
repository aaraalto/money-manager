# UX Tracking System: Gamifying the Ladder

**Objective:** Define the mechanics, metrics, and rewards that drive the user up the Stages of Wealth ladder.

---

## 1. The Core Loop
The application loop is built on the **OODA Loop** (Observe, Orient, Decide, Act), gamified:
1.  **Observe:** See current Level and XP (Cash Flow).
2.  **Orient:** Use the Simulator to find the optimal strategy.
3.  **Decide:** "Commit" to a plan (e.g., set a savings target).
4.  **Act:** Execute the plan (track transactions).
5.  **Reward:** Gain XP, Level Up, Unlock Features.

---

## 2. The "Level Up" Logic
The backend must calculate the user's level in real-time based on their financial data.

| Level | Title | Unlock Condition (Logic) |
| :--- | :--- | :--- |
| **0** | **The Dependent** | Default State. `Expenses > Income`. |
| **1** | **The Solvency Seeker** | `Income > Expenses` (Positive Cash Flow). |
| **2** | **The Stabilizer** | `Total Toxic Debt == 0`. |
| **3** | **The Protector** | `Liquid Assets >= (Monthly Expenses * 6)`. |
| **4** | **The Builder** | `Invested Assets >= (Annual Expenses * 5)`. |
| **5** | **The Independent** | `Safe Withdrawal Rate (4%) >= Annual Expenses`. |
| **6** | **The Abundant** | `Cash Flow >>> Needs`. (Manual specific threshold). |

---

## 3. The "XP" System (Experience Points)
To keep users engaged *between* levels (which can take years), we need a high-frequency feedback loop.

**Metric:** **"Velocity Points" (VP)**
*   **Definition:** The speed at which you are moving toward the next level.
*   **Formula:** `VP = (Monthly Surplus / Monthly Income) * 100`
*   **Example:**
    *   User earns \$10,000. Spends \$9,000. Surplus \$1,000.
    *   **VP = 10.**
    *   User cuts dining out, Surplus goes to \$1,500.
    *   **VP = 15.** (50% boost! Big animation!)

**Visual Feedback:**
*   The **"Velocity Meter"** on the dashboard dashboard glows brighter as VP increases.
*   High VP (>25) unlocks "Speed Multiplier" badges.

---

## 4. Unlockable Rewards (The "Tech Tree")

As users Level Up, they unlock "technologies" (app features). This prevents cognitive overload for beginners.

| Level | Unlocked Feature | Why? |
| :--- | :--- | :--- |
| **0-1** | **Debt Avalanche Simulator** | Focus on the immediate fire. |
| **1** | **"Spending Slasher" Tool** | Optimization is relevant now that solvency is possible. |
| **2** | **High-Yield Savings Logic** | Now that you have cash, where do you put it? |
| **3** | **Compound Interest Projector** | Now that you are investing, look 30 years out. |
| **4** | **FIRE Calculator** | (Financial Independence, Retire Early). |
| **5** | **Estate Planning Module** | Legacy focus. |

---

## 5. UX Metrics (How we measure App Success)

We will track the effectiveness of our UX by measuring **User Progression**.

### Key Performance Indicators (KPIs)
1.  **Level Velocity:** Average time (in months) users spend at Level 1 before reaching Level 2.
2.  **Commit Rate:** % of users who click "Commit" after running a simulation.
3.  **Engagement Frequency:** Do users check the app more often as their "Velocity Points" increase?

### Feedback Loop
*   **"The Monthly Retro":** A gamified summary screen at the end of each month.
    *   "You gained 450 XP this month!"
    *   "You cut your Debt Free Date by 3 months!"
    *   **Action:** Ask user: "How confident do you feel?" (1-5 stars).

---

## 6. Implementation Checklist
- [ ] Define `UserLevel` Enum in backend.
- [ ] Create `calculate_level(assets, liabilities, income, spending)` function.
- [ ] Design icons/badges for Levels 0-6.
- [ ] Build the "Locked Feature" UI state (greyed out with padlock).

