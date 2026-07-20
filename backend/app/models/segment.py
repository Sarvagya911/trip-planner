"""
Segment schema — the core data model of the trip planner.

A trip is a sequence of segments, not an origin/destination pair.
Each segment is one leg of travel (driving, flight, train, bus, ...),
sourced by exactly one SegmentProvider, and carries a status that
honestly reflects how good the underlying data is.

Adding a new mode or upgrading a mode from estimate -> live data
should never require changing this file. If you find yourself
wanting to add a mode-specific required field, put it in a mode-specific
extra dict (see `provider_data`) rather than growing the base model —
that's what keeps the orchestrator, frontend, and collaboration layer
mode-agnostic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class TravelMode(str, Enum):
    DRIVING = "driving"
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"


class SegmentStatus(str, Enum):
    """How trustworthy is this segment's data?

    Ordered roughly by data quality, worst to best. The frontend uses
    this directly to decide what badge/copy to show the user — never
    invent confidence the data doesn't have.
    """

    ROUGH_ESTIMATE = "rough_estimate"        # no live source; derived from static reference data
    STATIC_TIMETABLE = "static_timetable"    # real scheduled times, no live delay/availability data
    LIVE_SUGGESTED = "live_suggested"        # live search result, not yet booked
    LIVE_TRACKED = "live_tracked"            # live status/delay data merged in
    LIVE_BOOKED = "live_booked"              # user has confirmed/booked this segment


class CostEstimate(BaseModel):
    """A cost is either a single number (known/live) or a range (estimate).
    Always populate low/high even for a known cost (low == high == value) so
    callers never have to branch on which one is present.
    """

    low: float
    high: float
    currency: str = "INR"

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2


class Segment(BaseModel):
    segment_id: UUID = Field(default_factory=uuid4)
    order: int = Field(ge=1, description="1-indexed position in the trip's segment list")

    mode: TravelMode
    status: SegmentStatus
    provider: str = Field(description="Identifier of the SegmentProvider that produced this, e.g. 'ors', 'amadeus', 'indian_railways_static', 'deep_link_only'")

    origin: str
    destination: str

    departure: datetime | None = None
    arrival: datetime | None = None
    duration_hours_estimate: float | None = None

    cost: CostEstimate

    # Where the user actually books, when this segment isn't bookable in-app.
    # None only for modes that ARE bookable in-app (driving needs no booking;
    # a future live_booked flight might be None once in-app booking exists).
    book_external_url: str | None = None

    # Mode-specific payload that doesn't belong in the base schema.
    # e.g. driving -> {"route_polyline": ..., "waypoints": [...]}
    #      train   -> {"train_number": "12658", "train_name": "Bengaluru Mail"}
    provider_data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_consistency(self) -> "Segment":
        if self.status in (SegmentStatus.LIVE_SUGGESTED, SegmentStatus.LIVE_TRACKED, SegmentStatus.LIVE_BOOKED):
            if self.departure is None or self.arrival is None:
                raise ValueError(f"status={self.status} requires departure and arrival times")
        return self


class TripSegments(BaseModel):
    """The ordered segment list for one trip. Stitching validation (gap time,
    location continuity) happens in the orchestrator, not here — this model
    just guarantees structural validity (ordering, non-empty)."""

    segments: list[Segment]

    @model_validator(mode="after")
    def _validate_ordering(self) -> "TripSegments":
        if not self.segments:
            raise ValueError("a trip must have at least one segment")
        orders = [s.order for s in self.segments]
        if orders != sorted(orders):
            raise ValueError("segments must be provided in order")
        if len(set(orders)) != len(orders):
            raise ValueError("segment order values must be unique")
        return self