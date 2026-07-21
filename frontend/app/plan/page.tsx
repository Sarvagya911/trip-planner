"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, MessageSquare, SlidersHorizontal } from "lucide-react";
import { TripPlannerForm } from "@/components/TripPlannerForm";
import { ChatPanel } from "@/components/ChatPanel";
import { RefinePanel } from "@/components/RefinePanel";
import { SegmentCard } from "@/components/SegmentCard";
import { RestStopStrip } from "@/components/RestStopStrip";
import { RouteMap } from "@/components/RouteMap";
import { JourneyHero } from "@/components/JourneyHero";
import { WhereToStay } from "@/components/WhereToStay";
import {
  planTrip,
  emptyBrief,
  getScenicPhoto,
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
  const [bgPhoto, setBgPhoto] = useState<string | null>(null);

  const [activeBrief, setActiveBrief] = useState<TripBrief | null>(null);
  const [activeMessages, setActiveMessages] = useState<ConversationMessage[]>([]);

  useEffect(() => {
    getScenicPhoto("mountains scenic landscape dusk").then(setBgPhoto);
  }, []);

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
    <div className="min-h-screen relative overflow-hidden">
      {bgPhoto && (
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `url(${bgPhoto})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            opacity: 0.5,
          }}
        />
      )}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(155deg, rgba(45,31,74,0.62) 0%, rgba(74,47,92,0.58) 40%, rgba(107,58,82,0.55) 75%, rgba(140,74,74,0.58) 100%)",
        }}
      />
      <div className="floating-dot" style={{ top: 90, right: 90, width: 16, height: 16, background: "#F0B87A", opacity: 0.4, animationDelay: "0s" }} />
      <div className="floating-dot" style={{ top: 220, right: 200, width: 9, height: 9, background: "#E89DA8", opacity: 0.45, animationDelay: "0.6s" }} />
      <div className="floating-dot" style={{ top: 160, left: 80, width: 11, height: 11, background: "#C9A6E8", opacity: 0.4, animationDelay: "1s" }} />
      <div className="floating-dot" style={{ bottom: 140, left: 50, width: 13, height: 13, background: "#F0B87A", opacity: 0.3, animationDelay: "0.3s" }} />
      <div
        className="absolute rounded-full pointer-events-none"
        style={{ top: -120, right: -100, width: 340, height: 340, background: "radial-gradient(circle, rgba(240,184,122,0.14) 0%, transparent 70%)" }}
      />
      <div
        className="absolute rounded-full pointer-events-none"
        style={{ bottom: -140, left: -90, width: 300, height: 300, background: "radial-gradient(circle, rgba(201,166,232,0.12) 0%, transparent 70%)" }}
      />

      <main className="relative flex-1 max-w-3xl w-full mx-auto px-4 pt-24 pb-16 sm:pt-28">
      <header className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-white">Trip Planner</h1>
        <p className="text-white/65 mt-1 text-sm sm:text-base">
          Mix driving, flights, trains, and buses into one itinerary. Every leg is labeled honestly —
          live data where we have it, estimates where we don&apos;t.
        </p>
      </header>

      {/* Mode toggle */}
      <div className="inline-flex rounded-lg p-1 mb-6" style={{ background: "rgba(255,255,255,0.09)", border: "0.5px solid rgba(255,255,255,0.16)" }}>
        <button
          onClick={() => setMode("chat")}
          className={`inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition ${
            mode === "chat" ? "text-[#3A1F0A]" : "text-white/70 hover:text-white"
          }`}
          style={mode === "chat" ? { background: "linear-gradient(135deg, #F0B87A, #D97A4A)" } : undefined}
        >
          <MessageSquare size={15} /> Chat
        </button>
        <button
          onClick={() => setMode("form")}
          className={`inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition ${
            mode === "form" ? "text-[#3A1F0A]" : "text-white/70 hover:text-white"
          }`}
          style={mode === "form" ? { background: "linear-gradient(135deg, #F0B87A, #D97A4A)" } : undefined}
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
        <p className="mt-6 text-sm text-white/70">Planning your trip...</p>
      )}

      {result && (
        <div className="mt-10">
          <div className="mb-8">
            <JourneyHero segments={result.trip.segments} departDate={activeBrief?.depart_date ?? null} />
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wide text-white/60 mb-3">
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
    </div>
  );
}