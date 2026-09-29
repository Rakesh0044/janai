"""Gemini explanation layer for already-calculated Module 4 insights.

This module validates inputs and explains them. It never computes or changes
the deterministic scores supplied by Module 4.
"""

from __future__ import annotations

import json
import logging
import math
import re
from typing import Any, Literal, Mapping

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .config import settings

logger = logging.getLogger(__name__)

SYNTHETIC_DATA_NOTE = (
    "This is a prototype insight based on synthetic/demo data and does not represent real government infrastructure measurements."
)
GENERAL_DATA_NOTE = (
    "This explanation reflects only the supplied inputs and does not independently verify the underlying measurements."
)

SYSTEM_PROMPT = """You are the explanation layer of JanDrishti AI.

You receive structured numerical results that have already been calculated by a deterministic Python analytics pipeline. Your job is only to explain those results clearly and concisely for a government/development dashboard.

You MUST preserve every supplied numerical value exactly. Refer to numbers using the same numeric values and do not spell them out as words.
You MUST NOT calculate, change, reinterpret, rank, or invent numerical values. In particular, do not calculate or modify any score.
You MUST NOT introduce facts that are not present in the input. Describe indicator values neutrally; a low score is not proof of actual real-world conditions.
Mention all supplied numeric indicators in the explanation or key_factors, including the already-calculated priority score. Do not use causal claims such as "driven by" or claim a service fails to meet requirements. State the indicator names and supplied values neutrally, then state the Module 4 band and score as calculated outputs.
You MUST NOT claim that synthetic prototype data represents real government infrastructure conditions. If is_synthetic is true, use the exact supplied synthetic data note.
Do not make political recommendations or claims about political actors. Do not recommend funding, policy, or government action.
Use neutral development-intelligence language such as 'the prototype indicates' and 'the supplied dataset shows'.

Return only JSON matching the requested schema. Copy city, state, category, priority_band, and development_priority_score exactly from the input. Key factors must be supported by the supplied input. Confidence describes confidence in explaining the completeness/clarity of the input; it is not confidence that infrastructure measurements are true."""


class ExplanationInput(BaseModel):
    """Validated Module 4 result used as the source of numerical truth."""

    # Module 4 insights also include an explanation field; ignore that existing
    # descriptive field while selecting the numeric/source fields below.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    city: str = Field(min_length=1)
    state: str = Field(min_length=1)
    category: str = Field(min_length=1)
    citizen_demand_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    infrastructure_condition: float | None = Field(..., ge=0, le=100, allow_inf_nan=False)
    service_capacity: float | None = Field(..., ge=0, le=100, allow_inf_nan=False)
    population_pressure: float | None = Field(..., ge=0, le=100, allow_inf_nan=False)
    context_gap_score: float | None = Field(..., ge=0, le=100, allow_inf_nan=False)
    development_priority_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    priority_band: Literal["LOW", "MODERATE", "HIGH"]

    @field_validator("city", "state", "category")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class ExplanationRequest(BaseModel):
    """Input context flag kept separate from Module 4's scoring structure."""

    insight: ExplanationInput
    is_synthetic: bool


class AIExplanation(BaseModel):
    """Human-readable explanation with Module 4 protected fields echoed back."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    city: str = Field(min_length=1)
    state: str = Field(min_length=1)
    category: str = Field(min_length=1)
    priority_band: Literal["LOW", "MODERATE", "HIGH"]
    development_priority_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    explanation: str = Field(min_length=1)
    key_factors: list[str] = Field(min_length=1)
    data_note: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)


class ExplanationError(RuntimeError):
    """Base class for explanation generation errors."""


class ExplanationConfigurationError(ExplanationError):
    """Raised if the Gemini API key is not configured."""


class ExplanationGenerationError(ExplanationError):
    """Raised if Gemini cannot generate a usable explanation."""


class ExplanationValidationError(ExplanationError):
    """Raised if Gemini returns invalid content or alters protected data."""


_NUMBER_PATTERN = re.compile(r"(?<!\w)[+-]?\d+(?:\.\d+)?(?!\w)")


def _source_numbers(source: ExplanationInput) -> set[float]:
    return {
        float(value)
        for value in source.model_dump().values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _validate_response(
    result: AIExplanation,
    source: ExplanationInput,
    *,
    is_synthetic: bool,
) -> AIExplanation:
    """Reject changed protected values, unsupported numbers, and wrong data notes."""
    protected_fields = ("city", "state", "category", "priority_band", "development_priority_score")
    for field_name in protected_fields:
        if getattr(result, field_name) != getattr(source, field_name):
            raise ExplanationValidationError(
                f"Gemini changed protected Module 4 field '{field_name}'. The explanation was rejected."
            )

    expected_note = SYNTHETIC_DATA_NOTE if is_synthetic else GENERAL_DATA_NOTE
    if result.data_note != expected_note:
        raise ExplanationValidationError("Gemini returned an incorrect data note for the supplied dataset type.")

    allowed_numbers = _source_numbers(source)
    generated_text = " ".join([result.explanation, *result.key_factors])
    # The phrase "Module 4" names the upstream module; it is not an analytical value.
    generated_text = re.sub(r"\bModule\s+4\b", "Module Four", generated_text, flags=re.IGNORECASE)
    for token in _NUMBER_PATTERN.findall(generated_text):
        try:
            number = float(token)
        except ValueError:
            continue
        if not any(math.isclose(number, allowed, rel_tol=0, abs_tol=1e-9) for allowed in allowed_numbers):
            raise ExplanationValidationError(
                f"Gemini introduced an unsupported numerical value ({token}). The explanation was rejected."
            )
    mentioned_numbers = {float(token) for token in _NUMBER_PATTERN.findall(generated_text)}
    missing_numbers = {
        value for value in allowed_numbers
        if not any(math.isclose(value, mentioned, rel_tol=0, abs_tol=1e-9) for mentioned in mentioned_numbers)
    }
    if missing_numbers:
        raise ExplanationValidationError(
            "Gemini omitted one or more supplied numeric indicators from the explanation."
        )
    unsupported_claims = re.compile(
        r"\b(?:driven by|residents are suffering|government failed|worst (?:roads|water|sanitation|service)|"
        r"needs? immediate funding|requires? immediate funding|gap in meeting .{0,50} requirements)\b",
        re.IGNORECASE,
    )
    if unsupported_claims.search(generated_text):
        raise ExplanationValidationError(
            "Gemini made an unsupported real-world or causal claim. The explanation was rejected."
        )
    return result


def explain_development_priority(
    insight: Mapping[str, Any] | ExplanationInput | BaseModel,
    *,
    is_synthetic: bool,
    client: Any = None,
) -> AIExplanation:
    """Explain one Module 4 insight without changing its numerical result.

    Args:
        insight: A mapping or validated Module 4 insight.
        is_synthetic: Explicitly identifies synthetic/demo inputs.
        client: Optional SDK-compatible client, primarily for offline tests.

    Raises:
        ValidationError: The supplied Module 4 input is missing/invalid.
        ExplanationError: Configuration, API, response, or integrity failure.
    """
    try:
        if isinstance(insight, ExplanationInput):
            source = insight
        elif isinstance(insight, BaseModel):
            source = ExplanationInput.model_validate(insight.model_dump())
        else:
            source = ExplanationInput.model_validate(insight)
    except ValidationError:
        logger.warning("Module 4 explanation input validation failed.")
        raise

    if not settings.api_key and client is None:
        raise ExplanationConfigurationError("GEMINI_API_KEY is missing. Add it to your .env file.")

    request = ExplanationRequest(insight=source, is_synthetic=is_synthetic)
    user_prompt = (
        "Explain this already-calculated Module 4 result. Preserve the protected fields and every provided number. "
        "Use no numerical values that are absent from this input.\n"
        f"Required data_note: {SYNTHETIC_DATA_NOTE if is_synthetic else GENERAL_DATA_NOTE}\n"
        f"Input JSON:\n{json.dumps(request.model_dump(mode='json'), ensure_ascii=False, indent=2)}"
    )
    sdk_client = client or genai.Client(api_key=settings.api_key)
    try:
        response = sdk_client.models.generate_content(
            model=settings.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=AIExplanation.model_json_schema(),
                temperature=0.1,
                http_options=types.HttpOptions(timeout=settings.timeout_ms),
            ),
        )
    except Exception as exc:
        logger.error("Gemini explanation request failed (%s).", type(exc).__name__)
        raise ExplanationGenerationError(
            "Gemini could not generate an explanation. Check API/model configuration and retry."
        ) from exc

    raw = getattr(response, "text", None)
    if not raw or not raw.strip():
        raise ExplanationGenerationError("Gemini returned an empty explanation. Please retry.")
    try:
        result = AIExplanation.model_validate_json(raw)
    except (ValidationError, ValueError) as exc:
        logger.warning("Gemini explanation response validation failed (%s).", type(exc).__name__)
        raise ExplanationValidationError("Gemini returned malformed or schema-invalid explanation JSON.") from exc
    return _validate_response(result, source, is_synthetic=is_synthetic)
