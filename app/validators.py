"""Input checks and post-model business rules."""

from .schemas import CitizenRequest


class RequestInputError(ValueError):
    """Raised when a request is empty or exceeds configured limits."""


def validate_input(text: str, max_chars: int) -> str:
    """Validate request size while preserving the citizen's exact text."""
    if not text.strip():
        raise RequestInputError("Citizen request cannot be empty.")
    if len(text) > max_chars:
        raise RequestInputError(f"Citizen request is too long (maximum {max_chars} characters).")
    return text


def validate_business_rules(result: CitizenRequest, original_text: str) -> CitizenRequest:
    """Enforce invariants that schema validation alone cannot express."""
    if result.original_text != original_text:
        raise ValueError("Gemini response original_text does not match the submitted request.")
    if result.state is None and not result.district_or_city:
        return result
    if result.district_or_city is not None and not result.district_or_city.strip():
        raise ValueError("district_or_city must be null or a non-empty location.")
    if result.duration is not None and not result.duration.strip():
        raise ValueError("duration must be null or a non-empty value.")
    if result.affected_population is not None and not result.affected_population.strip():
        raise ValueError("affected_population must be null or a non-empty value.")
    return result
