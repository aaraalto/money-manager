# Spec 01: The Onboarding Flow

**Goal:** Establish the user's **Financial Level** (0-6) without a tedious survey.
**Tone:** Welcoming, Non-judgmental, Efficient.

## Flow Overview
1.  **Welcome Screen:** Brand promise.
2.  **Input 1: The Inflow:** Monthly Income.
3.  **Input 2: The Outflow:** Monthly Spend (Rough estimate).
4.  **Input 3: The Anchor:** Debt Check.
5.  **Result:** Level Assignment.

---

## Detailed Steps

### Step 1: The Welcome
*   **UI:** Full-screen hero. Clean typography.
*   **Copy:** "Radiant. Illuminate your financial future."
*   **Action:** Primary Button: "Let's Begin".

### Step 2: The Inflow (Income)
*   **Question:** "First, what is your monthly take-home pay?"
*   **Input:** Large currency input (auto-focus).
*   **Helper Text:** "An estimate is fine. You can refine this later."
*   **Interaction:** Typing numbers formats automatically (e.g., `$4,00_`).
*   **Action:** "Next" (appears only after input > 0).

### Step 3: The Outflow (Burn Rate)
*   **Question:** "Roughly how much do you spend in a month?"
*   **Input:** Large currency input.
*   **Context:** "Rent, food, bills, and fun."
*   **Action:** "Next".

### Step 4: The Anchor (Debt)
*   **Question:** "Do you have any credit card or high-interest debt?"
*   **UI:** Two large cards: "Yes" / "No".
*   **If Yes:**
    *   Slide up input: "What is the total balance?"
    *   Helper: "Just a ballpark figure for now."
*   **If No:** Skip to Liquid Assets check ("Do you have 6 months of expenses saved?").

### Step 5: The Revelation (Level Assignment)
*   **UI:** Analyzing animation ("Crunching the numbers...").
*   **Result Card:**
    *   **Icon:** Represents the Level (e.g., "Shield" for Level 1).
    *   **Title:** "You are a Solvency Seeker (Level 1)."
    *   **Description:** "You have strong income, but debt is holding you back. Your mission is to destroy it."
*   **Action:** "Enter the War Room" (Redirect to Level 1 Dashboard).

---

## Technical Requirements
*   **State:** Temporarily store inputs in client-side `sessionStorage` or a transient backend session until "Commit".
*   **Logic:** Use `backend.primitives.metrics.calculate_level()` (To be implemented).
*   **HTMX:** Use `hx-post` for step transitions to keep it single-page application (SPA) feel without page reloads.

