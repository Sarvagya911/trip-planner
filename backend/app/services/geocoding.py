"""
Shared geocoding + distance service.

Both the driving provider and the rough-estimate providers (flight, bus)
need to turn a place name into coordinates. Rather than each one carrying
its own geocoding logic, they share this service. It's built on ORS's
Pelias geocoder (already in use for driving) so there's no new API
dependency.

Results are cached in-memory per process: place names repeat constantly
within a session (the destination of one leg is the origin of the next),
and geocoding the same string twice is wasteful and eats into the ORS
free-tier quota.
"""

from __future__ import annotations

import math
import os

import httpx

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"


class GeocodingError(Exception):
    """Raised when a place name can't be resolved to coordinates."""


class GeocodingService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ORS_API_KEY", "")
        # (lon, lat) keyed by lowercased place name
        self._cache: dict[str, tuple[float, float]] = {}

    async def geocode(self, place_name: str) -> tuple[float, float]:
        """Return (lon, lat) for a place name. Cached per process."""
        key = place_name.strip().lower()
        if key in self._cache:
            return self._cache[key]

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                ORS_GEOCODE_URL,
                params={"api_key": self.api_key, "text": place_name, "size": 1},
            )
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features") or []
        if not features:
            raise GeocodingError(f"could not find coordinates for '{place_name}'")

        coords = features[0]["geometry"]["coordinates"]
        result = (coords[0], coords[1])
        self._cache[key] = result
        return result

    async def distance_km(self, origin: str, destination: str) -> float:
        """Great-circle (straight-line) distance between two place names.

        This is a lower bound on real travel distance — good enough for a
        rough flight/bus estimate, and honestly labeled as an estimate in
        the UI. Driving uses ORS's real road routing instead; this is only
        for modes where we don't have a routing engine."""
        o_lon, o_lat = await self.geocode(origin)
        d_lon, d_lat = await self.geocode(destination)
        return _haversine_km(o_lat, o_lon, d_lat, d_lon)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0  # earth radius km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Shared singleton — one cache for the whole process.
_default_service: GeocodingService | None = None


def get_geocoding_service() -> GeocodingService:
    global _default_service
    if _default_service is None:
        _default_service = GeocodingService()
    return _default_service