"""
Background Generator Agent
Builds comprehensive background information profiles from collected assessment data.
Runs asynchronously to generate profiles as data is collected.
"""

import logging
from typing import Optional
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class BackgroundGenerator(BaseAgent):
    """Generates comprehensive background profiles from assessment data."""

    def __init__(self):
        super().__init__(name="BackgroundGenerator", timeout=25.0, max_tokens=800)

    async def generate_profile(self, assessment_data: dict, student_info: dict) -> dict:
        """
        Generate a comprehensive background profile from all collected data.
        Returns: {
            "profile_summary": str,
            "key_concerns": list[str],
            "strengths": list[str],
            "areas_of_need": list[str],
            "severity_overview": dict,
            "recommendations_preview": list[str],
        }
        """
        student_name = student_info.get("student_name", "the student")
        student_age = student_info.get("student_age", "unknown")

        # Build data summary from assessment responses
        data_summary = self._build_data_summary(assessment_data)

        if not data_summary:
            return self._empty_profile(student_name)

        prompt = f"""You are an educational psychologist. Based on parent assessment responses, generate a background profile.

Student: {student_name}, Age: {student_age}
Assessment Data:
{data_summary}

Generate a JSON profile:
{{
  "profile_summary": "2-3 sentence overview of the student's presentation",
  "key_concerns": ["concern 1", "concern 2"],
  "strengths": ["strength 1", "strength 2"],
  "areas_of_need": ["need 1", "need 2"],
  "severity_overview": {{"attention": "low/medium/high", "social": "...", "emotional": "...", "academic": "...", "behavioral": "..."}},
  "recommendations_preview": ["rec 1", "rec 2"]
}}

Be specific and use British English. Base everything on the actual data provided."""

        result = await self.call_llm_json(prompt, max_tokens=600)

        if result and "profile_summary" in result:
            return result

        # Fallback: build from raw data
        return self._build_fallback_profile(assessment_data, student_name)

    async def check_completeness(self, assessment_data: dict) -> dict:
        """
        Check if collected data is sufficient for a meaningful profile.
        Returns: {
            "is_complete": bool,
            "completeness_pct": float,
            "covered_areas": list[str],
            "missing_areas": list[str],
            "suggestions": list[str],
        }
        """
        all_areas = ["attention", "social", "emotional", "academic", "behavioral"]
        covered = []
        missing = []

        for area in all_areas:
            area_data = assessment_data.get(area, {})
            if isinstance(area_data, dict) and area_data:
                # Check if there's meaningful data (not just empty dicts)
                has_data = any(
                    v for k, v in area_data.items()
                    if v and k not in ("category",)
                )
                if has_data:
                    covered.append(area)
                else:
                    missing.append(area)
            else:
                missing.append(area)

        completeness = len(covered) / len(all_areas) * 100 if all_areas else 0

        suggestions = []
        if missing:
            area_names = {
                "attention": "attention and focus",
                "social": "social interactions",
                "emotional": "emotional wellbeing",
                "academic": "academic performance",
                "behavioral": "behaviour patterns",
            }
            for area in missing[:2]:
                suggestions.append(
                    f"We still need to explore {area_names.get(area, area)}"
                )

        return {
            "is_complete": completeness >= 60,
            "completeness_pct": round(completeness, 1),
            "covered_areas": covered,
            "missing_areas": missing,
            "suggestions": suggestions,
        }

    async def update_running_profile(
        self,
        current_profile: dict,
        new_data: dict,
        category: str,
        student_name: str,
    ) -> dict:
        """
        Incrementally update the running profile with new assessment data.
        This is called after each meaningful response to keep the profile current.
        """
        if not current_profile:
            current_profile = {
                "categories": {},
                "overall_severity": "unknown",
                "data_points": 0,
            }

        # Update category data
        cat_data = current_profile.get("categories", {}).get(category, {})
        severity = new_data.get("severity", "medium")
        indicators = new_data.get("indicators", [])

        # Merge indicators
        existing_indicators = cat_data.get("indicators", [])
        all_indicators = list(set(existing_indicators + indicators))

        current_profile.setdefault("categories", {})[category] = {
            "severity": severity,
            "indicators": all_indicators,
            "data_points": cat_data.get("data_points", 0) + 1,
        }
        current_profile["data_points"] = current_profile.get("data_points", 0) + 1

        # Update overall severity
        severities = []
        for cat_info in current_profile["categories"].values():
            if isinstance(cat_info, dict) and "severity" in cat_info:
                severities.append(cat_info["severity"])

        if severities:
            severity_scores = {"low": 1, "medium": 2, "high": 3}
            avg = sum(severity_scores.get(s, 2) for s in severities) / len(severities)
            if avg >= 2.5:
                current_profile["overall_severity"] = "high"
            elif avg >= 1.5:
                current_profile["overall_severity"] = "medium"
            else:
                current_profile["overall_severity"] = "low"

        return current_profile

    def _build_data_summary(self, assessment_data: dict) -> str:
        """Build a text summary of assessment data for LLM prompt."""
        parts = []
        for category, data in assessment_data.items():
            if isinstance(data, dict) and data:
                severity = data.get("severity", "unknown")
                indicators = data.get("indicators", [])
                mcq_answers = data.get("mcq_answers", {})
                text_inputs = data.get("text_inputs", [])

                section = f"\n{category.upper()}:"
                section += f"\n  Severity: {severity}"
                if indicators:
                    section += f"\n  Indicators: {', '.join(indicators[:5])}"
                if mcq_answers:
                    answers = [f"{k}={v}" for k, v in list(mcq_answers.items())[:5]]
                    section += f"\n  Responses: {', '.join(answers)}"
                if text_inputs:
                    section += f"\n  Parent comments: {'; '.join(text_inputs[:3])}"
                parts.append(section)
            elif isinstance(data, str):
                parts.append(f"\n{category.upper()}: {data}")

        return "\n".join(parts) if parts else ""

    def _build_fallback_profile(self, assessment_data: dict, student_name: str) -> dict:
        """Build a basic profile without LLM when it's unavailable."""
        concerns = []
        areas_of_need = []
        severity_overview = {}

        for category, data in assessment_data.items():
            if isinstance(data, dict):
                severity = data.get("severity", "unknown")
                severity_overview[category] = severity
                if severity in ("medium", "high"):
                    areas_of_need.append(category)
                if severity == "high":
                    concerns.append(f"Significant {category} challenges reported")

        return {
            "profile_summary": f"Assessment data collected for {student_name} across {len(assessment_data)} areas.",
            "key_concerns": concerns or ["Full analysis pending professional review"],
            "strengths": ["To be identified through detailed professional analysis"],
            "areas_of_need": areas_of_need or ["Further assessment recommended"],
            "severity_overview": severity_overview,
            "recommendations_preview": ["Professional review of assessment data recommended"],
        }

    def _empty_profile(self, student_name: str) -> dict:
        return {
            "profile_summary": f"Assessment for {student_name} is in progress. Insufficient data for profile generation.",
            "key_concerns": [],
            "strengths": [],
            "areas_of_need": [],
            "severity_overview": {},
            "recommendations_preview": [],
        }
