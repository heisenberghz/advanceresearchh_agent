"""OpenRouter API client for LLM generation with structured outputs and error handling."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError
from app.config import Settings, get_settings

logger = logging.getLogger("researchops.openrouter")

T = TypeVar("T", bound=BaseModel)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Base exception for OpenRouter API failures."""


class OpenRouterClient:
    """Client for executing LLM requests through OpenRouter gateway."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        research_model: Optional[str] = None,
        writer_model: Optional[str] = None,
        timeout_seconds: float = 60.0,
        settings: Optional[Settings] = None,
    ):
        cfg = settings or get_settings()
        self.api_key = api_key or cfg.openrouter_api_key
        self.research_model = research_model or cfg.research_model
        self.writer_model = writer_model or cfg.writer_model
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    @property
    def is_configured(self) -> bool:
        """Check if OpenRouter API key is available."""
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with secure authentication."""
        if not self.is_configured:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured. "
                "Please configure it in backend/.env before calling the LLM."
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/christ-hackathon-pro/researchops",
            "X-Title": "ResearchOps",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """Execute a chat completion request through OpenRouter.

        Args:
            messages: List of message objects with 'role' and 'content'.
            model: Model name. Defaults to self.research_model if not specified.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum token limit for output.
            json_mode: If True, requests JSON response formatting.

        Returns:
            The string content returned by the assistant.
        """
        chosen_model = model or self.research_model
        headers = self._get_headers()

        payload: Dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        logger.debug("Dispatching request to OpenRouter model: %s", chosen_model)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                if not choices:
                    raise OpenRouterError("OpenRouter response did not contain any completion choices.")

                message_content = choices[0].get("message", {}).get("content", "")
                return message_content

        except httpx.TimeoutException as exc:
            logger.error("OpenRouter request timed out for model %s: %s", chosen_model, str(exc))
            raise OpenRouterError(f"OpenRouter request timed out after {self.timeout.read}s") from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            error_detail = exc.response.text
            logger.error("OpenRouter returned HTTP %d: %s", status_code, error_detail)
            raise OpenRouterError(f"OpenRouter HTTP error {status_code}: {error_detail}") from exc

        except Exception as exc:
            logger.error("Unexpected error during OpenRouter call: %s", str(exc))
            raise OpenRouterError(f"Failed to communicate with OpenRouter: {exc}") from exc

    async def chat_for_research(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> str:
        """Call LLM using configured fast research model (e.g. DeepSeek)."""
        return await self.chat(
            messages=messages,
            model=self.research_model,
            temperature=temperature,
            json_mode=json_mode,
        )

    async def chat_for_writer(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        """Call LLM using configured synthesis writer model (e.g. Claude 3.5 Sonnet)."""
        return await self.chat(
            messages=messages,
            model=self.writer_model,
            temperature=temperature,
            json_mode=json_mode,
        )

    async def chat_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Request structured output from OpenRouter and parse into a Pydantic model.

        Ensures markdown fences are stripped and validates against response_model schema.
        """
        raw_text = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            json_mode=True,
        )

        cleaned_text = self._clean_json_text(raw_text)

        try:
            parsed_json = json.loads(cleaned_text)
            return response_model.model_validate(parsed_json)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse structured response into %s: %s\nRaw output: %s",
                         response_model.__name__, str(exc), raw_text)
            raise OpenRouterError(
                f"Model response did not conform to {response_model.__name__} schema: {exc}"
            ) from exc

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """Strip markdown code block fences and leading/trailing whitespace."""
        stripped = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        pattern = r"^```(?:json)?\s*(.*?)\s*```$"
        match = re.search(pattern, stripped, re.DOTALL)
        if match:
            return match.group(1).strip()
        return stripped


def get_openrouter_client() -> OpenRouterClient:
    """Dependency provider for OpenRouterClient."""
    return OpenRouterClient()
