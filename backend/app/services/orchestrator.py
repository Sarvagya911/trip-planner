"""
Trip orchestrator: takes an ordered list of legs, calls the right provider
for each via the registry, stitches them into one TripSegments, and enriches
the trip — hotels per destination, and rest/fuel/food stops on long drives.

It never imports a concrete provider directly — only the registry.

All enrichment is best-effort: it runs after the legs are built, and any
failure there never breaks the core plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.places import DestinationInfo, RestStop
from app.models.segment import Segment, TravelMode, TripSegments
from app.providers.base import PartyComposition
from app.providers.registry import ProviderRegistry
from app.services.geocoding import GeocodingError, get_geocoding_service
from app.services.hotel_notes import annotate_hotels
from app.services.places import get_places_service

# A driving leg longer than this earns a suggested rest stop.
LONG_DRIVE_HOURS = 4.0


@dataclass
class LegRequest:
    mode: TravelMode
    origin: str
    destination: str


@dataclass
class TripPlanResult:
    trip: TripSegments
    warnings: list[str] = field(default_factory=list)
    destination_info: list[DestinationInfo] = field(default_factory=list)


class TripOrchestrator:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def plan_trip(
        self,
        legs: list[LegRequest],
        depart_date: date,
        party: PartyComposition,
        include_hotels: bool = True,
    ) -> TripPlanResult:
        if not legs:
            raise ValueError("a trip must have at least one leg")

        segments: list[Segment] = []
        warnings: list[str] = []

        for i, leg in enumerate(legs, start=1):
            provider = self.registry.get(leg.mode)
            candidates = await provider.search(leg.origin, leg.destination, depart_date, party)
            if not candidates:
                warnings.append(
                    f"leg {i} ({leg.mode.value}: {leg.origin} -> {leg.destination}): "
                    f"no data found, omitted from trip"
                )
                continue
            chosen = candidates[0]
            chosen.order = i
            segments.append(chosen)

        if not segments:
            raise ValueError("no data could be found for any leg of this trip")

        for idx, seg in enumerate(segments, start=1):
            seg.order = idx

        warnings.extend(self._check_continuity(segments))

        # Enrichment (best-effort).
        await self._add_rest_stops(segments)

        destination_info: list[DestinationInfo] = []
        if include_hotels:
            destination_info = await self._enrich_destinations(segments)

        return TripPlanResult(
            trip=TripSegments(segments=segments),
            warnings=warnings,
            destination_info=destination_info,
        )

    async def _add_rest_stops(self, segments: list[Segment]) -> None:
        """For each long driving leg, find a fuel + food option near the
        route midpoint and attach it to the segment's provider_data['stop'].
        Best-effort: silently skips on any failure."""
        geo = get_geocoding_service()
        places = get_places_service()
        for seg in segments:
            if seg.mode != TravelMode.DRIVING:
                continue
            if (seg.duration_hours_estimate or 0) < LONG_DRIVE_HOURS:
                continue
            try:
                o_lon, o_lat = await geo.geocode(seg.origin)
                d_lon, d_lat = await geo.geocode(seg.destination)
            except GeocodingError:
                continue
            mid_lat = (o_lat + d_lat) / 2
            mid_lon = (o_lon + d_lon) / 2

            fuel = await places.find_one_near(mid_lat, mid_lon, "fuel")
            food = await places.find_one_near(mid_lat, mid_lon, "food")
            if not fuel and not food:
                continue

            stop = RestStop(
                label="Around the halfway point",
                near_latitude=mid_lat,
                near_longitude=mid_lon,
                fuel=fuel,
                food=food,
            )
            # Attach without touching the Segment schema: ride in provider_data.
            seg.provider_data["stop"] = stop.model_dump()

    async def _enrich_destinations(self, segments: list[Segment]) -> list[DestinationInfo]:
        home = segments[0].origin.strip().lower()
        seen: set[str] = set()
        destinations: list[str] = []
        for s in segments:
            d = s.destination.strip()
            key = d.lower()
            if key in seen or key == home:
                continue
            seen.add(key)
            destinations.append(d)

        places = get_places_service()
        hotels_by_dest: dict[str, list] = {}
        for dest in destinations:
            hotels = await places.find_hotels(dest)
            if hotels:
                hotels_by_dest[dest] = hotels

        if not hotels_by_dest:
            return []

        try:
            await annotate_hotels(hotels_by_dest)
        except Exception:
            pass

        return [
            DestinationInfo(destination=dest, hotels=hotels)
            for dest, hotels in hotels_by_dest.items()
        ]

    def _check_continuity(self, segments: list[Segment]) -> list[str]:
        warnings = []
        for a, b in zip(segments, segments[1:]):
            if a.destination.strip().lower() not in b.origin.strip().lower() and \
               b.origin.strip().lower() not in a.destination.strip().lower():
                warnings.append(
                    f"possible gap between leg {a.order} destination "
                    f"('{a.destination}') and leg {b.order} origin ('{b.origin}') — "
                    f"verify these connect"
                )
        return warnings


# TODO (future work):
#   - Multiple stops on very long drives (every ~2.5h) instead of one midpoint
#   - Per-leg departure dates
#   - Restaurant enrichment at destinations