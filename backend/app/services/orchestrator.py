"""
Trip orchestrator: takes an ordered list of legs, calls the right provider
for each via the registry, stitches them into one TripSegments, and enriches
the trip — hotels + a destination photo, and rest/fuel/food stops on long
drives.

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
from app.services.destination_photos import get_destination_photo
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
            budget_inr: int | None = None,
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
            destination_info = await self._enrich_destinations(segments, depart_date, party.has_pets, budget_inr)

        return TripPlanResult(
            trip=TripSegments(segments=segments),
            warnings=warnings,
            destination_info=destination_info,
        )

    async def _add_rest_stops(self, segments: list[Segment]) -> None:
        """For each long driving leg, find a fuel + food option near the
        route midpoint and attach it to the segment's provider_data['stop'],
        along with rough cost estimates for fuel (distance-based, same rate
        as the leg's own fuel estimate) and a meal (flat regional band).
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

            # A rest stop isn't a full tank — rough estimate of what a
            # traveler spends topping up at this one stop, not the whole
            # trip's fuel. ~30% of the leg's total estimated fuel cost.
            leg_fuel_low = seg.cost.low if fuel else None
            leg_fuel_high = seg.cost.high if fuel else None
            stop_fuel_low = round(leg_fuel_low * 0.3, -1) if leg_fuel_low else None
            stop_fuel_high = round(leg_fuel_high * 0.3, -1) if leg_fuel_high else None

            # Flat regional estimate for a roadside meal in India — a rough
            # band, not a per-venue price (Foursquare doesn't provide one
            # on the free tier).
            meal_low, meal_high = (150.0, 400.0) if food else (None, None)

            stop = RestStop(
                label="Around the halfway point",
                near_latitude=mid_lat,
                near_longitude=mid_lon,
                fuel=fuel,
                food=food,
                fuel_cost_low=stop_fuel_low,
                fuel_cost_high=stop_fuel_high,
                meal_cost_low=meal_low,
                meal_cost_high=meal_high,
            )
            # Attach without touching the Segment schema: ride in provider_data.
            seg.provider_data["stop"] = stop.model_dump()

    async def _enrich_destinations(
            self, segments: list[Segment], depart_date: date, has_pets: bool, budget_inr: int | None = None
    ) -> list[DestinationInfo]:
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
            hotels = await places.find_hotels(
                dest, depart_date=depart_date, pet_friendly=has_pets, budget_inr=budget_inr
            )
            if hotels:
                hotels_by_dest[dest] = hotels

        if not hotels_by_dest:
            return []

        try:
            await annotate_hotels(hotels_by_dest)
        except Exception:
            pass

        result = []
        for dest, hotels in hotels_by_dest.items():
            try:
                photo = await get_destination_photo(dest)
            except Exception:
                photo = None
            result.append(DestinationInfo(destination=dest, hotels=hotels, photo_url=photo))
        return result

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
#   - Numeric budget filtering needs a budget_inr field threaded from
#     TripPlanRequest through to here — not yet wired (Foursquare has no
#     free price field to filter on anyway, so this would still only be a
#     soft query bias like pet_friendly, not a hard filter)