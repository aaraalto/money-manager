# Structured Financial Questions Guide

To get the most mathematically accurate advice from the Wealth OS algorithms, structure your questions using the **Data + Variable + Strategy + Metric** format.

This ensures we can run the specific python primitives (`simulate_debt_payoff`, `calculate_runway`, `project_compound_growth`) found in the codebase.

---

## 1. The "Debt Destroyer" Scenario
**Goal:** Optimize debt payoff to save maximum interest.

**The Question:**
> "Given my current liability list below, if I find an extra **$500/month** in my budget (Variable), how much **total interest** will I save (Metric) using the **Avalanche Method** vs the **Snowball Method** (Strategy)? Also, what is my exact **Debt Free Date** for both?"

**Required Data Context:**
```json
[
  { "name": "Chase Sapphire", "balance": 5000, "interest_rate": 0.24, "min_payment": 150 },
  { "name": "Personal Loan", "balance": 12000, "interest_rate": 0.09, "min_payment": 310 }
]
```

---

## 2. The "Runway & Risk" Scenario
**Goal:** Determine if you are safe to make a big financial move (e.g., quitting a job, buying a house).

**The Question:**
> "I currently have **$15,000 in liquid cash** (Data). My monthly burn rate is **$4,500** (Data). If I stop working today to start a business (Variable), how many **days of runway** do I have (Metric) before I reach $0? Does this meet the 6-month safety standard?"

**Required Data Context:**
*   **Liquid Assets:** $15,000
*   **Monthly Fixed Expenses (Needs):** $3,000
*   **Monthly Variable Expenses (Wants):** $1,500

---

## 3. The "Compound Growth" Scenario
**Goal:** Project future wealth based on savings rate.

**The Question:**
> "My current Net Worth is **$50,000** (Data). If I invest **$1,200/month** (Variable) into an S&P 500 index fund assuming a **7% average return** (Strategy/Assumption), what will my Net Worth be in **10 years** (Metric)? How much of that total is purely interest earned?"

**Required Data Context:**
*   **Current Principal:** $50,000
*   **Monthly Contribution:** $1,200
*   **Time Horizon:** 10 Years
*   **Rate:** 7% (0.07)

---

## 4. The "Affordability Check" Scenario
**Goal:** Assessing a large purchase without breaking the bank.

**The Question:**
> "I want to buy a **$40,000 car** (Variable). I have **$20,000 cash** for a down payment. My monthly take-home is **$8,000**. If I finance the rest at **5% for 48 months**, will the monthly payment keep my total 'Needs' category under **50% of my income** (Metric/Rule)?"

**Required Data Context:**
*   **Income:** $8,000/mo
*   **Current Fixed Costs:** $2,500/mo
*   **New Car Cost:** $40,000 ($20k down, $20k financed)

