"""
LLM service for AI report generation.

Cloud-only: calls OpenAI by default (USE_OPENAI=true in settings).
Groq is supported via explicit provider="groq" and is reserved for
future chat-flow integrations. Ollama / local LLM support has been
removed — the service always talks to a hosted provider.

Both OpenAI and Groq expose the same /chat/completions endpoint shape,
so a single _call_llm helper handles both; only base URL, API key, and
model differ.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Retry policy for LLM calls
LLM_MAX_RETRIES = 2
LLM_RETRY_DELAY_SECONDS = 3
LLM_REQUEST_TIMEOUT = 60  # seconds


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------
def _resolve_provider(preferred: str = "auto") -> str:
    """
    Resolve which provider to call.

    preferred:
        "auto"   — pick based on USE_OPENAI / USE_GROQ env flags
        "openai" — force OpenAI
        "groq"   — force Groq
    """
    if preferred == "openai":
        return "openai"
    if preferred == "groq":
        return "groq"

    # auto: prefer OpenAI, fall back to Groq
    if getattr(settings, "USE_OPENAI", False):
        return "openai"
    if getattr(settings, "USE_GROQ", False):
        return "groq"

    # Default: whichever has a key configured
    if getattr(settings, "OPENAI_API_KEY", ""):
        return "openai"
    if getattr(settings, "GROQ_API_KEY", ""):
        return "groq"

    # Nothing configured — callers will get a friendly failure response
    return "openai"


def _provider_config(provider: str) -> Dict[str, str]:
    """Return {api_key, base_url, model} for the given provider."""
    if provider == "groq":
        return {
            "api_key": settings.GROQ_API_KEY or "",
            "base_url": settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1",
            "model": settings.GROQ_MODEL or "llama-3.1-8b-instant",
        }
    # default: openai
    return {
        "api_key": settings.OPENAI_API_KEY or "",
        "base_url": settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
        "model": settings.OPENAI_MODEL or "gpt-4o",
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class LLMService:
    """
    Cloud LLM service used for report generation.

    generate_* methods default to the "reports" provider (OpenAI when
    USE_OPENAI=true). The optional `provider` argument on _call_llm lets
    callers force Groq — useful for planned chatbot features.
    """

    def __init__(self):
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS

    # ------------------------------------------------------------------
    # Core call
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        *,
        provider: str = "auto",
        max_tokens_override: Optional[int] = None,
        fallback_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call an OpenAI-compatible /chat/completions endpoint with retries."""
        resolved = _resolve_provider(provider)
        cfg = _provider_config(resolved)

        if not cfg["api_key"]:
            logger.error(
                "LLM call skipped: no API key configured for provider '%s'", resolved
            )
            return self._build_failure_response(
                error=f"No API key configured for provider '{resolved}'",
                fallback_text=fallback_text,
            )

        max_tokens = (
            max_tokens_override if max_tokens_override is not None else self.max_tokens
        )
        url = f"{cfg['base_url'].rstrip('/')}/chat/completions"

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }

        last_error: Optional[str] = None

        for attempt in range(1, LLM_MAX_RETRIES + 2):  # 1, 2, 3
            try:
                logger.info(
                    "Calling %s /chat/completions (attempt %d/%d) model=%s",
                    resolved,
                    attempt,
                    LLM_MAX_RETRIES + 1,
                    cfg["model"],
                )
                start_time = datetime.now()

                response = requests.post(
                    url, json=payload, headers=headers, timeout=LLM_REQUEST_TIMEOUT
                )
                response.raise_for_status()

                duration = (datetime.now() - start_time).total_seconds()
                data = response.json()

                choice = (data.get("choices") or [{}])[0]
                content = (choice.get("message") or {}).get("content", "")
                usage = data.get("usage") or {}

                logger.info(
                    "%s response OK in %.2fs (tokens in=%s out=%s)",
                    resolved,
                    duration,
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                )

                return {
                    "success": True,
                    "text": content,
                    "model": data.get("model", cfg["model"]),
                    "provider": resolved,
                    "duration": duration,
                    "tokens": usage.get("completion_tokens", 0),
                }

            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {LLM_REQUEST_TIMEOUT}s"
                logger.warning("%s attempt %d timed out", resolved, attempt)
            except requests.exceptions.HTTPError as e:
                body = ""
                try:
                    body = e.response.text[:500] if e.response is not None else ""
                except Exception:
                    pass
                last_error = f"HTTP {e.response.status_code if e.response is not None else '?'}: {body}"
                logger.warning("%s attempt %d HTTP error: %s", resolved, attempt, last_error)
                # Stop retrying on auth or client errors — retry won't help
                if e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.warning("%s attempt %d connection error", resolved, attempt)
            except Exception as e:
                last_error = str(e)
                logger.warning("%s attempt %d unexpected error: %s", resolved, attempt, e)

            if attempt <= LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_DELAY_SECONDS)

        logger.error(
            "LLM call failed after %d attempts. Provider=%s. Last error: %s",
            LLM_MAX_RETRIES + 1,
            resolved,
            last_error,
        )
        return self._build_failure_response(
            error=last_error, fallback_text=fallback_text
        )

    def _build_failure_response(
        self,
        error: Optional[str] = None,
        fallback_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a uniform failure envelope so callers don't crash."""
        return {
            "success": False,
            "error": error or "Unknown error",
            "text": fallback_text or "",
        }

    # ------------------------------------------------------------------
    # Public generation methods — each defaults to the auto provider
    # (i.e. OpenAI when USE_OPENAI=true)
    # ------------------------------------------------------------------
    def generate_profile_section(
        self, chatbot_data: Dict[str, Any], provider: str = "auto"
    ) -> Dict[str, Any]:
        """Generate the Profile section of the psychological report."""
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

        return self._call_llm(
            prompt,
            system_prompt,
            provider=provider,
            max_tokens_override=800,
            fallback_text=fallback,
        )

    def generate_impact_section(
        self,
        chatbot_data: Dict[str, Any],
        cognitive_profile: Optional[Dict[str, Any]] = None,
        provider: str = "auto",
    ) -> Dict[str, Any]:
        """Generate the Impact section of the report."""
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

        return self._call_llm(
            prompt,
            system_prompt,
            provider=provider,
            max_tokens_override=1000,
            fallback_text=fallback,
        )

    def generate_recommendations_section(
        self,
        chatbot_data: Dict[str, Any],
        cognitive_profile: Optional[Dict[str, Any]] = None,
        provider: str = "auto",
    ) -> Dict[str, Any]:
        """Generate the Recommendations section of the report."""
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

        return self._call_llm(
            prompt,
            system_prompt,
            provider=provider,
            max_tokens_override=1200,
            fallback_text=fallback,
        )

    def parse_ocr_text(
        self, ocr_text: str, provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extract structured IQ-test scores from OCR'd PDF text. The LLM is
        instructed to return pure JSON, which we then json.loads.
        """
        system_prompt = (
            "You are a data extraction specialist. "
            "Extract IQ test scores from OCR text and return valid JSON only."
        )

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
    "Visual Spatial": 63
  }}
}}

If you cannot extract certain information, use null. Return ONLY the JSON, no other text.
"""

        result = self._call_llm(prompt, system_prompt, provider=provider)

        if result.get("success"):
            try:
                parsed_data = json.loads(result["text"])
                return {
                    "success": True,
                    "parsed_scores": parsed_data,
                    "confidence": 0.85,
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from LLM response")
                return {
                    "success": False,
                    "error": "Invalid JSON response from LLM",
                    "parsed_scores": None,
                }
        return result

    def check_health(self) -> bool:
        """Return True if at least one provider has an API key configured."""
        if getattr(settings, "OPENAI_API_KEY", ""):
            return True
        if getattr(settings, "GROQ_API_KEY", ""):
            return True
        return False


# Backwards-compatibility alias: callers still import `LocalLLMService` / `llm_service`
LocalLLMService = LLMService
llm_service = LLMService()
