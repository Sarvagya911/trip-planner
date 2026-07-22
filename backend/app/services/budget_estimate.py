"""
Whole-trip budget summary.

Combines the trip's real travel cost (summed from the segments the
orchestrator already priced) with clearly-labeled regional estimate bands
for stay, food, and local transport/activities — the same kind of "this is
a rough regional estimate, not a specific price" honesty already used for
rest-stop fuel/meal costs.

Stay and food are scaled PROPORTIONALLY to the stated budget (a percentage
of it), rather than jumping between a few fixed brackets — so a higher
budget gives a smoothly higher estimate, never a sudden jump to a luxury
range just because a threshold was crossed. A floor keeps very low budgets
from producing an unrealistically tiny number.

Deliberately does NOT multiply stay/food into a fake trip total: there's no
reliable "number of nights" anywhere in the current data (only a departure
date, no tracked return date), so presenting a false total would overclaim
precision we don't have. Per-night/per-day bands let the user do that math
themselves with a number they actually know.
"""

from __future__ import annotations

from app.models.places import TripBudgetEstimate
from app.models.segment import Segment

# Stay per night, as a fraction of the whole stated trip budget.
STAY_RATIO_LOW = 0.125
STAY_RATIO_HIGH = 0.25
STAY_FLOOR_LOW = 600.0
STAY_FLOOR_HIGH = 1200.0

# Food per day, as a fraction of the whole stated trip budget.
FOOD_RATIO_LOW = 0.03
FOOD_RATIO_HIGH = 0.06
FOOD_FLOOR_LOW = 300.0
FOOD_FLOOR_HIGH = 600.0

# Used only when no budget is stated at all — a wide honest fallback.
DEFAULT_STAY_LOW, DEFAULT_STAY_HIGH = 800.0, 4000.0
DEFAULT_FOOD_LOW, DEFAULT_FOOD_HIGH = 400.0, 1000.0

# Flat rough estimate for local transport (auto/cab short hops) + one
# activity/entry fee per day — genuinely rough, not budget-scaled.
LOCAL_TRANSPORT_PER_DAY = (200.0, 600.0)


def _round100(value: float) -> float:
    return round(value / 100) * 100


def compute_budget_estimate(
    segments: list[Segment], budget_inr: int | None
) -> TripBudgetEstimate:
    travel_low = sum(s.cost.low for s in segments)
    travel_high = sum(s.cost.high for s in segments)

    if budget_inr is not None and budget_inr > 0:
        stay_low = max(STAY_FLOOR_LOW, _round100(budget_inr * STAY_RATIO_LOW))
        stay_high = max(STAY_FLOOR_HIGH, _round100(budget_inr * STAY_RATIO_HIGH))
        food_low = max(FOOD_FLOOR_LOW, _round100(budget_inr * FOOD_RATIO_LOW))
        food_high = max(FOOD_FLOOR_HIGH, _round100(budget_inr * FOOD_RATIO_HIGH))
    else:
        stay_low, stay_high = DEFAULT_STAY_LOW, DEFAULT_STAY_HIGH
        food_low, food_high = DEFAULT_FOOD_LOW, DEFAULT_FOOD_HIGH

    exceeds = budget_inr is not None and travel_low > budget_inr

    return TripBudgetEstimate(
        travel_cost_low=round(travel_low, -1),
        travel_cost_high=round(travel_high, -1),
        stay_per_night_low=stay_low,
        stay_per_night_high=stay_high,
        food_per_day_low=food_low,
        food_per_day_high=food_high,
        local_transport_per_day_low=LOCAL_TRANSPORT_PER_DAY[0],
        local_transport_per_day_high=LOCAL_TRANSPORT_PER_DAY[1],
        budget_inr=budget_inr,
        travel_exceeds_budget=exceeds,
    )