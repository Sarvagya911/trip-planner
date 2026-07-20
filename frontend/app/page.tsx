"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { TripPlannerForm } from "@/components/TripPlannerForm";
import { SegmentCard } from "@/components/SegmentCard";
import { planTrip, ApiError, type TripPlanResponse, type LegInput } from "@/lib/api";

export default function Home() {
  const [result, setResult] = useState<TripPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(params: {
    legs: LegInput[];
    departDate: string;
    adults: number;
    children: number;
    elders: number;
    hasPets: boolean;
  }) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await planTrip({
        legs: params.legs,
        depart_date: params.departDate,
        adults: params.adults,
        children: params.children,
        elders: params.elders,
        has_pets: params.hasPets,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong reaching the planner.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-10 sm:py-16">
      <header className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Trip Planner</h1>
        <p className="text-ink-soft mt-1 text-sm sm:text-base">
          Mix driving, flights, trains, and buses into one itinerary. Every leg is labeled honestly —
          live data where we have it, estimates where we don&apos;t.
        </p>
      </header>

      <TripPlannerForm onSubmit={handleSubmit} loading={loading} />

      {error && (
        <div className="mt-6 flex items-start gap-2 bg-amber-soft border border-amber/30 rounded-lg p-4 text-sm">
          <AlertTriangle size={18} className="text-amber shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft mb-3">
            Your itinerary
          </h2>
          <div className="space-y-3">
            {result.trip.segments.map((seg) => (
              <SegmentCard key={seg.segment_id} segment={seg} />
            ))}
          </div>

          {result.warnings.length > 0 && (
            <div className="mt-6 bg-amber-soft border border-amber/30 rounded-lg p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber mb-2">
                Heads up
              </p>
              <ul className="text-sm space-y-1 text-ink-soft">
                {result.warnings.map((w, i) => (
                  <li key={i}>&bull; {w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </main>
  );
}