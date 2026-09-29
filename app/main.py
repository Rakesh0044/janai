"""Command-line interface for JanDrishti AI Module 1."""

import json
import logging
import sys

from pydantic import ValidationError

from .config import settings
from .gemini_client import ConfigurationError, understand_request
from .validators import RequestInputError


def configure_console_encoding() -> None:
    """Use UTF-8 in Windows terminals when the stream supports reconfiguration."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    configure_console_encoding()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Application startup. Model: %s", settings.model)
    print("========================================")
    print("JAN DRISHTI AI")
    print("Module 1 - Citizen Request Understanding")
    print("========================================")
    try:
        text = input("\nEnter citizen request:\n> ")
        result = understand_request(text)
        print("\n" + json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        return 0
    except (RequestInputError, ConfigurationError, ValidationError, RuntimeError, ValueError) as exc:
        logger.error("Could not process request: %s", exc)
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.exception("Unexpected application error.")
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        return 1
