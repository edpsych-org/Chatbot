"""
Empathy Agent
Generates short, natural acknowledgments that feel human — not AI-generated.
"""

import logging
from typing import Optional
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Short fallback acknowledgments — varied, human-sounding, no AI patterns
FALLBACK_RESPONSES = {
    "attention": [
        "Noted, that's helpful.",
        "Got it — that gives useful context.",
        "Right, that makes sense.",
        "Understood, thanks for that.",
        "Okay, good to know.",
    ],
    "social": [
        "That paints a clear picture.",
        "Got it, thanks.",
        "Okay, understood.",
        "Right, helpful to know.",
        "Noted — thanks for sharing that.",
    ],
    "emotional": [
        "That's really helpful, thanks.",
        "Understood — appreciate that.",
        "Got it, that's useful context.",
        "Okay, noted.",
        "Right, that helps.",
    ],
    "academic": [
        "Got it, thanks for that.",
        "Helpful — noted.",
        "Okay, that's clear.",
        "Understood, thanks.",
        "Right, good to know.",
    ],
    "behavioral": [
        "Noted, that's useful.",
        "Got it — thanks.",
        "Okay, understood.",
        "Right, that's helpful context.",
        "Thanks for that.",
    ],
    "general": [
        "Got it, thanks.",
        "Noted.",
        "Okay, understood.",
        "Right, helpful to know.",
        "Thanks for that.",
    ],
}


class EmpathyAgent(BaseAgent):
    """Generates very short, natural acknowledgments to parent input."""

    def __init__(self):
        super().__init__(name="EmpathyAgent", timeout=8.0, max_tokens=60)
        self._response_index = {}

    async def generate_response(
        self,
        user_input: str,
        category: str = "general",
        student_name: str = "your child",
        severity: str = "medium",
        context_summary: str = "",
        next_question: str = "",
    ) -> str:
        """Generate a very short acknowledgment. Always returns something."""

        prompt = f"""A parent just answered a question about their child.

Parent said: "{user_input}"

Write ONE short sentence (max 8 words) to acknowledge their answer. Strict rules:
- Sound like a real person, NOT a chatbot
- BANNED words/phrases: "consistently", "you mentioned", "thank you for sharing", "I understand", "appreciate", "that's really", "it sounds like", "concerns", "assessment", "AI", "psychology", "valuable"
- NEVER repeat any word the parent just said
- NEVER ask a question
- NEVER use the child's name
- Each response must feel completely different from the last
- Keep it casual and brief — 3-8 words max

Good: "Got it." / "Right, noted." / "Okay, clear." / "Makes sense." / "Fair enough." / "Understood." / "Good to know."
Bad: "You mentioned that consistently..." / "Thank you for sharing that about..." / "I understand your concerns..."\""""

        response = await self.call_llm(prompt, temperature=0.7)

        if response and 3 < len(response) < 80:
            response = response.strip().strip('"').strip("'")
            if response.startswith("Response:"):
                response = response[9:].strip()
            return response

        return self._get_fallback(category)

    def _get_fallback(self, category: str) -> str:
        """Get a rotating fallback response."""
        responses = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES["general"])
        idx = self._response_index.get(category, 0)
        response = responses[idx % len(responses)]
        self._response_index[category] = idx + 1
        return response
