"""
Empathy Agent
Returns short, predefined transitional acknowledgments. No LLM call —
the previous LLM path produced inconsistent fluff that didn't match the
product's "thanks, next question" style, so we use a rotating canned set.
"""

import logging
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Short transitional acknowledgments — forward-flowing, no evaluation, no fluff.
# Same neutral set across every category by design.
_TRANSITIONAL_ACKS = [
    "Thanks. Next question:",
    "Got it. Moving on.",
    "Noted. Next part:",
    "Thanks — let's move on.",
    "Okay, moved to the next one:",
]

FALLBACK_RESPONSES = {
    "attention":  _TRANSITIONAL_ACKS,
    "social":     _TRANSITIONAL_ACKS,
    "emotional":  _TRANSITIONAL_ACKS,
    "academic":   _TRANSITIONAL_ACKS,
    "behavioral": _TRANSITIONAL_ACKS,
    "general":    _TRANSITIONAL_ACKS,
}


class EmpathyAgent(BaseAgent):
    """Returns a rotating predefined acknowledgment. No LLM call."""

    def __init__(self):
        # Kept as BaseAgent subclass so the orchestrator wiring is unchanged,
        # but call_llm is never invoked here.
        super().__init__(
            name="EmpathyAgent",
            timeout=8.0,
            max_tokens=60,
            default_provider="groq",
        )
        self._response_index = {}

    async def generate_response(
        self,
        user_input: str = "",
        category: str = "general",
        student_name: str = "your child",
        severity: str = "medium",
        context_summary: str = "",
        next_question: str = "",
    ) -> str:
        """Return the next rotating predefined transitional ack for this category."""
        del user_input, student_name, severity, context_summary, next_question
        return self._get_fallback(category)

    def _get_fallback(self, category: str) -> str:
        """Rotating index into the predefined ack list."""
        responses = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES["general"])
        idx = self._response_index.get(category, 0)
        response = responses[idx % len(responses)]
        self._response_index[category] = idx + 1
        return response
