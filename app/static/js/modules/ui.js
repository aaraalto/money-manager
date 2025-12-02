export function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

export function renderReasoning(elementId, lines) {
    const el = document.getElementById(elementId);
    if (!el) return; // Safety check
    if (!lines || lines.length === 0) return;

    const ul = document.createElement("ul");
    lines.forEach(line => {
        const li = document.createElement("li");
        li.textContent = line;
        ul.appendChild(li);
    });
    el.innerHTML = "";
    el.appendChild(ul);
}

// Constant for syncing number animations with content entry
const NUMBER_ANIMATION_DELAY = 1.2;

export function animateValue(elementId, endValue, delay = 0) {
    const el = document.getElementById(elementId);
    if (!el) return; // Safety check

    if (typeof gsap !== 'undefined') {
        const obj = { val: 0 };
        gsap.to(obj, {
            val: endValue,
            duration: 2.0,
            delay: delay,
            ease: "expo.out",
            onUpdate: function () {
                const updateEl = document.getElementById(elementId);
                if(updateEl) updateEl.textContent = formatCurrency(obj.val);
            }
        });
    } else {
        el.textContent = formatCurrency(endValue);
    }
}

export function renderNetWorth(data) {
    animateValue("nw-total", data.total, NUMBER_ANIMATION_DELAY);
    animateValue("nw-liquid", data.liquid, NUMBER_ANIMATION_DELAY);
    animateValue("nw-debt", data.liabilities_total, NUMBER_ANIMATION_DELAY);
    renderReasoning("nw-reasoning", data.reasoning);
}

export function renderDailyAllowance(data) {
    // Handle both old format (just number) and new format (object)
    const amount = typeof data === 'number' ? data : data.daily;
    const monthly = typeof data === 'number' ? amount * 30 : (data.monthly || amount * 30);
    const percentage = typeof data === 'number' ? null : (data.percentage_of_income || null);
    
    animateValue("daily-allowance-value", amount, NUMBER_ANIMATION_DELAY);
    animateValue("hero-safe-spend", amount, NUMBER_ANIMATION_DELAY);
    
    // Update monthly total
    const monthlyEl = document.getElementById("monthly-allowance");
    if (monthlyEl) {
        if (typeof gsap !== 'undefined') {
            const obj = { val: 0 };
            gsap.to(obj, {
                val: monthly,
                duration: 2.0,
                delay: NUMBER_ANIMATION_DELAY,
                ease: "expo.out",
                onUpdate: function () {
                    monthlyEl.textContent = formatCurrency(obj.val);
                }
            });
        } else {
            monthlyEl.textContent = formatCurrency(monthly);
        }
    }
    
    // Update percentage if available
    const percentageEl = document.getElementById("allowance-percentage");
    if (percentageEl && percentage !== null) {
        if (typeof gsap !== 'undefined') {
            const obj = { val: 0 };
            gsap.to(obj, {
                val: percentage,
                duration: 2.0,
                delay: NUMBER_ANIMATION_DELAY,
                ease: "expo.out",
                onUpdate: function () {
                    percentageEl.textContent = Math.round(obj.val) + "%";
                }
            });
        } else {
            percentageEl.textContent = Math.round(percentage) + "%";
        }
    } else if (percentageEl) {
        percentageEl.textContent = "--";
    }
}

export function renderSystemStatus(status) {
    if (!status) return;

    const updateStatus = (id, isOk) => {
        const el = document.getElementById(id);
        if (el) {
            if (isOk) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        }
    };

    updateStatus('status-fixed', status.fixed_costs_covered);
    updateStatus('status-debt', status.debt_strategy_active);
    updateStatus('status-savings', status.savings_automated);
}

export function renderFinancialHealth(data) {
    // Savings Rate (percentage)
    const savingsRatePct = (data.savings_rate * 100).toFixed(1) + "%";
    const dtiPct = (data.debt_to_income_ratio * 100).toFixed(1) + "%";

    const savingsEl = document.getElementById("savings-rate");
    if (savingsEl) savingsEl.textContent = savingsRatePct;

    // Monthly Growth (Surplus)
    if (data.monthly_surplus !== undefined) {
        const growthEl = document.getElementById("nw-monthly-growth");
        if (growthEl) {
             growthEl.textContent = "+" + formatCurrency(data.monthly_surplus);
        }
    }

    const dtiEl = document.getElementById("debt-income-ratio");
    if (dtiEl) dtiEl.textContent = dtiPct;

    // Savings Change
    if (data.savings_rate_change !== undefined) {
        const changeEl = document.getElementById("savings-change");
        if (changeEl) {
            const changeVal = (data.savings_rate_change * 100).toFixed(1) + "%";
            const isPositive = data.savings_rate_change >= 0;

            changeEl.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
            changeEl.querySelector("span").textContent = `vs last month (${isPositive ? '+' : ''}${changeVal})`;

            // Update icon rotation if negative
            const icon = changeEl.querySelector("svg");
            if (icon) {
                if (!isPositive) {
                    icon.style.transform = "rotate(180deg)";
                } else {
                    icon.style.transform = "none";
                }
            }
        }
    }
}

export function animateEntry() {
    if (typeof gsap === 'undefined') return;
    
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // 1. Header Fade In (Fast & crisp)
    tl.to(".app-header", {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: "power2.out"
    });

    // Check if we are on the Overview Dashboard
    const overviewCards = document.querySelectorAll(".dashboard-overview .card");
    if (overviewCards.length > 0) {
        // Specific choreographed sequence for Overview
        
        // "Daily Capacity" and "Expense Composition" are children of .dashboard-overview
        // We treat them as the primary heroes.
        tl.to(".dashboard-overview .card", {
            y: 0,
            opacity: 1,
            scale: 1,
            duration: 0.8,
            stagger: 0.15, // Distinct steps between the two main cards
            ease: "expo.out"
        }, "-=0.4");

        // Grid cards (Secondary info)
        // Enter slightly faster, with a tighter stagger
        const gridCards = document.querySelectorAll(".grid .card");
        if (gridCards.length > 0) {
            tl.to(gridCards, {
                y: 0,
                opacity: 1,
                scale: 1,
                duration: 0.6,
                stagger: {
                    amount: 0.3, // Distribute start times over 0.3s
                    grid: "auto",
                    from: "start"
                },
                ease: "back.out(1.2)" // Subtle pop
            }, "-=0.6"); // Start before overview finishes
        }

    } else {
        // Fallback / Universal Animation for other pages (Simulator, Spending Editor)
        const contentSelectors = [
            ".simulator-container",
            ".simulation-layout .controls-section",
            ".simulation-layout .results-section",
            ".visualization-panel",
            ".spending-summary",
            ".spending-category",
            ".spending-row",
            ".editor-header",
            ".insights-panel",
            ".spending-table-form",
            ".hero-allowance-container", // Dashboard Level 1 Hero
            ".section-header"
        ];
        
        const contentElements = document.querySelectorAll(contentSelectors.join(", "));
        
        if (contentElements.length > 0) {
            tl.to(contentElements, {
                y: 0,
                opacity: 1,
                scale: 1,
                duration: 0.8,
                stagger: 0.06,
                ease: "expo.out"
            }, "-=0.4");
        }
    }
}

export function setupInitialState() {
    if (typeof gsap !== 'undefined') {
         // Universal Targets
         // We add a slight scale down (0.98) for a subtle "pop" in effect
         gsap.set(".app-header", { y: -20, opacity: 0 });
         
         // Cards and Containers
         const targets = [
             ".card", 
             ".simulator-container",
             ".simulation-layout .controls-section", 
             ".simulation-layout .results-section",
             ".visualization-panel",
             ".spending-summary",
             ".spending-category",
             ".editor-header",
             ".insights-panel",
             ".spending-table-form",
             ".hero-allowance-container",
             ".section-header"
         ];

         gsap.set(targets.join(", "), { 
             y: 20, 
             opacity: 0,
             scale: 0.98
         });
         
         // Specific rows (might be too many to scale, just fade/slide)
         gsap.set(".spending-row", { y: 10, opacity: 0 });
    }
}

export function showDashboard() {
    const loadingEl = document.getElementById("loading");
    const dashboardEl = document.getElementById("dashboard");
    if (loadingEl) loadingEl.style.display = "none";
    if (dashboardEl) dashboardEl.classList.remove("hidden");
}

export function showError(error) {
    const loadingEl = document.getElementById("loading");
    if (!loadingEl) return;
    
    console.error("Failed to load data:", error);
    loadingEl.innerHTML = `
        <div class="alert alert-danger" style="max-width: 400px; margin: 0 auto;">
            <div class="alert-content">
                <div class="alert-title">Connection Error</div>
                <div class="alert-description">${error.message}</div>
                <button onclick="window.location.reload()" class="btn-nav" style="margin-top: 10px; background: var(--bg-card); color: var(--text-primary);">Retry</button>
            </div>
        </div>
    `;
}
