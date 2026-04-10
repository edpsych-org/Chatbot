"""
Orchestrator Agent
Coordinates all agents to process parent messages.
Runs validator, assessor, and empathy agents in parallel for speed.
"""

import asyncio
import logging
from typing import Optional
from app.agents.validator import InputValidatorAgent
from app.agents.empathy import EmpathyAgent
from app.agents.assessor import AssessmentAgent
from app.agents.background import BackgroundGenerator

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Coordinates all agents for optimal response generation.

    Flow:
    1. Validate input (fast heuristics)
    2. If insufficient -> return validation feedback
    3. If sufficient -> run Assessor + Empathy in parallel
    4. Update background profile asynchronously
    5. Return combined response
    """

    def __init__(self):
        self.validator = InputValidatorAgent()
        self.empathy = EmpathyAgent()
        self.assessor = AssessmentAgent()
        self.background = BackgroundGenerator()

    async def process_free_text(
        self,
        user_input: str,
        context_data: dict,
        current_category: str = "general",
        next_question: str = "",
        current_question: str = "",
    ) -> dict:
        """
        Process a free-text parent response through the multi-agent pipeline.

        Returns: {
            "response_type": "validation_feedback" | "empathetic_response",
            "content": str,
            "classification": dict | None,
            "background_update": dict | None,
            "is_sufficient": bool,
        }
        """
        student_name = context_data.get("user_profile", {}).get("student_name", "your child")
        context_summary = self._summarize_context(context_data)

        # Step 1: Validate input (heuristics + LLM for long inputs)
        validation = await self.validator.validate(
            user_input=user_input,
            category=current_category,
            student_name=student_name,
            question_context=current_question,
        )

        if not validation["is_sufficient"]:
            return {
                "response_type": "validation_feedback",
                "content": validation["feedback"],
                "classification": None,
                "background_update": None,
                "is_sufficient": False,
            }

        # Step 2: Run Assessor + Empathy in parallel for speed
        assessor_task = self.assessor.analyze(
            user_input=user_input,
            current_category=current_category,
            student_name=student_name,
            context_summary=context_summary,
        )
        empathy_task = self.empathy.generate_response(
            user_input=user_input,
            category=current_category,
            student_name=student_name,
            context_summary=context_summary,
            next_question=next_question,
        )

        assessment_result, empathetic_response = await asyncio.gather(
            assessor_task, empathy_task, return_exceptions=True
        )

        # Handle exceptions from parallel tasks
        if isinstance(assessment_result, Exception):
            logger.error(f"Assessor failed: {assessment_result}")
            assessment_result = {
                "category": current_category,
                "severity": "medium",
                "indicators": [],
                "confidence": 0.3,
            }

        if isinstance(empathetic_response, Exception):
            logger.error(f"Empathy failed: {empathetic_response}")
            empathetic_response = f"Thank you for sharing that about {student_name}. This is really helpful for the assessment."

        # Step 3: Update background profile (non-blocking)
        background_update = None
        try:
            current_profile = context_data.get("background_profile", {})
            background_update = await self.background.update_running_profile(
                current_profile=current_profile,
                new_data=assessment_result,
                category=assessment_result.get("category", current_category),
                student_name=student_name,
            )
        except Exception as e:
            logger.error(f"Background update failed: {e}")

        return {
            "response_type": "empathetic_response",
            "content": empathetic_response,
            "classification": assessment_result,
            "background_update": background_update,
            "is_sufficient": True,
        }

    async def generate_transition(
        self,
        user_choice: str,
        current_category: str,
        next_category: str,
        student_name: str = "your child",
        context_summary: str = "",
        next_question: str = "",
    ) -> str:
        """
        Generate a brief AI acknowledgment + transition between questions.
        Makes the flow feel conversational rather than scripted.
        """
        response = await self.empathy.generate_response(
            user_input=user_choice,
            category=current_category,
            student_name=student_name,
            severity="medium",
            context_summary=context_summary,
            next_question=next_question,
        )
        return response

    async def process_elaboration_request(
        self,
        context_data: dict,
        current_category: str = "general",
    ) -> str:
        """Handle 'Tell me more' requests."""
        student_name = context_data.get("user_profile", {}).get("student_name", "your child")
        context_summary = self._summarize_context(context_data)

        response = await self.empathy.generate_response(
            user_input="Tell me more about this topic",
            category=current_category,
            student_name=student_name,
            context_summary=context_summary,
        )

        return response

    async def generate_background_report(
        self,
        context_data: dict,
    ) -> dict:
        """
        Generate a comprehensive background profile from all collected data.
        Called when assessment is nearing completion.
        """
        assessment_data = context_data.get("assessment_data", {})
        student_info = context_data.get("user_profile", {})

        # Check data completeness first
        completeness = await self.background.check_completeness(assessment_data)

        # Generate profile
        profile = await self.background.generate_profile(assessment_data, student_info)

        return {
            "profile": profile,
            "completeness": completeness,
        }

    def _summarize_context(self, context_data: dict) -> str:
        """Create compact context summary for agent prompts."""
        parts = []

        assessment = context_data.get("assessment_data", {})
        if assessment:
            severity_items = []
            for cat, data in assessment.items():
                if isinstance(data, dict) and "severity" in data:
                    severity_items.append(f"{cat}={data['severity']}")
            if severity_items:
                parts.append("Severities: " + ", ".join(severity_items))

        summary = context_data.get("conversation_summary", "")
        if summary:
            parts.append(f"Summary: {summary}")

        explored = context_data.get("explored_areas", [])
        if explored:
            parts.append("Explored: " + ", ".join(explored))

        return " | ".join(parts) if parts else "No prior context."
