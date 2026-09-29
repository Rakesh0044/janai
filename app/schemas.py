"""Validated data contract for citizen request understanding."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Language = Literal["Kannada", "Telugu", "Malayalam", "English"]
State = Literal["Karnataka", "Andhra Pradesh", "Kerala"]
Category = Literal[
    "Water Supply", "Roads", "Public Transportation", "Healthcare",
    "Education", "Sanitation", "Electricity", "Waste Management",
    "Public Safety", "Other",
]


class CitizenRequest(BaseModel):
    """Structured, source-grounded representation of one citizen request."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    original_text: str = Field(min_length=1, description="Exact citizen input")
    language: Language
    state: State | None
    district_or_city: str | None
    category: Category
    subcategory: str
    problem: str
    duration: str | None
    affected_population: str | None
    severity: int = Field(ge=1, le=5)
    urgency: str
    normalized_summary: str
    keywords: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
