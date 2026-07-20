"""
Trip orchestrator: takes an ordered list of legs (each with its own mode,
origin, destination) and calls the right provider for each one via the
registry, producing one stitched TripSegments.

This is intentionally the ONLY place that knows how to go from "a list of
legs the user wants" to "a validated multi-segment trip." It never imports
a concrete provider directly — only the registry.

Known simplification for this version (flagged, not hidden): all legs
currently share one depart_date. Per-leg scheduling (leg 2 departs the
day after leg 1 arrives) is real future work — see TODO below — but is
deliberately out of scope for the first working orchestrator so the
core stitching logic can be proven first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.segment import Segment, TravelMode, TripSegments
from app.providers.base import PartyComposition
from app.providers.registry import ProviderRegistry


@dataclass
class LegRequest:
    mode: TravelMode
    origin: str
    destination: str


@dataclass
class TripPlanResult:
    trip: TripSegments
    warnings: list[str] = field(default_factory=list)


class TripOrchestrator:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def plan_trip(
        self,
        legs: list[LegRequest],
        depart_date: date,
        party: PartyComposition,
    ) -> TripPlanResult:
        if not legs:
            raise ValueError("a trip must have at least one leg")

        segments: list[Segment] = []
        warnings: list[str] = []

        for i, leg in enumerate(legs, start=1):
            provider = self.registry.get(leg.mode)
            candidates = await provider.search(leg.origin, leg.destination, depart_date, party)

            if not candidates:
                # Honest gap, not a fabricated segment. Most likely today:
                # a train leg with no static-timetable match for this route.
                warnings.append(
                    f"leg {i} ({leg.mode.value}: {leg.origin} -> {leg.destination}): "
                    f"no data found, omitted from trip"
                )
                continue

            # Take the first candidate for now. Once the synthesis service
            # (Gemini ranking step) exists, this is where it would rank
            # `candidates` against user preferences instead of just
            # taking index 0.
            chosen = candidates[0]
            chosen.order = i
            segments.append(chosen)

        if not segments:
            raise ValueError("no data could be found for any leg of this trip")

        # Re-number in case any legs were dropped, so order stays contiguous.
        for idx, seg in enumerate(segments, start=1):
            seg.order = idx

        warnings.extend(self._check_continuity(segments))

        return TripPlanResult(trip=TripSegments(segments=segments), warnings=warnings)

    def _check_continuity(self, segments: list[Segment]) -> list[str]:
        """Warn (don't fail) when one leg's destination doesn't obviously
        match the next leg's origin — e.g. user typed 'Delhi Airport' for
        one and 'New Delhi' for the next. This is a warning, not a hard
        validation error, because place-name matching is inherently fuzzy;
        a stricter geocoded-distance check is a good future improvement
        (see TODO)."""
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
#   - Minimum transfer buffer validation using real departure/arrival times
#     where available (currently only rough string-matching on place names)
#   - Multiple candidates per leg passed to the synthesis service for ranking
#     instead of always taking candidates[0]