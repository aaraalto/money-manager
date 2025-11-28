// Wealth OS Dashboard Logic

const API_URL = "http://localhost:8000/api/view";

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
        
        // Animate cards entry if GSAP is available
        if (typeof gsap !== 'undefined') {
            gsap.to(".card", {
                duration: 0.6,
                opacity: 1,
                y: 0,
                stagger: 0.1,
                ease: "power2.out"
            });
        } else {
            // Fallback: make visible immediately
            document.querySelectorAll('.card').forEach(el => {
                el.style.opacity = 1;
                el.style.transform = 'none';
            });
        }
        
        renderNetWorth(data.net_worth);
        renderProjection(data.projection);
        renderDebtPayoff(data.debt_payoff);
        
    } catch (error) {
        console.error("Failed to load data:", error);
        document.getElementById("loading").innerHTML = `
            <div style="color: #ff3b30; padding: 20px; background: #fff; border-radius: 12px;">
                <h3>Error Loading Dashboard</h3>
                <p>${error.message}</p>
                <small>Check console for details.</small>
            </div>
        `;
    }
}

function renderNetWorth(data) {
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
        duration: 1.5,
        ease: "power2.out",
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
    
    const margin = {top: 20, right: 30, bottom: 30, left: 60};
    const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    
    const svg = container.append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
        
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);
        
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) * 1.1])
        .range([height, 0]);
        
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));
        
    svg.append("g")
        .call(d3.axisLeft(y));
        
    // Area generator
    const area = d3.area()
        .x(d => x(d.date))
        .y0(height) 
        .y1(d => y(d.value));
        
    const areaFinal = d3.area()
        .x(d => x(d.date))
        .y0(y(0)) 
        .y1(d => y(d.value));

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value));

    // Clip path for revealing the graph
    const clipId = "clip-projection-" + Math.random().toString(36).substr(2, 9);
    svg.append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", typeof gsap !== 'undefined' ? 0 : width) // Start hidden if animating
        .attr("height", height);

    // Add Area
    svg.append("path")
        .datum(data)
        .attr("fill", "#cce5ff")
        .attr("d", areaFinal)
        .attr("clip-path", `url(#${clipId})`)
        .style("opacity", 0.6);

    // Add Line
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#007aff")
        .attr("stroke-width", 2)
        .attr("d", line)
        .attr("clip-path", `url(#${clipId})`);

    if (typeof gsap !== 'undefined') {
        gsap.to(`#${clipId} rect`, {
            width: width,
            duration: 2,
            ease: "power2.out"
        });
    }
}

function drawMultiLineChart(selector, data1, data2) {
    if (typeof d3 === 'undefined') return;

    const container = d3.select(selector);
    container.html("");
    
    const margin = {top: 20, right: 100, bottom: 30, left: 60};
    const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    
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
        
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));
        
    svg.append("g")
        .call(d3.axisLeft(y));
        
    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value));

    // Helper to add and animate line
    function addLine(data, color, dashed = false, delay = 0) {
        const path = svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", 2)
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
                    duration: 2,
                    delay: delay,
                    ease: "power2.out"
                });
            } else {
                // Fade animation for dashed lines
                path.attr("opacity", 0);
                gsap.to(path.node(), {
                    opacity: 1,
                    duration: 2,
                    delay: delay,
                    ease: "power2.out"
                });
            }
        }
    }

    addLine(data1, "#ff3b30", false, 0); // Snowball
    addLine(data2, "#34c759", true, 0.5); // Avalanche

    // Legend
    const legend = svg.append("g");
    legend.append("text").attr("x", width + 10).attr("y", 20).text("Snowball").style("fill", "#ff3b30").style("font-size", "12px");
    legend.append("text").attr("x", width + 10).attr("y", 40).text("Avalanche").style("fill", "#34c759").style("font-size", "12px");
    
    if (typeof gsap !== 'undefined') {
        legend.style("opacity", 0);
        gsap.to(legend.node(), {
            opacity: 1,
            delay: 1.5,
            duration: 1
        });
    }
}

// Start
init();
