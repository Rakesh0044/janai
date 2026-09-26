# JanDrishti AI — Frontend

A Next.js (App Router) + TypeScript + Tailwind CSS frontend for the JanDrishti AI
development-intelligence platform. This frontend consumes the existing Python
backend's outputs (Modules 1–5) — it does not reimplement any AI/ML logic or
recalculate any backend scores.

## 1. Requirements

- Node.js 18.18 or newer (Node 20 LTS recommended)
- npm 9+ (comes with Node)

## 2. Install

```bash
cd jandrishti-ai
npm install
```

This downloads Next.js, React, Tailwind, Recharts and Leaflet/react-leaflet —
you need an internet connection for this step.

## 3. Configure environment variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:

| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of your running Python backend | `http://localhost:8000` |
| `NEXT_PUBLIC_FORCE_DEMO_MODE` | Set to `true` to always use synthetic demo data, even with a backend configured | `false` |

If `NEXT_PUBLIC_API_BASE_URL` is unreachable or unset, every page automatically
falls back to synthetic demo data and shows an on-screen "Showing synthetic
demo data" banner — the UI never fails silently.

## 4. Run it

```bash
npm run dev
```

Open http://localhost:3000.

For a production build:

```bash
npm run build
npm run start
```

## 5. Add the real logo

No logo file was supplied with this brief. A placeholder wordmark (an outlined
mark + "JanDrishti AI" text) is rendered by `components/Logo.tsx`. Once you have
the real logo:

1. Drop the file at `public/logo.svg` (or `.png`).
2. Replace the `<svg>...</svg>` in `components/Logo.tsx` with `<img src="/logo.svg" alt="JanDrishti AI" />`.
3. Re-check `tailwind.config.ts` — the palette there (`primary` teal, `accent`
   amber, `base` navy) was chosen as a neutral civic-tech placeholder and should
   be adjusted to match the logo's actual colors.

## How frontend and backend communicate

`lib/api.ts` is the single integration point. Each function:

1. Calls `NEXT_PUBLIC_API_BASE_URL` + a REST path (see table below).
2. On success, returns the backend's JSON untouched.
3. On any network/HTTP error, falls back to the matching synthetic dataset in
   `lib/mockData.ts` and marks the result as demo mode.

### Assumed API endpoints

These endpoints were **not** provided in the brief and are assumed — update
`lib/api.ts` to match your actual backend routes if they differ:

| Function | Method & path | Backend module |
|---|---|---|
| `submitCitizenRequestText` | `POST /api/citizen-request` `{ text }` | Module 1 |
| `submitCitizenRequestVoice` | `POST /api/citizen-request/voice` (multipart `audio`) | Module 2 → 1 |
| `getInsights` | `GET /api/insights` | Modules 3 + 4 (merged) |
| `getDashboardSummary` | `GET /api/dashboard-summary` | Aggregated Module 3 data |
| `getExplanation` | `GET /api/explanation?city=&category=` | Module 5 |

Each function's TypeScript return type (`types/index.ts`) mirrors the field
names given in the brief exactly (`CitizenRequest`, `DemandInsight`,
`ContextInsight`, `ExplanationInsight`), so once the real routes are wired in,
no other file needs to change as long as the JSON shape matches.

## Project structure

```
app/
  page.tsx                 Landing page
  citizen-request/page.tsx Text + voice submission, AI Understanding result
  dashboard/page.tsx       KPI cards + charts (Recharts)
  hotspot-map/page.tsx     Leaflet map (Karnataka / Andhra Pradesh / Kerala)
  insights/page.tsx        Searchable/sortable city-category insight table
  methodology/page.tsx     Pipeline + Module 4 formula explanation
components/                Reusable UI (Navbar, forms, cards, badges, map)
lib/
  api.ts                   All backend calls + demo-mode fallback
  mockData.ts              SYNTHETIC DEMO DATA (clearly labeled everywhere it's shown)
  utils.ts                 Small class/formatting helpers
types/index.ts              TypeScript interfaces matching the Python schemas
hooks/useDemoMode.ts        Small demo-mode state helper
```

## What was and wasn't done

- No backend files were created, modified, or executed.
- No Module 3/4 scoring logic exists in this frontend — every score shown
  (`demand_score`, `context_gap_score`, `development_priority_score`, bands)
  comes directly from the API response or the mock dataset.
- Demo mode is real fallback behavior (triggered by fetch failure), not a
  toggle that fakes success.
- The map uses `react-leaflet` + OpenStreetMap tiles as requested. City
  latitude/longitude pairs are hardcoded in `lib/mockData.ts` (`CITY_COORDINATES`)
  since the brief's schemas don't include coordinates — if your backend can
  return them, wire them into `getInsights`/a new endpoint instead.
- Accessibility basics included: semantic headings, labeled form controls,
  visible focus outlines, `aria-live`/`role="status"` on async states,
  `aria-label`s on the microphone and dialog, and priority bands are shown as
  both color and a text label (never color alone).
- No automated build/lint was run in this environment (no network access to
  install dependencies here) — run `npm run build` locally before your demo to
  catch any TypeScript issues early.
