"""Deterministic Module 3 cleaning, aggregation, and scoring tests."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from app.analytics import DemandScoreConfig, aggregate_requests, calculate_demand_scores, clean_requests
from app.analysis import analyze_requests
from app.synthetic_data import make_synthetic_requests


def request(**overrides):
    item = {
        "original_text": "A resident reports a local issue.", "language": "English",
        "state": "Karnataka", "district_or_city": "Mysuru", "category": "Water Supply",
        "severity": 3, "confidence": 0.8,
    }
    item.update(overrides)
    return item


def test_cleaning_normalizes_city_category_and_aliases():
    clean = clean_requests([request(district_or_city="  MYSORE ", category="water")])
    assert clean.loc[0, "district_or_city"] == "Mysuru"
    assert clean.loc[0, "category"] == "Water Supply"


def test_missing_severity_remains_missing():
    clean = clean_requests([request(severity=None), request(severity=8), request(severity="bad")])
    assert clean["severity"].isna().all()


def test_missing_and_out_of_scope_locations_are_not_invented():
    clean = clean_requests([
        request(state=None, district_or_city=None),
        request(state="Tamil Nadu", district_or_city="Chennai"),
    ])
    assert clean.loc[0, "state"] is None and clean.loc[0, "district_or_city"] is None
    assert clean.loc[1, "state"] is None and clean.loc[1, "district_or_city"] is None


def test_city_state_mismatch_excludes_city_without_rewriting_state():
    clean = clean_requests([request(state="Kerala", district_or_city="Mysuru")])
    assert clean.loc[0, "district_or_city"] is None
    assert clean.loc[0, "state"] == "Kerala"


def test_completely_invalid_record_is_removed_but_partial_record_survives():
    clean = clean_requests([None, "bad", {}, request(original_text=None)])
    assert len(clean) == 1


def test_aggregation_by_city_state_category_and_city_category():
    records = [
        request(original_text="A", severity=2, language="Kannada"),
        request(original_text="B", severity=4, language="English"),
        request(original_text="C", state="Kerala", district_or_city="Kochi", category="Roads", severity=5),
    ]
    groups = aggregate_requests(records, as_of=datetime(2026, 1, 1, tzinfo=timezone.utc))
    city_water = groups["by_city_category"].query("district_or_city == 'Mysuru' and category == 'Water Supply'").iloc[0]
    assert city_water["request_count"] == 2
    assert city_water["average_severity"] == 3
    assert city_water["high_severity_count"] == 1
    assert city_water["language_distribution"] == {"Kannada": 1, "English": 1}
    assert set(groups["by_state"]["state"]) == {"Karnataka", "Kerala"}
    assert set(groups["by_category"]["category"]) == {"Water Supply", "Roads"}


def test_recent_count_only_when_timestamps_exist():
    now = datetime(2026, 9, 25, tzinfo=timezone.utc)
    with_dates = aggregate_requests([
        request(timestamp="2026-09-20T00:00:00Z"),
        request(timestamp="2026-08-01T00:00:00Z"),
    ], as_of=now)["by_city_category"]
    assert with_dates.loc[0, "recent_request_count"] == 1
    without_dates = aggregate_requests([request()])["by_city_category"]
    assert "recent_request_count" not in without_dates.columns


def test_demand_score_formula_without_recency():
    rows = pd.DataFrame([
        {"request_count": 2, "average_severity": 5.0},
        {"request_count": 4, "average_severity": 2.5},
    ])
    scored = calculate_demand_scores(rows)
    assert scored.loc[0, "request_frequency_score"] == 50
    assert scored.loc[0, "severity_score"] == 100
    assert scored.loc[0, "demand_score"] == pytest.approx((50 * 0.50 + 100 * 0.35) / 0.85)


def test_recency_score_is_added_and_weights_renormalize_for_partial_values():
    rows = pd.DataFrame([
        {"request_count": 4, "average_severity": 4.0, "recent_request_count": 2, "timestamp_count": 4},
        {"request_count": 2, "average_severity": None, "recent_request_count": 1, "timestamp_count": 2},
    ])
    scored = calculate_demand_scores(rows)
    assert scored.loc[0, "recency_score"] == 100
    assert scored.loc[0, "demand_score"] == pytest.approx(80 * 0.35 + 100 * 0.50 + 100 * 0.15)
    assert pd.notna(scored.loc[1, "demand_score"])


def test_invalid_config_weights_rejected():
    with pytest.raises(ValueError, match="sum to 1.0"):
        DemandScoreConfig(frequency_weight=0.6, severity_weight=0.3, recency_weight=0.2)


def test_empty_dataset_returns_empty_groups_and_insights():
    result = analyze_requests([])
    assert result.cleaned_request_count == 0
    assert result.insights == []
    assert result.aggregations["by_city_category"].empty


def test_single_request_and_multiple_city_category_values():
    single = analyze_requests([request()])
    assert len(single.insights) == 1 and single.insights[0].request_count == 1
    multiple = analyze_requests([
        request(), request(state="Karnataka", district_or_city="Bengaluru", category="Roads"),
    ])
    assert {(item.city, item.category) for item in multiple.insights} == {
        ("Mysuru", "Water Supply"), ("Bengaluru", "Roads")
    }


def test_synthetic_dataset_covers_supported_prototype_scope_without_pii():
    records = make_synthetic_requests()
    cleaned = clean_requests(records)
    assert len(cleaned) > 100
    assert cleaned["district_or_city"].nunique() == 15
    assert set(cleaned["category"].dropna().unique()) >= {
        "Water Supply", "Roads", "Public Transportation", "Healthcare", "Education",
        "Sanitation", "Electricity", "Waste Management", "Public Safety",
    }
    assert all("phone" not in text.casefold() for text in cleaned["original_text"])


def test_analysis_is_deterministic_for_same_input_and_reference_time():
    data = make_synthetic_requests()
    reference = datetime(2026, 9, 25, 12)
    one = analyze_requests(data, as_of=reference).to_dict()
    two = analyze_requests(data, as_of=reference).to_dict()
    assert one == two
