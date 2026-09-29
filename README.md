# JanDrishti AI backend

FastAPI API for the Next.js frontend in `work/janai-main`. It persists citizen
submissions and supplied city/context insights in SQLite. The frontend contract
comes from that project's `types/index.ts` and `lib/api.ts`.

## Run locally (PowerShell)

Use Python 3.10 or newer. From the backend folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI docs: <http://localhost:8000/docs>. Health: <http://localhost:8000/health>.
SQLite creates `janai.db` beside `main.py` by default. Set `JANAI_DB_PATH` to
move it. Set `FRONTEND_ORIGINS` to a comma-separated list if the frontend uses
a different local or deployed origin.

In the frontend's `.env.local`, use:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_FORCE_DEMO_MODE=false
```

Run the frontend from `work/janai-main` with `npm install` and `npm run dev`.
The existing frontend API client calls the same routes listed below.

## API routes

- `GET /health` checks the process and SQLite connection.
- `POST /api/citizen-request` accepts `{ "text": "..." }`, applies transparent
  keyword/script heuristics, saves the structured request, and returns the
  frontend's `CitizenRequest` schema.
- `POST /api/citizen-request/voice` accepts multipart field `audio`. The ZIP
  contains no speech-to-text engine, so this returns HTTP 501 explicitly; the
  frontend's existing fallback handles it as demo data.
- `GET /api/insights` returns saved city insights in the frontend's
  `CityInsightRecord` shape. It starts empty because no real infrastructure
  dataset was included.
- `POST /api/insights` accepts upstream demand and infrastructure inputs,
  computes the methodology page's context gap and priority formulas, then
  upserts the result in SQLite.
- `GET /api/dashboard-summary` summarizes persisted citizen requests and
  insight records using the frontend's `DashboardSummary` shape.
- `GET /api/explanation?city=...&category=...` returns an explanation stored
  with an insight, or an explicit 404/503 if one is unavailable.

## Current limitations

The project archive supplies frontend contracts and a methodology description,
but no trained multilingual model, speech-to-text service, real infrastructure
data, demand aggregation definition, or explanation model. Request
understanding is therefore a small, inspectable keyword heuristic, not an AI
model. The context and priority formulas follow the methodology page. The
thresholds (70 HIGH, 40 MODERATE) follow the frontend's synthetic data helper.
No synthetic city records are inserted into the database. Insight results
remain empty until real/upstream values are posted. Configure an actual ASR,
Module 1 model and explanation service with your team before describing those
capabilities as AI-powered.

SQLite is suitable for this prototype. The insight write endpoint has no
authentication and is intended for local/team integration only.
