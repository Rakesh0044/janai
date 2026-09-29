"""Transparent classification of city/category demand intensity."""

from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .analytics import DEFAULT_SCORE_CONFIG, DemandScoreConfig, calculate_demand_scores

HotspotStatus = Literal["LOW", "MODERATE", "HIGH"]


class DevelopmentDemandInsight(BaseModel):
    """Structured prototype insight; not an objective service-quality judgment."""

    model_config = ConfigDict(extra="forbid")

    city: str
    state: str | None
    category: str
    request_count: int = Field(ge=0)
    average_severity: float | None
    high_severity_count: int = Field(ge=0)
    demand_score: float = Field(ge=0, le=100)
    hotspot_status: HotspotStatus
    reason: str
    recent_request_count: int | None = None


def _classify(score: float, config: DemandScoreConfig) -> HotspotStatus:
    if score >= config.high_threshold:
        return "HIGH"
    if score >= config.moderate_threshold:
        return "MODERATE"
    return "LOW"


def _reason(row: pd.Series) -> str:
    frequency = float(row.get("request_frequency_score", 0) or 0)
    severity = row.get("severity_score")
    severity_value = float(severity) if pd.notna(severity) else None
    if frequency >= 70 and severity_value is not None and severity_value >= 70:
        return "High request frequency combined with elevated reported severity relative to this dataset."
    if frequency >= 70:
        return "High request frequency in citizen reports relative to this dataset."
    if severity_value is not None and severity_value >= 80:
        return "Elevated reported severity among submitted requests relative to this dataset."
    return "Citizen-reported demand intensity relative to this dataset."


def detect_hotspots(
    city_category_metrics: pd.DataFrame,
    *,
    config: DemandScoreConfig = DEFAULT_SCORE_CONFIG,
) -> list[DevelopmentDemandInsight]:
    """Score city/category groups and assign configurable LOW/MODERATE/HIGH bands."""
    scored = calculate_demand_scores(city_category_metrics, config=config)
    if scored.empty:
        return []
    scored = scored.sort_values(
        ["demand_score", "district_or_city", "category"],
        ascending=[False, True, True], kind="mergesort",
    )
    insights: list[DevelopmentDemandInsight] = []
    for _, row in scored.iterrows():
        average_severity = row.get("average_severity")
        insights.append(DevelopmentDemandInsight(
            city=str(row["district_or_city"]),
            state=str(row["state"]) if pd.notna(row.get("state")) else None,
            category=str(row["category"]),
            request_count=int(row["request_count"]),
            average_severity=float(average_severity) if pd.notna(average_severity) else None,
            high_severity_count=int(row["high_severity_count"]),
            demand_score=round(float(row["demand_score"]), 1),
            hotspot_status=_classify(float(row["demand_score"]), config),
            reason=_reason(row),
            recent_request_count=(
                int(row["recent_request_count"]) if "recent_request_count" in row and pd.notna(row["recent_request_count"]) else None
            ),
        ))
    return insights
