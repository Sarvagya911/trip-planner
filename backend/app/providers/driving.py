"""
Driving segment provider, backed by OpenRouteService (ORS).

ORS is free-tier and OSM-based. Kept behind the SegmentProvider interface
so it can be swapped for a self-hosted OSRM instance later purely by
writing a new class and re-registering it — nothing else changes.
"""

from __future__ import annotations

import os
from datetime import date

import httpx

from app.models.segment import CostEstimate, Segment, SegmentStatus, TravelMode
from app.providers.base import PartyComposition, SegmentProvider

ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
# Rough fuel-cost heuristic for cost estimation before a live route is fetched.
FUEL_COST_PER_KM_INR = 8.0


class DrivingProvider(SegmentProvider):
    mode = TravelMode.DRIVING

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ORS_API_KEY", "")

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        party: PartyComposition,
    ) -> list[Segment]:
        origin_coords = await self._geocode(origin)
        dest_coords = await self._geocode(destination)

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                ORS_BASE_URL,
                params={
                    "api_key": self.api_key,
                    "start": f"{origin_coords[0]},{origin_coords[1]}",
                    "end": f"{dest_coords[0]},{dest_coords[1]}",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        route = data["features"][0]
        summary = route["properties"]["summary"]
        duration_hours = summary["duration"] / 3600
        distance_km = summary["distance"] / 1000
        polyline = route["geometry"]

        cost = CostEstimate(
            low=distance_km * FUEL_COST_PER_KM_INR * 0.85,
            high=distance_km * FUEL_COST_PER_KM_INR * 1.15,
        )

        return [
            Segment(
                order=1,  # caller (orchestrator) reassigns real order in the full trip
                mode=self.mode,
                status=SegmentStatus.ROUGH_ESTIMATE,
                provider="ors",
                origin=origin,
                destination=destination,
                duration_hours_estimate=round(duration_hours, 2),
                cost=cost,
                provider_data={
                    "route_polyline": polyline,
                    "distance_km": round(distance_km, 1),
                },
            )
        ]

    async def estimate_cost(
        self,
        origin: str,
        destination: str,
        party: PartyComposition,
    ) -> CostEstimate:
        # Cheap path for the budget/suggestion step: avoid a full directions
        # call, use a straight-line-distance-based heuristic instead.
        # A real implementation would use a distance matrix endpoint;
        # stubbed here since exact behavior depends on the geocoding provider.
        raise NotImplementedError("wire up ORS matrix API or a geocoding-based haversine estimate")

    async def _geocode(self, place_name: str) -> tuple[float, float]:
        """Returns (lon, lat). Uses ORS's own geocoding endpoint (Pelias-based)
        so we don't add a second provider dependency just for geocoding."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.openrouteservice.org/geocode/search",
                params={"api_key": self.api_key, "text": place_name, "size": 1},
            )
            resp.raise_for_status()
            data = resp.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        return coords[0], coords[1]