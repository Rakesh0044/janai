"""Unit tests use mocked Gemini responses; no network calls are made."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.gemini_client import ConfigurationError, GeminiResponseError, understand_request
from app.schemas import CitizenRequest
from app.validators import RequestInputError, validate_business_rules, validate_input


def record(**overrides):
    value = {
        "original_text": "Our street needs repairs.", "language": "English", "state": None,
        "district_or_city": None, "category": "Roads", "subcategory": "Potholes",
        "problem": "Road surface has potholes.", "duration": None,
        "affected_population": None, "severity": 3, "urgency": "Moderate",
        "normalized_summary": "The road has potholes.", "keywords": ["road", "potholes"],
        "confidence": 0.9,
    }
    value.update(overrides)
    return value


@pytest.mark.parametrize("language", ["Kannada", "Telugu", "Malayalam", "English"])
def test_valid_language_values(language):
    assert CitizenRequest.model_validate(record(language=language)).language == language


def test_valid_citizen_request_and_optional_fields():
    result = CitizenRequest.model_validate(record())
    assert result.duration is None and result.affected_population is None


@pytest.mark.parametrize("value", [0, 6, -1, 2.5])
def test_invalid_severity(value):
    with pytest.raises(ValidationError):
        CitizenRequest.model_validate(record(severity=value))


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_invalid_confidence(value):
    with pytest.raises(ValidationError):
        CitizenRequest.model_validate(record(confidence=value))


def test_unsupported_state_rejected():
    with pytest.raises(ValidationError):
        CitizenRequest.model_validate(record(state="Tamil Nadu"))


def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        CitizenRequest.model_validate(record(language="Hindi"))


def test_empty_and_long_input_rejected():
    with pytest.raises(RequestInputError):
        validate_input("  ", 10)
    with pytest.raises(RequestInputError):
        validate_input("12345", 4)


def test_business_rule_requires_exact_original_text():
    with pytest.raises(ValueError, match="does not match"):
        validate_business_rules(CitizenRequest.model_validate(record()), "different")


def test_mocked_gemini_response_pipeline():
    text = record()["original_text"]
    mock_client = Mock()
    mock_client.models.generate_content.return_value = SimpleNamespace(
        text=CitizenRequest.model_validate(record()).model_dump_json()
    )
    result = understand_request(text, config=Settings(api_key="test-key", model="test-model"), client=mock_client)
    assert result.original_text == text
    mock_client.models.generate_content.assert_called_once()


def test_empty_gemini_response():
    mock_client = Mock()
    mock_client.models.generate_content.return_value = SimpleNamespace(text="")
    with pytest.raises(GeminiResponseError, match="empty response"):
        understand_request("Request", config=Settings(api_key="test", model="test"), client=mock_client)


def test_missing_api_configuration():
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        understand_request("Request", config=Settings(api_key=None, model="test"))


@pytest.mark.parametrize("text,language,state,city,duration", [
    ("ಮೈಸೂರಿನಲ್ಲಿ ಕಳೆದ ಮೂರು ತಿಂಗಳಿಂದ ಕುಡಿಯುವ ನೀರು ಸರಿಯಾಗಿ ಬರುತ್ತಿಲ್ಲ.", "Kannada", "Karnataka", "Mysuru", "three months"),
    ("మా ప్రాంతంలో గత రెండు నెలలుగా తాగునీరు సరిగా రావడం లేదు.", "Telugu", None, None, "two months"),
    ("കഴിഞ്ഞ മൂന്ന് മാസമായി ഞങ്ങളുടെ പ്രദേശത്ത് കുടിവെള്ള വിതരണം ശരിയായി ലഭിക്കുന്നില്ല.", "Malayalam", None, None, "three months"),
    ("Our area has several large potholes and ambulances are having difficulty reaching the hospital.", "English", None, None, None),
])
def test_multilingual_fixture_expectations(text, language, state, city, duration):
    """The mocked structured response handles each supported script without a live API."""
    expected = CitizenRequest.model_validate(record(
        original_text=text, language=language, state=state, district_or_city=city,
        duration=duration, category="Water Supply" if language != "English" else "Roads",
    ))
    mock_client = Mock()
    mock_client.models.generate_content.return_value = SimpleNamespace(text=expected.model_dump_json())
    result = understand_request(
        text, config=Settings(api_key="test-key", model="test-model"), client=mock_client
    )
    assert result.original_text == text
    assert result.language == language
    assert result.state == state
    assert result.district_or_city == city
    assert result.duration == duration


@pytest.mark.parametrize("state", ["Karnataka", "Andhra Pradesh", "Kerala"])
def test_supported_states(state):
    assert CitizenRequest.model_validate(record(state=state, district_or_city="Example" )).state == state


def test_unsupported_location_can_remain_unmapped():
    result = CitizenRequest.model_validate(record(state=None, district_or_city="Chennai"))
    assert result.state is None and result.district_or_city == "Chennai"


def test_severity_levels_are_bounded():
    for value in range(1, 6):
        assert CitizenRequest.model_validate(record(severity=value)).severity == value
