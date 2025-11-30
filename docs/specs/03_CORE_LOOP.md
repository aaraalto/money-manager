# Spec 03: The Core Loop (Input -> Feedback -> Reward)

**Goal:** Make financial management feel like a game loop, not data entry.
**The Loop:** **Simulate -> Commit -> Track -> Reward.**

## 1. The Input: "Simulate & Commit"

Instead of just "editing a budget," the user enters a **Simulation Mode**.

### Scene: The Simulator (`/generative`)
*   **Action:** User turns the Rotary Knob to increase debt payment by $200.
*   **Visual:** The "Debt Free Date" slides from *Oct 2027* to *Jan 2026*.
*   **The "Magic Moment":** A "Commit" button pulses.
*   **Interaction:** User taps "Commit".
    *   *Animation:* The new path "locks in" (lines turn from dashed to solid).
    *   *Backend:* Updates `spending_plan.csv`.

## 2. The Feedback: Micro-Interactions

Every successful action triggers immediate sensory feedback.

### Success Toasts
*   **Style:** Small pop-up at bottom of screen.
*   **Content:** "Plan Saved. You just bought yourself 14 months of freedom!"
*   **Icon:** Checkmark or Party Popper.

### The "Filling" Animation
*   **Context:** When adding to Savings or paying Debt.
*   **Visual:** Liquid fill effect or Progress Bar surge.
*   **Sound:** (Optional) Subtle "Coin" or "Click" sound (respecting system mute).

## 3. The Reward: XP & Velocity

We gamify the "boring middle" execution phase.

### Velocity Points (VP)
*   **Display:** A speedometer or gauge on the Dashboard.
*   **Trigger:** Every time `Monthly Surplus` increases, VP goes up.
*   **Notification:** "New Velocity Record! You're moving 15% faster than last month."

### The Monthly Retro (The "Level Complete" Screen)
*   **Timing:** First login of a new month.
*   **UI:** Modal overlay.
*   **Stats:**
    *   "Debt Paid: $1,200"
    *   "Net Worth Change: +$2,500"
    *   "XP Earned: 450"
*   **Action:** "Claim Rewards" (Close modal).

---

## 4. Error Handling (The "Gentle Correction")

*   **Scenario:** User tries to commit a plan where `Expenses > Income`.
*   **Bad Error:** "Invalid Input. Negative Balance."
*   **Good Error:** "Whoops! That plan needs $200 more cash. Check your 'Wants' category?"
*   **Visual:** Highlight the problem area in Warm Amber, shake animation.

