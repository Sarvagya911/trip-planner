"""
Places service — finds hotels near a destination, and fuel/food near a point
along a route, backed by Foursquare Places API.

Uses only free-tier fields (name, location, geocodes) — NOT the Premium
`rating` or `price` fields, which consume paid credits.
Behind a simple interface so a different provider (Google Places, etc.)
could be swapped in later without touching the orchestrator.

Budget filtering: Foursquare's free tier has no price field, and biasing
the search QUERY text toward "budget"/"affordable" proved unreliable in
testing — its relevance ranking still surfaces prominent luxury chains
(Marriott, Taj) regardless of the extra keywords. Instead, when a low
budget is given, results are POST-FILTERED by real hotel brand name: known
luxury chains are excluded, known budget chains are boosted to the front.
This is a deterministic, honest signal (real, publicly-known brand market
positioning) rather than hoping search relevance cooperates.

Hotels link to a dated Booking.com search (check-in/check-out are required
for Booking.com to actually run a search rather than show its homepage).
Fuel/food link to a Google search, which reliably surfaces the specific
place.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from urllib.parse import quote_plus

import httpx

from app.models.places import Place
from app.services.geocoding import GeocodingError, get_geocoding_service

FSQ_SEARCH_URL = "https://places-api.foursquare.com/places/search"
FSQ_API_VERSION = "2025-06-17"

HOTEL_CATEGORY_ID = "4bf58dd8d48988d1fa931735"   # Hotel
FUEL_CATEGORY_ID = "4bf58dd8d48988d113951735"    # Gas / fuel station
FOOD_CATEGORY_ID = "4d4b7105d754a06374d81259"    # Food (top-level dining)

HOTEL_RADIUS_M = 8000
STOP_RADIUS_M = 15000
DEFAULT_LIMIT = 4

# Real, publicly-known luxury hotel brands — excluded when a low budget is
# given. Matched case-insensitively as a substring of the venue name.
LUXURY_BRANDS = [
    "taj", "oberoi", "leela", "itc", "jw marriott", "marriott", "sheraton",
    "hyatt regency", "grand hyatt", "park hyatt", "ritz-carlton", "ritz carlton",
    "four seasons", "st regis", "conrad", "waldorf", "shangri-la", "shangri la",
    "trident", "westin", "le meridien", "intercontinental",
]

# Real, publicly-known budget hotel chains in India — moved to the front of
# results when a low budget is given.
BUDGET_BRANDS = [
    "oyo", "fabhotel", "fabhotels", "treebo", "ginger", "spot on", "spoton",
    "collection o", "zostel", "backpacker", "hostel", "lodge", "guest house",
    "guesthouse",
]

# Below this per-night budget, apply the brand filter/boost.
BUDGET_FILTER_THRESHOLD_INR = 4000


class PlacesService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("FOURSQUARE_API_KEY", "")

    async def find_hotels(
        self,
        destination: str,
        limit: int = DEFAULT_LIMIT,
        depart_date: date | None = None,
        pet_friendly: bool = False,
        budget_inr: int | None = None,
    ) -> list[Place]:
        """Find hotels near a destination. Returns [] on failure.

        `pet_friendly` biases the search query text (a mild, tolerable soft
        signal). `budget_inr` below BUDGET_FILTER_THRESHOLD_INR triggers a
        deterministic post-filter by known hotel brand name — see module
        docstring for why this replaced query-text budget biasing.
        """
        try:
            lon, lat = await get_geocoding_service().geocode(destination)
        except GeocodingError:
            return []

        apply_budget_filter = budget_inr is not None and budget_inr <= BUDGET_FILTER_THRESHOLD_INR
        query = "pet friendly hotel" if pet_friendly else None
        # Over-fetch when budget-filtering, since some results get excluded.
        raw_limit = 20 if apply_budget_filter else 10

        results = await self._search(
            lat, lon, HOTEL_CATEGORY_ID, HOTEL_RADIUS_M, query=query, raw_limit=raw_limit
        )

        candidates: list[Place] = []
        seen: set[str] = set()
        for r in results:
            name = (r.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            loc = r.get("location", {}) or {}
            geo = (r.get("geocodes", {}) or {}).get("main", {}) or {}
            candidates.append(Place(
                name=name,
                category="hotel",
                rating=None,
                address=loc.get("formatted_address") or loc.get("address"),
                latitude=geo.get("latitude"),
                longitude=geo.get("longitude"),
                book_external_url=_booking_link(name, destination, depart_date),
            ))

        if apply_budget_filter:
            candidates = _filter_and_rank_for_budget(candidates)

        return candidates[:limit]

    async def find_one_near(self, lat: float, lon: float, category: str) -> Place | None:
        """Find the single nearest place of a category to a coordinate.
        Used for fuel/food along a route. Returns None on failure/none-found."""
        cat_id = FUEL_CATEGORY_ID if category == "fuel" else FOOD_CATEGORY_ID
        results = await self._search(lat, lon, cat_id, STOP_RADIUS_M, sort="DISTANCE")
        for r in results:
            name = (r.get("name") or "").strip()
            if not name:
                continue
            loc = r.get("location", {}) or {}
            geo = (r.get("geocodes", {}) or {}).get("main", {}) or {}
            addr = loc.get("formatted_address") or loc.get("address")
            return Place(
                name=name,
                category=category,
                rating=None,
                address=addr,
                latitude=geo.get("latitude"),
                longitude=geo.get("longitude"),
                book_external_url=_google_find_link(name, addr or ""),
            )
        return None

    async def _search(
        self,
        lat: float,
        lon: float,
        cat_id: str,
        radius: int,
        sort: str = "RELEVANCE",
        query: str | None = None,
        raw_limit: int = 10,
    ) -> list[dict]:
        """Raw Foursquare search. Returns [] on any error (best-effort)."""
        params = {
            "ll": f"{lat},{lon}",
            "radius": radius,
            "fsq_category_ids": cat_id,
            "limit": raw_limit,
            "sort": sort,
        }
        if query:
            params["query"] = query
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    FSQ_SEARCH_URL,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Places-Api-Version": FSQ_API_VERSION,
                        "accept": "application/json",
                    },
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except httpx.HTTPError:
            return []


def _filter_and_rank_for_budget(candidates: list[Place]) -> list[Place]:
    """Excludes known luxury brands entirely, then sorts so known budget
    brands come first. Anything not matching either list stays in the
    middle, unranked — we don't know its price tier either way, so it's
    neither excluded nor prioritized."""
    kept = [c for c in candidates if not _matches_any(c.name, LUXURY_BRANDS)]

    def sort_key(place: Place) -> int:
        return 0 if _matches_any(place.name, BUDGET_BRANDS) else 1

    kept.sort(key=sort_key)
    return kept


def _matches_any(name: str, brands: list[str]) -> bool:
    lowered = name.lower()
    return any(brand in lowered for brand in brands)


def _booking_link(hotel_name: str, destination: str, depart_date: date | None) -> str:
    """Booking.com requires check-in/check-out dates to run an actual
    search rather than show its homepage. Defaults to a 1-night stay
    starting at the trip's departure date if no return date is known."""
    checkin = depart_date or (date.today() + timedelta(days=7))
    checkout = checkin + timedelta(days=1)
    q = quote_plus(f"{hotel_name} {destination}")
    return (
        f"https://www.booking.com/searchresults.html?ss={q}"
        f"&checkin={checkin.isoformat()}&checkout={checkout.isoformat()}"
        f"&group_adults=2&no_rooms=1"
    )


def _google_find_link(name: str, context: str) -> str:
    q = quote_plus(f"{name} {context}".strip())
    return f"https://www.google.com/search?q={q}"


_default_service: PlacesService | None = None


def get_places_service() -> PlacesService:
    global _default_service
    if _default_service is None:
        _default_service = PlacesService()
    return _default_service