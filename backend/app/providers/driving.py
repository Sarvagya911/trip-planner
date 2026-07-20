"""
Driving segment provider, backed by OpenRouteService (ORS) for routing
and the shared geocoding service for place -> coordinates.

Kept behind the SegmentProvider interface so it can be swapped for a
self-hosted OSRM instance later purely by writing a new class and
re-registering it — nothing else changes.
"""

from __future__ import annotations

import os
from datetime import date

import httpx

from app.models.segment import CostEstimate, Segment, SegmentStatus, TravelMode
from app.providers.base import PartyComposition, SegmentProvider
from app.services.geocoding import GeocodingError, get_geocoding_service

ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
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
        geo = get_geocoding_service()
        try:
            origin_coords = await geo.geocode(origin)
            dest_coords = await geo.geocode(destination)
        except GeocodingError:
            return []

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
                order=1,
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
        # Cheap path for the budget/suggestion step: straight-line distance
        # times a fuel heuristic, no full routing call.
        distance_km = await get_geocoding_service().distance_km(origin, destination)
        return CostEstimate(
            low=distance_km * FUEL_COST_PER_KM_INR * 0.85,
            high=distance_km * FUEL_COST_PER_KM_INR * 1.30,
        )