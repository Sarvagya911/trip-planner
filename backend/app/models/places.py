"""
Place and destination-enrichment models.

Places (hotels now, restaurants later) are NOT travel segments — they're
things attached to a destination. So they live in their own models and ride
alongside the trip as `destination_info`, keeping the Segment schema clean
and mode-agnostic (the rule that's kept everything extensible).

Same metasearch pattern as the rest of the app: real data shown in-app,
booking happens on an external platform via `book_external_url`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Place(BaseModel):
    name: str
    category: str = "hotel"          # "hotel" | "restaurant" | ...
    rating: float | None = None      # Foursquare 0-10 scale, if available
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    # Short LLM-written line on why this place is worth considering.
    # Optional: filled by a batched Groq call, absent if that call is skipped.
    why: str | None = None
    # Where the user actually books — external, per the metasearch pattern.
    book_external_url: str | None = None


class DestinationInfo(BaseModel):
    """Enrichment for one destination in the trip."""
    destination: str
    hotels: list[Place] = Field(default_factory=list)
    photo_url: str | None = None  # destination hero photo (Unsplash), best-effort
    # restaurants: list[Place] = Field(default_factory=list)  # next build


class RestStop(BaseModel):
    """A suggested break along a long driving leg — roughly at a point on the
    route. Holds a fuel option and/or a food option found near that point.
    Attached to a driving segment, not to a destination."""
    label: str                          # e.g. "Around the halfway point"
    near_latitude: float
    near_longitude: float
    fuel: Place | None = None
    food: Place | None = None
    # Rough cost estimates — distance-based fuel cost + a flat meal estimate,
    # same "clearly labeled estimate" pattern as flight/bus pricing. None
    # of these are fabricated per-venue prices; they're regional averages.
    fuel_cost_low: float | None = None
    fuel_cost_high: float | None = None
    meal_cost_low: float | None = None
    meal_cost_high: float | None = None


class TripBudgetEstimate(BaseModel):
    """A whole-trip budget summary: real travel cost (summed from the
    planned legs) plus clearly-labeled per-night/per-day estimate bands for
    stay and food. Never pretends to know the trip's length in nights —
    there's no reliable data for that yet — so stay/food are shown as
    per-unit estimates rather than multiplied into a fabricated total."""
    travel_cost_low: float
    travel_cost_high: float
    stay_per_night_low: float
    stay_per_night_high: float
    food_per_day_low: float
    food_per_day_high: float
    local_transport_per_day_low: float
    local_transport_per_day_high: float
    budget_inr: int | None = None
    # True only when travel cost alone already exceeds the stated budget —
    # the one thing we CAN honestly compare without knowing trip length.
    travel_exceeds_budget: bool = False