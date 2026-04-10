"""
Local LLM Service using Ollama
Integrates with Qwen2.5:7b for AI report generation
"""

import requests
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Max retries and delay for Ollama calls
OLLAMA_MAX_RETRIES = 2
OLLAMA_RETRY_DELAY_SECONDS = 3


class LocalLLMService:
    """Service for interacting with Ollama local LLM"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS

    def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens_override: Optional[int] = None,
        fallback_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make a call to Ollama API with retry logic.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt.
            max_tokens_override: Override the default max_tokens for this call.
            fallback_text: Text to return on final failure instead of crashing.

        Returns:
            Dictionary with success status, text, model, duration, and tokens.
        """
        # Fail fast: check if Ollama is reachable before attempting generation
        if not self.check_health():
            logger.error("Ollama health check failed - service is unreachable")
            return self._build_failure_response(
                error="Ollama service is not available",
                fallback_text=fallback_text,
            )

        num_predict = max_tokens_override if max_tokens_override is not None else self.max_tokens
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_predict": num_predict,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        last_error: Optional[str] = None

        for attempt in range(1, OLLAMA_MAX_RETRIES + 2):  # attempt 1, 2, 3 (initial + 2 retries)
            try:
                logger.info(
                    f"Calling Ollama API (attempt {attempt}/{OLLAMA_MAX_RETRIES + 1}) "
                    f"with model: {self.model}"
                )
                start_time = datetime.now()

                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = response.json()
                logger.info(f"Ollama response received in {duration:.2f}s (attempt {attempt})")

                return {
                    "success": True,
                    "text": result.get("response", ""),
                    "model": result.get("model", self.model),
                    "duration": duration,
                    "tokens": result.get("eval_count", 0),
                }

            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {self.timeout}s"
                logger.warning(
                    f"Ollama attempt {attempt} timed out after {self.timeout}s"
                )
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.warning(f"Ollama attempt {attempt} connection error: {e}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Ollama attempt {attempt} error: {e}")

            # Wait before retrying (skip delay after last attempt)
            if attempt <= OLLAMA_MAX_RETRIES:
                logger.info(
                    f"Retrying Ollama call in {OLLAMA_RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(OLLAMA_RETRY_DELAY_SECONDS)

        # All attempts exhausted
        logger.error(
            f"Ollama call failed after {OLLAMA_MAX_RETRIES + 1} attempts. "
            f"Last error: {last_error}"
        )
        return self._build_failure_response(error=last_error, fallback_text=fallback_text)

    def _build_failure_response(
        self,
        error: Optional[str] = None,
        fallback_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a structured failure response instead of crashing."""
        return {
            "success": False,
            "error": error or "Unknown error",
            "text": fallback_text or "",
        }

    def generate_profile_section(self, chatbot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the Profile section of the psychological report

        Args:
            chatbot_data: Dictionary containing student info and chatbot answers

        Returns:
            Dictionary with generated text and metadata
        """
        system_prompt = (
            "You are an Educational Psychologist writing a formal report in British English. "
            "Be empathetic, evidence-based, and use appropriate psychological terminology."
        )

        student_name = chatbot_data.get("student_name", "the student")
        age = chatbot_data.get("age", "unknown")
        school = chatbot_data.get("school", "not specified")
        concerns = chatbot_data.get("concerns", "")
        family_background = chatbot_data.get("family_background", "")

        prompt = f"""Write the "Profile" section (200-300 words) for an educational psychology report.

Student: {student_name}, Age: {age}, School: {school}
Concerns: {concerns}
Family background: {family_background}

Output structure:
1. Opening sentence: "{student_name} is a {age}-year-old pupil..."
2. Referral reason (1-2 sentences)
3. Relevant background (2-3 sentences)
4. Key concerns from parents/school (2-3 sentences)
5. Concluding context sentence

Use formal British English. Be objective and compassionate."""

        fallback = (
            f"{student_name} is a {age}-year-old pupil attending {school}. "
            f"A referral was made due to concerns regarding: {concerns}. "
            "Further assessment details will follow in subsequent sections."
        )

        result = self._call_ollama(
            prompt, system_prompt, max_tokens_override=800, fallback_text=fallback
        )
        return result

    def generate_impact_section(
        self,
        chatbot_data: Dict[str, Any],
        cognitive_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate the Impact section analysing how conditions affect learning

        Args:
            chatbot_data: Dictionary containing student info and chatbot answers
            cognitive_profile: Optional cognitive test results

        Returns:
            Dictionary with generated text and metadata
        """
        system_prompt = (
            "You are an Educational Psychologist analysing learning impact. "
            "Use evidence-based language, psychological theory, and British English."
        )

        student_name = chatbot_data.get("student_name", "the student")
        difficulties = chatbot_data.get("learning_difficulties", "")
        classroom_behavior = chatbot_data.get("classroom_behavior", "")

        cognitive_info = ""
        if cognitive_profile:
            scores = cognitive_profile.get("parsed_scores", {})
            cognitive_info = f"\nCognitive scores: {json.dumps(scores)}"

        prompt = f"""Write the "Impact" section (250-350 words) for an educational psychology report.

Student: {student_name}
Difficulties: {difficulties}
Classroom observations: {classroom_behavior}{cognitive_info}

Output structure:
1. Academic impact (how difficulties affect learning, 2-3 sentences)
2. Social and emotional impact (peer relationships, self-esteem, 2-3 sentences)
3. Classroom implications (attention, participation, task completion, 2-3 sentences)
4. Cognitive profile commentary (if scores provided, 1-2 sentences)
5. Summary linking all areas (1-2 sentences)

Use formal British English with psychological terminology."""

        fallback = (
            f"The identified difficulties are likely to impact {student_name}'s "
            "academic progress, social interactions, and emotional wellbeing. "
            "A detailed analysis will be provided following further assessment."
        )

        result = self._call_ollama(
            prompt, system_prompt, max_tokens_override=1000, fallback_text=fallback
        )
        return result

    def generate_recommendations_section(
        self,
        chatbot_data: Dict[str, Any],
        cognitive_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate the Recommendations section with intervention strategies

        Args:
            chatbot_data: Dictionary containing student info and chatbot answers
            cognitive_profile: Optional cognitive test results

        Returns:
            Dictionary with generated text and metadata
        """
        system_prompt = (
            "You are an Educational Psychologist providing practical, evidence-based recommendations. "
            "Write in formal British English."
        )

        student_name = chatbot_data.get("student_name", "the student")
        age = chatbot_data.get("age", "")
        needs = chatbot_data.get("identified_needs", "")
        current_support = chatbot_data.get("current_support", "None specified")

        prompt = f"""Write the "Recommendations" section (300-400 words) for an educational psychology report.

Student: {student_name}, Age: {age}
Identified needs: {needs}
Current support: {current_support}

Output structure (use these as headings):
1. Classroom Interventions - 2-3 specific, actionable strategies
2. Teaching Strategies - 2-3 approaches suited to the student's needs
3. Environmental Modifications - 1-2 adjustments to the learning environment
4. Emotional and Social Support - 1-2 targeted strategies
5. Home-School Collaboration - 1-2 practical suggestions
6. Further Assessment - any additional evaluations recommended

Each recommendation must be specific, achievable, and age-appropriate.
Use formal British English with professional psychological terminology."""

        fallback = (
            f"Recommendations for {student_name} should focus on targeted classroom "
            "interventions, differentiated teaching strategies, and close home-school "
            "collaboration. A detailed set of recommendations will be provided "
            "following completion of the full assessment."
        )

        result = self._call_ollama(
            prompt, system_prompt, max_tokens_override=1200, fallback_text=fallback
        )
        return result

    def parse_ocr_text(self, ocr_text: str) -> Dict[str, Any]:
        """
        Parse OCR text from IQ test to extract structured scores

        Args:
            ocr_text: Raw OCR text from scanned IQ test

        Returns:
            Dictionary with parsed scores in JSON format
        """
        system_prompt = """You are a data extraction specialist. Extract IQ test scores from OCR text and return valid JSON only."""

        prompt = f"""Extract test scores from this OCR text and return ONLY valid JSON (no additional text):

OCR Text:
{ocr_text}

Return JSON in this exact format:
{{
  "test_name": "WISC-V",
  "test_date": "YYYY-MM-DD or null",
  "scores": {{
    "Verbal Comprehension": 112,
    "Visual Spatial": 105,
    "Fluid Reasoning": 98,
    "Working Memory": 89,
    "Processing Speed": 92,
    "Full Scale IQ": 99
  }},
  "percentiles": {{
    "Verbal Comprehension": 79,
    "Visual Spatial": 63,
    ...
  }}
}}

If you cannot extract certain information, use null. Return ONLY the JSON, no other text.
"""

        result = self._call_ollama(prompt, system_prompt)

        if result.get("success"):
            try:
                # Parse the JSON response
                parsed_data = json.loads(result["text"])
                return {
                    "success": True,
                    "parsed_scores": parsed_data,
                    "confidence": 0.85  # You could implement confidence scoring
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from LLM response")
                return {
                    "success": False,
                    "error": "Invalid JSON response from LLM",
                    "parsed_scores": None
                }
        else:
            return result

    def check_health(self) -> bool:
        """Check if Ollama service is available"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False


# Singleton instance
llm_service = LocalLLMService()
