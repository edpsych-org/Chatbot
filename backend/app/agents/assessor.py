"""
Assessment Agent
Extracts clinical insights from parent responses: category classification,
severity rating, and key indicators.
Uses fast keyword matching with optional LLM enhancement.
"""

import logging
from typing import Optional
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "attention": [
        "focus", "concentrate", "distract", "fidget", "hyperactive",
        "restless", "attention", "sit still", "wander", "daydream",
        "homework", "task", "zoning out", "off-task", "forgetful",
    ],
    "social": [
        "friend", "play", "share", "interact", "lonely", "bully",
        "peer", "social", "group", "cooperate", "empathy", "turn-taking",
        "left out", "rejected", "argue with friends",
    ],
    "emotional": [
        "angry", "sad", "anxious", "worry", "fear", "cry", "mood",
        "tantrum", "frustrate", "overwhelm", "meltdown", "calm",
        "upset", "scared", "panic", "nervous", "clingy",
    ],
    "academic": [
        "read", "write", "math", "school", "grade", "learn", "study",
        "spell", "comprehend", "struggle", "test", "score", "homework",
        "tutor", "behind", "difficulty",
    ],
    "behavioral": [
        "rule", "behave", "defy", "comply", "argue", "disrupt",
        "impulsive", "aggressive", "disobey", "consequence", "hit",
        "throw", "refuse", "opposition",
    ],
}

HIGH_SEVERITY = [
    "very", "always", "never", "extremely", "severe", "serious",
    "constant", "every day", "impossible", "unbearable", "crisis",
    "aggressive", "violent", "dangerous", "self-harm",
]
LOW_SEVERITY = [
    "sometimes", "occasionally", "minor", "slight", "a bit",
    "now and then", "rarely", "mild", "little", "not really",
]


class AssessmentAgent(BaseAgent):
    """Extracts clinical assessment data from parent responses."""

    def __init__(self):
        super().__init__(name="AssessmentAgent", timeout=10.0, max_tokens=200)

    async def analyze(
        self,
        user_input: str,
        current_category: str = "general",
        student_name: str = "your child",
        context_summary: str = "",
    ) -> dict:
        """
        Analyze parent input for clinical insights.
        Returns: {
            "category": str,
            "severity": str ("low"/"medium"/"high"),
            "indicators": list[str],
            "confidence": float,
        }
        """
        # Fast keyword-based classification
        keyword_result = self._keyword_classify(user_input, current_category)

        # If keyword matching is confident enough, skip LLM
        if keyword_result["confidence"] >= 0.7:
            return keyword_result

        # Try LLM for better classification
        llm_result = await self._llm_classify(user_input, current_category, student_name, context_summary)
        if llm_result:
            return llm_result

        # Fall back to keyword result
        return keyword_result

    def _keyword_classify(self, text: str, current_category: str) -> dict:
        """Fast keyword-based classification."""
        text_lower = text.lower()

        # Score each category
        scores = {}
        matched_keywords = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in text_lower]
            scores[cat] = len(matches)
            matched_keywords[cat] = matches

        # Best category
        best_cat = max(scores, key=scores.get) if any(scores.values()) else current_category
        best_score = scores.get(best_cat, 0)

        # If no keywords matched, use current category
        if best_score == 0:
            best_cat = current_category

        # Severity
        severity = "medium"
        if any(word in text_lower for word in HIGH_SEVERITY):
            severity = "high"
        elif any(word in text_lower for word in LOW_SEVERITY):
            severity = "low"

        # Confidence based on keyword matches
        confidence = min(0.4 + (best_score * 0.15), 0.9) if best_score > 0 else 0.3

        return {
            "category": best_cat,
            "severity": severity,
            "indicators": matched_keywords.get(best_cat, [])[:5],
            "confidence": confidence,
        }

    async def _llm_classify(
        self, text: str, current_category: str, student_name: str, context_summary: str
    ) -> Optional[dict]:
        """LLM-based classification for nuanced responses."""
        prompt = f"""Classify this parent's response about their child {student_name}.
Context area: {current_category}
Parent says: "{text}"

Return JSON: {{"category":"attention|social|emotional|academic|behavioral|general","severity":"low|medium|high","indicators":["keyword1","keyword2"],"confidence":0.0}}"""

        result = await self.call_llm_json(prompt, max_tokens=150)
        if result and "category" in result:
            return {
                "category": result.get("category", current_category),
                "severity": result.get("severity", "medium"),
                "indicators": result.get("indicators", []),
                "confidence": min(float(result.get("confidence", 0.6)), 1.0),
            }
        return None
