"""
Places service — finds hotels near a destination, and fuel/food near a point
along a route, backed by Foursquare Places API.

Uses only free-tier fields (name, location, geocodes) — NOT the Premium
`rating` or `price` fields, which consume paid credits.

Behind a simple interface so a different provider (Google Places, etc.)
could be swapped in later without touching the orchestrator.

Hotels link to a dated Booking.com search (check-in/check-out are required
for Booking.com to actually run a search rather than show its homepage).
Fuel/food link to a Google search, which reliably surfaces the specific
place. Budget and pet-friendliness aren't real Foursquare filters (no
free-tier price field, no pets attribute) — both are applied as a soft
search-query bias instead, never a fabricated hard filter.
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

        `pet_friendly` and `budget_inr` bias the Foursquare search query
        toward matching stays — a soft signal, not a guaranteed filter,
        since Foursquare's free tier has no pets-allowed or price attribute
        to filter on directly.
        """
        try:
            lon, lat = await get_geocoding_service().geocode(destination)
        except GeocodingError:
            return []

        terms = []
        if budget_inr is not None:
            # Rough per-night budget banding for Indian hotel search terms.
            if budget_inr < 2000:
                terms.append("budget hotel")
            elif budget_inr < 5000:
                terms.append("affordable hotel")
            # Above that, no bias needed — default search already covers it.
        if pet_friendly:
            terms.append("pet friendly")
        query = " ".join(terms) + " hotel" if terms else None

        results = await self._search(lat, lon, HOTEL_CATEGORY_ID, HOTEL_RADIUS_M, query=query)

        hotels: list[Place] = []
        seen: set[str] = set()
        for r in results:
            name = (r.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            loc = r.get("location", {}) or {}
            geo = (r.get("geocodes", {}) or {}).get("main", {}) or {}
            hotels.append(Place(
                name=name,
                category="hotel",
                rating=None,
                address=loc.get("formatted_address") or loc.get("address"),
                latitude=geo.get("latitude"),
                longitude=geo.get("longitude"),
                book_external_url=_booking_link(name, destination, depart_date),
            ))
            if len(hotels) >= limit:
                break
        return hotels

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
    ) -> list[dict]:
        """Raw Foursquare search. Returns [] on any error (best-effort)."""
        params = {
            "ll": f"{lat},{lon}",
            "radius": radius,
            "fsq_category_ids": cat_id,
            "limit": 10,
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