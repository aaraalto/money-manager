import re
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates

class ChatService:
    def __init__(self, templates: Jinja2Templates):
        self.templates = templates

    async def process_query(self, query: str, context_data: Dict[str, Any]) -> str:
        """
        Process a natural language query.
        In a real implementation, this would call an LLM (Grok/OpenAI).
        Here we use heuristics to demonstrate Generative UI.
        """
        query_lower = query.lower()
        
        # Intent: Change Payment
        # "What if I pay 500 more?" "Set payment to 1000"
        payment_match = re.search(r'(\d+)', query)
        if ("pay" in query_lower or "extra" in query_lower) and payment_match:
            amount = float(payment_match.group(1))
            return self._generate_payment_update_response(amount)
            
        # Intent: Explain Debt Strategy
        if "snowball" in query_lower or "avalanche" in query_lower:
            return self._generate_strategy_explanation(query_lower)

        # Intent: General
        return self._generate_text_response("I can help you simulate scenarios. Try asking: 'What if I pay $200 extra per month?'")

    def _generate_payment_update_response(self, amount: float) -> str:
        """
        Generates a response that updates the UI State (Rotary Knob) via HTMX OOB.
        """
        # 1. The Chat Message
        message_html = f"""
        <div class="message ai">
            I've updated the simulation to an extra <strong>${amount:,.0f}/mo</strong> payment. 
            Check the trajectory update above!
        </div>
        """
        
        # 2. The OOB Update for the Hidden Input (which triggers the simulation)
        # We also update the rotary display text manually since the rotary JS listens to input changes
        # but standard inputs don't always trigger 'input' events when changed programmatically without dispatch.
        # However, HTMX swap triggers can be used.
        
        # We will replace the hidden input. The new input must have the same attributes to keep working.
        # Crucially, we add hx-trigger="load" so it fires the calculation immediately upon being swapped in.
        oob_html = f"""
        <input type="hidden" name="monthly_payment" id="hidden-payment-input" value="{amount}"
            hx-get="/partials/calculate" 
            hx-trigger="load, change delay:200ms" 
            hx-include="[name='filter_tag']"
            hx-indicator="#loader"
            hx-swap-oob="true">
            
        <span id="rotary-display" class="rotary-amount" hx-swap-oob="true">{amount:,.0f}</span>
        """
        
        # Also update the rotary knob visual position? 
        # That requires JS. We can send a script tag.
        script_html = f"""
        <script>
            // Update rotary knob position visually if global instance exists
            // This assumes the RotaryKnob instance is accessible or we re-init
            // For now, we just update the value which drives the calculation.
        </script>
        """
        
        return message_html + oob_html

    def _generate_strategy_explanation(self, query: str) -> str:
        if "snowball" in query:
            text = "The <strong>Snowball</strong> method targets smallest balances first. It gives you quick wins but costs more in interest over time."
        else:
            text = "The <strong>Avalanche</strong> method targets highest interest rates first. It is mathematically optimal and saves you the most money."
            
        return f'<div class="message ai">{text}</div>'

    def _generate_text_response(self, text: str) -> str:
        return f'<div class="message ai">{text}</div>'

