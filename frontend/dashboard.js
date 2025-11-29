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


const API_URL = "/api/view";

async function init() {
    const loadingEl = document.getElementById("loading");
    const dashboardEl = document.getElementById("dashboard");

    try {
        // Robust check for dependencies
        if (typeof d3 === 'undefined') {
            console.error("D3.js library not found. Charts will not render.");
        }

        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        // Prepare for Animation (if GSAP exists)
        // We set initial state BEFORE revealing the dashboard to prevent FOUC
        if (typeof gsap !== 'undefined') {
             gsap.set(".app-header", { y: -20, opacity: 0 });
             gsap.set(".card", { y: 20, opacity: 0 });
             gsap.set(".kpi", { scale: 0.9, opacity: 0 });
        }

        // Reveal Dashboard
        loadingEl.style.display = "none";
        dashboardEl.classList.remove("hidden");

        // Render Data First
        renderNetWorth(data.net_worth);
        renderFinancialHealth(data.financial_health);
        
        // Render Charts (wait for layout)
        // We use requestAnimationFrame to ensure DOM is updated and visible
        // so D3 can calculate widths correctly.
        requestAnimationFrame(() => {
             renderProjection(data.projection);
             renderDebtPayoff(data.debt_payoff);
        });

        // Animate Entry
        if (typeof gsap !== 'undefined') {
            animateEntry();
        }

        // Add Resize Listener for Charts
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                 renderProjection(data.projection);
                 renderDebtPayoff(data.debt_payoff);
            }, 250);
        });

    } catch (error) {
        console.error("Failed to load data:", error);
        loadingEl.innerHTML = `
            <div style="color: #EF4444; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 12px; text-align: center; border: 1px solid #EF4444; max-width: 400px; margin: 0 auto;">
                <h3 style="margin-top:0; color: #EF4444;">Connection Error</h3>
                <p>${error.message}</p>
                <button onclick="window.location.reload()" style="background: #EF4444; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 10px; font-weight: 600;">Retry</button>
            </div>
        `;
    }
}

function animateEntry() {
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

function renderNetWorth(data) {
    // If GSAP is available, we animate the numbers
    if (typeof gsap !== 'undefined') {
        animateValue("nw-total", data.total);
        animateValue("nw-liquid", data.liquid);
        animateValue("nw-debt", data.liabilities_total);
    } else {
        document.getElementById("nw-total").textContent = formatCurrency(data.total);
        document.getElementById("nw-liquid").textContent = formatCurrency(data.liquid);
        document.getElementById("nw-debt").textContent = formatCurrency(data.liabilities_total);
    }

    renderReasoning("nw-reasoning", data.reasoning);
}

function renderFinancialHealth(data) {
    // Savings Rate (percentage)
    const savingsRatePct = (data.savings_rate * 100).toFixed(1) + "%";
    const dtiPct = (data.debt_to_income_ratio * 100).toFixed(1) + "%";

    document.getElementById("savings-rate").textContent = savingsRatePct;
    document.getElementById("debt-income-ratio").textContent = dtiPct;

    // Savings Change
    // We assume data.savings_rate_change is a decimal (e.g., 0.02 for 2%)
    if (data.savings_rate_change !== undefined) {
        const changeEl = document.getElementById("savings-change");
        const changeVal = (data.savings_rate_change * 100).toFixed(1) + "%";
        const isPositive = data.savings_rate_change >= 0;

        changeEl.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
        changeEl.querySelector("span").textContent = `vs last month (${isPositive ? '+' : ''}${changeVal})`;

        // Update icon rotation if negative
        const icon = changeEl.querySelector("svg");
        if (!isPositive) {
            icon.style.transform = "rotate(180deg)";
        } else {
            icon.style.transform = "none";
        }
    }
}

function animateValue(elementId, endValue) {
    const obj = { val: 0 };
    gsap.to(obj, {
        val: endValue,
        duration: 2,
        ease: "power4.out",
        onUpdate: function () {
            document.getElementById(elementId).textContent = formatCurrency(obj.val);
        }
    });
}

function renderProjection(data) {
    const container = "#chart-projection";
    const series = data.series.map(d => ({ date: new Date(d.date), value: d.value }));

    drawAreaChart(container, series, "Net Worth ($)");
    renderReasoning("proj-context", [data.context]);
}

function renderDebtPayoff(data) {
    const container = "#chart-debt";

    const seriesSnowball = data.snowball.series.map(d => ({ date: new Date(d.date), value: d.value, strategy: "Snowball" }));
    const seriesAvalanche = data.avalanche.series.map(d => ({ date: new Date(d.date), value: d.value, strategy: "Avalanche" }));

    drawMultiLineChart(container, seriesSnowball, seriesAvalanche);
    renderReasoning("debt-reasoning", data.comparison);
}

function renderReasoning(elementId, lines) {
    const el = document.getElementById(elementId);
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

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

// --- D3 Charts ---

function drawAreaChart(selector, data, yLabel) {
    if (typeof d3 === 'undefined') return;

    const container = d3.select(selector);
    container.html(""); // Clear

    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    // Robust width calculation
    const containerNode = container.node();
    if (!containerNode) return;
    const width = containerNode.getBoundingClientRect().width - margin.left - margin.right;
    const height = 320 - margin.top - margin.bottom;

    if (width <= 0) return; // Don't render if hidden or too small

    const svg = container.append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Gradients
    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "area-gradient")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "0%")
        .attr("y2", "100%");

    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#6366f1").attr("stop-opacity", 0.15);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#6366f1").attr("stop-opacity", 0);

    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    const extent = d3.extent(data, d => d.value);
    const padding = (extent[1] - extent[0]) * 0.1;

    const y = d3.scaleLinear()
        .domain([extent[0] - padding, extent[1] + padding])
        .range([height, 0]);

    // Axes
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(10));

    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(10).tickFormat(d => d >= 1000 ? d / 1000 + "k" : d));

    // Grid lines
    svg.selectAll("line.horizontalGrid").data(y.ticks(5)).enter()
        .append("line")
        .attr("class", "grid-line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", d => y(d))
        .attr("y2", d => y(d));

    // Area generator
    const area = d3.area()
        .x(d => x(d.date))
        .y0(height)
        .y1(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Clip path for revealing the graph
    const clipId = "clip-projection-" + Math.random().toString(36).substr(2, 9);
    svg.append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", 0) // Start hidden
        .attr("height", height);

    // Add Area
    svg.append("path")
        .datum(data)
        .attr("fill", "url(#area-gradient)")
        .attr("d", area)
        .attr("clip-path", `url(#${clipId})`);

    // Add Line
    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", "#6366f1")
        .attr("stroke-width", "2.5")
        .attr("d", line)
        .attr("clip-path", `url(#${clipId})`);

    // Animate Chart
    if (typeof gsap !== 'undefined') {
        gsap.to(`#${clipId} rect`, {
            width: width,
            duration: 2.5,
            ease: "power2.out",
            delay: 0.5
        });
    } else {
        d3.select(`#${clipId} rect`).attr("width", width);
    }
}

function drawMultiLineChart(selector, data1, data2) {
    if (typeof d3 === 'undefined') return;

    const container = d3.select(selector);
    container.html("");

    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const containerNode = container.node();
    if (!containerNode) return;
    const width = containerNode.getBoundingClientRect().width - margin.left - margin.right;
    const height = 320 - margin.top - margin.bottom;

    if (width <= 0) return;

    const svg = container.append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const allData = [...data1, ...data2];

    const x = d3.scaleTime()
        .domain(d3.extent(allData, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(allData, d => d.value) * 1.1])
        .range([height, 0]);

    // Axes
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(10));

    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(10).tickFormat(d => d >= 1000 ? d / 1000 + "k" : d));

    // Grid lines
    svg.selectAll("line.horizontalGrid").data(y.ticks(5)).enter()
        .append("line")
        .attr("class", "grid-line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", d => y(d))
        .attr("y2", d => y(d));

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Helper to add and animate line
    function addLine(data, color, dashed = false, delay = 0) {
        const path = svg.append("path")
            .datum(data)
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("d", line);

        // Set stroke width
        path.attr("stroke-width", "2.5");

        if (dashed) {
            path.attr("stroke-dasharray", "3,3");
        }

        if (typeof gsap !== 'undefined') {
            const length = path.node().getTotalLength();

            if (!dashed) {
                // Draw animation for solid lines
                path.attr("stroke-dasharray", length + " " + length)
                    .attr("stroke-dashoffset", length);

                gsap.to(path.node(), {
                    strokeDashoffset: 0,
                    duration: 2.5,
                    delay: delay,
                    ease: "power2.out"
                });
            } else {
                // Fade animation for dashed lines
                path.attr("opacity", 0);
                gsap.to(path.node(), {
                    opacity: 1,
                    duration: 2.5,
                    delay: delay,
                    ease: "power2.out"
                });
            }
        }
    }

    addLine(data1, "#f59e0b", false, 0.8); // Snowball (Amber)
    addLine(data2, "#10b981", true, 1.2); // Avalanche (Emerald)

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${width - 120}, 0)`);

    legend.append("line").attr("x1", 0).attr("x2", 16).attr("y1", 5).attr("y2", 5).attr("stroke", "#f59e0b").attr("stroke-width", 2.5);
    legend.append("text").attr("x", 22).attr("y", 10).text("Snowball").style("font-size", "11px").style("fill", "#888").style("font-family", "var(--font-body)");

    legend.append("line").attr("x1", 0).attr("x2", 16).attr("y1", 25).attr("y2", 25).attr("stroke", "#10b981").attr("stroke-width", 2.5).attr("stroke-dasharray", "3,3");
    legend.append("text").attr("x", 22).attr("y", 30).text("Avalanche").style("font-size", "11px").style("fill", "#888").style("font-family", "var(--font-body)");

    if (typeof gsap !== 'undefined') {
        legend.style("opacity", 0);
        gsap.to(legend.node(), {
            opacity: 1,
            delay: 2,
            duration: 1
        });
    }
}

// Start
init();
