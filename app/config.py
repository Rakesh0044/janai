"""Environment-backed application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str | None = os.getenv("GEMINI_API_KEY")
    model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    max_input_chars: int = 10_000
    timeout_ms: int = 30_000


settings = Settings()
