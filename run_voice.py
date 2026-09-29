"""Transcribe an audio file and process the transcript with Module 1."""

import argparse
import json
import logging

from app.voice import VoiceProcessingError, process_voice_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Process a citizen request from a WAV, MP3, or M4A recording.")
    parser.add_argument("audio_file", help="Path to the citizen's audio recording")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        result = process_voice_request(args.audio_file)
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return 0
    except VoiceProcessingError as exc:
        logging.error("Could not process audio: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
