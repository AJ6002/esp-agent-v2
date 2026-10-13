"""AI Client: OpenAI-compatible interface adapter layer for Qwen 2.5 on Server 134."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("agent.llm")


class LLMClient:
    """Unified LLM call entrypoint. Returns Mock result when AI unavailable."""

    def __init__(self) -> None:
        self.enabled = settings.ai_actually_enabled
        self.model = settings.LLM_MODEL or "Qwen2.5-Coder-3B-Instruct-Q4_K_M"
        self.api_base = settings.LLM_API_BASE.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.timeout = settings.LLM_TIMEOUT

    @property
    def is_mock(self) -> bool:
        return not self.enabled

    def chat(
        self,
        messages: list[dict[str, Any]],
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Returns {'content': str, 'is_mock': bool, 'model': str, 'error': str|None}."""
        if not self.enabled:
            return {
                "content": "",
                "is_mock": True,
                "model": "mock",
                "error": None,
            }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        try:
            start = time.time()
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.api_base}/chat/completions", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
            content = data["choices"][0]["message"]["content"]
            latency = int((time.time() - start) * 1000)
            return {
                "content": content,
                "is_mock": False,
                "model": self.model,
                "error": None,
                "latency_ms": latency,
            }
        except Exception as e:  # Fallback degradation
            logger.warning(f"LLM request error ({self.api_base}): {e}")
            return {
                "content": "",
                "is_mock": True,
                "model": self.model,
                "error": str(e),
            }

    def parse_json(self, content: str) -> dict[str, Any] | None:
        """Safely parse JSON returned by model."""
        if not content:
            return None
        try:
            return json.loads(content)
        except Exception:
            # Attempt to extract JSON within markdown code blocks or text
            import re
            m = re.search(r"\{[\s\S]*\}", content)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    return None
            return None


llm_client = LLMClient()
