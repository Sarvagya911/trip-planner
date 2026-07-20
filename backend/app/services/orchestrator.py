"""
Trip orchestrator: takes an ordered list of legs (each with its own mode,
origin, destination) and calls the right provider for each one via the
registry, producing one stitched TripSegments — and now also enriches the
trip's destinations with hotel suggestions.

This is intentionally the ONLY place that knows how to go from "a list of
legs the user wants" to "a validated multi-segment trip." It never imports
a concrete provider directly — only the registry.

Destination enrichment (hotels) is best-effort: it runs after the legs are
built, and any failure there never breaks the core plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.places import DestinationInfo
from app.models.segment import Segment, TravelMode, TripSegments
from app.providers.base import PartyComposition
from app.providers.registry import ProviderRegistry
from app.services.hotel_notes import annotate_hotels
from app.services.places import get_places_service


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

        destination_info: list[DestinationInfo] = []
        if include_hotels:
            destination_info = await self._enrich_destinations(segments)

        return TripPlanResult(
            trip=TripSegments(segments=segments),
            warnings=warnings,
            destination_info=destination_info,
        )

    async def _enrich_destinations(self, segments: list[Segment]) -> list[DestinationInfo]:
        """Find hotels for each distinct destination in the trip, then batch-
        annotate them with a short 'why' via one Groq call. Best-effort:
        returns whatever succeeds, never raises."""
        # The trip's starting point (first leg's origin) is "home" — don't
        # suggest hotels there. Every other distinct destination is fair game,
        # including a place you return from on a round trip.
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

        # One batched Groq call to add "why stay here" lines.
        try:
            await annotate_hotels(hotels_by_dest)
        except Exception:
            pass  # best-effort flavor; hotels still returned without notes

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


# TODO (future work, not done here):
#   - Per-leg departure dates instead of one shared date across the whole trip
#   - Restaurant enrichment (same pattern as hotels)
#   - Mid-drive rest/fuel/food stops for long driving legs