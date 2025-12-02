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

    // Adjusted margins to give more space to the pie
    const margin = { top: 10, right: 10, bottom: 50, left: 10 };
    const containerNode = container.node();
    if (!containerNode) return;
    
    const width = containerNode.getBoundingClientRect().width;
    const height = (containerNode.getBoundingClientRect().height || 220);
    
    // FIX: Correctly calculate available dimensions
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // FIX: Radius is half of the smallest dimension, without extra subtraction
    const radius = Math.min(chartWidth, chartHeight) / 2;

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        // FIX: Center the group based on calculated margins and dimensions
        .attr("transform", `translate(${margin.left + chartWidth / 2},${margin.top + chartHeight / 2})`);

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
        .innerRadius(radius * 0.65) // Slightly thicker donut
        .outerRadius(radius)
        .padAngle(0.02);

    const outerArc = d3.arc()
        .innerRadius(radius * 1.1)
        .outerRadius(radius * 1.1);

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
        .style("opacity", 0.9)
        .on("mouseover", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("transform", "scale(1.05)")
                .style("opacity", 1);
            
            // Highlight in legend
            const label = d.data.label;
            svg.selectAll(".legend-item")
                .filter(d => d === label)
                .select("rect")
                .style("opacity", 1)
                .style("stroke-width", "2px");
        })
        .on("mouseout", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("transform", "scale(1)")
                .style("opacity", 0.9);
            
            // Reset legend
            svg.selectAll(".legend-item")
                .select("rect")
                .style("opacity", 0.8)
                .style("stroke-width", "1px");
        });

    // Animate arcs with D3 transition (more reliable than GSAP for paths)
    path.transition()
        .duration(800)
        .delay((d, i) => i * 100)
        .attrTween("d", function(d) {
            const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
            return function(t) {
                return arc(interpolate(t));
            };
        });

    // Add center text (Total) with proper typography
    const total = displayData.reduce((acc, curr) => acc + curr.value, 0);
    
    const centerGroup = svg.append("g")
        .attr("class", "center-text");
    
    centerGroup.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "-0.2em")
        .style("font-size", "clamp(1.5rem, 3vw, 2.5rem)")
        .style("font-weight", "700")
        .style("fill", textPrimary)
        .style("font-family", fontMono)
        .style("opacity", 0)
        .text(`$${(total/1000).toFixed(1)}k`)
        .transition()
        .delay(1000)
        .duration(500)
        .style("opacity", 1);
        
    centerGroup.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "1.4em")
        .style("font-size", "0.85rem")
        .style("fill", textSecondary)
        .style("font-family", fontBody)
        .style("opacity", 0)
        .text("Total")
        .transition()
        .delay(1000)
        .duration(500)
        .style("opacity", 1);

    // Add interactive legend below chart
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${-width/2 + margin.left}, ${chartHeight/2 + margin.top + 20})`);

    const legendItem = legend.selectAll(".legend-item")
        .data(displayData)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => {
            const itemWidth = 140;
            const itemsPerRow = Math.floor((width - margin.left - margin.right) / itemWidth);
            const row = Math.floor(i / itemsPerRow);
            const col = i % itemsPerRow;
            return `translate(${col * itemWidth}, ${row * 24})`;
        })
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            // Highlight corresponding arc
            path.filter(p => p.data.label === d.label)
                .transition()
                .duration(200)
                .attr("transform", "scale(1.05)")
                .style("opacity", 1);
        })
        .on("mouseout", function(event, d) {
            path.filter(p => p.data.label === d.label)
                .transition()
                .duration(200)
                .attr("transform", "scale(1)")
                .style("opacity", 0.9);
        });

    legendItem.append("rect")
        .attr("width", 12)
        .attr("height", 12)
        .attr("rx", 2)
        .attr("fill", d => color(d.label))
        .style("opacity", 0.8)
        .style("stroke", bgCard)
        .style("stroke-width", "1px");

    legendItem.append("text")
        .attr("x", 16)
        .attr("y", 9)
        .style("font-size", "0.75rem")
        .style("fill", textSecondary)
        .style("font-family", fontBody)
        .text(d => {
            const pct = ((d.value / total) * 100).toFixed(0);
            return `${d.label} (${pct}%)`;
        });

    // Animate legend
    if (typeof gsap !== 'undefined') {
        legend.style("opacity", 0);
        gsap.to(legend.node(), {
            opacity: 1,
            duration: 0.5,
            delay: 1.2
        });
    }
}

