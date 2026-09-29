"""Offline tests for the Module 5 Gemini explanation layer."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.explanations import (
    SYNTHETIC_DATA_NOTE,
    AIExplanation,
    ExplanationGenerationError,
    ExplanationValidationError,
    explain_development_priority,
)


def module4_input(**overrides):
    result = {
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "category": "Sanitation",
        "citizen_demand_score": 89.5,
        "infrastructure_condition": 50.0,
        "service_capacity": 41.0,
        "population_pressure": 95.0,
        "context_gap_score": 64.4,
        "development_priority_score": 79.5,
        "priority_band": "HIGH",
        "explanation": "The prototype indicates high demand intensity based on supplied inputs.",
    }
    result.update(overrides)
    return result


def valid_output(source=None, **overrides):
    source = source or module4_input()
    result = {
        "city": source["city"],
        "state": source["state"],
        "category": source["category"],
        "priority_band": source["priority_band"],
        "development_priority_score": source["development_priority_score"],
        "explanation": (
            f"{source['category']} has a high development-demand signal in the prototype dataset. "
            f"Citizen demand score is {source['citizen_demand_score']}, infrastructure condition is {source['infrastructure_condition']}, "
            f"context gap score is {source['context_gap_score']}, "
            f"service capacity is {source['service_capacity']}, and population pressure is {source['population_pressure']}. "
            f"The supplied Module 4 priority score is {source['development_priority_score']}."
        ),
        "key_factors": [
            f"Citizen demand score: {source['citizen_demand_score']}.",
            f"Infrastructure condition: {source['infrastructure_condition']}.",
            f"Context gap score: {source['context_gap_score']}.",
            f"Service capacity: {source['service_capacity']} and population pressure: {source['population_pressure']}.",
        ],
        "data_note": SYNTHETIC_DATA_NOTE,
        "confidence": 0.92,
    }
    result.update(overrides)
    return result


def mocked_client(output):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        text=output if isinstance(output, str) else json.dumps(output)
    )
    return client


def test_successful_explanation_generation_and_valid_input():
    source = module4_input()
    client = mocked_client(valid_output(source))
    result = explain_development_priority(source, is_synthetic=True, client=client)
    assert isinstance(result, AIExplanation)
    assert result.city == source["city"]
    assert result.explanation
    client.models.generate_content.assert_called_once()


def test_module4_pydantic_insight_is_accepted():
    from app.insights import DevelopmentPriorityInsight

    source = DevelopmentPriorityInsight.model_validate(module4_input())
    result = explain_development_priority(source, is_synthetic=True, client=mocked_client(valid_output()))
    assert result.development_priority_score == source.development_priority_score


@pytest.mark.parametrize("field", ["city", "state", "category", "development_priority_score"])
def test_missing_required_fields_fail_before_gemini_call(field):
    source = module4_input()
    source.pop(field)
    client = mocked_client(valid_output())
    with pytest.raises(ValidationError):
        explain_development_priority(source, is_synthetic=True, client=client)
    client.models.generate_content.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("citizen_demand_score", -0.1), ("infrastructure_condition", 100.1),
    ("service_capacity", "not a number"), ("context_gap_score", float("nan")),
    ("development_priority_score", 101),
])
def test_invalid_or_out_of_range_scores_fail_before_gemini(field, value):
    client = mocked_client(valid_output())
    with pytest.raises(ValidationError):
        explain_development_priority(module4_input(**{field: value}), is_synthetic=True, client=client)
    client.models.generate_content.assert_not_called()


def test_invalid_priority_band_fails_input_validation():
    with pytest.raises(ValidationError):
        explain_development_priority(module4_input(priority_band="URGENT"), is_synthetic=True, client=Mock())


@pytest.mark.parametrize("field,value", [
    ("development_priority_score", 79.6),
    ("priority_band", "MODERATE"),
    ("city", "Guntur"),
    ("state", "Kerala"),
    ("category", "Roads"),
])
def test_gemini_changes_to_protected_fields_are_rejected(field, value):
    source = module4_input()
    output = valid_output(source, **{field: value})
    with pytest.raises(ExplanationValidationError, match="changed protected"):
        explain_development_priority(source, is_synthetic=True, client=mocked_client(output))


def test_score_and_band_are_preserved_exactly():
    source = module4_input()
    result = explain_development_priority(source, is_synthetic=True, client=mocked_client(valid_output(source)))
    assert result.development_priority_score == source["development_priority_score"]
    assert result.priority_band == source["priority_band"]


def test_synthetic_data_disclaimer_is_required_exactly():
    result = explain_development_priority(
        module4_input(), is_synthetic=True, client=mocked_client(valid_output())
    )
    assert result.data_note == SYNTHETIC_DATA_NOTE
    with pytest.raises(ExplanationValidationError, match="incorrect data note"):
        explain_development_priority(
            module4_input(), is_synthetic=True,
            client=mocked_client(valid_output(data_note="This is real government data.")),
        )


def test_non_synthetic_input_gets_non_verifying_data_note():
    from app.explanations import GENERAL_DATA_NOTE

    result = explain_development_priority(
        module4_input(), is_synthetic=False,
        client=mocked_client(valid_output(data_note=GENERAL_DATA_NOTE)),
    )
    assert result.data_note == GENERAL_DATA_NOTE


def test_unsupported_numerical_value_is_rejected():
    output = valid_output()
    output["explanation"] += " This result is ranked 99."
    with pytest.raises(ExplanationValidationError, match="unsupported numerical value"):
        explain_development_priority(module4_input(), is_synthetic=True, client=mocked_client(output))


def test_unsupported_claim_is_rejected():
    output = valid_output()
    output["explanation"] = output["explanation"].replace(
        "has a high development-demand signal", "has a high development-demand signal driven by"
    )
    with pytest.raises(ExplanationValidationError, match="unsupported real-world or causal claim"):
        explain_development_priority(module4_input(), is_synthetic=True, client=mocked_client(output))


@pytest.mark.parametrize("raw", ["not json", "{\"city\": \"Vijayawada\"}"])
def test_malformed_or_schema_invalid_gemini_json_is_rejected(raw):
    with pytest.raises(ExplanationValidationError, match="malformed or schema-invalid"):
        explain_development_priority(module4_input(), is_synthetic=True, client=mocked_client(raw))


def test_gemini_api_failure_is_handled_without_exposing_exception_text():
    client = Mock()
    client.models.generate_content.side_effect = RuntimeError("secret API key material")
    with pytest.raises(ExplanationGenerationError, match="could not generate") as error:
        explain_development_priority(module4_input(), is_synthetic=True, client=client)
    assert "secret API key" not in str(error.value)


@pytest.mark.parametrize("raw", [None, "", "  "])
def test_empty_gemini_response_is_rejected(raw):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=raw)
    with pytest.raises(ExplanationGenerationError, match="empty explanation"):
        explain_development_priority(module4_input(), is_synthetic=True, client=client)


def test_blank_explanation_is_rejected_by_schema():
    output = valid_output(explanation="   ")
    with pytest.raises(ExplanationValidationError, match="malformed or schema-invalid"):
        explain_development_priority(module4_input(), is_synthetic=True, client=mocked_client(output))
