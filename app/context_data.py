"""Validated synthetic infrastructure/context indicators for the prototype."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .analytics import CATEGORY_ALIASES, CITY_STATES, SUPPORTED_CITIES
from .synthetic_data import DEMO_CATEGORIES

SYNTHETIC_CONTEXT_LABEL = "SYNTHETIC CONTEXT DATA — NOT REAL INFRASTRUCTURE MEASUREMENTS"


class ContextIndicator(BaseModel):
    """Context values normalized on a 0-100 scale; fields may be unavailable."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    city: str
    state: str
    category: str
    infrastructure_condition: float | None = Field(default=None, ge=0, le=100)
    service_capacity: float | None = Field(default=None, ge=0, le=100)
    population_pressure: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="before")
    @classmethod
    def normalize_dimensions(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        normalized = dict(value)
        city = normalized.get("city")
        if isinstance(city, str):
            normalized["city"] = SUPPORTED_CITIES.get(city.strip().casefold(), city.strip())
        category = normalized.get("category")
        if isinstance(category, str):
            key = category.strip().casefold()
            normalized["category"] = CATEGORY_ALIASES.get(key, category.strip())
        state = normalized.get("state")
        if isinstance(state, str):
            normalized["state"] = state.strip().title() if state.strip().casefold() != "andhra pradesh" else "Andhra Pradesh"
        return normalized

    @model_validator(mode="after")
    def validate_prototype_dimensions(self) -> "ContextIndicator":
        if self.city not in CITY_STATES:
            raise ValueError(f"Unsupported prototype city: {self.city}")
        if CITY_STATES[self.city] != self.state:
            raise ValueError(f"{self.city} must use its supported state, {CITY_STATES[self.city]}.")
        if self.category not in DEMO_CATEGORIES:
            raise ValueError(f"Unsupported prototype category: {self.category}")
        return self


def make_synthetic_context_data() -> list[ContextIndicator]:
    """Build deterministic, anonymous context values for every demo city/category."""
    records: list[ContextIndicator] = []
    for city_index, (city, state) in enumerate(CITY_STATES.items()):
        for category_index, category in enumerate(DEMO_CATEGORIES):
            records.append(ContextIndicator(
                city=city,
                state=state,
                category=category,
                infrastructure_condition=float(25 + (city_index * 17 + category_index * 13) % 71),
                service_capacity=float(20 + (city_index * 23 + category_index * 7) % 76),
                population_pressure=float(15 + (city_index * 11 + category_index * 19) % 81),
            ))
    return records


def validate_context_data(
    records: Iterable[ContextIndicator | Mapping[str, Any]],
) -> list[ContextIndicator]:
    """Validate mappings or already-validated context rows."""
    return [row if isinstance(row, ContextIndicator) else ContextIndicator.model_validate(row) for row in records]
