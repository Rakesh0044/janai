"""Deterministic cleaning, aggregation, and demand-intensity scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from .schemas import CitizenRequest

CATEGORIES = (
    "Water Supply", "Roads", "Public Transportation", "Healthcare", "Education",
    "Sanitation", "Electricity", "Waste Management", "Public Safety", "Other",
)

SUPPORTED_CITIES: dict[str, str] = {
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
    "mysuru": "Mysuru", "mysore": "Mysuru",
    "mangaluru": "Mangaluru", "mangalore": "Mangaluru",
    "hubballi-dharwad": "Hubballi-Dharwad", "hubli-dharwad": "Hubballi-Dharwad",
    "belagavi": "Belagavi", "belgaum": "Belagavi",
    "visakhapatnam": "Visakhapatnam", "vizag": "Visakhapatnam",
    "vijayawada": "Vijayawada", "guntur": "Guntur", "tirupati": "Tirupati", "kurnool": "Kurnool",
    "thiruvananthapuram": "Thiruvananthapuram", "trivandrum": "Thiruvananthapuram",
    "kochi": "Kochi", "cochin": "Kochi", "kozhikode": "Kozhikode", "calicut": "Kozhikode",
    "thrissur": "Thrissur", "trichur": "Thrissur", "kollam": "Kollam", "quilon": "Kollam",
}
CITY_STATES = {
    "Bengaluru": "Karnataka", "Mysuru": "Karnataka", "Mangaluru": "Karnataka",
    "Hubballi-Dharwad": "Karnataka", "Belagavi": "Karnataka",
    "Visakhapatnam": "Andhra Pradesh", "Vijayawada": "Andhra Pradesh", "Guntur": "Andhra Pradesh",
    "Tirupati": "Andhra Pradesh", "Kurnool": "Andhra Pradesh",
    "Thiruvananthapuram": "Kerala", "Kochi": "Kerala", "Kozhikode": "Kerala",
    "Thrissur": "Kerala", "Kollam": "Kerala",
}
SUPPORTED_STATES = {"karnataka": "Karnataka", "andhra pradesh": "Andhra Pradesh", "kerala": "Kerala"}
CATEGORY_ALIASES = {
    "water": "Water Supply", "water supply": "Water Supply", "drinking water": "Water Supply",
    "road": "Roads", "roads": "Roads", "transport": "Public Transportation",
    "public transport": "Public Transportation", "public transportation": "Public Transportation",
    "health": "Healthcare", "healthcare": "Healthcare", "school": "Education",
    "education": "Education", "sanitation": "Sanitation", "electricity": "Electricity",
    "power": "Electricity", "waste": "Waste Management", "waste management": "Waste Management",
    "safety": "Public Safety", "public safety": "Public Safety", "other": "Other",
}
DATA_COLUMNS = [
    "original_text", "language", "state", "district_or_city", "category", "subcategory",
    "severity", "urgency", "duration", "affected_population", "confidence", "timestamp",
]


@dataclass(frozen=True)
class DemandScoreConfig:
    """Weights and thresholds for the prototype demand-intensity score."""

    frequency_weight: float = 0.50
    severity_weight: float = 0.35
    recency_weight: float = 0.15
    recent_days: int = 30
    moderate_threshold: float = 40.0
    high_threshold: float = 70.0

    def __post_init__(self) -> None:
        weights = (self.frequency_weight, self.severity_weight, self.recency_weight)
        if any(weight < 0 for weight in weights) or not np.isclose(sum(weights), 1.0):
            raise ValueError("Demand score weights must be non-negative and sum to 1.0.")
        if self.recent_days < 1:
            raise ValueError("recent_days must be at least 1.")
        if not (0 <= self.moderate_threshold < self.high_threshold <= 100):
            raise ValueError("Thresholds must satisfy 0 <= moderate < high <= 100.")


DEFAULT_SCORE_CONFIG = DemandScoreConfig()


def _record_dict(record: CitizenRequest | Mapping[str, Any] | Any) -> dict[str, Any] | None:
    """Convert supported record representations to a dictionary."""
    if isinstance(record, CitizenRequest):
        return record.model_dump()
    if isinstance(record, Mapping):
        return dict(record)
    return None


def _normalise_category(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return CATEGORY_ALIASES.get(value.strip().casefold())


def _normalise_state(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return SUPPORTED_STATES.get(value.strip().casefold())


def _normalise_city(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return SUPPORTED_CITIES.get(value.strip().casefold())


def _valid_severity(value: Any) -> int | None:
    """Return valid 1-5 integer severity, otherwise preserve it as missing."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer() or not 1 <= numeric <= 5:
        return None
    return int(numeric)


def clean_requests(
    requests: Iterable[CitizenRequest | Mapping[str, Any] | Any],
) -> pd.DataFrame:
    """Normalize usable records and safely represent absent or invalid fields.

    Known city aliases and category labels are canonicalized. Unsupported or
    unknown locations/categories remain null so they are omitted from affected
    geographic/category groupings rather than guessed.
    """
    rows: list[dict[str, Any]] = []
    for item in requests:
        source = _record_dict(item)
        if source is None:
            continue
        original_text = source.get("original_text")
        category = _normalise_category(source.get("category"))
        city = _normalise_city(source.get("district_or_city"))
        state = _normalise_state(source.get("state"))
        if city and state and CITY_STATES[city] != state:
            city = None

        # Drop only records that carry no useful request, category, or supported location.
        has_text = isinstance(original_text, str) and bool(original_text.strip())
        if not (has_text or category or city or state):
            continue

        confidence = source.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else np.nan
            if not np.isfinite(confidence) or not 0 <= confidence <= 1:
                confidence = np.nan
        except (TypeError, ValueError):
            confidence = np.nan

        rows.append({
            "original_text": original_text if has_text else None,
            "language": source.get("language") if isinstance(source.get("language"), str) else None,
            "state": state,
            "district_or_city": city,
            "category": category,
            "subcategory": source.get("subcategory") if isinstance(source.get("subcategory"), str) else None,
            "severity": _valid_severity(source.get("severity")),
            "urgency": source.get("urgency") if isinstance(source.get("urgency"), str) else None,
            "duration": source.get("duration") if isinstance(source.get("duration"), str) else None,
            "affected_population": source.get("affected_population") if isinstance(source.get("affected_population"), str) else None,
            "confidence": confidence,
            "timestamp": pd.to_datetime(
                source.get("timestamp", source.get("created_at", source.get("submitted_at"))),
                errors="coerce", utc=True,
            ),
        })
    frame = pd.DataFrame(rows, columns=DATA_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    return frame


def _group_metrics(frame: pd.DataFrame, group_columns: list[str], as_of: datetime, recent_days: int) -> pd.DataFrame:
    if frame.empty or not group_columns:
        return pd.DataFrame(columns=group_columns + ["request_count", "average_severity", "high_severity_count", "language_distribution"])
    subset = frame.dropna(subset=group_columns)
    if subset.empty:
        return pd.DataFrame(columns=group_columns + ["request_count", "average_severity", "high_severity_count", "language_distribution"])
    work = subset.copy()
    work["_high_severity"] = work["severity"].ge(4).fillna(False).astype(int)
    if work["timestamp"].notna().any():
        work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", utc=True)
        work["_recent"] = (
            work["timestamp"].notna()
            & (work["timestamp"] >= as_of - timedelta(days=recent_days))
        ).astype(int)
    else:
        work["_recent"] = 0
    metrics = work.groupby(group_columns, as_index=False, dropna=False).agg(
        request_count=("original_text", "size"),
        average_severity=("severity", "mean"),
        high_severity_count=("_high_severity", "sum"),
        _timestamp_count=("timestamp", "count"),
        recent_request_count=("_recent", "sum"),
    )
    languages = work.groupby(group_columns, dropna=False)["language"].agg(
        lambda values: values.dropna().value_counts().to_dict()
    ).reset_index(name="language_distribution")
    metrics = metrics.merge(languages, on=group_columns, how="left")
    if not frame["timestamp"].notna().any():
        metrics = metrics.drop(columns=["recent_request_count", "_timestamp_count"])
    else:
        metrics = metrics.rename(columns={"_timestamp_count": "timestamp_count"})
    metrics["average_severity"] = metrics["average_severity"].round(2)
    return metrics


def aggregate_requests(
    requests: Iterable[CitizenRequest | Mapping[str, Any] | Any] | pd.DataFrame,
    *,
    as_of: datetime | None = None,
    config: DemandScoreConfig = DEFAULT_SCORE_CONFIG,
) -> dict[str, pd.DataFrame]:
    """Return request metrics grouped by city, state, category, and city/category."""
    clean = clean_requests(requests.to_dict(orient="records")) if isinstance(requests, pd.DataFrame) else clean_requests(requests)
    if not clean.empty:
        # A DataFrame may be supplied directly, so normalize its essential dimensions too.
        if "category" not in clean:
            clean["category"] = None
        if "district_or_city" not in clean:
            clean["district_or_city"] = None
        if "state" not in clean:
            clean["state"] = None
        if "severity" not in clean:
            clean["severity"] = np.nan
        if "language" not in clean:
            clean["language"] = None
        if "timestamp" not in clean:
            clean["timestamp"] = pd.NaT
        for column in ("original_text",):
            if column not in clean:
                clean[column] = None
    reference = as_of or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    reference = reference.astimezone(timezone.utc)
    return {
        "cleaned_requests": clean,
        "by_city": _group_metrics(clean, ["district_or_city"], reference, config.recent_days),
        "by_state": _group_metrics(clean, ["state"], reference, config.recent_days),
        "by_category": _group_metrics(clean, ["category"], reference, config.recent_days),
        "by_city_category": _group_metrics(
            clean, ["district_or_city", "state", "category"], reference, config.recent_days
        ),
    }


def calculate_demand_scores(
    city_category: pd.DataFrame,
    *,
    config: DemandScoreConfig = DEFAULT_SCORE_CONFIG,
) -> pd.DataFrame:
    """Combine normalized frequency, severity, and optional recency (0-100)."""
    if city_category.empty:
        result = city_category.copy()
        for name in ("request_frequency_score", "severity_score", "recency_score", "demand_score"):
            result[name] = pd.Series(dtype="float64")
        return result

    result = city_category.copy()
    frequency_max = max(float(result["request_count"].max()), 1.0)
    result["request_frequency_score"] = result["request_count"].astype(float) / frequency_max * 100
    result["severity_score"] = result["average_severity"].astype(float) / 5.0 * 100
    has_recency = "recent_request_count" in result.columns
    if has_recency:
        recent_max = max(float(result["recent_request_count"].max()), 1.0)
        result["recency_score"] = result["recent_request_count"].astype(float) / recent_max * 100
        if "timestamp_count" in result:
            result.loc[result["timestamp_count"].eq(0), "recency_score"] = np.nan
    else:
        result["recency_score"] = np.nan

    components = ["request_frequency_score", "severity_score"]
    weights = [config.frequency_weight, config.severity_weight]
    if has_recency:
        components.append("recency_score")
        weights.append(config.recency_weight)
    matrix = result[components].to_numpy(dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    available = np.isfinite(matrix)
    weighted_total = np.nansum(matrix * weight_array, axis=1)
    active_weight = (available * weight_array).sum(axis=1)
    result["demand_score"] = np.divide(
        weighted_total, active_weight, out=np.zeros_like(weighted_total), where=active_weight > 0
    )
    return result
