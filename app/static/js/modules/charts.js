import { renderReasoning } from './ui.js';

export function renderProjection(data) {
    const container = "#chart-projection";
    const series = data.series.map(d => ({ date: new Date(d.date), value: d.value }));

    drawAreaChart(container, series, "Net Worth ($)");
    renderReasoning("proj-context", [data.context]);
}

export function renderDebtPayoff(data) {
    const container = "#chart-debt";

    const seriesSnowball = data.snowball.series.map(d => ({ date: new Date(d.date), value: d.value, strategy: "Snowball" }));
    const seriesAvalanche = data.avalanche.series.map(d => ({ date: new Date(d.date), value: d.value, strategy: "Avalanche" }));

    drawMultiLineChart(container, seriesSnowball, seriesAvalanche);
    renderReasoning("debt-reasoning", data.comparison);
}

function drawAreaChart(selector, data, yLabel) {
    if (typeof d3 === 'undefined') return;

    const container = d3.select(selector);
    container.html(""); // Clear

    const margin = { top: 20, right: 20, bottom: 25, left: 40 };
    const containerNode = container.node();
    if (!containerNode) return;
    const width = containerNode.getBoundingClientRect().width - margin.left - margin.right;
    const containerHeight = containerNode.getBoundingClientRect().height;
    const height = (containerHeight > 0 ? containerHeight : 150) - margin.top - margin.bottom;

    if (width <= 0) return;

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

    // Get colors from CSS variables
    const style = getComputedStyle(document.documentElement);
    const primaryColor = style.getPropertyValue('--primary').trim() || '#6366f1';
    const warningColor = style.getPropertyValue('--warning').trim() || '#f59e0b';
    const successColor = style.getPropertyValue('--success').trim() || '#10b981';

    gradient.append("stop").attr("offset", "0%").attr("stop-color", primaryColor).attr("stop-opacity", 0.15);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", primaryColor).attr("stop-opacity", 0);

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

    // Clip path
    const clipId = "clip-projection-" + Math.random().toString(36).substr(2, 9);
    svg.append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", 0)
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
        .attr("stroke", primaryColor)
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

    // Get colors
    const style = getComputedStyle(document.documentElement);
    const warningColor = style.getPropertyValue('--warning').trim() || '#f59e0b';
    const successColor = style.getPropertyValue('--success').trim() || '#10b981';

    const container = d3.select(selector);
    container.html("");

    const margin = { top: 20, right: 20, bottom: 25, left: 40 };
    const containerNode = container.node();
    if (!containerNode) return;
    const width = containerNode.getBoundingClientRect().width - margin.left - margin.right;
    const containerHeight = containerNode.getBoundingClientRect().height;
    const height = (containerHeight > 0 ? containerHeight : 150) - margin.top - margin.bottom;

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

    function addLine(data, color, dashed = false, delay = 0) {
        const path = svg.append("path")
            .datum(data)
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("d", line);

        path.attr("stroke-width", "2.5");

        if (dashed) {
            path.attr("stroke-dasharray", "3,3");
        }

        if (typeof gsap !== 'undefined') {
            const length = path.node().getTotalLength();

            if (!dashed) {
                path.attr("stroke-dasharray", length + " " + length)
                    .attr("stroke-dashoffset", length);

                gsap.to(path.node(), {
                    strokeDashoffset: 0,
                    duration: 2.5,
                    delay: delay,
                    ease: "power2.out"
                });
            } else {
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

    addLine(data1, warningColor, false, 0.8); // Snowball
    addLine(data2, successColor, true, 1.2); // Avalanche

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${width - 120}, 0)`);

    legend.append("line").attr("x1", 0).attr("x2", 16).attr("y1", 5).attr("y2", 5).attr("stroke", warningColor).attr("stroke-width", 2.5);
    legend.append("text").attr("x", 22).attr("y", 10).text("Snowball").style("font-size", "11px").style("fill", "#888").style("font-family", "var(--font-body)");

    legend.append("line").attr("x1", 0).attr("x2", 16).attr("y1", 25).attr("y2", 25).attr("stroke", successColor).attr("stroke-width", 2.5).attr("stroke-dasharray", "3,3");
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

export function renderSpendingBreakdown(data) {
    const container = "#chart-spending";
    drawPieChart(container, data);
}

function drawPieChart(selector, data) {
    if (typeof d3 === 'undefined') return;

    const container = d3.select(selector);
    container.html("");

    // Filter out zero values
    const cleanData = data.filter(d => d.value > 0);
    if (cleanData.length === 0) {
        container.append("div")
            .style("text-align", "center")
            .style("padding", "2rem")
            .style("color", "var(--text-tertiary)")
            .text("No spending data available");
        return;
    }

    // Get CSS variables for colors
    const style = getComputedStyle(document.documentElement);
    const primaryColor = style.getPropertyValue('--primary').trim() || '#5b8de8';
    const warningColor = style.getPropertyValue('--warning').trim() || '#f59e0b';
    const successColor = style.getPropertyValue('--success').trim() || '#37a770';
    const dangerColor = style.getPropertyValue('--danger').trim() || '#eb5757';
    const bgCard = style.getPropertyValue('--bg-card').trim() || '#252525';
    const textPrimary = style.getPropertyValue('--text-primary').trim() || '#e9e9e7';
    const textSecondary = style.getPropertyValue('--text-secondary').trim() || '#9b9a97';
    const fontBody = style.getPropertyValue('--font-body').trim() || 'Inter, sans-serif';
    const fontMono = style.getPropertyValue('--font-mono').trim() || 'SF Mono, monospace';

    // Only top 5 categories + Others
    const topN = 5;
    let displayData = cleanData.slice(0, topN);
    const othersValue = cleanData.slice(topN).reduce((acc, curr) => acc + curr.value, 0);
    if (othersValue > 0) {
        displayData.push({ label: "Others", value: othersValue, type: "Mixed" });
    }

    // Use flex column for layout, remove Grid Legend
    container.style("display", "flex")
             .style("justify-content", "center")
             .style("align-items", "center")
             .style("height", "100%"); // Fill parent

    const containerNode = container.node();
    const width = containerNode.getBoundingClientRect().width || 300;
    const height = containerNode.getBoundingClientRect().height || 300;
    
    // Maximize radius within container
    const radius = Math.min(width, height) / 2 - 20;

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${width / 2},${height / 2})`);

    // Use design system colors with semantic mapping
    const colorPalette = [
        primaryColor,
        warningColor,
        successColor,
        dangerColor,
        '#8b5cf6', // Purple for variety
        '#64748b'  // Slate for "Others"
    ];

    const color = d3.scaleOrdinal()
        .domain(displayData.map(d => d.label))
        .range(colorPalette);

    const pie = d3.pie()
        .value(d => d.value)
        .sort((a, b) => b.value - a.value); // Sort descending

    const arc = d3.arc()
        .innerRadius(radius * 0.7) // Thicker donut
        .outerRadius(radius)
        .padAngle(0.02);

    // Create arcs with proper animation
    const arcs = svg.selectAll("path.arc")
        .data(pie(displayData))
        .enter()
        .append("g")
        .attr("class", "arc");

    const path = arcs.append("path")
        .attr("d", arc)
        .attr("fill", d => color(d.data.label))
        .attr("stroke", bgCard)
        .style("stroke-width", "2px")
        .style("cursor", "pointer")
        .style("opacity", 0.9);

    // Animate arcs with D3 transition
    path.transition()
        .duration(800)
        .delay((d, i) => i * 100)
        .attrTween("d", function(d) {
            const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
            return function(t) {
                return arc(interpolate(t));
            };
        });

    // Center Text Group
    const centerGroup = svg.append("g")
        .attr("class", "center-text");
    
    // Value Text
    const valueText = centerGroup.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0") // Vertically centered
        .style("font-size", "1.75rem") // Smaller, fit nicely
        .style("font-weight", "700")
        .style("fill", textPrimary)
        .style("font-family", fontMono)
        .style("opacity", 0)
        .text(`$${(total/1000).toFixed(1)}k`);

    // Label Text
    const labelText = centerGroup.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "1.5em")
        .style("font-size", "0.75rem")
        .style("fill", textSecondary)
        .style("font-family", fontBody)
        .style("text-transform", "uppercase")
        .style("letter-spacing", "0.05em")
        .style("opacity", 0)
        .text("Total Spending");

    // Reveal Animation
    valueText.transition().delay(1000).duration(500).style("opacity", 1);
    labelText.transition().delay(1000).duration(500).style("opacity", 1);

    // Interactions
    path.on("mouseover", function(event, d) {
        // Highlight Arc
        d3.select(this)
            .transition().duration(200)
            .attr("transform", "scale(1.05)")
            .style("opacity", 1);

        // Update Center Text
        const val = d.data.value;
        const pct = ((val / total) * 100).toFixed(0);
        
        valueText.text(`${pct}%`)
            .style("fill", color(d.data.label)); // Match slice color
            
        labelText.text(d.data.label);
    })
    .on("mouseout", function(event, d) {
        // Reset Arc
        d3.select(this)
            .transition().duration(200)
            .attr("transform", "scale(1)")
            .style("opacity", 0.9);

        // Reset Center Text
        valueText.text(`$${(total/1000).toFixed(1)}k`)
            .style("fill", textPrimary);
            
        labelText.text("Total Spending");
    });
}

