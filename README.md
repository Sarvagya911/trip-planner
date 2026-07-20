# Trip Planner

An all-in-one, conversational, multi-mode trip planner. Describe a trip in
plain language — or fill in a form — and get a single itinerary mixing
driving, flights, trains, and buses. Every leg is labeled honestly: live
data where we have it, clearly-marked estimates where we don't.

## What it does

- **Chat planning** — tell the assistant where you're starting, who's coming,
  and the kind of trip you want. It asks follow-ups, suggests destinations if
  you're unsure, and builds a structured plan.
- **Manual planning** — or skip the chat and enter legs directly in a form.
- **Multi-mode, mixed trips** — one itinerary can chain a flight, then a drive,
  then a train. Each leg is planned by its own provider.
- **Honest data** — driving uses live OpenRouteService routing; flights/buses
  are distance-based estimates with deep links to book externally; trains are
  scheduled-timetable-ready.

## Architecture at a glance

A trip is modeled as an **ordered list of segments**, not a fixed origin →
destination. Each travel mode is a provider behind one shared interface, so new
modes or upgrades slot in without touching the orchestrator, the frontend, or
anything else.

trip-planner/
├── backend/ FastAPI — providers, orchestrator, conversation, APIs
└── frontend/ Next.js (TypeScript + Tailwind) responsive web app


Key backend files:
- `app/models/segment.py` — the core Segment schema (read this first)
- `app/models/conversation.py` — the TripBrief the chat fills in
- `app/providers/` — one provider per mode, all behind `SegmentProvider`
- `app/services/orchestrator.py` — stitches legs into one trip
- `app/services/geocoding.py` — shared place → coordinates (ORS)
- `app/services/conversation.py` — the LLM layer (Groq)

Key frontend files:
- `lib/api.ts` — TypeScript mirror of the backend schema + API client
- `components/ChatPanel.tsx` — the conversational planner
- `components/TripPlannerForm.tsx` — the manual form
- `components/SegmentCard.tsx` — an itinerary leg

## Prerequisites

- Python 3.11+
- Node.js 18+
- Three free API keys (all no-cost, no credit card):
  - **OpenRouteService** (driving routes + geocoding): https://openrouteservice.org/dev
  - **Groq** (the planning conversation): https://console.groq.com
  - Google Gemini key is no longer required — the conversation now runs on Groq.

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

Create a `.env` file in `backend/` (NOT committed — each person makes their own):

ORS_API_KEY=your_openrouteservice_key
GROQ_API_KEY=your_groq_key


See `backend/.env.example` for the full list.

### Frontend

```bash
cd frontend
npm install
```

Create a `.env.local` file in `frontend/`:

NEXT_PUBLIC_API_URL=http://127.0.0.1:8000


## Running it (two terminals, both at once)

The frontend calls the backend, so both run together.

**Terminal 1 — backend** (run from the `backend/` folder):
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```
Runs at http://127.0.0.1:8000 — interactive API docs at http://127.0.0.1:8000/docs

**Terminal 2 — frontend** (run from the `frontend/` folder):
```bash
cd frontend
npm run dev
```
Runs at http://localhost:3000 — open this in your browser.

> Note: uvicorn must be run from inside `backend/` (so `app.main` resolves),
> with the virtualenv activated (so `uvicorn` is on PATH).

## Travel mode status

| Mode    | Data source                          | Status today            |
|---------|--------------------------------------|-------------------------|
| Driving | OpenRouteService (live routing)      | Live                    |
| Flight  | Distance estimate + Google Flights   | Estimate                |
| Train   | Static timetable (dataset TBD)       | Empty until data loaded |
| Bus     | Distance estimate + redBus link      | Estimate                |

## Important notes

- **Never commit secrets.** `.env` and `.env.local` are gitignored on purpose.
  Each contributor supplies their own keys.
- `.venv/` and `node_modules/` are not committed — regenerated from
  `requirements.txt` and `package.json`.
- The rule that keeps the design extensible: nothing outside
  `app/providers/` imports a concrete provider directly — always go through the
  registry.
- Free LLM tiers have daily request caps. Groq's free tier (~1,000/day) is
  generous for development; if you hit it, it resets daily.

## Roadmap (next up)

- Load a real train timetable dataset
- Budget/city suggestion endpoint (`/trip/suggest`)
- Live flight search (Amadeus)
- Real-time collaboration (Supabase)