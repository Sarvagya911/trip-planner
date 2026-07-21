"use client";

import { useState } from "react";
import { AlertTriangle, MessageSquare, SlidersHorizontal } from "lucide-react";
import { TripPlannerForm } from "@/components/TripPlannerForm";
import { ChatPanel } from "@/components/ChatPanel";
import { RefinePanel } from "@/components/RefinePanel";
import { SegmentCard } from "@/components/SegmentCard";
import { RestStopStrip } from "@/components/RestStopStrip";
import { RouteMap } from "@/components/RouteMap";
import { WhereToStay } from "@/components/WhereToStay";
import {
  planTrip,
  emptyBrief,
  ApiError,
  type TripPlanResponse,
  type LegInput,
  type BriefLeg,
  type TripBrief,
  type ConversationMessage,
  type RestStop,
} from "@/lib/api";

type Mode = "chat" | "form";

export default function Home() {
  const [mode, setMode] = useState<Mode>("chat");
  const [result, setResult] = useState<TripPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeBrief, setActiveBrief] = useState<TripBrief | null>(null);
  const [activeMessages, setActiveMessages] = useState<ConversationMessage[]>([]);

  async function runPlan(brief: TripBrief, legs: BriefLeg[]) {
    setLoading(true);
    setError(null);
    try {
      const res = await planTrip({
        legs,
        depart_date: brief.depart_date ?? new Date().toISOString().slice(0, 10),
        adults: brief.adults,
        children: brief.children,
        elders: brief.elders,
        has_pets: brief.has_pets,
      });
      setResult(res);
      setActiveBrief(brief);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong reaching the planner.");
    } finally {
      setLoading(false);
    }
  }

  function handleChatPlanReady(legs: BriefLeg[], brief: TripBrief) {
    setActiveMessages([]);
    runPlan(brief, legs);
  }

  function handleFormSubmit(params: {
    legs: LegInput[];
    departDate: string;
    adults: number;
    children: number;
    elders: number;
    hasPets: boolean;
  }) {
    const brief: TripBrief = {
      ...emptyBrief(),
      origin: params.legs[0]?.origin ?? null,
      depart_date: params.departDate,
      adults: params.adults,
      children: params.children,
      elders: params.elders,
      has_pets: params.hasPets,
      proposed_legs: params.legs,
      destinations: params.legs.map((l) => l.destination),
      ready: true,
    };
    setActiveMessages([]);
    runPlan(brief, params.legs);
  }

  function handleReplan(legs: BriefLeg[], brief: TripBrief, messages: ConversationMessage[]) {
    setActiveMessages(messages);
    runPlan(brief, legs);
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
        <TripPlannerForm onSubmit={handleFormSubmit} loading={loading} />
      )}

      {error && (
        <div className="mt-6 flex items-start gap-2 bg-amber-soft border border-amber/30 rounded-lg p-4 text-sm">
          <AlertTriangle size={18} className="text-amber shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <p className="mt-6 text-sm text-ink-soft">Planning your trip...</p>
      )}

      {result && (
        <div className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft mb-3">
            Your itinerary
          </h2>
          <div className="space-y-3">
            {result.trip.segments.map((seg) => {
              const stop = (seg.provider_data as { stop?: RestStop })?.stop;
              return (
                <div key={seg.segment_id}>
                  <SegmentCard segment={seg} />
                  {stop && <RestStopStrip stop={stop} />}
                </div>
              );
            })}
          </div>

          <RouteMap segments={result.trip.segments} />

          <WhereToStay destinations={result.destination_info} />

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

          {activeBrief && (
            <RefinePanel
              brief={activeBrief}
              messages={activeMessages}
              onReplan={handleReplan}
            />
          )}
        </div>
      )}
    </main>
  );
}