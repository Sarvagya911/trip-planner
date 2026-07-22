import { Wallet, AlertTriangle } from "lucide-react";
import type { TripBudgetEstimate } from "@/lib/api";

function range(low: number, high: number): string {
  return `INR ${Math.round(low).toLocaleString("en-IN")}\u2013${Math.round(high).toLocaleString("en-IN")}`;
}

export function BudgetSummary({ estimate }: { estimate: TripBudgetEstimate }) {
  return (
    <div
      className="mt-8 rounded-3xl p-6"
      style={{
        background: "rgba(255,255,255,0.09)",
        backdropFilter: "blur(16px)",
        border: "0.5px solid rgba(255,255,255,0.16)",
        boxShadow: "0 24px 48px -16px rgba(20,10,35,0.5), inset 0 1px 0 rgba(255,255,255,0.1)",
      }}
    >
      <div className="flex items-center gap-2 mb-1">
        <Wallet size={17} style={{ color: "#F0B87A" }} />
        <h2 className="text-sm font-semibold text-white">Estimated trip budget</h2>
      </div>
      <p className="text-xs text-white/55 mb-4">
        Travel is a real total from your itinerary. Stay, food, and local costs are
        regional per-night/per-day estimates &mdash; multiply by your trip length for
        the full picture.
      </p>

      <div className="space-y-2.5">
        <Row label="Travel (this itinerary)" value={range(estimate.travel_cost_low, estimate.travel_cost_high)} />
        <Row label="Stay, per night" value={range(estimate.stay_per_night_low, estimate.stay_per_night_high)} />
        <Row label="Food, per day" value={range(estimate.food_per_day_low, estimate.food_per_day_high)} />
        <Row
          label="Local transport & activities, per day"
          value={range(estimate.local_transport_per_day_low, estimate.local_transport_per_day_high)}
        />
      </div>

      {estimate.budget_inr != null && (
        <div className="mt-4 pt-4" style={{ borderTop: "0.5px solid rgba(255,255,255,0.14)" }}>
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/70">Your stated budget</span>
            <span className="font-medium text-white">
              INR {estimate.budget_inr.toLocaleString("en-IN")}
            </span>
          </div>
          {estimate.travel_exceeds_budget && (
            <div className="flex items-start gap-2 mt-3 text-xs rounded-lg px-3 py-2" style={{ background: "rgba(232,157,168,0.15)", color: "#E89DA8" }}>
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              <span>
                Travel alone is already above your stated budget, before stay or food.
                Try &quot;Make it cheaper&quot; in Refine, or a lower budget hotel tier.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-white/65">{label}</span>
      <span className="font-medium text-white font-mono">{value}</span>
    </div>
  );
}