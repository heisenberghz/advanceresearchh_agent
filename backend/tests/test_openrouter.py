"""Unit tests for OpenRouter API integration client."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from pydantic import BaseModel

from app.integrations.openrouter import OpenRouterClient, OpenRouterError


class SampleOutput(BaseModel):
    summary: str
    score: int


@pytest.mark.anyio
async def test_unconfigured_openrouter_raises_error():
    """Verify that calling OpenRouter without an API key raises a clear OpenRouterError."""
    with patch("app.integrations.openrouter.get_settings") as mock_settings:
        mock_settings.return_value.openrouter_api_key = ""
        mock_settings.return_value.gemini_api_key = ""
        client = OpenRouterClient(api_key="", gemini_api_key="")
        assert not client.is_configured

        with pytest.raises(OpenRouterError) as exc_info:
            await client.chat(messages=[{"role": "user", "content": "Hello"}])
        assert "OPENROUTER_API_KEY is not configured" in str(exc_info.value)


@pytest.mark.anyio
async def test_chat_for_research_and_writer_models():
    """Verify configurable model routing for research vs writer requests."""
    client = OpenRouterClient(
        api_key="sk-or-test-key",
        research_model="deepseek/deepseek-chat",
        writer_model="anthropic/claude-3.5-sonnet",
    )
    assert client.is_configured

    mock_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": "Sample output"}}]},
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # Test research call
        res1 = await client.chat_for_research([{"role": "user", "content": "Extract facts"}])
        assert res1 == "Sample output"
        assert mock_post.call_args.kwargs["json"]["model"] == "deepseek/deepseek-chat"

        # Test writer call
        res2 = await client.chat_for_writer([{"role": "user", "content": "Write summary"}])
        assert res2 == "Sample output"
        assert mock_post.call_args.kwargs["json"]["model"] == "anthropic/claude-3.5-sonnet"


@pytest.mark.anyio
async def test_chat_structured_with_fences_cleanup():
    """Verify chat_structured strips markdown fences and validates against Pydantic schema."""
    client = OpenRouterClient(api_key="sk-or-test-key")

    raw_llm_json = "```json\n{\"summary\": \"Market leader in CRM\", \"score\": 95}\n```"

    mock_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": raw_llm_json}}]},
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result: SampleOutput = await client.chat_structured(
            messages=[{"role": "user", "content": "Generate evaluation"}],
            response_model=SampleOutput,
        )
        assert isinstance(result, SampleOutput)
        assert result.summary == "Market leader in CRM"
        assert result.score == 95


@pytest.mark.anyio
async def test_openrouter_http_error_handling():
    """Verify HTTP error codes (like 401 or 429) are converted to clean OpenRouterError."""
    client = OpenRouterClient(api_key="sk-or-test-key")

    mock_response = httpx.Response(
        status_code=401,
        text="Invalid API key",
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterError) as exc_info:
            await client.chat(messages=[{"role": "user", "content": "Ping"}])
        assert "OpenRouter HTTP error 401" in str(exc_info.value)


@pytest.mark.anyio
async def test_openrouter_timeout_handling():
    """Verify network timeouts are safely caught and wrapped in OpenRouterError."""
    client = OpenRouterClient(api_key="sk-or-test-key", timeout_seconds=1.0)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(OpenRouterError) as exc_info:
            await client.chat(messages=[{"role": "user", "content": "Heavy query"}])
        assert "timed out" in str(exc_info.value)
