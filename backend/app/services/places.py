"""
Places service — finds hotels near a destination, and fuel/food near a point
along a route, backed by Foursquare Places API.

Uses only free-tier fields (name, location, geocodes) — NOT the Premium
`rating` field, which consumes paid credits.

Behind a simple interface so a different provider (Google Places, etc.)
could be swapped in later without touching the orchestrator.

Finding is external: places link to a Google search that reliably surfaces
the specific place with map/booking options.
"""

from __future__ import annotations

import os
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

    async def find_hotels(self, destination: str, limit: int = DEFAULT_LIMIT) -> list[Place]:
        """Find hotels near a destination (by name). Returns [] on failure."""
        try:
            lon, lat = await get_geocoding_service().geocode(destination)
        except GeocodingError:
            return []
        results = await self._search(lat, lon, HOTEL_CATEGORY_ID, HOTEL_RADIUS_M)
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
                book_external_url=_google_find_link(name, destination),
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

    async def _search(self, lat: float, lon: float, cat_id: str, radius: int, sort: str = "RELEVANCE") -> list[dict]:
        """Raw Foursquare search. Returns [] on any error (best-effort)."""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    FSQ_SEARCH_URL,
                    params={
                        "ll": f"{lat},{lon}",
                        "radius": radius,
                        "fsq_category_ids": cat_id,
                        "limit": 10,
                        "sort": sort,
                    },
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


def _google_find_link(name: str, context: str) -> str:
    q = quote_plus(f"{name} {context}".strip())
    return f"https://www.google.com/search?q={q}"


_default_service: PlacesService | None = None


def get_places_service() -> PlacesService:
    global _default_service
    if _default_service is None:
        _default_service = PlacesService()
    return _default_service