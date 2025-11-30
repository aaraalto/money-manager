# UX Audit: The Static Dashboard Problem

**Date:** November 30, 2025
**Reviewer:** AI Product Designer
**Scope:** Dashboard, Spending Editor, Future Simulator

## 1. Executive Summary
The current application functions as a **competent calculator but a poor coach**. It successfully displays financial data (Net Worth, Debt Payoff) but fails to contextualize *where* the user is in their financial lifecycle.

The user experience is **static and anxiety-inducing**. It presents the "hard truth" (e.g., "You are burning money") without providing a structured, gamified path out of the hole. It feels like a report card, not a video game.

To align with the **Stages of Wealth** model, the app must shift from "monitoring" to "leveling up."

---

## 2. Flow Analysis & Friction Points

### A. The Dashboard (`dashboard.html`)
*   **Current State:** A collection of disconnected cards (Financial Health, Net Worth, Debt Plan).
*   **The Friction:**
    *   **No Narrative:** There is no "You are Here" indicator. A user with \$50k debt sees the same UI structure as a user with \$1M assets.
    *   **Read-Only Anxiety:** The "Quick Insights" tell you what's wrong (e.g., "Runway is too short") but don't offer an immediate action button to fix it.
    *   **Metric Overload:** "Debt-to-Income," "Savings Rate," "Liquid Assets" are thrown at the user simultaneously.
*   **Verdict:** Functional, but emotionally flat. It fails to answer: "What is the *one* thing I need to do today?"

### B. The Spending Editor (`spending_editor.html`)
*   **Current State:** A spreadsheet-like interface for editing categories.
*   **The Friction:**
    *   **Chore vs. Strategy:** Editing rows feels like tax work. It should feel like "optimizing the engine."
    *   **Lack of Feedback:** Cutting "Dining Out" by \$200 updates a number, but it doesn't visually show how much *faster* I reach Financial Freedom.
*   **Verdict:** High friction. Needs to be gamified: "Find \$200 to unlock Level 2."

### C. The Future Simulator (`generative_example.html`)
*   **Current State:** An interactive rotary knob to test monthly payments.
*   **The Magic Moment:** This is the strongest feature. Seeing the curve change instantly is high-dopamine.
*   **The Friction:**
    *   **Disconnected:** It lives in a silo. Once I find a scenario I like, I can't "commit" to it and make it my actual plan.
    *   **Abstract:** It simulates numbers, not life milestones.
*   **Verdict:** The "Engine" of the app, but currently disconnected from the chassis.

---

## 3. Gap Analysis: The Wealth Ladder

We are auditing the app against the **6 Stages of Wealth**:

| Level | Stage | Current App Support | Gap |
| :--- | :--- | :--- | :--- |
| **0** | **Financially Dependent** | Weak. Shows "burn rate" but no emergency intervention flow. | Needs "Crisis Mode" UI. |
| **1** | **Financial Solvency** | **Strong.** Debt payoff charts are the core feature. | Good foundation. |
| **2** | **Financial Stability** | Moderate. Tracks "Liquid Assets" but no dedicated "Emergency Fund" goal tracker. | Needs specific "Fill the Bucket" visualization. |
| **3** | **Financial Security** | Weak. Investment projections exist but are generic. | No distinction between "Assets" and "Security Assets." |
| **4** | **Financial Independence** | None. | "Work Optional" metrics missing. |
| **5** | **Financial Freedom** | None. | No lifestyle modeling. |
| **6** | **Financial Abundance** | None. | No legacy/philanthropy features. |

---

## 4. Key Recommendations

1.  **Kill the Dashboard (as we know it):** Replace the generic dashboard with a **"Level Progress"** view. If I am Level 1, I should arguably *only* see Debt Payoff and Solvency metrics. Don't distract me with S&P 500 returns if I have credit card debt.
2.  **Gamify the Spending Editor:** Rename to "Resource Allocation." Show a real-time "XP Bar" (Free Cash Flow) growing as users cut expenses.
3.  **The "Commit" Button:** The Simulator must allow users to "Lock in" a strategy. "I choose the Avalanche method with \$500 extra." This becomes the new "Quest."

## 5. Conclusion
The technology is sound (Python backend, d3.js charts). The failure is in **framing**. By wrapping the existing tools in a "Level Up" framework, we can transform financial anxiety into competitive drive.

