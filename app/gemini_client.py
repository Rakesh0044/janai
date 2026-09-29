"""Gemini structured-output integration."""

import json
import logging
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .config import Settings, settings
from .prompts import SYSTEM_PROMPT, make_user_prompt
from .schemas import CitizenRequest
from .validators import validate_business_rules, validate_input

logger = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Missing or invalid runtime configuration."""


class GeminiResponseError(RuntimeError):
    """Gemini returned no usable structured content."""


def _is_transient(error: BaseException) -> bool:
    """Retry network timeouts, rate limits, and server-side API errors only."""
    if isinstance(error, (TimeoutError, ConnectionError)):
        return True
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    name = type(error).__name__.lower()
    return status == 429 or (isinstance(status, int) and status >= 500) or "timeout" in name or "servererror" in name


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _generate(client: Any, model: str, prompt: str, timeout_ms: int) -> Any:
    """Call Gemini with JSON schema constrained output."""
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=CitizenRequest.model_json_schema(),
            http_options=types.HttpOptions(timeout=timeout_ms),
        ),
    )


def understand_request(text: str, *, config: Settings = settings, client: Any = None) -> CitizenRequest:
    """Run validation, structured Gemini extraction, and business checks."""
    cleaned = validate_input(text, config.max_input_chars)
    if not config.api_key and client is None:
        raise ConfigurationError("GEMINI_API_KEY is missing. Add it to your .env file.")
    logger.info("Request processing started (%d characters).", len(cleaned))
    sdk_client = client or genai.Client(api_key=config.api_key)
    started = time.monotonic()
    try:
        response = _generate(sdk_client, config.model, make_user_prompt(cleaned), config.timeout_ms)
    except Exception:
        logger.exception("Gemini API request failed.")
        raise
    logger.debug("Gemini request completed in %.2f seconds.", time.monotonic() - started)
    raw = getattr(response, "text", None)
    if not raw:
        logger.error("Gemini returned an empty response.")
        raise GeminiResponseError("Gemini returned an empty response. Please retry the request.")
    try:
        result = CitizenRequest.model_validate_json(raw)
        result = validate_business_rules(result, cleaned)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("Gemini response validation failed.")
        raise GeminiResponseError(f"Gemini returned an invalid request record: {exc}") from exc
    logger.info("Request processed successfully.")
    return result
