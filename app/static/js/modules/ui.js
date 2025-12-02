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
    
    const tl = gsap.timeline({ defaults: { ease: "expo.out" } });

    // Header Fade In
    tl.to(".app-header", {
        y: 0,
        opacity: 1,
        duration: 0.8
    });

    // Primary Content Wave (Overview, Simulator, Spending Plan)
    // We select all possible major containers and stagger them collectively
    // to ensure a unified flow regardless of the page.
    const contentSelectors = [
        ".dashboard-overview .card",
        ".grid .card",
        ".simulator-container",
        ".simulation-layout .controls-section",
        ".simulation-layout .results-section",
        ".visualization-panel",
        ".spending-summary",
        ".spending-category"
    ];
    
    const contentElements = document.querySelectorAll(contentSelectors.join(", "));
    
    if (contentElements.length > 0) {
        tl.to(contentElements, {
            y: 0,
            opacity: 1,
            duration: 1.2,
            stagger: 0.08
        }, "-=0.4"); // Slight overlap with header
    }
}

export function setupInitialState() {
    if (typeof gsap !== 'undefined') {
         // Universal Targets
         gsap.set(".app-header", { y: -15, opacity: 0 });
         gsap.set(".card", { y: 15, opacity: 0 });
         
         // Specific Page Containers (if they exist outside .card)
         gsap.set(".simulator-container", { y: 15, opacity: 0 });
         gsap.set(".simulation-layout .controls-section", { y: 15, opacity: 0 });
         gsap.set(".simulation-layout .results-section", { y: 15, opacity: 0 });
         gsap.set(".visualization-panel", { y: 15, opacity: 0 });
         gsap.set(".spending-summary", { y: 15, opacity: 0 });
         gsap.set(".spending-category", { y: 15, opacity: 0 });
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
