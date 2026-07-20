"""
Provider registry — the single place that knows which concrete provider
is active for each mode. Swapping a provider (e.g. flight rough-estimate
-> Amadeus) means changing exactly one line here plus adding the new
provider class. Nothing else in the codebase should import a concrete
provider directly; always go through get_provider().
"""

from __future__ import annotations

from app.models.segment import TravelMode
from app.providers.base import SegmentProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[TravelMode, SegmentProvider] = {}

    def register(self, provider: SegmentProvider) -> None:
        self._providers[provider.mode] = provider

    def get(self, mode: TravelMode) -> SegmentProvider:
        try:
            return self._providers[mode]
        except KeyError as exc:
            raise ValueError(f"no provider registered for mode={mode}") from exc

    def all_modes(self) -> list[TravelMode]:
        return list(self._providers.keys())


def build_default_registry() -> ProviderRegistry:
    """Wire up the providers that are active today. This is the function
    to edit when you upgrade a provider (e.g. swap FlightRoughEstimateProvider
    for FlightAmadeusProvider once Phase 4 lands)."""
    from app.providers.driving import DrivingProvider
    from app.providers.rough_estimate import (
        BusRoughEstimateProvider,
        FlightRoughEstimateProvider,
    )
    from app.providers.train_static import TrainStaticTimetableProvider

    registry = ProviderRegistry()
    registry.register(DrivingProvider())
    registry.register(FlightRoughEstimateProvider())
    registry.register(TrainStaticTimetableProvider())
    registry.register(BusRoughEstimateProvider())
    return registry