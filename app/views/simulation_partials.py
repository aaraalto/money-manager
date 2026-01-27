"""
HTML generation helpers for simulation partials.

These functions generate HTMX-compatible HTML fragments for the simulator page.
Keeps HTML generation separate from business logic for cleaner architecture.
"""
import html as html_module
from typing import List

from app.models import Liability
from app.services.simulation import SimulationResult
from app.core.config import FINANCIAL


def render_fcf_metric(result: SimulationResult) -> str:
    """Render the Free Cash Flow metric HTML."""
    fcf_class = "positive" if result.fcf_is_positive else "negative"
    return f'<span class="value {fcf_class}" id="metric-fcf" hx-swap-oob="true">${result.fcf:,.0f}</span>'


def render_date_metric(result: SimulationResult) -> str:
    """Render the payoff date metric HTML."""
    return f'<div class="value date" id="metric-date" hx-swap-oob="true">{result.payoff_date_str}</div>'


def render_savings_metric(result: SimulationResult) -> str:
    """Render the interest saved metric HTML."""
    return f'<div class="value positive" id="metric-savings" hx-swap-oob="true">${result.interest_saved:,.0f}</div>'


def render_chart(result: SimulationResult) -> str:
    """Render the chart container HTML."""
    return f'<div id="chart-container" hx-swap-oob="true">{result.chart_svg}</div>'


def render_liability_row(
    liability: Liability, 
    payoff_date_str: str, 
    is_paid_off: bool
) -> str:
    """
    Render a single liability row HTML.
    
    Args:
        liability: The liability to render
        payoff_date_str: Formatted payoff date string
        is_paid_off: Whether the liability is paid off
        
    Returns:
        HTML string for the table row
    """
    row_class = "row-paid-off" if is_paid_off else ""
    
    # Escape user data to prevent XSS
    debt_name_escaped = html_module.escape(liability.name)
    
    if is_paid_off:
        p_date = "-"
        pay_action = ""
    else:
        p_date = payoff_date_str
        # Pay Link (Action) - visible on hover
        if getattr(liability, 'payment_url', None):
            payment_url_escaped = html_module.escape(liability.payment_url)
            pay_action = f'<a href="{payment_url_escaped}" target="_blank" class="pay-link" title="Pay off {debt_name_escaped}">Pay</a>'
        else:
            pay_action = f'<a href="/pay/{liability.id}" class="pay-link" title="Pay off {debt_name_escaped}">Pay</a>'
    
    apr = f"{liability.interest_rate * 100:.1f}%"
    apr_class = "text-danger" if liability.interest_rate > FINANCIAL.DANGER_INTEREST_THRESHOLD else ""
    
    return f"""
    <tr class="{row_class}">
        <td class="cell-name">{debt_name_escaped}</td>
        <td class="text-right"><span class="badge badge-soft {apr_class}">{apr}</span></td>
        <td class="cell-mono">${liability.balance:,.0f}</td>
        <td class="cell-mono text-right">{p_date}</td>
        <td class="cell-action text-right">{pay_action}</td>
    </tr>
    """


def render_empty_table_state() -> str:
    """Render the empty state for when there are no liabilities."""
    return """
    <tr>
        <td colspan="5" class="empty-state">
            <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                <p>No liabilities found.</p>
                <p style="font-size: 0.85rem;">Add debts to start tracking your payoff journey.</p>
            </div>
        </td>
    </tr>
    """


def render_liabilities_table(result: SimulationResult) -> str:
    """
    Render the full liabilities table HTML.
    
    Args:
        result: The simulation result containing liabilities data
        
    Returns:
        HTML string for the table container
    """
    if not result.filtered_liabilities:
        table_rows = render_empty_table_state()
    else:
        rows = []
        for liability in result.filtered_liabilities:
            is_paid_off = liability.balance <= 0
            payoff_date = result.payoff_dates.get(liability.name, result.payoff_date)
            payoff_date_str = "-" if is_paid_off else payoff_date.strftime("%b %Y")
            
            rows.append(render_liability_row(liability, payoff_date_str, is_paid_off))
        table_rows = "".join(rows)
    
    return f"""
    <div id="payment-table-container" hx-swap-oob="true">
        <div class="sim-table-container">
            <table class="sim-table">
                <thead>
                    <tr>
                        <th class="text-left">Debt Name</th>
                        <th class="text-right">APR</th>
                        <th class="text-left">Balance</th>
                        <th class="text-right">Payoff Date</th>
                        <th class="text-right">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>
    """


def render_filter_dropdown(result: SimulationResult) -> str:
    """
    Render the filter dropdown HTML.
    
    Args:
        result: The simulation result containing filter metadata
        
    Returns:
        HTML string for the filter container
    """
    options = ""
    for tag in result.available_tags:
        selected = "selected" if tag == result.filter_tag else ""
        options += f'<option value="{tag}" {selected}>{tag}</option>'
    
    filter_dropdown = f"""
    <div class="select-wrapper">
        <select class="filter-select" 
                onchange="document.querySelector('[name=filter_tag]').value=this.value; htmx.trigger('#hidden-payment-input', 'change')">
            {options}
        </select>
        <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
    </div>
    """
    
    return f'<div id="filter-container" class="filter-row" hx-swap-oob="true">{filter_dropdown}</div>'


def render_simulation_partial(result: SimulationResult) -> str:
    """
    Render the complete simulation partial HTML.
    
    Combines all individual components into the full HTMX response.
    
    Args:
        result: The simulation result
        
    Returns:
        Complete HTML string for HTMX out-of-band swaps
    """
    parts = [
        render_fcf_metric(result),
        render_date_metric(result),
        render_savings_metric(result),
        render_chart(result),
        render_liabilities_table(result),
        render_filter_dropdown(result),
    ]
    
    return "".join(parts)
