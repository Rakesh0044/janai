"""Offline unit tests for voice input and Module 1 handoff."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.schemas import CitizenRequest
from app.voice import (
    AudioInputError,
    TranscriptionError,
    VoiceRequestResult,
    _validate_audio,
    process_voice_request,
    transcribe_audio,
)


KANNADA_TEXT = "ಮೈಸೂರಿನಲ್ಲಿ ಕಳೆದ ಮೂರು ತಿಂಗಳಿಂದ ಕುಡಿಯುವ ನೀರು ಸರಿಯಾಗಿ ಬರುತ್ತಿಲ್ಲ."


def make_wav(path: Path) -> Path:
    """Write a minimal WAV header for format-validation tests."""
    path.write_bytes(b"RIFF" + (4).to_bytes(4, "little") + b"WAVE" + b"data")
    return path


def test_missing_audio_file(tmp_path):
    with pytest.raises(AudioInputError, match="does not exist"):
        _validate_audio(tmp_path / "missing.wav")


def test_unsupported_file_type(tmp_path):
    path = tmp_path / "recording.ogg"
    path.write_bytes(b"OggS\x00")
    with pytest.raises(AudioInputError, match="Unsupported audio format"):
        _validate_audio(path)


@pytest.mark.parametrize("name,header", [
    ("recording.mp3", b"ID3\x04\x00\x00\x00\x00\x00\x00"),
    ("recording.m4a", b"\x00\x00\x00\x18ftypM4A "),
])
def test_supported_mp3_and_m4a_signatures(tmp_path, name, header):
    path = tmp_path / name
    path.write_bytes(header)
    checked_path, mime_type = _validate_audio(path)
    assert checked_path == path
    assert mime_type in {"audio/mp3", "audio/m4a"}


@pytest.mark.parametrize("contents,message", [(b"", "empty"), (b"not audio", "do not look like WAV")])
def test_empty_or_invalid_audio(tmp_path, contents, message):
    path = tmp_path / "recording.wav"
    path.write_bytes(contents)
    with pytest.raises(AudioInputError, match=message):
        _validate_audio(path)


def test_successful_transcription_preserves_language(tmp_path):
    path = make_wav(tmp_path / "kannada.wav")
    mock_client = Mock()
    mock_client.files.upload.return_value = SimpleNamespace(name="files/temp-audio")
    mock_client.models.generate_content.return_value = SimpleNamespace(text=KANNADA_TEXT)

    transcript = transcribe_audio(path, client=mock_client)

    assert transcript == KANNADA_TEXT
    mock_client.files.upload.assert_called_once()
    mock_client.models.generate_content.assert_called_once()
    assert mock_client.models.generate_content.call_args.kwargs["model"] == "gemini-3.5-transcribe"
    mock_client.files.delete.assert_called_once_with(name="files/temp-audio")


def test_transcript_passed_unchanged_to_module1(tmp_path):
    path = make_wav(tmp_path / "request.wav")
    expected = CitizenRequest(
        original_text=KANNADA_TEXT, language="Kannada", state="Karnataka", district_or_city="Mysuru",
        category="Water Supply", subcategory="Drinking water supply", problem="Water supply is unreliable.",
        duration="three months", affected_population=None, severity=3, urgency="Moderate",
        normalized_summary="Mysuru has had unreliable drinking water for three months.",
        keywords=["water", "Mysuru"], confidence=0.9,
    )
    with patch("app.voice.transcribe_audio", return_value=KANNADA_TEXT), patch(
        "app.voice.understand_request", return_value=expected
    ) as module1:
        result = process_voice_request(path)

    module1.assert_called_once_with(KANNADA_TEXT)
    assert result == VoiceRequestResult(transcript=KANNADA_TEXT, request=expected)
    assert result.model_dump()["request"]["language"] == "Kannada"


def test_api_failure_is_reported_without_sdk_details(tmp_path):
    path = make_wav(tmp_path / "broken.wav")
    mock_client = Mock()
    mock_client.files.upload.side_effect = RuntimeError("secret api key should not leak")
    with pytest.raises(TranscriptionError, match="could not transcribe") as error:
        transcribe_audio(path, client=mock_client)
    assert "secret api key" not in str(error.value)


def test_empty_transcription_is_reported(tmp_path):
    path = make_wav(tmp_path / "silent.wav")
    mock_client = Mock()
    mock_client.files.upload.return_value = SimpleNamespace(name="files/silent")
    mock_client.models.generate_content.return_value = SimpleNamespace(text="  ")
    with pytest.raises(TranscriptionError, match="No clear speech"):
        transcribe_audio(path, client=mock_client)


def test_module1_failure_is_handled_after_transcription(tmp_path):
    path = make_wav(tmp_path / "request.wav")
    with patch("app.voice.transcribe_audio", return_value=KANNADA_TEXT), patch(
        "app.voice.understand_request", side_effect=RuntimeError("validation failed")
    ):
        with pytest.raises(Exception, match="Module 1 could not process"):
            process_voice_request(path)
