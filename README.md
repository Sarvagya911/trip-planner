# Trip Planner

An all-in-one, conversational, multi-mode trip planner. Describe a trip in
plain language — or fill in a form — and get a full itinerary with a route
map, a cinematic journey view, hotel suggestions, mid-drive rest stops, and
a whole-trip budget estimate, across a proper multi-page site.

## Pages

- **`/`** — cinematic marketing home page (video hero, scroll-reveal feature highlights)
- **`/features`** — a deeper walkthrough of everything the app does
- **`/plan`** — the actual planner (chat or manual entry, the itinerary, everything below)

## What it does

- **Chat planning** — tell the assistant where you're starting from, who's
  coming, and the kind of trip you want. It asks follow-ups, suggests
  destinations if you're unsure, and builds a structured plan.
- **Manual planning** — or skip the chat and enter legs directly in a form,
  including an optional budget.
- **Chat replanning** — after a trip is planned, keep talking: "make it
  cheaper," "avoid flights," "I have a dog." The assistant edits the existing
  plan and explains what it changed.
- **Multi-mode, mixed trips** — one itinerary can chain a flight, then a
  drive, then a bus. Each leg is planned by its own provider.
- **Cinematic journey hero** — a scenic looping video matched to your current
  leg's mode (driving/flight/bus/train), with a progress indicator estimated
  from your planned schedule (not live GPS — see note below).
- **Route map** — an interactive map of the driving route with markers for
  origin, destination, and any suggested rest stop.
- **Hotels per destination** — real nearby hotels (Foursquare) with a short
  AI-written note, a destination hero photo, and a dated Booking.com link.
  When a low budget is stated, known luxury chains (Taj, Marriott, Oberoi,
  etc.) are excluded and known budget chains (OYO, Treebo, etc.) are
  prioritized — see the budget note below for the full picture. Ratings
  aren't shown — check reviews on the booking site before you book.
- **Mid-drive rest stops** — for driving legs over 4 hours, a suggested fuel
  stop and food option near the route's midpoint, each with a rough cost
  estimate.
- **Whole-trip budget estimate** — a summary card showing the itinerary's
  real travel cost alongside regional per-night/per-day estimates for stay,
  food, and local transport, scaled proportionally to your stated budget.
  Flags when travel cost alone already exceeds what you said you'd spend.
- **Start navigation** — a one-tap link on each driving leg that opens Google
  Maps (or prompts Apple Maps on iOS) with turn-by-turn directions already
  loaded.
- **Honest data** — driving uses live OpenRouteService routing; flights/buses
  are distance-based estimates with deep links to book externally.

## Architecture at a glance

A trip is modeled as an **ordered list of segments**, not a fixed origin →
destination. Each travel mode is a provider behind one shared interface, so
new modes or upgrades slot in without touching the orchestrator, the
frontend, or anything else. Enrichment (hotels, photos, rest stops, budget)
rides alongside the trip rather than living inside the Segment schema.

trip-planner/
├── backend/ FastAPI — providers, orchestrator, conversation, APIs
└── frontend/ Next.js (TypeScript + Tailwind) — home, features, and the planner


Key backend files:
- `app/models/segment.py` — the core Segment schema (read this first)
- `app/models/conversation.py` — the TripBrief the chat fills in
- `app/models/places.py` — Place / DestinationInfo / RestStop / TripBudgetEstimate models
- `app/providers/` — one provider per mode, all behind `SegmentProvider`
- `app/services/orchestrator.py` — stitches legs into one trip, runs enrichment
- `app/services/geocoding.py` — shared place → coordinates (ORS)
- `app/services/conversation.py` — the LLM layer (Groq)
- `app/services/places.py` — Foursquare-backed hotels + fuel/food lookups,
  including the brand-based budget filter (see note below)
- `app/services/budget_estimate.py` — whole-trip budget summary computation
- `app/services/destination_photos.py` — Unsplash photo lookup (destination hero + scenic backgrounds)
- `app/services/journey_videos.py` — Pixabay-backed scenic video per travel mode
- `app/services/hotel_notes.py` — one batched Groq call for hotel "why" lines

Key frontend files:
- `app/page.tsx` — the marketing home page
- `app/features/page.tsx` — the features page
- `app/plan/page.tsx` — the actual planner
- `lib/api.ts` — TypeScript mirror of the backend schema + API client
- `components/Nav.tsx` — site navigation (transparent-to-solid on scroll on home)
- `components/ChatPanel.tsx` — the conversational planner
- `components/RefinePanel.tsx` — post-plan chat replanning + quick actions
- `components/TripPlannerForm.tsx` — the manual form (includes budget)
- `components/SegmentCard.tsx` — an itinerary leg, with the navigation link
- `components/RestStopStrip.tsx` — the suggested fuel/food stop with cost estimates
- `components/RouteMap.tsx` — the Leaflet route map
- `components/JourneyHero.tsx` — the cinematic journey progress hero
- `components/WhereToStay.tsx` — destination photo + hotel cards
- `components/BudgetSummary.tsx` — the whole-trip budget estimate card

## Prerequisites

- Python 3.11+
- Node.js 18+
- Five free API keys (all no-cost, no credit card required):
  - **OpenRouteService** (driving routes + geocoding): https://openrouteservice.org/dev
  - **Groq** (the planning conversation): https://console.groq.com
  - **Foursquare** (hotels + fuel/food places): https://foursquare.com/developers
  - **Unsplash** (destination + scenic background photos): https://unsplash.com/developers
  - **Pixabay** (scenic journey-hero videos): https://pixabay.com/api/docs (key shown right on that page after signup)

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
PIXABAY_API_KEY=your_pixabay_key


See `backend/.env.example` for the current list — it also notes a couple of
keys planned for future features that aren't used yet.

### Frontend

```bash
cd frontend
npm install
```

No `.env.local` needed for the API URL — see the note on the Next.js proxy
below.

## Running it (two terminals, both at once)

**Terminal 1 — backend** (run from the `backend/` folder):
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8004
```

**Terminal 2 — frontend** (run from the `frontend/` folder):
```bash
cd frontend
npm run dev
```
Runs at http://localhost:3000 — open this in your browser. The frontend
proxies API calls to the backend internally (see below), so this is the
only URL you need to visit.

> Note: uvicorn must be run from inside `backend/` (so `app.main` resolves),
> with the virtualenv activated (so `uvicorn` is on PATH).

### A note on the backend port and the Next.js proxy

Some network security software (e.g. Sophos, common on school/managed
devices) blocks or intercepts direct browser → localhost connections on
certain ports, which looks like a CORS error or an endless hang. We hit this
enough times, on enough different ports (8000, then 8002, then 8003), to
build a permanent architectural fix rather than keep changing numbers:
**the frontend proxies all `/api/*` calls to the backend internally**, via a
`rewrites()` rule in `frontend/next.config.ts`. The browser only ever talks
to `localhost:3000`; Next.js's own server forwards requests to the backend
port behind the scenes (a server-to-server hop that network filters
watching browser traffic never see). This also eliminates CORS entirely,
since everything is same-origin from the browser's point of view.

**If the backend port ever needs to change again** (blocked, or just in
use), update it in exactly two places, both required:
1. The `uvicorn --port` flag when starting the backend
2. The `destination` URL inside `rewrites()` in `frontend/next.config.ts`

After changing either, do a full frontend restart (not just hot-reload):
`Remove-Item -Recurse -Force .next` then `npm run dev` — Next.js config
changes aren't picked up by hot-reload. Also confirm `frontend/lib/api.ts`
has `const API_BASE_URL = "";` (empty string) — if it ever gets reset to a
hardcoded `http://127.0.0.1:PORT`, the proxy is bypassed and the port-block
problem comes back.

## Travel mode status

| Mode    | Data source                          | Status today            |
|---------|---------------------------------------|--------------------------|
| Driving | OpenRouteService (live routing)      | Live                     |
| Flight  | Distance estimate + Google Flights   | Estimate                 |
| Bus     | Distance estimate + redBus link      | Estimate                 |
| Train   | No timetable data source yet         | Disabled (see Roadmap)   |

## Important notes

- **Never commit secrets.** `.env` is gitignored on purpose. Each
  contributor supplies their own keys.
- `.venv/` and `node_modules/` are not committed — regenerated from
  `requirements.txt` and `package.json`.
- The rule that keeps the design extensible: nothing outside
  `app/providers/` imports a concrete provider directly — always go through
  the registry.
- **Hotel ratings are intentionally not shown.** Foursquare's free tier only
  includes ratings as a paid ("Premium") field; rather than pay for that or
  have an LLM guess at a rating (a fabricated number), the app shows real
  hotel names/locations/notes and tells the user to check reviews on the
  booking site.
- **Hotel budget filtering is a real, deterministic brand-name filter — not
  a price filter.** We tried biasing the Foursquare search QUERY text
  ("budget hotel," etc.) first; it proved unreliable, still surfacing
  luxury chains regardless. What actually works: known luxury brands (Taj,
  Marriott, Oberoi, ITC, Leela, and others — see `LUXURY_BRANDS` in
  `places.py`) are excluded outright when a low budget is stated, and known
  budget chains (OYO, Treebo, Ginger, and others — see `BUDGET_BRANDS`) are
  boosted to the front. This catches named chains reliably; an independent
  or boutique hotel with no recognizable brand name is invisible to this
  filter either way, since there's still no real price data behind it.
- **The whole-trip budget estimate scales proportionally to your stated
  budget**, not fixed brackets — e.g. stay/night is roughly 12.5–25% of the
  total trip budget, with a floor so very low budgets don't collapse to an
  unrealistic number. Travel cost is a real total from the planned
  itinerary; stay/food/local are regional per-unit estimates, deliberately
  not multiplied into a fake grand total since trip length (nights) isn't
  reliably tracked yet.
- **Booking.com hotel links include real check-in/check-out dates** (using
  the trip's departure date, defaulting to a 1-night stay), required for
  Booking.com to run an actual search rather than show its homepage. A
  specific hotel — especially budget listings like OYO properties, which
  often don't resolve cleanly in Booking's public search — can still land
  on an error/homepage instead of that exact listing. This is a limitation
  of the public search form; a reliable fix needs Booking's Partner API
  (a business approval process), not pursued here to stay free-tier.
- **Real-time flight/hotel pricing is not available on any free data
  source we found.** We evaluated and ruled out, in order: Foursquare's
  `price` field (Premium/paid), Google Places (needs a billing account),
  and Amadeus's Self-Service flight API (its free sandbox tier was
  decommissioned July 17, 2026, now enterprise-only). This is a hard
  ceiling of free-tier data, not a bug — see Roadmap for what a real fix
  would require.
- **The journey hero's progress is schedule-based, not live GPS.** It
  calculates elapsed time against your trip's planned departure and each
  leg's estimated duration, updating periodically — clearly not the same as
  knowing your actual position. Full in-app GPS navigation is a real
  possible future project (see Roadmap) but a substantially larger one.
- Free LLM tiers have daily request caps. Groq's free tier (~1,000/day) is
  generous for development; if you hit it, it resets daily.

## Roadmap (next up)

- Finish the visual redesign pass on `RefinePanel` and any remaining
  light-theme components
- Persistence (Supabase/Postgres) — save trips, enables real-time collaboration
- Load a real train timetable dataset, re-enable train legs
- Restaurant suggestions at destinations (same pattern as hotels)
- Track trip length (nights) so the budget estimate can show a real total,
  not just per-night/per-day bands
- Real hotel/flight pricing — needs a paid data source (Google Places with
  a capped budget, or a Booking.com/flights Partner API); every free
  option we could find has been ruled out (see notes above) — deliberately
  deferred, a real decision to revisit rather than a gap to keep patching
- Full in-app GPS turn-by-turn navigation — a substantial future project in
  its own right (continuous location, live rerouting, voice guidance); the
  realistic near-term version is today's "Start navigation" handoff to
  Google/Apple Maps