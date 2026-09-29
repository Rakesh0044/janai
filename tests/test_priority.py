"""Validation and calculation tests for Module 4 score mathematics."""

import pytest
from pydantic import ValidationError

from app.context_data import ContextIndicator
from app.priority import (
    ContextGapConfig,
    PriorityScoreConfig,
    calculate_context_gap,
    combine_demand_and_context,
)


def test_context_indicator_validates_and_normalizes_input():
    context = ContextIndicator(
        city="mysore", state="karnataka", category="water", infrastructure_condition=42,
        service_capacity=55, population_pressure=78,
    )
    assert context.city == "Mysuru"
    assert context.state == "Karnataka"
    assert context.category == "Water Supply"


@pytest.mark.parametrize("field,value", [
    ("infrastructure_condition", -1), ("service_capacity", 101), ("population_pressure", 101),
])
def test_context_values_outside_zero_to_hundred_rejected(field, value):
    fields = {"city": "Mysuru", "state": "Karnataka", "category": "Roads", field: value}
    with pytest.raises(ValidationError):
        ContextIndicator.model_validate(fields)


def test_context_city_state_and_category_are_in_scope():
    with pytest.raises(ValidationError, match="supported state"):
        ContextIndicator(city="Mysuru", state="Kerala", category="Roads")
    with pytest.raises(ValidationError, match="Unsupported prototype category"):
        ContextIndicator(city="Mysuru", state="Karnataka", category="Agriculture")


def test_missing_context_values_remain_missing():
    context = ContextIndicator(city="Kochi", state="Kerala", category="Roads")
    assert context.infrastructure_condition is None
    assert context.service_capacity is None
    assert context.population_pressure is None
    assert calculate_context_gap(context) is None


def test_context_gap_formula():
    context = ContextIndicator(
        city="Bengaluru", state="Karnataka", category="Roads",
        infrastructure_condition=42, service_capacity=55, population_pressure=78,
    )
    assert calculate_context_gap(context) == pytest.approx(58.5)


def test_context_gap_reweights_only_available_metrics():
    context = ContextIndicator(
        city="Mysuru", state="Karnataka", category="Roads",
        infrastructure_condition=50, population_pressure=100,
    )
    assert calculate_context_gap(context) == pytest.approx(69.2)


def test_context_weights_are_configurable_and_validated():
    custom = ContextGapConfig(infrastructure_weight=0.5, service_capacity_weight=0.25, population_pressure_weight=0.25)
    context = ContextIndicator(
        city="Mysuru", state="Karnataka", category="Roads",
        infrastructure_condition=0, service_capacity=100, population_pressure=0,
    )
    assert calculate_context_gap(context, config=custom) == 50
    with pytest.raises(ValueError, match="sum to 1.0"):
        ContextGapConfig(infrastructure_weight=0.7, service_capacity_weight=0.2, population_pressure_weight=0.2)


def test_demand_context_combination_formula_and_missing_context():
    assert combine_demand_and_context(89.5, 71.4) == 82.3
    assert combine_demand_and_context(89.5, None) is None


@pytest.mark.parametrize("demand,context", [(-1, 50), (101, 50), (50, -1), (50, 101)])
def test_combination_rejects_values_outside_zero_to_hundred(demand, context):
    with pytest.raises(ValueError):
        combine_demand_and_context(demand, context)


def test_score_config_is_validated():
    assert PriorityScoreConfig(citizen_demand_weight=0.7, context_gap_weight=0.3)
    with pytest.raises(ValueError, match="sum to 1.0"):
        PriorityScoreConfig(citizen_demand_weight=0.5, context_gap_weight=0.6)

