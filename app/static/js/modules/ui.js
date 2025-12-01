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

export function animateValue(elementId, endValue) {
    const el = document.getElementById(elementId);
    if (!el) return; // Safety check

    if (typeof gsap !== 'undefined') {
        const obj = { val: 0 };
        gsap.to(obj, {
            val: endValue,
            duration: 2,
            ease: "power4.out",
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
    animateValue("nw-total", data.total);
    animateValue("nw-liquid", data.liquid);
    animateValue("nw-debt", data.liabilities_total);
    renderReasoning("nw-reasoning", data.reasoning);
}

export function renderDailyAllowance(amount) {
    animateValue("daily-allowance-value", amount);
    animateValue("hero-safe-spend", amount);
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

    // Header Fade In
    tl.to(".app-header", {
        y: 0,
        opacity: 1,
        duration: 0.8
    });

    // Cards Stagger
    tl.to(".card", {
        y: 0,
        opacity: 1,
        duration: 0.8,
        stagger: 0.15
    }, "-=0.4");

    // KPIs pop in
    tl.to(".kpi", {
        scale: 1,
        opacity: 1,
        duration: 0.5,
        stagger: 0.1
    }, "-=0.6");
}

export function setupInitialState() {
    if (typeof gsap !== 'undefined') {
         gsap.set(".app-header", { y: -20, opacity: 0 });
         gsap.set(".card", { y: 20, opacity: 0 });
         gsap.set(".kpi", { scale: 0.9, opacity: 0 });
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
