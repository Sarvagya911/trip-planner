"use client";

import { useState } from "react";
import { AlertTriangle, MessageSquare, SlidersHorizontal } from "lucide-react";
import { TripPlannerForm } from "@/components/TripPlannerForm";
import { ChatPanel } from "@/components/ChatPanel";
import { SegmentCard } from "@/components/SegmentCard";
import {
  planTrip,
  ApiError,
  type TripPlanResponse,
  type LegInput,
  type BriefLeg,
  type TripBrief,
} from "@/lib/api";

type Mode = "chat" | "form";

export default function Home() {
  const [mode, setMode] = useState<Mode>("chat");
  const [result, setResult] = useState<TripPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runPlan(params: {
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

  // When the chat's brief is ready, convert it into a plan request.
  function handleChatPlanReady(legs: BriefLeg[], brief: TripBrief) {
    runPlan({
      legs,
      departDate: brief.depart_date ?? new Date().toISOString().slice(0, 10),
      adults: brief.adults,
      children: brief.children,
      elders: brief.elders,
      hasPets: brief.has_pets,
    });
  }

  return (
    <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-10 sm:py-16">
      <header className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Trip Planner</h1>
        <p className="text-ink-soft mt-1 text-sm sm:text-base">
          Mix driving, flights, trains, and buses into one itinerary. Every leg is labeled honestly —
          live data where we have it, estimates where we don&apos;t.
        </p>
      </header>

      {/* Mode toggle */}
      <div className="inline-flex rounded-lg border border-line bg-card p-1 mb-6">
        <button
          onClick={() => setMode("chat")}
          className={`inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition ${
            mode === "chat" ? "bg-route text-white" : "text-ink-soft hover:text-ink"
          }`}
        >
          <MessageSquare size={15} /> Chat
        </button>
        <button
          onClick={() => setMode("form")}
          className={`inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition ${
            mode === "form" ? "bg-route text-white" : "text-ink-soft hover:text-ink"
          }`}
        >
          <SlidersHorizontal size={15} /> Manual
        </button>
      </div>

      {mode === "chat" ? (
        <ChatPanel onPlanReady={handleChatPlanReady} />
      ) : (
        <TripPlannerForm onSubmit={runPlan} loading={loading} />
      )}

      {error && (
        <div className="mt-6 flex items-start gap-2 bg-amber-soft border border-amber/30 rounded-lg p-4 text-sm">
          <AlertTriangle size={18} className="text-amber shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {loading && mode === "chat" && (
        <p className="mt-6 text-sm text-ink-soft">Planning your trip...</p>
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
              <p className="text-xs font-semibold uppercase tracking-wide text-amber mb-2">Heads up</p>
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