# JanDrishti AI — Modules 1–5

The Citizen Request Understanding Engine turns one development request in Kannada, Telugu, Malayalam, or English into a validated structured record. Gemini performs multilingual understanding; Pydantic and business checks validate the result. This module only structures requests for later analysis. It does not make government decisions or calculate a priority score.

Module 2 adds voice input: a recording is transcribed in its spoken language and the transcript is sent directly into Module 1's existing `understand_request(transcript)` function. There is no separate voice classification path.

Module 3 aggregates structured requests with deterministic Pandas/NumPy calculations and reports relative demand-intensity hotspots. It does not use Gemini for numerical analysis or make government funding decisions.

Module 4 combines Module 3 demand insights with clearly labeled synthetic infrastructure/context indicators to produce Development Priority Insights. It uses deterministic Python/NumPy calculations only.

Module 5 uses Gemini only to explain a Module 4 result in concise, neutral language. Module 4 remains the source of numerical truth; Module 5 validates the response and rejects changes to protected values.

## Prerequisites

- Python 3.11 or newer
- A Gemini API key

## Install (Windows PowerShell)

```powershell
cd .\jandrishti-ai
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY` to your key. Set `GEMINI_MODEL` to a model available to your Gemini API account; the default when omitted is `gemini-2.5-flash`. Voice transcription uses `GEMINI_TRANSCRIPTION_MODEL`, which defaults to `gemini-3.5-transcribe`.

## Run

```powershell
python run.py
```

Enter a request when prompted. Example inputs:

- Kannada: `ಮೈಸೂರಿನಲ್ಲಿ ಕಳೆದ ಮೂರು ತಿಂಗಳಿಂದ ಕುಡಿಯುವ ನೀರು ಸರಿಯಾಗಿ ಬರುತ್ತಿಲ್ಲ.`
- Telugu: `మా ప్రాంతంలో గత రెండు నెలలుగా తాగునీరు సరిగా రావడం లేదు.`
- Malayalam: `കഴിഞ്ഞ മൂന്ന് മാസമായി ഞങ്ങളുടെ പ്രദേശത്ത് കുടിവെള്ള വിതരണം ശരിയായി ലഭിക്കുന്നില്ല.`
- English: `Our area has several large potholes and ambulances are having difficulty reaching the hospital.`

The console prints UTF-8 JSON. Fields not stated by the citizen, such as duration or affected population, remain null. Names outside the supported states are not mapped to a supported state.

## Module 2: voice input

Voice input supports Kannada, Telugu, Malayalam, and English. Supported recordings are WAV, MP3, and M4A, up to 20 MB. Gemini automatically identifies the spoken language and is asked for a verbatim transcript; the transcript is not translated before Module 1.

Run the voice CLI by passing an audio file path:

```powershell
python run_voice.py "C:\recordings\citizen-request.wav"
```

The JSON result contains `transcript` and `request`. `request` is the same validated `CitizenRequest` returned by Module 1. For example, a Kannada recording is transcribed in Kannada, then that exact transcript is passed into `understand_request`.

## Module 3 — Demand Aggregation & Hotspot Detection

**Input:** structured citizen requests from Module 1 or Module 2. The analysis accepts `CitizenRequest` objects or dictionaries and handles absent fields safely.

**Processing:** Pandas cleans and groups the records by city, state, category, and city/category. NumPy combines normalized request frequency, reported severity, and—when timestamps exist—recency. Gemini is not used for these calculations.

**Output:** Development Demand Insights with request counts, average reported severity, high-severity counts, a 0–100 demand-intensity score, hotspot band, and a short reason.

Run the demo:

```powershell
python run_analysis.py
```

The bundled demo is labeled **SYNTHETIC DEMO DATA — NOT REAL GOVERNMENT DATA**. It contains no personal information and must not be interpreted as a statement about actual city conditions. Prototype scores describe only the supplied citizen-report dataset; they are not government funding, policy, or objective service-quality decisions.

Default scoring weights are configurable in `DemandScoreConfig`: frequency 0.50, severity 0.35, and recency 0.15. If timestamps are absent, recency is excluded and the other available components are renormalized. Component scores are normalized to 0–100; the weighted average is also 0–100. Hotspot thresholds default to LOW below 40, MODERATE from 40 to below 70, and HIGH at 70 or above. Change weights and thresholds by passing a customized `DemandScoreConfig` to the analysis functions.

## Module 4 — Infrastructure & Context Analysis

**Input:** Module 3 city/category demand insights plus contextual indicators for infrastructure condition, service capacity, and population pressure. All context values use a 0–100 scale; a missing value remains missing and the remaining available context weights are renormalized. If no context indicators exist for a demand insight, the combined score is unavailable.

**Output:** Development Priority Insights with the demand score, context indicators, context-gap score, combined development-priority score, band, and careful explanation.

Run the combined synthetic demo:

```powershell
python run_priority.py
```

The output and input are both labeled **SYNTHETIC DEMO DATA — NOT REAL GOVERNMENT DATA** / **SYNTHETIC CONTEXT DATA — NOT REAL INFRASTRUCTURE MEASUREMENTS**. These values are fabricated for demonstration, contain no PII, and do not describe actual conditions in Karnataka, Andhra Pradesh, Kerala, or their cities. A score is an analytical prototype insight; it is not an actual government funding or policy decision.

Default context-gap weights in `ContextGapConfig` are infrastructure condition 0.40, service capacity 0.35, and population pressure 0.25. The formula is:

```text
context_gap_score = 0.40 × (100 − infrastructure_condition)
                  + 0.35 × (100 − service_capacity)
                  + 0.25 × population_pressure
```

This normalizes poor infrastructure and low capacity into larger gaps; high population pressure also increases the gap. Default priority weights in `PriorityScoreConfig` are citizen demand 0.60 and context gap 0.40:

```text
development_priority_score = 0.60 × citizen_demand_score
                           + 0.40 × context_gap_score
```

Both weighted formulas remain on the 0–100 scale. Priority bands default to LOW below 40, MODERATE from 40 to below 70, and HIGH at 70 or above. Both sets of weights and the band thresholds are configurable in code.

## Module 5 — AI Explanation Layer

**Architecture:** citizen request → Modules 1–2 → Module 3 demand analysis → Module 4 numerical context/priority insight → Module 5 human-readable explanation.

Module 5 receives an already-calculated Module 4 insight and asks the configured Gemini model to explain the supplied factors. Gemini does **not** calculate, modify, rank, or recalculate scores. The output is checked against the input so city, state, category, priority band, and development-priority score remain unchanged. Explanations are also rejected if they introduce numeric values not present in the Module 4 input.

Run the demo from the project directory after setting `GEMINI_API_KEY` in `.env`:

```powershell
.venv\Scripts\python.exe run_explanation.py
```

The CLI runs one synthetic Module 4 insight, labels it `AI EXPLANATION DEMO` and `SYNTHETIC DEMO DATA — NOT REAL GOVERNMENT DATA`, then prints the input and generated explanation, key factors, and data note.

Example Module 4 input:

```json
{
  "city": "Vijayawada",
  "state": "Andhra Pradesh",
  "category": "Sanitation",
  "citizen_demand_score": 89.5,
  "infrastructure_condition": 50.0,
  "service_capacity": 41.0,
  "population_pressure": 95.0,
  "context_gap_score": 64.4,
  "development_priority_score": 79.5,
  "priority_band": "HIGH"
}
```

Example explanation shape (wording may vary; protected values and the synthetic note are validated):

```json
{
  "city": "Vijayawada",
  "state": "Andhra Pradesh",
  "category": "Sanitation",
  "priority_band": "HIGH",
  "development_priority_score": 79.5,
  "explanation": "Sanitation shows a high development-demand signal in the prototype dataset. Citizen demand is 89.5 and the context gap is 64.4. The supplied contextual indicators include service capacity 41.0 and population pressure 95.0. The calculated Module 4 priority score is 79.5.",
  "key_factors": ["Citizen demand score: 89.5", "Context gap score: 64.4", "Service capacity: 41.0", "Population pressure: 95.0"],
  "data_note": "This is a prototype insight based on synthetic/demo data and does not represent real government infrastructure measurements.",
  "confidence": 0.92
}
```

The confidence value describes how clear and complete the supplied inputs are for explanation; it does not measure whether synthetic infrastructure values are true. The output is explanatory only and is not a funding decision, policy recommendation, or political judgment.

Example output shape (actual values depend on the input and Gemini):

```json
{
  "original_text": "Our street needs repairs.",
  "language": "English",
  "state": null,
  "district_or_city": null,
  "category": "Roads",
  "subcategory": "Potholes",
  "problem": "The road surface has potholes.",
  "duration": null,
  "affected_population": null,
  "severity": 3,
  "urgency": "Moderate",
  "normalized_summary": "The road has potholes.",
  "keywords": ["road", "potholes"],
  "confidence": 0.9
}
```

## Tests

```powershell
python -m pytest
```

Unit tests mock the Gemini response and do not require a key or network. They cover schema constraints, missing fields, location rules, configuration errors, and the response pipeline.

## Architecture and data flow

`run.py` starts the text CLI. The CLI calls `app.gemini_client.understand_request`, which validates input length, calls the official `google-genai` SDK with a Pydantic structured-output schema, parses the JSON into `CitizenRequest`, then applies business rules before returning it for display.

For audio, `run_voice.py` calls `app.voice.process_voice_request`. That module validates the recording, uses `google-genai` audio transcription, then passes the original-language transcript to the same `understand_request` function.

For Module 3, `app.analysis.analyze_requests` cleans records, returns the aggregation tables, computes scores, and produces hotspot insights. `app.synthetic_data` creates the clearly labeled demo records; `run_analysis.py` displays them.

For Module 4, `app.context_data` validates and creates synthetic context indicators, `app.priority` provides the gap and combination formulas, and `app.insights.build_development_priority_insights` joins context to Module 3 demand insights. `run_priority.py` runs both synthetic datasets through that pipeline.

For Module 5, `app.explanations.explain_development_priority` validates a Module 4 insight, calls the configured Gemini model using structured JSON output, and checks the generated explanation against the source values. `run_explanation.py` demonstrates the full path using synthetic Module 4 output.

- `app/config.py`: environment settings, dotenv loading, model and limits.
- `app/schemas.py`: strict Pydantic data contract and constrained fields.
- `app/prompts.py`: extraction instructions and request framing.
- `app/gemini_client.py`: SDK integration, transient retries, parsing, and API errors.
- `app/validators.py`: input and cross-field checks.
- `app/main.py`: UTF-8-aware interactive CLI and logging.
- `app/voice.py`: audio validation, Gemini transcription, and Module 1 handoff.
- `run_voice.py`: command-line entry point for audio files.
- `app/analytics.py`: record cleaning, group metrics, configurable demand score.
- `app/hotspots.py`: configurable hotspot classification and structured insight records.
- `app/analysis.py`: reusable end-to-end Module 3 analysis pipeline.
- `app/synthetic_data.py`: deterministic, anonymous synthetic demo records.
- `run_analysis.py`: CLI for the synthetic Module 3 demonstration.
- `app/context_data.py`: validated, synthetic city/category context indicators.
- `app/priority.py`: configurable context-gap and combined-score mathematics.
- `app/insights.py`: joins demand and context into Development Priority Insights.
- `run_priority.py`: combined synthetic Module 4 CLI demonstration.
- `app/explanations.py`: Module 4 input validation, Gemini explanation prompt/call, and output-integrity checks.
- `run_explanation.py`: AI explanation demonstration using a synthetic Module 4 insight.
- `tests/test_module1.py`: offline contract and mocked-client tests.
- `tests/test_voice.py`: offline audio validation and mocked voice pipeline tests.
- `tests/test_analytics.py` and `tests/test_hotspots.py`: deterministic analysis and hotspot tests.
- `tests/test_priority.py` and `tests/test_insights.py`: context validation, formulas, bands, and deterministic joins.
- `tests/test_explanations.py`: mocked Gemini responses, validation, numeric integrity, and synthetic-data notes.

## Security

Keep `.env` private; it is ignored by Git. Never commit an API key or paste it into logs. Logs include request length and processing status, not citizen text. Review extracted records before using them in any downstream process.

## Future module

Future modules may consume these insights for additional geographic analysis. Keep all numerical analysis separate from Gemini's semantic extraction so its criteria can be inspected and audited.
