"""Module 4 joining, banding, and deterministic insight tests."""

from app.context_data import make_synthetic_context_data
from app.hotspots import DevelopmentDemandInsight
from app.insights import build_development_priority_insights
from app.priority import PriorityScoreConfig


def demand(city, category, score):
    return DevelopmentDemandInsight(
        city=city, state=None, category=category, request_count=3,
        average_severity=3.0, high_severity_count=1, demand_score=score,
        hotspot_status="MODERATE", reason="Test fixture.",
    )


def context(city, state, category, infra=50, capacity=50, pressure=50):
    return {
        "city": city, "state": state, "category": category,
        "infrastructure_condition": infra, "service_capacity": capacity,
        "population_pressure": pressure,
    }


def test_combines_demand_and_context_into_structured_insight():
    result = build_development_priority_insights(
        [demand("Bengaluru", "Roads", 89.5)],
        [context("Bengaluru", "Karnataka", "Roads", 42, 55, 78)],
    )[0]
    assert result.citizen_demand_score == 89.5
    assert result.context_gap_score == 58.5
    assert result.development_priority_score == 77.1
    assert result.priority_band == "HIGH"
    assert "prototype indicates high" in result.explanation


def test_priority_bands_are_configurable():
    rows = [demand("Mysuru", "Roads", 20), demand("Kochi", "Roads", 50), demand("Guntur", "Roads", 90)]
    contexts = [
        context("Mysuru", "Karnataka", "Roads"),
        context("Kochi", "Kerala", "Roads"),
        context("Guntur", "Andhra Pradesh", "Roads"),
    ]
    results = build_development_priority_insights(rows, contexts)
    by_city = {row.city: row for row in results}
    assert by_city["Mysuru"].priority_band == "LOW"
    assert by_city["Kochi"].priority_band == "MODERATE"
    assert by_city["Guntur"].priority_band == "HIGH"
    custom = PriorityScoreConfig(citizen_demand_weight=1, context_gap_weight=0, moderate_threshold=25, high_threshold=75)
    custom_result = build_development_priority_insights(rows, contexts, priority_config=custom)
    assert {row.city: row.priority_band for row in custom_result}["Mysuru"] == "LOW"


def test_missing_context_is_marked_unavailable_without_fabricated_score():
    result = build_development_priority_insights([demand("Mysuru", "Roads", 80)], [])[0]
    assert result.development_priority_score is None
    assert result.context_gap_score is None
    assert result.priority_band == "UNAVAILABLE"
    assert "unavailable" in result.explanation


def test_partial_context_produces_score_from_available_values_only():
    result = build_development_priority_insights(
        [demand("Mysuru", "Roads", 60)],
        [context("Mysuru", "Karnataka", "Roads", infra=50, capacity=None, pressure=None)],
    )[0]
    assert result.service_capacity is None
    assert result.population_pressure is None
    assert result.context_gap_score == 50
    assert result.development_priority_score == 56


def test_empty_input_returns_no_insights():
    assert build_development_priority_insights([], make_synthetic_context_data()) == []


def test_multiple_cities_and_categories_join_separately():
    demands = [demand("Bengaluru", "Roads", 75), demand("Kochi", "Water Supply", 55)]
    contexts = [
        context("Bengaluru", "Karnataka", "Roads", 20, 30, 80),
        context("Kochi", "Kerala", "Water Supply", 80, 90, 20),
    ]
    results = build_development_priority_insights(demands, contexts)
    assert {(item.city, item.category) for item in results} == {
        ("Bengaluru", "Roads"), ("Kochi", "Water Supply")
    }


def test_duplicate_context_is_rejected_as_ambiguous():
    rows = [context("Mysuru", "Karnataka", "Roads"), context("Mysuru", "Karnataka", "Roads")]
    import pytest

    with pytest.raises(ValueError, match="Duplicate contextual indicators"):
        build_development_priority_insights([demand("Mysuru", "Roads", 50)], rows)


def test_synthetic_insights_are_deterministic_and_scores_are_bounded():
    requests = make_synthetic_context_data()
    demands = [demand(row.city, row.category, 72.5) for row in requests]
    first = build_development_priority_insights(demands, requests)
    second = build_development_priority_insights(demands, requests)
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert all(item.development_priority_score is not None and 0 <= item.development_priority_score <= 100 for item in first)
    assert len({(item.city, item.category) for item in first}) == 135
