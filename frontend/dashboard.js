// Wealth OS Dashboard Logic

const API_URL = "http://localhost:8000/api/view";

async function init() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        
        document.getElementById("loading").style.display = "none";
        document.getElementById("dashboard").style.display = "block";
        
        renderNetWorth(data.net_worth);
        renderProjection(data.projection);
        renderDebtPayoff(data.debt_payoff);
        
    } catch (error) {
        console.error("Failed to load data:", error);
        document.getElementById("loading").textContent = "Error loading data. Is the backend running?";
    }
}

function renderNetWorth(data) {
    document.getElementById("nw-total").textContent = formatCurrency(data.total);
    document.getElementById("nw-liquid").textContent = formatCurrency(data.liquid);
    document.getElementById("nw-debt").textContent = formatCurrency(data.liabilities_total);
    
    renderReasoning("nw-reasoning", data.reasoning);
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
    
    // Combine for multi-line chart
    const combined = [...seriesSnowball, ...seriesAvalanche];
    
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
        
    // Area
    svg.append("path")
        .datum(data)
        .attr("fill", "#cce5ff")
        .attr("stroke", "#007aff")
        .attr("stroke-width", 1.5)
        .attr("d", d3.area()
            .x(d => x(d.date))
            .y0(y(0))
            .y1(d => y(d.value))
        );
}

function drawMultiLineChart(selector, data1, data2) {
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
        
    // Line 1 (Snowball)
    svg.append("path")
        .datum(data1)
        .attr("fill", "none")
        .attr("stroke", "#ff3b30") // Red
        .attr("stroke-width", 2)
        .attr("d", d3.line()
            .x(d => x(d.date))
            .y(d => y(d.value))
        );
        
    // Line 2 (Avalanche)
    svg.append("path")
        .datum(data2)
        .attr("fill", "none")
        .attr("stroke", "#34c759") // Green
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")
        .attr("d", d3.line()
            .x(d => x(d.date))
            .y(d => y(d.value))
        );

    // Legend
    svg.append("text").attr("x", width + 10).attr("y", 20).text("Snowball").style("fill", "#ff3b30").style("font-size", "12px");
    svg.append("text").attr("x", width + 10).attr("y", 40).text("Avalanche").style("fill", "#34c759").style("font-size", "12px");
}

// Start
init();

