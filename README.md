# Trip Planner

An all-in-one, conversational, multi-mode trip planner. Describe a trip in
plain language — or fill in a form — and get a single itinerary mixing
driving, flights, and buses, complete with a route map, hotel suggestions,
mid-drive rest stops, and one-tap navigation.

## What it does

- **Chat planning** — tell the assistant where you're starting from, who's
  coming, and the kind of trip you want. It asks follow-ups, suggests
  destinations if you're unsure, and builds a structured plan.
- **Manual planning** — or skip the chat and enter legs directly in a form.
- **Chat replanning** — after a trip is planned, keep talking: "make it
  cheaper," "avoid flights," "I have a dog." The assistant edits the existing
  plan and explains what it changed.
- **Multi-mode, mixed trips** — one itinerary can chain a flight, then a
  drive, then a bus. Each leg is planned by its own provider.
- **Route map** — an interactive map of the driving route with markers for
  origin, destination, and any suggested rest stop.
- **Hotels per destination** — real nearby hotels (Foursquare) with a short
  AI-written note on each, a destination hero photo, and a "find & book" link.
  Ratings aren't shown (see note below) — check reviews before booking.
- **Mid-drive rest stops** — for driving legs over 4 hours, a suggested fuel
  stop and food option near the route's midpoint.
- **Start navigation** — a one-tap link on each driving leg that opens Google
  Maps (or prompts Apple Maps on iOS) with turn-by-turn directions already
  loaded. (Full in-app GPS navigation is a possible future project — see
  Roadmap.)
- **Honest data** — driving uses live OpenRouteService routing; flights/buses
  are distance-based estimates with deep links to book externally.

## Architecture at a glance

A trip is modeled as an **ordered list of segments**, not a fixed origin →
destination. Each travel mode is a provider behind one shared interface, so
new modes or upgrades slot in without touching the orchestrator, the
frontend, or anything else. Enrichment (hotels, photos, rest stops) rides
alongside the trip rather than living inside the Segment schema, keeping
that schema clean and mode-agnostic.

trip-planner/
├── backend/ FastAPI — providers, orchestrator, conversation, APIs
└── frontend/ Next.js (TypeScript + Tailwind) responsive web app


Key backend files:
- `app/models/segment.py` — the core Segment schema (read this first)
- `app/models/conversation.py` — the TripBrief the chat fills in
- `app/models/places.py` — Place / DestinationInfo / RestStop enrichment models
- `app/providers/` — one provider per mode, all behind `SegmentProvider`
- `app/services/orchestrator.py` — stitches legs into one trip, runs enrichment
- `app/services/geocoding.py` — shared place → coordinates (ORS)
- `app/services/conversation.py` — the LLM layer (Groq)
- `app/services/places.py` — Foursquare-backed hotels + fuel/food lookups
- `app/services/destination_photos.py` — Unsplash destination hero photos
- `app/services/hotel_notes.py` — one batched Groq call for hotel "why" lines

Key frontend files:
- `lib/api.ts` — TypeScript mirror of the backend schema + API client
- `components/ChatPanel.tsx` — the conversational planner
- `components/RefinePanel.tsx` — post-plan chat replanning + quick actions
- `components/TripPlannerForm.tsx` — the manual form
- `components/SegmentCard.tsx` — an itinerary leg, with the navigation link
- `components/RestStopStrip.tsx` — the suggested fuel/food stop on a long drive
- `components/RouteMap.tsx` — the Leaflet route map
- `components/WhereToStay.tsx` — destination photo + hotel cards

## Prerequisites

- Python 3.11+
- Node.js 18+
- Four free API keys (all no-cost, no credit card required):
  - **OpenRouteService** (driving routes + geocoding): https://openrouteservice.org/dev
  - **Groq** (the planning conversation): https://console.groq.com
  - **Foursquare** (hotels + fuel/food places): https://foursquare.com/developers
  - **Unsplash** (destination photos): https://unsplash.com/developers

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
FOURSQUARE_API_KEY=your_foursquare_key
UNSPLASH_ACCESS_KEY=your_unsplash_key


See `backend/.env.example` for the current list — it also notes a couple of
keys planned for future features that aren't used yet, so don't worry about
signing up for those.

### Frontend

```bash
cd frontend
npm install
```

Create a `.env.local` file in `frontend/`:

NEXT_PUBLIC_API_URL=http://127.0.0.1:8002


## Running it (two terminals, both at once)

The frontend calls the backend, so both run together.

**Terminal 1 — backend** (run from the `backend/` folder):
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```
Runs at http://127.0.0.1:8002 — interactive API docs at http://127.0.0.1:8002/docs

> **Why port 8002, not the default 8000?** Some network security software
> (e.g. Sophos, common on school/managed devices) intercepts or blocks
> port 8000 for local traffic, which looks like a CORS error or an endless
> hang in the browser. Port 8002 sidesteps it. If you don't have that
> problem, 8000 works fine too — just make sure the port in this command
> matches `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.

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
|---------|---------------------------------------|--------------------------|
| Driving | OpenRouteService (live routing)      | Live                     |
| Flight  | Distance estimate + Google Flights   | Estimate                 |
| Bus     | Distance estimate + redBus link      | Estimate                 |
| Train   | No timetable data source yet         | Disabled (see Roadmap)   |

## Important notes

- **Never commit secrets.** `.env` and `.env.local` are gitignored on purpose.
  Each contributor supplies their own keys.
- `.venv/` and `node_modules/` are not committed — regenerated from
  `requirements.txt` and `package.json`.
- The rule that keeps the design extensible: nothing outside
  `app/providers/` imports a concrete provider directly — always go through
  the registry.
- Hotel **ratings are intentionally not shown**. Foursquare's free tier only
  includes ratings as a paid ("Premium") field; rather than pay for that or
  have an LLM guess at a rating (which would be a fabricated number), the app
  shows real hotel names/locations/notes and tells the user to check reviews
  on the booking site. Same reasoning kept us off Google Places for hotel
  photos — we use free Unsplash destination photos instead, which are
  honestly generic rather than misleadingly specific.
- Free LLM tiers have daily request caps. Groq's free tier (~1,000/day) is
  generous for development; if you hit it, it resets daily.

## Roadmap (next up)

- Cohesive UI redesign over the full feature set
- Persistence (Supabase/Postgres) — save trips, enables real-time collaboration
- Load a real train timetable dataset, re-enable train legs
- Restaurant suggestions at destinations (same pattern as hotels)
- Live flight search (Amadeus) — not yet integrated, key not required today
- Full in-app GPS turn-by-turn navigation — a substantial future project in
  its own right (continuous location, live rerouting, voice guidance); the
  realistic near-term version is today's "Start navigation" handoff to
  Google/Apple Maps