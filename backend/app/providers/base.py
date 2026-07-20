"""
SegmentProvider interface.

Every travel mode (driving, flight, train, bus, and anything added later)
implements this same contract. The orchestrator only ever talks to this
interface — it never imports a concrete provider class directly. That's
what lets a provider be upgraded (e.g. TrainProvider going from rough
estimate to static-timetable-backed) without touching orchestration,
the frontend, or the collaboration layer.

To add a new mode or upgrade an existing one:
  1. Subclass SegmentProvider.
  2. Implement search() and estimate_cost().
  3. Register an instance in the ProviderRegistry (see registry.py).
That's the entire integration surface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.models.segment import CostEstimate, Segment, TravelMode


class PartyComposition:
    """Minimal shape needed by providers to size vehicles/fares/etc.
    Kept separate from the API request model so providers don't depend
    on the full request schema."""

    def __init__(self, adults: int, children: int = 0, elders: int = 0, has_pets: bool = False):
        self.adults = adults
        self.children = children
        self.elders = elders
        self.has_pets = has_pets

    @property
    def total_people(self) -> int:
        return self.adults + self.children + self.elders


class SegmentProvider(ABC):
    """One provider serves exactly one mode. A mode may have more than one
    provider available over time (e.g. flight rough-estimate now, Amadeus
    later) but only one is active per mode at a time via the registry."""

    mode: TravelMode

    @abstractmethod
    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        party: PartyComposition,
    ) -> list[Segment]:
        """Return candidate segments for this leg. May return a single
        rough-estimate segment (no live source) or multiple live options
        for the caller/synthesis step to rank. Must never raise on "no
        live data available" — fall back to a rough estimate instead;
        raise only on genuine failure (network error, invalid input)."""
        raise NotImplementedError

    @abstractmethod
    async def estimate_cost(
        self,
        origin: str,
        destination: str,
        party: PartyComposition,
    ) -> CostEstimate:
        """Cheap, always-available cost estimate used by the budget/city
        suggestion step (Phase 3) — must not require a full search() call,
        since suggestion runs before the user has committed to a route."""
        raise NotImplementedError