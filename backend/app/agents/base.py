"""
Base Agent - Common LLM integration with robust error handling
All agents inherit from this for Ollama and Groq communication.
"""

import asyncio
import json
import logging
import re
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base agent with LLM integration (OpenAI, Groq, or Ollama) and retry logic."""

    def __init__(self, name: str, timeout: float = 15.0, max_tokens: int = 300):
        self.name = name
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.groq_model = settings.GROQ_MODEL
        self.timeout = timeout
        self.max_tokens = max_tokens

    async def call_llm(
        self,
        prompt: str,
        format_json: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Call LLM (OpenAI, Groq, or Ollama) with error handling. Returns raw text or None on failure."""
        if settings.USE_OPENAI:
            return await self._call_openai(prompt, format_json, max_tokens, temperature)
        if settings.USE_GROQ:
            return await self._call_groq(prompt, format_json, max_tokens, temperature)
        return await self._call_ollama(prompt, format_json, max_tokens, temperature)

    async def _call_openai(
        self,
        prompt: str,
        format_json: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Call OpenAI API. Returns raw text or None on failure."""
        tokens = max_tokens or self.max_tokens

        messages = []
        if format_json:
            messages.append({"role": "system", "content": "You must respond with valid JSON."})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "max_tokens": tokens,
            "temperature": temperature,
        }
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{settings.OPENAI_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        finish_reason = data["choices"][0].get("finish_reason", "unknown")
                        content = data["choices"][0]["message"]["content"].strip()
                        if finish_reason == "length":
                            logger.warning(
                                f"[{self.name}] OpenAI response truncated (finish_reason=length, "
                                f"max_tokens={tokens}). Response length: {len(content)} chars"
                            )
                        return content

                    if resp.status_code == 429:
                        wait_seconds = 5.0 * (attempt + 1)
                        logger.info(
                            f"[{self.name}] OpenAI rate limited (attempt {attempt + 1}/{max_retries}), "
                            f"waiting {wait_seconds:.1f}s..."
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    logger.warning(f"[{self.name}] OpenAI returned {resp.status_code}: {resp.text}")
                    return None

            except httpx.TimeoutException:
                logger.warning(f"[{self.name}] OpenAI timeout after {self.timeout}s (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3.0)
                    continue
            except Exception as e:
                logger.warning(f"[{self.name}] OpenAI LLM call failed: {e}")
                return None

        logger.warning(f"[{self.name}] OpenAI exhausted all {max_retries} retries")
        return None

    async def _call_groq(
        self,
        prompt: str,
        format_json: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Call Groq API with automatic retry on rate limits. Returns raw text or None."""
        tokens = max_tokens or self.max_tokens

        messages = []
        if format_json:
            messages.append({"role": "system", "content": "You must respond with valid JSON."})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.groq_model,
            "messages": messages,
            "max_tokens": tokens,
            "temperature": temperature,
        }
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        max_retries = 4
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{settings.GROQ_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"].strip()

                    if resp.status_code == 429:
                        # Parse retry-after from response
                        wait_seconds = 15.0  # default
                        try:
                            body = resp.json()
                            msg = body.get("error", {}).get("message", "")
                            match = re.search(r"try again in (\d+\.?\d*)s", msg, re.IGNORECASE)
                            if match:
                                wait_seconds = float(match.group(1)) + 1.0
                        except Exception:
                            pass
                        wait_seconds = min(wait_seconds, 60.0)
                        logger.info(
                            f"[{self.name}] Groq rate limited (attempt {attempt + 1}/{max_retries}), "
                            f"waiting {wait_seconds:.1f}s..."
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    logger.warning(f"[{self.name}] Groq returned {resp.status_code}: {resp.text}")
                    return None

            except httpx.TimeoutException:
                logger.warning(f"[{self.name}] Groq timeout after {self.timeout}s (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5.0)
                    continue
            except Exception as e:
                logger.warning(f"[{self.name}] Groq LLM call failed: {e}")
                return None

        logger.warning(f"[{self.name}] Groq exhausted all {max_retries} retries")
        return None

    async def _call_ollama(
        self,
        prompt: str,
        format_json: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Call Ollama API. Returns raw text or None on failure."""
        tokens = max_tokens or self.max_tokens

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": tokens,
                "temperature": temperature,
            },
        }
        if format_json:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
                logger.warning(f"[{self.name}] Ollama returned {resp.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"[{self.name}] Ollama timeout after {self.timeout}s")
        except Exception as e:
            logger.warning(f"[{self.name}] LLM call failed: {e}")

        return None

    async def call_llm_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[dict]:
        """Call Ollama expecting JSON response. Returns parsed dict or None."""
        raw = await self.call_llm(prompt, format_json=True, max_tokens=max_tokens, temperature=temperature)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning(f"[{self.name}] Failed to parse JSON from LLM response. First 500 chars: {raw[:500]}")
            return None
