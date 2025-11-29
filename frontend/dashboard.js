// Wealth OS Dashboard Logic

const API_URL = "/api/view";

async function init() {
    try {
        // Robust check for dependencies
        if (typeof d3 === 'undefined') {
            throw new Error("D3.js library not found. Please check your internet connection.");
        }
        if (typeof gsap === 'undefined') {
            console.warn("GSAP not found. Animations will be disabled.");
        }

        const response = await fetch(API_URL);
        const data = await response.json();
        
        document.getElementById("loading").style.display = "none";
        document.getElementById("dashboard").style.display = "block";
        
        // Render Data First
        renderNetWorth(data.net_worth);
        renderProjection(data.projection);
        renderDebtPayoff(data.debt_payoff);
        
        // Animate Entry
        if (typeof gsap !== 'undefined') {
            animateEntry();
        } else {
            // Fallback: make visible immediately
            document.querySelectorAll('.card').forEach(el => {
                el.style.opacity = 1;
                el.style.transform = 'none';
            });
        }
        
    } catch (error) {
        console.error("Failed to load data:", error);
        document.getElementById("loading").innerHTML = `
            <div style="color: #EF4444; padding: 20px; background: #FEF2F2; border-radius: 12px; text-align: center;">
                <h3 style="margin-top:0">We hit a snag.</h3>
                <p>${error.message}</p>
                <small>Check console for details.</small>
            </div>
        `;
    }
}

function animateEntry() {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
    
    // Header Fade In
    tl.from("header", {
        y: -20,
        opacity: 0,
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
    tl.from(".kpi", {
        scale: 0.9,
        opacity: 0,
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

function animateValue(elementId, endValue) {
    const obj = { val: 0 };
    gsap.to(obj, {
        val: endValue,
        duration: 2,
        ease: "power4.out",
        onUpdate: function() {
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
    
    const margin = {top: 20, right: 20, bottom: 30, left: 50};
    const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
    const height = 320 - margin.top - margin.bottom;
    
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
    
    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#2563EB").attr("stop-opacity", 0.2);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#2563EB").attr("stop-opacity", 0);

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
        .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(10).tickFormat(d => d >= 1000 ? d/1000 + "k" : d));

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
        .attr("stroke", "#2563EB")
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
    
    const margin = {top: 20, right: 20, bottom: 30, left: 50};
    const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
    const height = 320 - margin.top - margin.bottom;
    
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
        .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(10).tickFormat(d => d >= 1000 ? d/1000 + "k" : d));
        
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
            
        if (dashed) {
            path.attr("stroke-dasharray", "5,5");
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

    addLine(data1, "#EF4444", false, 0.8); // Snowball (Red)
    addLine(data2, "#10B981", true, 1.2); // Avalanche (Green)

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${width - 120}, 0)`);
    
    legend.append("rect").attr("width", 10).attr("height", 10).attr("fill", "#EF4444");
    legend.append("text").attr("x", 15).attr("y", 10).text("Snowball").style("font-size", "12px").style("fill", "#64748B").style("font-family", "var(--font-body)");
    
    legend.append("rect").attr("width", 10).attr("height", 10).attr("y", 20).attr("fill", "#10B981");
    legend.append("text").attr("x", 15).attr("y", 30).text("Avalanche").style("font-size", "12px").style("fill", "#64748B").style("font-family", "var(--font-body)");
    
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
