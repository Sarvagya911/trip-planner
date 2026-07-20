"""
Places service — finds hotels (and later restaurants) near a destination,
backed by Foursquare Places API.

Uses only free-tier fields (name, location, geocodes) — NOT the Premium
`rating` field, which consumes paid credits. Hotels are sorted by relevance
(proximity), and the frontend notes that ratings aren't shown so users check
reviews on the booking site first.

Behind a simple interface so a different provider (Google Places, etc.)
could be swapped in later without touching the orchestrator. Uses the shared
geocoding service to turn a destination name into coordinates.

Booking is external: each hotel links to a Google search that reliably
surfaces that specific hotel with aggregated booking options.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus

import httpx

from app.models.places import Place
from app.services.geocoding import GeocodingError, get_geocoding_service

FSQ_SEARCH_URL = "https://places-api.foursquare.com/places/search"
FSQ_API_VERSION = "2025-06-17"
HOTEL_CATEGORY_ID = "4bf58dd8d48988d1fa931735"  # Foursquare "Hotel"
SEARCH_RADIUS_M = 8000
DEFAULT_LIMIT = 4


class PlacesService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("FOURSQUARE_API_KEY", "")

    async def find_hotels(self, destination: str, limit: int = DEFAULT_LIMIT) -> list[Place]:
        """Find hotels near a destination. Returns [] on any failure
        (geocoding miss, API error, exhausted credits) rather than raising —
        an enrichment feature must never break the core trip plan."""
        try:
            lon, lat = await get_geocoding_service().geocode(destination)
        except GeocodingError:
            return []

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    FSQ_SEARCH_URL,
                    params={
                        "ll": f"{lat},{lon}",
                        "radius": SEARCH_RADIUS_M,
                        "fsq_category_ids": HOTEL_CATEGORY_ID,
                        "limit": 20,          # over-fetch, we dedupe + trim
                        "sort": "RELEVANCE",
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Places-Api-Version": FSQ_API_VERSION,
                        "accept": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        results = data.get("results", [])
        hotels: list[Place] = []
        seen: set[str] = set()
        for r in results:
            name = (r.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())

            loc = r.get("location", {}) or {}
            address = loc.get("formatted_address") or loc.get("address")
            geo = (r.get("geocodes", {}) or {}).get("main", {}) or {}
            place = Place(
                name=name,
                category="hotel",
                rating=None,  # free tier: no ratings — frontend notes this
                address=address,
                latitude=geo.get("latitude"),
                longitude=geo.get("longitude"),
                book_external_url=_booking_deep_link(name, destination),
            )
            hotels.append(place)
            if len(hotels) >= limit:
                break

        return hotels


def _booking_deep_link(hotel_name: str, destination: str) -> str:
    # Booking.com doesn't offer reliable non-affiliate deep links to a
    # specific hotel — its search URL often lands on the homepage. A Google
    # search for the hotel reliably surfaces that hotel's info panel with
    # booking options aggregated (Booking, MakeMyTrip, Agoda, etc.), which
    # is more robust and gives the user more choice.
    q = quote_plus(f"{hotel_name} {destination} hotel")
    return f"https://www.google.com/search?q={q}"


_default_service: PlacesService | None = None


def get_places_service() -> PlacesService:
    global _default_service
    if _default_service is None:
        _default_service = PlacesService()
    return _default_service