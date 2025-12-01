import { fetchDashboardData } from './api.js';
import { renderNetWorth, renderFinancialHealth, renderDailyAllowance, renderSystemStatus, animateEntry, setupInitialState, showDashboard, showError } from './ui.js';
import { renderProjection, renderDebtPayoff, renderSpendingBreakdown } from './charts.js';

// Radiant Dashboard Logic
console.log(`%c
    ___          ___          ___                       ___          ___          ___
   /  /\\        /  /\\        /  /\\        ___          /  /\\        /__/\\        /__/\\
  /  /::\\      /  /::\\      /  /::\\      /  /\\        /  /::\\       \\  \\:\\       \\  \\:\\
 /  /:/\\:\\    /  /:/\\:\\    /  /:/\\:\\    /  /:/       /  /:/\\:\\       \\  \\:\\       \\  \\:\\
/  /:/~/:/   /  /:/~/::\\  /  /:/~/::\\  /__/::\\      /  /:/~/::\\  _____\\__\\:\\  _____\\__\\:\\
/__/:/ /:/   /__/:/ /:/\\:|/__/:/ /:/\\:\\ \\__\\/\\:\\__  /__/:/ /:/\\:|/__/:::::::::\\/__/::::::::\\
\\  \\:\\/:/    \\  \\:\\/:/~/:/\\  \\:\\/:/__\\/    \\  \\:\\/\\ \\  \\:\\/:/__\\/\\  \\:\\~~\\~~\\/\\  \\:\\~~\\~~\\/
 \\  \\::/      \\  \\::/ /:/  \\  \\::/          \\__\\::/  \\  \\::/      \\  \\:\\  ~~~  \\  \\:\\  ~~~
  \\  \\:\\       \\__\\/ /:/    \\  \\:\\          /__/:/    \\  \\:\\       \\  \\:\\       \\  \\:\\
   \\  \\:\\        /__/:/      \\  \\:\\         \\__\\/      \\  \\:\\       \\  \\:\\       \\  \\:\\
    \\__\\/        \\__\\/        \\__\\/                     \\__\\/        \\__\\/        \\__\\/
`, "color: #6366f1; font-weight: bold;");

async function init() {
    try {
        // Robust check for dependencies
        if (typeof d3 === 'undefined') {
            console.error("D3.js library not found. Charts will not render.");
        }

        // We set initial state BEFORE revealing the dashboard to prevent FOUC
        setupInitialState();
        
        const data = await fetchDashboardData();

        // Reveal Dashboard
        showDashboard();

        // Render Data First
        renderNetWorth(data.net_worth);
        renderFinancialHealth(data.financial_health);
        renderDailyAllowance(data.daily_allowance);
        renderSystemStatus(data.system_status);
        
        // Render Charts (wait for layout)
        requestAnimationFrame(() => {
             renderProjection(data.projection);
             renderDebtPayoff(data.debt_payoff);
             renderSpendingBreakdown(data.spending_breakdown);
        });

        // Animate Entry
        animateEntry();

        // Add Resize Listener for Charts
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                 renderProjection(data.projection);
                 renderDebtPayoff(data.debt_payoff);
                 renderSpendingBreakdown(data.spending_breakdown);
            }, 250);
        });

    } catch (error) {
        showError(error);
    }
}

// Start
init();

