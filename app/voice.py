"""Speech-to-text adapter that sends its transcript through Module 1."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field

from .config import settings
from .gemini_client import understand_request
from .schemas import CitizenRequest

logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 20 * 1024 * 1024
TRANSCRIPTION_MODEL = os.getenv("GEMINI_TRANSCRIPTION_MODEL", "gemini-3.5-transcribe")
AUDIO_TYPES: dict[str, tuple[str, bytes]] = {
    ".wav": ("audio/wav", b"RIFF"),
    ".mp3": ("audio/mp3", b""),
    ".m4a": ("audio/m4a", b"ftyp"),
}


class VoiceProcessingError(RuntimeError):
    """Base error for audio validation and transcription failures."""


class AudioInputError(VoiceProcessingError):
    """Audio path, format, or file-content problem."""


class VoiceConfigurationError(VoiceProcessingError):
    """Missing configuration needed to call Gemini transcription."""


class TranscriptionError(VoiceProcessingError):
    """Gemini could not return a usable transcript."""


class VoiceRequestResult(BaseModel):
    """Original-language transcript and its Module 1 interpretation."""

    model_config = ConfigDict(extra="forbid")

    transcript: str = Field(min_length=1)
    request: CitizenRequest


def _validate_audio(path: str | os.PathLike[str]) -> tuple[Path, str]:
    """Validate supported extension, size, and a basic format signature."""
    audio_path = Path(path)
    if not audio_path.exists() or not audio_path.is_file():
        raise AudioInputError("Audio file does not exist or is not a regular file.")

    file_type = AUDIO_TYPES.get(audio_path.suffix.lower())
    if file_type is None:
        raise AudioInputError("Unsupported audio format. Use WAV, MP3, or M4A.")

    size = audio_path.stat().st_size
    if size == 0:
        raise AudioInputError("Audio file is empty.")
    if size > MAX_AUDIO_BYTES:
        raise AudioInputError("Audio file exceeds the 20 MB limit.")

    with audio_path.open("rb") as audio_file:
        header = audio_file.read(12)
    mime_type, signature = file_type
    if audio_path.suffix.lower() == ".wav":
        valid_signature = len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"
    elif audio_path.suffix.lower() == ".m4a":
        valid_signature = len(header) >= 8 and header[4:8] == signature
    else:
        # MP3 may start with an ID3 tag or an MPEG audio frame sync word.
        valid_signature = header.startswith(b"ID3") or (
            len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0
        )
    if not valid_signature:
        raise AudioInputError(f"File contents do not look like {audio_path.suffix[1:].upper()} audio.")

    return audio_path, mime_type


def transcribe_audio(
    audio_path: str | os.PathLike[str],
    *,
    client=None,
    api_key: str | None = None,
    model: str = TRANSCRIPTION_MODEL,
    timeout_ms: int | None = None,
) -> str:
    """Transcribe audio with Gemini, preserving the spoken language."""
    path, mime_type = _validate_audio(audio_path)
    key = api_key if api_key is not None else settings.api_key
    if not key and client is None:
        raise VoiceConfigurationError("GEMINI_API_KEY is missing. Add it to your .env file.")

    sdk_client = client or genai.Client(api_key=key)
    timeout = timeout_ms or settings.timeout_ms
    uploaded_file = None
    logger.info("Audio transcription started (%s, %d bytes).", path.suffix.lower(), path.stat().st_size)
    try:
        uploaded_file = sdk_client.files.upload(
            file=str(path),
            config=types.UploadFileConfig(mime_type=mime_type),
        )
        response = sdk_client.models.generate_content(
            model=model,
            contents=[uploaded_file],
            config=types.GenerateContentConfig(
                audio_transcription_config=types.AudioTranscriptionConfig(
                    mode="VERBATIM",
                    language_codes=[],
                ),
                http_options=types.HttpOptions(timeout=timeout),
            ),
        )
    except Exception as exc:
        # Keep SDK exception text out of user-facing messages and logs; it can
        # contain request details. The exception class is useful for debugging.
        logger.error("Gemini audio transcription failed (%s).", type(exc).__name__)
        raise TranscriptionError(
            "Gemini could not transcribe this audio. Check the API/model configuration and retry."
        ) from exc
    finally:
        if uploaded_file is not None and getattr(uploaded_file, "name", None):
            try:
                sdk_client.files.delete(name=uploaded_file.name)
            except Exception as exc:
                logger.warning("Could not remove temporary uploaded audio (%s).", type(exc).__name__)

    transcript = (getattr(response, "text", None) or "").strip()
    no_speech_markers = {"[no speech detected]", "no speech detected", "[inaudible]", "..."}
    if not transcript or transcript.casefold() in no_speech_markers:
        raise TranscriptionError("No clear speech was found in the audio. Try a clearer recording.")
    return transcript


def process_voice_request(audio_path: str | os.PathLike[str]) -> VoiceRequestResult:
    """Transcribe audio and pass the original-language text to Module 1."""
    transcript = transcribe_audio(audio_path)
    logger.info("Transcript ready; sending it to Module 1 (%d characters).", len(transcript))
    try:
        request = understand_request(transcript)
    except Exception as exc:
        logger.error("Module 1 could not process the audio transcript (%s).", type(exc).__name__)
        raise VoiceProcessingError(
            "Audio was transcribed, but Module 1 could not process the transcript."
        ) from exc
    return VoiceRequestResult(transcript=transcript, request=request)
