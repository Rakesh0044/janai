"""Combine citizen-demand insights with contextual indicators."""

from typing import Any, Iterable, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from .context_data import ContextIndicator, validate_context_data
from .hotspots import DevelopmentDemandInsight
from .priority import (
    DEFAULT_CONTEXT_GAP_CONFIG,
    DEFAULT_PRIORITY_CONFIG,
    ContextGapConfig,
    PriorityScoreConfig,
    calculate_context_gap,
    combine_demand_and_context,
)

PriorityBand = Literal["LOW", "MODERATE", "HIGH", "UNAVAILABLE"]


class DevelopmentPriorityInsight(BaseModel):
    """Structured prototype priority insight, not a policy or funding decision."""

    model_config = ConfigDict(extra="forbid")

    city: str
    state: str | None
    category: str
    citizen_demand_score: float = Field(ge=0, le=100)
    infrastructure_condition: float | None = Field(ge=0, le=100)
    service_capacity: float | None = Field(ge=0, le=100)
    population_pressure: float | None = Field(ge=0, le=100)
    context_gap_score: float | None = Field(ge=0, le=100)
    development_priority_score: float | None = Field(ge=0, le=100)
    priority_band: PriorityBand
    explanation: str


def _demand_record(value: DevelopmentDemandInsight | Mapping[str, Any]) -> DevelopmentDemandInsight:
    return value if isinstance(value, DevelopmentDemandInsight) else DevelopmentDemandInsight.model_validate(value)


def _priority_band(score: float | None, config: PriorityScoreConfig) -> PriorityBand:
    if score is None:
        return "UNAVAILABLE"
    if score >= config.high_threshold:
        return "HIGH"
    if score >= config.moderate_threshold:
        return "MODERATE"
    return "LOW"


def _explanation(city: str, category: str, score: float | None, band: PriorityBand) -> str:
    if score is None:
        return f"Context indicators are unavailable for {category} in {city}; no combined development-priority score is assigned."
    if band == "HIGH":
        level = "high"
    elif band == "MODERATE":
        level = "moderate"
    else:
        level = "lower"
    return (
        f"The prototype indicates {level} development-demand intensity for {category} in {city} "
        "based on citizen requests and contextual indicators. This is an analytical insight, not a funding decision."
    )


def build_development_priority_insights(
    demand_insights: Iterable[DevelopmentDemandInsight | Mapping[str, Any]],
    context_records: Iterable[ContextIndicator | Mapping[str, Any]],
    *,
    gap_config: ContextGapConfig = DEFAULT_CONTEXT_GAP_CONFIG,
    priority_config: PriorityScoreConfig = DEFAULT_PRIORITY_CONFIG,
) -> list[DevelopmentPriorityInsight]:
    """Join demand results to city/category context and compute priority insights.

    Demand rows without a matching context row are retained with an unavailable
    band and no combined score. Duplicate context keys are rejected as ambiguous.
    """
    contexts = validate_context_data(context_records)
    context_index: dict[tuple[str, str], ContextIndicator] = {}
    for row in contexts:
        key = (row.city, row.category)
        if key in context_index:
            raise ValueError(f"Duplicate contextual indicators for {row.city} / {row.category}.")
        context_index[key] = row

    results: list[DevelopmentPriorityInsight] = []
    for item in demand_insights:
        demand = _demand_record(item)
        context = context_index.get((demand.city, demand.category))
        gap = calculate_context_gap(context, config=gap_config) if context is not None else None
        priority_score = combine_demand_and_context(
            demand.demand_score, gap, config=priority_config
        )
        band = _priority_band(priority_score, priority_config)
        results.append(DevelopmentPriorityInsight(
            city=demand.city,
            state=demand.state or (context.state if context is not None else None),
            category=demand.category,
            citizen_demand_score=demand.demand_score,
            infrastructure_condition=context.infrastructure_condition if context else None,
            service_capacity=context.service_capacity if context else None,
            population_pressure=context.population_pressure if context else None,
            context_gap_score=gap,
            development_priority_score=priority_score,
            priority_band=band,
            explanation=_explanation(demand.city, demand.category, priority_score, band),
        ))
    return sorted(
        results,
        key=lambda row: (
            row.development_priority_score is None,
            -(row.development_priority_score or 0),
            row.city,
            row.category,
        ),
    )
