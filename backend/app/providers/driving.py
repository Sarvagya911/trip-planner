"""
Driving segment provider, backed by OpenRouteService (ORS) for routing
and the shared geocoding service for place -> coordinates.

Uses the ORS directions POST endpoint (coordinates in the JSON body),
which is the documented, stable way to request a route.

Degrades gracefully: if geocoding fails, or ORS can't route between the
points (e.g. a place resolves to a non-routable spot like a region centroid
off any road), the provider returns [] instead of raising. The orchestrator
then reports an honest "no data for this leg" warning rather than crashing
the whole trip.
"""

from __future__ import annotations

import os
from datetime import date

import httpx

from app.models.segment import CostEstimate, Segment, SegmentStatus, TravelMode
from app.providers.base import PartyComposition, SegmentProvider
from app.services.geocoding import GeocodingError, get_geocoding_service

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
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
            origin_coords = await geo.geocode(origin)      # (lon, lat)
            dest_coords = await geo.geocode(destination)   # (lon, lat)
        except GeocodingError:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    ORS_DIRECTIONS_URL,
                    headers={
                        "Authorization": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "coordinates": [
                            [origin_coords[0], origin_coords[1]],
                            [dest_coords[0], dest_coords[1]],
                        ]
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError:
            # ORS couldn't route between these points (e.g. a place resolved
            # to a non-routable spot). Honest empty result, not a crash.
            return []

        try:
            route = data["routes"][0]
            summary = route["summary"]
            duration_hours = summary["duration"] / 3600
            distance_km = summary["distance"] / 1000
            polyline = route.get("geometry", "")
        except (KeyError, IndexError):
            return []

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
        distance_km = await get_geocoding_service().distance_km(origin, destination)
        return CostEstimate(
            low=distance_km * FUEL_COST_PER_KM_INR * 0.85,
            high=distance_km * FUEL_COST_PER_KM_INR * 1.30,
        )