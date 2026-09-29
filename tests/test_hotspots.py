"""Hotspot classification and insight serialization tests."""

import pandas as pd

from app.analytics import DemandScoreConfig
from app.hotspots import DevelopmentDemandInsight, detect_hotspots


def test_hotspot_thresholds_and_explanation_are_configurable():
    metrics = pd.DataFrame([
        {"district_or_city": "Mysuru", "state": "Karnataka", "category": "Water Supply", "request_count": 1,
         "average_severity": 2.0, "high_severity_count": 0},
        {"district_or_city": "Kochi", "state": "Kerala", "category": "Roads", "request_count": 2,
         "average_severity": 4.0, "high_severity_count": 1},
        {"district_or_city": "Bengaluru", "state": "Karnataka", "category": "Healthcare", "request_count": 4,
         "average_severity": 5.0, "high_severity_count": 2},
    ])
    config = DemandScoreConfig(frequency_weight=1, severity_weight=0, recency_weight=0)
    insights = detect_hotspots(metrics, config=config)
    assert [item.hotspot_status for item in insights] == ["HIGH", "MODERATE", "LOW"]
    assert "relative to this dataset" in insights[0].reason
    assert isinstance(insights[0], DevelopmentDemandInsight)


def test_empty_hotspot_input():
    assert detect_hotspots(pd.DataFrame()) == []


def test_missing_severity_does_not_break_insight_output():
    metrics = pd.DataFrame([{
        "district_or_city": "Mysuru", "state": "Karnataka", "category": "Water Supply",
        "request_count": 1, "average_severity": float("nan"), "high_severity_count": 0,
    }])
    insight = detect_hotspots(metrics)[0]
    assert insight.average_severity is None
    assert 0 <= insight.demand_score <= 100
