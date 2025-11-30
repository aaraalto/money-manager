// Spectra Dashboard Logic

document.addEventListener('DOMContentLoaded', () => {
    initSpectra();
});

function initSpectra() {
    // 1. Initialize Rotary Dial
    // We assume RotaryKnob is available from rotary.js
    const rotary = new RotaryKnob('#payment-rotary', {
        minValue: 0,
        maxValue: 5000,
        initialValue: 500,
        displaySelector: '#rotary-display'
    });

    // Hook into rotary updates (monkey patch or event listener if available)
    // For now, we'll just simulate updates on drag end or periodically
    // Ideally RotaryKnob would emit events. Let's assume we can add a callback.
    // Since we can't easily modify rotary.js right now without breaking other things, 
    // we will observe the DOM changes on the display element as a proxy for value changes.

    const displayElement = document.getElementById('rotary-display');
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'characterData' || mutation.type === 'childList') {
                const value = parseInt(displayElement.textContent.replace(/,/g, ''));
                updateSimulation(value);
            }
        });
    });

    observer.observe(displayElement, { characterData: true, subtree: true, childList: true });

    // 2. Initial Render
    updateSimulation(500);

    // 3. Handle Resize
    window.addEventListener('resize', () => {
        const value = parseInt(displayElement.textContent.replace(/,/g, ''));
        renderCharts(generateData(value));
    });
}

function updateSimulation(monthlyPayment) {
    const data = generateData(monthlyPayment);

    // Update Metrics
    document.getElementById('metric-surplus').textContent = formatCurrency(data.surplus);
    document.getElementById('metric-date').textContent = data.debtFreeDate;
    document.getElementById('metric-saved').textContent = formatCurrency(data.interestSaved);

    // Render Charts
    renderCharts(data);

    // Update Table
    renderTable(data.tableData);
}

function generateData(payment) {
    // Mock Liabilities
    const liabilities = [
        { name: 'Chase Sapphire', balance: 5400, rate: 0.24, min: 150 },
        { name: 'Amex Gold', balance: 0, rate: 0.21, min: 0 }, // Should be hidden
        { name: 'Student Loan', balance: 9600, rate: 0.06, min: 100 },
        { name: 'Personal Loan', balance: 0, rate: 0.12, min: 0 } // Should be hidden
    ];

    // Filter out zero balance liabilities
    const activeLiabilities = liabilities.filter(l => l.balance > 0);

    // Simulation Logic (Simplified)
    const baseSurplus = 2000;
    const surplus = baseSurplus - payment;

    // Total Debt from active liabilities
    const totalDebt = activeLiabilities.reduce((sum, l) => sum + l.balance, 0);
    const weightedRate = activeLiabilities.reduce((sum, l) => sum + (l.rate * l.balance), 0) / totalDebt;
    const monthlyInterest = weightedRate / 12;

    let balance = totalDebt;
    let totalInterest = 0;
    const tableData = [];

    const today = new Date();

    // Generate projection data
    const wealthData = [];
    const debtDataSnowball = [];
    const debtDataAvalanche = [];

    let currentWealth = 5000; // Starting net worth

    // Simulate 24 months
    for (let i = 0; i <= 24; i++) {
        const date = new Date(today.getFullYear(), today.getMonth() + i, 1);

        // Wealth Growth
        wealthData.push({ date: date, value: currentWealth });
        currentWealth += surplus + (payment * 0.5); // Assume some investment growth

        // Debt Payoff (Snowball)
        let snowBalance = Math.max(0, totalDebt - (payment * i)); // Linear approx for viz
        debtDataSnowball.push({ date: date, value: snowBalance });

        // Debt Payoff (Avalanche - faster)
        let avBalance = Math.max(0, totalDebt - ((payment + 100) * i)); // Fake efficiency
        debtDataAvalanche.push({ date: date, value: avBalance });

        // Table Data (first 3 months)
        if (i < 3) {
            const interest = balance * monthlyInterest;
            const principal = payment - interest;
            balance -= principal;
            totalInterest += interest;

            tableData.push({
                date: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                payment: payment,
                principal: principal > 0 ? principal : 0,
                interest: interest > 0 ? interest : 0,
                remaining: balance > 0 ? balance : 0
            });
        }
    }

    // Calculate "Debt Free By"
    const monthsToPayoff = totalDebt / payment;
    const payoffDate = new Date(today.getFullYear(), today.getMonth() + monthsToPayoff, 1);
    const debtFreeDate = payoffDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

    return {
        surplus: surplus,
        debtFreeDate: debtFreeDate,
        interestSaved: Math.round(totalInterest * 0.8), // Fake savings calculation
        wealthData: wealthData,
        debtDataSnowball: debtDataSnowball,
        debtDataAvalanche: debtDataAvalanche,
        tableData: tableData,
        activeLiabilities: activeLiabilities
    };
}

function renderCharts(data) {
    renderWealthChart(data.wealthData);
    renderDebtChart(data.debtDataSnowball, data.debtDataAvalanche);
    renderLiabilities(data.activeLiabilities);
}

function renderLiabilities(liabilities) {
    const container = document.getElementById('liabilities-list');
    if (!container) return;

    container.innerHTML = '';

    liabilities.forEach(l => {
        const item = document.createElement('div');
        item.className = 'liability-item';
        item.innerHTML = `
            <div class="liability-info">
                <div class="liability-name">${l.name}</div>
                <div class="liability-rate">${(l.rate * 100).toFixed(1)}% APR</div>
            </div>
            <div class="liability-balance">${formatCurrency(l.balance)}</div>
        `;
        container.appendChild(item);
    });
}

function renderWealthChart(data) {
    const container = document.getElementById('wealth-chart');
    container.innerHTML = '';

    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = container.clientHeight - margin.top - margin.bottom;

    const svg = d3.select(container).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value)])
        .range([height, 0]);

    // Area
    const area = d3.area()
        .x(d => x(d.date))
        .y0(height)
        .y1(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Gradient
    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "wealth-gradient")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "0%")
        .attr("y2", "100%");
    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#3b82f6").attr("stop-opacity", 0.5);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#3b82f6").attr("stop-opacity", 0);

    // Draw Area
    svg.append("path")
        .datum(data)
        .attr("fill", "url(#wealth-gradient)")
        .attr("d", area);

    // Draw Line
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#3b82f6")
        .attr("stroke-width", 3)
        .attr("d", d3.line()
            .x(d => x(d.date))
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX)
        );

    // Axes
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(10))
        .style("color", "#52525b");

    svg.append("g")
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => "$" + d / 1000 + "k").tickSize(0).tickPadding(10))
        .style("color", "#52525b")
        .select(".domain").remove();
}

function renderDebtChart(data1, data2) {
    const container = document.getElementById('debt-chart');
    container.innerHTML = '';

    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = container.clientHeight - margin.top - margin.bottom;

    const svg = d3.select(container).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const allData = [...data1, ...data2];

    const x = d3.scaleTime()
        .domain(d3.extent(allData, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(allData, d => d.value)])
        .range([height, 0]);

    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Snowball Line (Red)
    svg.append("path")
        .datum(data1)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 3)
        .attr("d", line);

    // Avalanche Line (Green)
    svg.append("path")
        .datum(data2)
        .attr("fill", "none")
        .attr("stroke", "#10b981")
        .attr("stroke-width", 3)
        .attr("stroke-dasharray", "5,5")
        .attr("d", line);

    // Axes
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(10))
        .style("color", "#52525b");

    svg.append("g")
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => "$" + d / 1000 + "k").tickSize(0).tickPadding(10))
        .style("color", "#52525b")
        .select(".domain").remove();
}

function renderTable(data) {
    const tbody = document.getElementById('payment-table-body');
    tbody.innerHTML = '';

    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.date}</td>
            <td>${formatCurrency(row.payment)}</td>
            <td>${formatCurrency(row.principal)}</td>
            <td>${formatCurrency(row.interest)}</td>
            <td class="text-right">${formatCurrency(row.remaining)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
    }).format(val);
}
