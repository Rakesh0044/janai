"""JanDrishti AI API.

Module 1 currently uses transparent keyword/script heuristics because the ZIP
does not include a trained multilingual model. Citizen requests are persisted
in SQLite. Insight endpoints expose only records with real context inputs;
the frontend's synthetic demo records are not copied into the backend.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


DB_PATH = Path(os.getenv("JANAI_DB_PATH", str(Path(__file__).with_name("janai.db"))))
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app = FastAPI(title="JanDrishti AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class CitizenRequestInput(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value


class CitizenRequestOutput(BaseModel):
    original_text: str
    language: str
    state: str
    district_or_city: str | None
    category: str
    subcategory: str
    problem: str
    duration: str | None
    affected_population: int | None
    severity: int | None
    urgency: str
    normalized_summary: str
    keywords: list[str]
    confidence: float


class ContextInsightInput(BaseModel):
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=120)
    citizen_demand_score: float = Field(ge=0, le=100)
    infrastructure_condition: float = Field(ge=0, le=100)
    service_capacity: float = Field(ge=0, le=100)
    population_pressure: float = Field(ge=0, le=100)
    request_count: int = Field(ge=0)
    explanation: str | None = Field(default=None, max_length=4000)

    @field_validator("city", "state", "category")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS citizen_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                language TEXT NOT NULL,
                state TEXT NOT NULL,
                district_or_city TEXT,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                problem TEXT NOT NULL,
                duration TEXT,
                affected_population INTEGER,
                severity INTEGER,
                urgency TEXT NOT NULL,
                normalized_summary TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS city_insights (
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                category TEXT NOT NULL,
                citizen_demand_score REAL NOT NULL,
                infrastructure_condition REAL NOT NULL,
                service_capacity REAL NOT NULL,
                population_pressure REAL NOT NULL,
                context_gap_score REAL NOT NULL,
                development_priority_score REAL NOT NULL,
                priority_band TEXT NOT NULL CHECK(priority_band IN ('LOW','MODERATE','HIGH')),
                request_count INTEGER NOT NULL,
                explanation TEXT,
                PRIMARY KEY (city, category)
            )"""
        )


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    try:
        initialize_database()
        with db() as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "ok"}


LANGUAGE_MARKERS = {
    "Kannada": (0x0C80, 0x0CFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Malayalam": (0x0D00, 0x0D7F),
}


def detect_language(text: str) -> tuple[str, float]:
    for language, (start, end) in LANGUAGE_MARKERS.items():
        if any(start <= ord(char) <= end for char in text):
            return language, 0.55
    if re.search(r"[A-Za-z]", text):
        return "English", 0.45
    return "Unknown", 0.0


CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "Water Supply": ("water", "drinking water", "tap", "ಕುಡಿಯುವ ನೀರು", "ನೀರು", "నీరు", "വെള്ളം"),
    "Sanitation": ("toilet", "sewage", "drain", "sanitation", "ಶೌಚ", "మరుగుదొడ్డి", "മലിനജലം"),
    "Waste Management": ("garbage", "waste", "rubbish", "trash", "ಕಸ", "చెత్త", "മാലിന്യം"),
    "Roads & Transport": ("road", "pothole", "traffic", "ರಸ್ತೆ", "రోడ్డు", "റോഡ്"),
    "Public Health": ("hospital", "clinic", "health", "ಆಸ್ಪತ್ರೆ", "ఆసుపత్రి", "ആശുപത്രി"),
    "Electricity": ("electricity", "power cut", " बिजली", "ವಿದ್ಯುತ್", "విద్యుత్", "വൈദ്യുതി"),
}

CITY_STATES = {
    "bengaluru": ("Bengaluru", "Karnataka"), "mysuru": ("Mysuru", "Karnataka"),
    "hubballi": ("Hubballi", "Karnataka"), "belagavi": ("Belagavi", "Karnataka"),
    "vijayawada": ("Vijayawada", "Andhra Pradesh"),
    "visakhapatnam": ("Visakhapatnam", "Andhra Pradesh"),
    "tirupati": ("Tirupati", "Andhra Pradesh"), "kochi": ("Kochi", "Kerala"),
    "thiruvananthapuram": ("Thiruvananthapuram", "Kerala"),
    "kozhikode": ("Kozhikode", "Kerala"),
}


def classify_request(text: str) -> CitizenRequestOutput:
    language, confidence = detect_language(text)
    lowered = text.casefold()
    category = "Other"
    subcategory = "Unclassified"
    for name, terms in CATEGORY_TERMS.items():
        matching = next((term for term in terms if term.casefold() in lowered), None)
        if matching:
            category = name
            subcategory = matching.title() if matching.isascii() else "Keyword match"
            confidence = min(0.75, confidence + 0.2)
            break

    city = state = None
    for key, (city_name, state_name) in CITY_STATES.items():
        if key in lowered:
            city, state = city_name, state_name
            confidence = min(0.85, confidence + 0.1)
            break

    duration_match = re.search(r"\b(\d+)\s*(day|week|month|year)s?\b", lowered)
    duration = f"{duration_match.group(1)} {duration_match.group(2)}{'s' if duration_match.group(1) != '1' else ''}" if duration_match else None
    population_match = re.search(r"\b(\d[\d,]*)\s+(?:people|residents|families)\b", lowered)
    population = int(population_match.group(1).replace(",", "")) if population_match else None
    severe = any(term in lowered for term in ("urgent", "emergency", "severe", "danger", "ತುರ್ತು", "అత్యవసర", "അടിയന്തിര"))
    severity = 5 if severe else (3 if category != "Other" else None)
    urgency = "High" if severe else ("Moderate" if category != "Other" else "Unknown")
    words = re.findall(r"[A-Za-z]{3,}", lowered)
    stop = {"the", "and", "for", "are", "was", "with", "from", "our", "area", "please", "there"}
    keywords = list(dict.fromkeys(word for word in words if word not in stop))[:8]
    summary = f"{category} concern" + (f" reported in {city}" if city else "") + "."
    if duration:
        summary = summary[:-1] + f" for {duration}."

    return CitizenRequestOutput(
        original_text=text, language=language, state=state or "Unknown",
        district_or_city=city, category=category, subcategory=subcategory,
        problem=text, duration=duration, affected_population=population,
        severity=severity, urgency=urgency, normalized_summary=summary,
        keywords=keywords, confidence=round(confidence, 2),
    )


def save_request(result: CitizenRequestOutput) -> None:
    with db() as connection:
        connection.execute(
            """INSERT INTO citizen_requests
            (original_text, language, state, district_or_city, category, subcategory,
             problem, duration, affected_population, severity, urgency,
             normalized_summary, keywords_json, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (result.original_text, result.language, result.state, result.district_or_city,
             result.category, result.subcategory, result.problem, result.duration,
             result.affected_population, result.severity, result.urgency,
             result.normalized_summary, json.dumps(result.keywords), result.confidence,
             utc_now()),
        )


@app.post("/api/citizen-request", response_model=CitizenRequestOutput)
def submit_citizen_request(payload: CitizenRequestInput) -> CitizenRequestOutput:
    result = classify_request(payload.text)
    try:
        save_request(result)
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Could not save request") from exc
    return result


@app.post("/api/citizen-request/voice", response_model=CitizenRequestOutput)
async def submit_voice_request(audio: UploadFile = File(...)) -> CitizenRequestOutput:
    # The frontend records audio, but the ZIP supplies no speech-to-text engine.
    # Refuse clearly so its existing demo fallback can handle voice submissions.
    content = await audio.read(20 * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file exceeds 20 MB")
    raise HTTPException(status_code=501, detail="Speech transcription is not configured")


def insight_record(row: sqlite3.Row) -> dict:
    return {
        "city": row["city"], "state": row["state"], "category": row["category"],
        "citizen_demand_score": row["citizen_demand_score"],
        "infrastructure_condition": row["infrastructure_condition"],
        "service_capacity": row["service_capacity"], "population_pressure": row["population_pressure"],
        "context_gap_score": row["context_gap_score"],
        "development_priority_score": row["development_priority_score"],
        "priority_band": row["priority_band"], "request_count": row["request_count"],
        **({"explanation": row["explanation"]} if row["explanation"] else {}),
    }


@app.get("/api/insights")
def get_insights() -> list[dict]:
    """Return context insights explicitly entered by an upstream data pipeline."""
    with db() as connection:
        rows = connection.execute("SELECT * FROM city_insights ORDER BY development_priority_score DESC").fetchall()
    return [insight_record(row) for row in rows]


@app.post("/api/insights", response_model=dict)
def upsert_context_insight(payload: ContextInsightInput) -> dict:
    """Persist Module 3/4 output after an upstream pipeline supplies inputs."""
    context_gap = round(
        0.40 * (100 - payload.infrastructure_condition)
        + 0.35 * (100 - payload.service_capacity)
        + 0.25 * payload.population_pressure,
        1,
    )
    priority = round(0.60 * payload.citizen_demand_score + 0.40 * context_gap, 1)
    band = "HIGH" if priority >= 70 else "MODERATE" if priority >= 40 else "LOW"
    try:
        with db() as connection:
            connection.execute(
                """INSERT INTO city_insights
                (city, state, category, citizen_demand_score, infrastructure_condition,
                 service_capacity, population_pressure, context_gap_score,
                 development_priority_score, priority_band, request_count, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(city, category) DO UPDATE SET
                  state=excluded.state,
                  citizen_demand_score=excluded.citizen_demand_score,
                  infrastructure_condition=excluded.infrastructure_condition,
                  service_capacity=excluded.service_capacity,
                  population_pressure=excluded.population_pressure,
                  context_gap_score=excluded.context_gap_score,
                  development_priority_score=excluded.development_priority_score,
                  priority_band=excluded.priority_band,
                  request_count=excluded.request_count,
                  explanation=excluded.explanation""",
                (payload.city, payload.state, payload.category, payload.citizen_demand_score,
                 payload.infrastructure_condition, payload.service_capacity,
                 payload.population_pressure, context_gap, priority, band,
                 payload.request_count, payload.explanation),
            )
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Could not save insight") from exc
    return {
        "city": payload.city, "state": payload.state, "category": payload.category,
        "citizen_demand_score": payload.citizen_demand_score,
        "infrastructure_condition": payload.infrastructure_condition,
        "service_capacity": payload.service_capacity,
        "population_pressure": payload.population_pressure,
        "context_gap_score": context_gap,
        "development_priority_score": priority, "priority_band": band,
        "request_count": payload.request_count,
    }


@app.get("/api/dashboard-summary")
def get_dashboard_summary() -> dict:
    with db() as connection:
        request_rows = connection.execute(
            "SELECT category, state, COUNT(*) AS count FROM citizen_requests GROUP BY category, state"
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM citizen_requests").fetchone()[0]
        cities = connection.execute(
            "SELECT COUNT(DISTINCT district_or_city) FROM citizen_requests WHERE district_or_city IS NOT NULL"
        ).fetchone()[0]
        insight_rows = connection.execute("SELECT priority_band, COUNT(*) AS count FROM city_insights GROUP BY priority_band").fetchall()
    by_category: dict[str, int] = {}
    by_state: dict[str, int] = {}
    for row in request_rows:
        by_category[row["category"]] = by_category.get(row["category"], 0) + row["count"]
        if row["state"] != "Unknown":
            by_state[row["state"]] = by_state.get(row["state"], 0) + row["count"]
    bands = {row["priority_band"]: row["count"] for row in insight_rows}
    return {
        "total_requests": total,
        "active_hotspots": bands.get("MODERATE", 0) + bands.get("HIGH", 0),
        "high_priority_insights": bands.get("HIGH", 0),
        "cities_covered": cities,
        "category_distribution": [{"category": key, "count": value} for key, value in sorted(by_category.items())],
        "state_distribution": [{"state": key, "count": value} for key, value in sorted(by_state.items())],
        "hotspot_distribution": [{"band": band, "count": bands.get(band, 0)} for band in ("LOW", "MODERATE", "HIGH")],
    }


@app.get("/api/explanation")
def get_explanation(city: str = Query(min_length=1), category: str = Query(min_length=1)) -> dict:
    with db() as connection:
        row = connection.execute(
            "SELECT * FROM city_insights WHERE lower(city)=lower(?) AND lower(category)=lower(?)",
            (city, category),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No context insight exists for this city and category")
    if not row["explanation"]:
        raise HTTPException(status_code=503, detail="Explanation service is not configured")
    return {
        "city": row["city"], "state": row["state"], "category": row["category"],
        "priority_band": row["priority_band"],
        "development_priority_score": row["development_priority_score"],
        "explanation": row["explanation"], "key_factors": [],
        "data_note": "Explanation stored with the supplied context insight.", "confidence": 0.0,
    }
