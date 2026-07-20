"""
Train segment provider, backed by a static open-data timetable
(e.g. a data.gov.in rail schedule dataset loaded into a local table/DB).

Status is STATIC_TIMETABLE, not LIVE_TRACKED: we have real scheduled
times but no live delay/availability feed. Booking always happens
externally via IRCTC — book_external_url is always populated.

TODO when a live status source is available (Phase: post-launch):
  - Add a LiveStatusEnricher that merges delay data onto segments this
    provider returns, and bump status to LIVE_TRACKED. This provider's
    search()/estimate_cost() signatures don't need to change for that.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.models.segment import CostEstimate, Segment, SegmentStatus, TravelMode
from app.providers.base import PartyComposition, SegmentProvider


class TrainStaticTimetableProvider(SegmentProvider):
    mode = TravelMode.TRAIN

    def __init__(self, timetable_lookup: "TimetableLookup | None" = None) -> None:
        # Injected so tests can supply a fake lookup instead of a real DB/dataset.
        self.timetable_lookup = timetable_lookup or _StubTimetableLookup()

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        party: PartyComposition,
    ) -> list[Segment]:
        candidates = self.timetable_lookup.find_trains(origin, destination)
        if not candidates:
            # No scheduled train found for this route in the dataset —
            # honest fallback, don't fabricate a train.
            return []

        segments = []
        for i, train in enumerate(candidates):
            departure = datetime.combine(depart_date, train.departure_time)
            arrival = departure + timedelta(hours=train.duration_hours)
            segments.append(
                Segment(
                    order=1,
                    mode=self.mode,
                    status=SegmentStatus.STATIC_TIMETABLE,
                    provider="indian_railways_static",
                    origin=origin,
                    destination=destination,
                    departure=departure,
                    arrival=arrival,
                    cost=CostEstimate(low=train.fare_low, high=train.fare_high),
                    book_external_url="https://www.irctc.co.in/nget/train-search",
                    provider_data={
                        "train_number": train.number,
                        "train_name": train.name,
                    },
                )
            )
        return segments

    async def estimate_cost(self, origin: str, destination: str, party: PartyComposition) -> CostEstimate:
        candidates = self.timetable_lookup.find_trains(origin, destination)
        if not candidates:
            return CostEstimate(low=0, high=0)
        lows = [t.fare_low for t in candidates]
        highs = [t.fare_high for t in candidates]
        return CostEstimate(low=min(lows), high=max(highs))


class TrainSchedule:
    def __init__(self, number: str, name: str, departure_time: time, duration_hours: float, fare_low: float, fare_high: float):
        self.number = number
        self.name = name
        self.departure_time = departure_time
        self.duration_hours = duration_hours
        self.fare_low = fare_low
        self.fare_high = fare_high


class TimetableLookup:
    def find_trains(self, origin: str, destination: str) -> list[TrainSchedule]:
        raise NotImplementedError


class _StubTimetableLookup(TimetableLookup):
    """Placeholder until the real open-data timetable is loaded (Phase 2).
    Swap this for a real implementation backed by the data.gov.in dataset
    (or a Postgres table it's loaded into) — the provider above doesn't
    need to change."""

    def find_trains(self, origin: str, destination: str) -> list[TrainSchedule]:
        return []