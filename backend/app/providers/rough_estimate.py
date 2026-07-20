"""
Rough-estimate providers: used for modes with no free live/static data
source yet. Never claim precision they don't have — costs and durations
here are always ranges pulled from static reference tables, not real
searches.

FlightRoughEstimateProvider is the one most likely to be replaced soon
(Phase 4 -> Amadeus). BusRoughEstimateProvider is the long-term default
for buses since no open schedule data source exists for private operators
in India today (see roadmap Phase 9 for the stretch goal).
"""

from __future__ import annotations

from datetime import date

from app.models.segment import CostEstimate, Segment, SegmentStatus, TravelMode
from app.providers.base import PartyComposition, SegmentProvider

# Very rough reference bands. Replace with a real fare-distance model or
# historical data once available — these exist so /trip/suggest has
# *something* to reason over, not to be presented as authoritative.
FLIGHT_COST_PER_KM_INR = (4.5, 9.0)
FLIGHT_AVG_SPEED_KMH = 750

BUS_COST_PER_KM_INR = (1.2, 2.5)
BUS_AVG_SPEED_KMH = 45


class FlightRoughEstimateProvider(SegmentProvider):
    mode = TravelMode.FLIGHT

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        party: PartyComposition,
    ) -> list[Segment]:
        distance_km = _straight_line_distance_km(origin, destination)
        duration_hours = distance_km / FLIGHT_AVG_SPEED_KMH + 0.75  # + taxi/boarding buffer
        cost = CostEstimate(
            low=distance_km * FLIGHT_COST_PER_KM_INR[0],
            high=distance_km * FLIGHT_COST_PER_KM_INR[1],
        )
        return [
            Segment(
                order=1,
                mode=self.mode,
                status=SegmentStatus.ROUGH_ESTIMATE,
                provider="rough_estimate",
                origin=origin,
                destination=destination,
                duration_hours_estimate=round(duration_hours, 2),
                cost=cost,
                book_external_url=_flight_search_deep_link(origin, destination, depart_date),
                provider_data={"note": "estimate only — no live fare source configured"},
            )
        ]

    async def estimate_cost(self, origin: str, destination: str, party: PartyComposition) -> CostEstimate:
        distance_km = _straight_line_distance_km(origin, destination)
        return CostEstimate(
            low=distance_km * FLIGHT_COST_PER_KM_INR[0],
            high=distance_km * FLIGHT_COST_PER_KM_INR[1],
        )


class BusRoughEstimateProvider(SegmentProvider):
    mode = TravelMode.BUS

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        party: PartyComposition,
    ) -> list[Segment]:
        distance_km = _straight_line_distance_km(origin, destination)
        duration_hours = distance_km / BUS_AVG_SPEED_KMH
        cost = CostEstimate(
            low=distance_km * BUS_COST_PER_KM_INR[0],
            high=distance_km * BUS_COST_PER_KM_INR[1],
        )
        return [
            Segment(
                order=1,
                mode=self.mode,
                status=SegmentStatus.ROUGH_ESTIMATE,
                provider="deep_link_only",
                origin=origin,
                destination=destination,
                duration_hours_estimate=round(duration_hours, 2),
                cost=cost,
                book_external_url=_redbus_deep_link(origin, destination, depart_date),
                provider_data={"note": "no open schedule data source — timing is a rough estimate"},
            )
        ]

    async def estimate_cost(self, origin: str, destination: str, party: PartyComposition) -> CostEstimate:
        distance_km = _straight_line_distance_km(origin, destination)
        return CostEstimate(
            low=distance_km * BUS_COST_PER_KM_INR[0],
            high=distance_km * BUS_COST_PER_KM_INR[1],
        )


def _straight_line_distance_km(origin: str, destination: str) -> float:
    """Placeholder — wire to a geocoding + haversine calculation, or reuse
    the driving provider's geocoder. Stubbed with a fixed value so the
    rest of the pipeline is runnable/testable before geocoding is wired up."""
    return 500.0


def _flight_search_deep_link(origin: str, destination: str, depart_date: date) -> str:
    return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{depart_date.isoformat()}"


def _redbus_deep_link(origin: str, destination: str, depart_date: date) -> str:
    return f"https://www.redbus.in/search?fromCity={origin}&toCity={destination}&onward={depart_date.isoformat()}"