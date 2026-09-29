"""Configurable deterministic infrastructure gap and priority scoring."""

from dataclasses import dataclass

import numpy as np

from .context_data import ContextIndicator


@dataclass(frozen=True)
class ContextGapConfig:
    """Relative contributions to the context gap, which range from 0 to 100."""

    infrastructure_weight: float = 0.40
    service_capacity_weight: float = 0.35
    population_pressure_weight: float = 0.25

    def __post_init__(self) -> None:
        weights = (self.infrastructure_weight, self.service_capacity_weight, self.population_pressure_weight)
        if any(weight < 0 for weight in weights) or not np.isclose(sum(weights), 1.0):
            raise ValueError("Context gap weights must be non-negative and sum to 1.0.")


@dataclass(frozen=True)
class PriorityScoreConfig:
    """Weights and thresholds for combining demand and context gap."""

    citizen_demand_weight: float = 0.60
    context_gap_weight: float = 0.40
    moderate_threshold: float = 40.0
    high_threshold: float = 70.0

    def __post_init__(self) -> None:
        weights = (self.citizen_demand_weight, self.context_gap_weight)
        if any(weight < 0 for weight in weights) or not np.isclose(sum(weights), 1.0):
            raise ValueError("Priority score weights must be non-negative and sum to 1.0.")
        if not (0 <= self.moderate_threshold < self.high_threshold <= 100):
            raise ValueError("Thresholds must satisfy 0 <= moderate < high <= 100.")


DEFAULT_CONTEXT_GAP_CONFIG = ContextGapConfig()
DEFAULT_PRIORITY_CONFIG = PriorityScoreConfig()


def calculate_context_gap(
    context: ContextIndicator,
    *,
    config: ContextGapConfig = DEFAULT_CONTEXT_GAP_CONFIG,
) -> float | None:
    """Compute weighted poor-condition/capacity/pressure gap (0-100).

    Poor condition contributes ``100 - infrastructure_condition``; low service
    capacity contributes ``100 - service_capacity``; population pressure is
    used directly. If a metric is missing, the remaining weights are scaled to
    sum to one. No available metrics returns None.
    """
    components = (
        (None if context.infrastructure_condition is None else 100 - context.infrastructure_condition,
         config.infrastructure_weight),
        (None if context.service_capacity is None else 100 - context.service_capacity,
         config.service_capacity_weight),
        (context.population_pressure, config.population_pressure_weight),
    )
    available = [(float(value), weight) for value, weight in components if value is not None and weight > 0]
    total_weight = sum(weight for _, weight in available)
    if total_weight == 0:
        return None
    score = sum(value * weight for value, weight in available) / total_weight
    return round(float(np.clip(score, 0, 100)), 1)


def combine_demand_and_context(
    citizen_demand_score: float,
    context_gap_score: float | None,
    *,
    config: PriorityScoreConfig = DEFAULT_PRIORITY_CONFIG,
) -> float | None:
    """Combine demand and context scores using configurable 0-100 weights."""
    if not np.isfinite(citizen_demand_score) or not 0 <= citizen_demand_score <= 100:
        raise ValueError("citizen_demand_score must be between 0 and 100.")
    if context_gap_score is None:
        return None
    if not np.isfinite(context_gap_score) or not 0 <= context_gap_score <= 100:
        raise ValueError("context_gap_score must be between 0 and 100.")
    score = config.citizen_demand_weight * citizen_demand_score + config.context_gap_weight * context_gap_score
    return round(float(np.clip(score, 0, 100)), 1)
