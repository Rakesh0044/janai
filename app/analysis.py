"""High-level Module 3 pipeline and serializable result container."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

import pandas as pd

from .analytics import DEFAULT_SCORE_CONFIG, DemandScoreConfig, aggregate_requests
from .hotspots import DevelopmentDemandInsight, detect_hotspots
from .schemas import CitizenRequest
from .synthetic_data import SYNTHETIC_DATA_LABEL


@dataclass
class DemandAnalysis:
    """Aggregations and insights produced from citizen request records."""

    cleaned_request_count: int
    aggregations: dict[str, pd.DataFrame]
    insights: list[DevelopmentDemandInsight]
    dataset_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert pandas and Pydantic results to JSON-ready Python values."""
        groups = {
            name: frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")
            for name, frame in self.aggregations.items() if name != "cleaned_requests"
        }
        result = {
            "dataset_label": self.dataset_label,
            "cleaned_request_count": self.cleaned_request_count,
            "aggregations": groups,
            "development_demand_insights": [item.model_dump(mode="json") for item in self.insights],
        }
        return result


def analyze_requests(
    requests: Iterable[CitizenRequest | Mapping[str, Any] | Any] | pd.DataFrame,
    *,
    config: DemandScoreConfig = DEFAULT_SCORE_CONFIG,
    as_of: datetime | None = None,
    dataset_label: str | None = None,
) -> DemandAnalysis:
    """Clean, aggregate, score, and classify a collection of request records."""
    aggregates = aggregate_requests(requests, as_of=as_of, config=config)
    insights = detect_hotspots(aggregates["by_city_category"], config=config)
    return DemandAnalysis(
        cleaned_request_count=len(aggregates["cleaned_requests"]),
        aggregations=aggregates,
        insights=insights,
        dataset_label=dataset_label,
    )


def analyze_synthetic_demo(*, config: DemandScoreConfig = DEFAULT_SCORE_CONFIG) -> DemandAnalysis:
    """Run the demonstration dataset with a fixed reference time."""
    from .synthetic_data import make_synthetic_requests

    return analyze_requests(
        make_synthetic_requests(),
        config=config,
        as_of=datetime(2026, 9, 25, 12),
        dataset_label=SYNTHETIC_DATA_LABEL,
    )
