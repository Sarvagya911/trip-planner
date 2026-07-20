# Trip Planner

An all-in-one, multi-mode trip planner. Mix driving, flights, trains, and buses
into a single itinerary — each leg labeled honestly with live data where we have
it and clearly-marked estimates where we don't.

## Architecture at a glance

A trip is modeled as an **ordered list of segments**, not a fixed origin →
destination. Each travel mode (driving, flight, train, bus) is a provider behind
one shared interface, so new modes or upgrades (e.g. live flight search later)
slot in without touching the orchestrator, the frontend, or anything else.

trip-planner/
├── backend/ FastAPI service — providers, orchestrator, /trip/plan API
└── frontend/ Next.js (TypeScript + Tailwind) responsive web app


- **backend/app/models/segment.py** — the core Segment schema (read this first)
- **backend/app/providers/** — one provider per mode, all behind `SegmentProvider`
- **backend/app/services/orchestrator.py** — stitches legs into one trip
- **frontend/lib/api.ts** — TypeScript mirror of the backend schema + API client
- **frontend/components/** — the itinerary cards and trip form

## Prerequisites

- Python 3.11+
- Node.js 18+
- A free OpenRouteService API key (for driving routes): https://openrouteservice.org/dev

## First-time setup

Clone the repo, then set up each half.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

Create a `.env` file in `backend/` (it is NOT committed — each person makes their own):

ORS_API_KEY=your_openrouteservice_key_here


See `backend/.env.example` for the full list of keys the project can use.

### Frontend

```bash
cd frontend
npm install
```

Create a `.env.local` file in `frontend/`:

NEXT_PUBLIC_API_URL=http://127.0.0.1:8000


## Running it (two terminals)

The frontend calls the backend, so both run at the same time.

**Terminal 1 — backend:**
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```
Runs at http://127.0.0.1:8000 — interactive API docs at http://127.0.0.1:8000/docs

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```
Runs at http://localhost:3000

Open http://localhost:3000, build a trip, and hit **Plan trip**.

## Travel mode status

| Mode    | Data source                        | Status today            |
|---------|------------------------------------|-------------------------|
| Driving | OpenRouteService (live)            | Live routing            |
| Flight  | Rough estimate + Google Flights link | Estimate (Amadeus planned) |
| Train   | Static timetable (dataset TBD)     | Empty until data loaded |
| Bus     | Rough estimate + redBus link       | Estimate                |

## Important notes

- **Never commit secrets.** `.env` and `.env.local` are gitignored on purpose.
  Each contributor supplies their own keys.
- Virtual environments (`.venv/`) and `node_modules/` are not committed — they're
  regenerated from `requirements.txt` and `package.json`.
- The one rule that keeps the design extensible: nothing outside
  `backend/app/providers/` imports a concrete provider directly — always go
  through the registry.

## Roadmap (next up)

- Real geocoding for flight/bus estimates (currently a flat placeholder distance)
- Load a real train timetable dataset
- Budget/city suggestion endpoint (`/trip/suggest`)
- Real-time collaboration (Supabase)