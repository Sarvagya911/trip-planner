"use client";

import Link from "next/link";
import { motion } from "motion/react";
import {
  ArrowRight,
  MessageSquare,
  Building2,
  Map as MapIcon,
  Fuel,
  Wand2,
  Navigation,
  Sparkles,
} from "lucide-react";

function FadeUp({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

const DEEP_FEATURES = [
  {
    icon: MessageSquare,
    title: "A conversation, not a form",
    tag: "Chat planning",
    body: "Say where you're starting from, who's coming, and what kind of trip you're after. If you don't know where to go yet, it suggests real, specific destinations — and it never invents distances, durations, or prices; those come from real routing and data underneath.",
  },
  {
    icon: Sparkles,
    title: "Your cinematic journey view",
    tag: "Journey hero",
    body: "Once a trip is planned, watch it unfold — scenery matched to your mode of travel, a progress indicator based on your actual schedule, and a smooth animated path from origin to destination. It's an estimate based on your planned timing, clearly labeled as such — not live GPS tracking.",
  },
  {
    icon: MapIcon,
    title: "The whole route, mapped",
    tag: "Route map",
    body: "Every driving leg renders on a real interactive map, with markers for your origin, destination, and any suggested rest stop along the way.",
  },
  {
    icon: Building2,
    title: "Somewhere real to stay",
    tag: "Hotels",
    body: "Actual nearby hotels for each destination — names, addresses, a short honest note on each — plus a link to find and book. Ratings aren't shown here on purpose: rather than pay for a premium data field or have an AI guess at a number, we tell you plainly to check reviews on the booking site first.",
  },
  {
    icon: Fuel,
    title: "Stops built into long drives",
    tag: "Rest stops",
    body: "Any driving leg over four hours gets a suggested midpoint stop — a nearby fuel station and a place to eat — so the trip is planned door to door, not just city to city.",
  },
  {
    icon: Wand2,
    title: "Keep talking after it's planned",
    tag: "Replanning",
    body: "\"Make it cheaper,\" \"avoid flights,\" \"I have a dog\" — the assistant edits your existing plan instead of starting over, and always explains what it changed and why.",
  },
  {
    icon: Navigation,
    title: "From plan to on the road",
    tag: "Navigation handoff",
    body: "When you're ready to leave, one tap opens Google Maps (or prompts Apple Maps on iOS) with turn-by-turn directions already loaded for that exact leg.",
  },
];

export default function FeaturesPage() {
  return (
    <main
      className="flex-1 relative overflow-hidden"
      style={{ background: "linear-gradient(155deg, #2D1F4A 0%, #4A2F5C 35%, #6B3A52 70%, #8C4A4A 100%)" }}
    >
      <div className="absolute rounded-full pointer-events-none" style={{ top: -100, right: -90, width: 340, height: 340, background: "radial-gradient(circle, rgba(240,184,122,0.12) 0%, transparent 70%)" }} />
      <div className="absolute rounded-full pointer-events-none" style={{ top: 500, left: -100, width: 300, height: 300, background: "radial-gradient(circle, rgba(201,166,232,0.10) 0%, transparent 70%)" }} />

      <section className="relative pt-40 pb-20 max-w-4xl mx-auto px-6 text-center">
        <FadeUp>
          <p className="font-medium text-sm uppercase tracking-wide mb-3" style={{ color: "#F0B87A" }}>
            Under the hood
          </p>
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight mb-6 text-white">
            Everything that goes into one trip
          </h1>
          <p className="text-white/70 text-lg max-w-2xl mx-auto">
            Every piece here is built to be honest about what it knows — real data
            where it exists, clearly labeled estimates everywhere else.
          </p>
        </FadeUp>
      </section>

      <section className="relative max-w-4xl mx-auto px-6 pb-28 space-y-6">
        {DEEP_FEATURES.map((f, i) => (
          <FadeUp key={f.title} delay={i * 0.05}>
            <div
              className="flex gap-6 items-start rounded-2xl p-6"
              style={{
                background: "rgba(255,255,255,0.08)",
                backdropFilter: "blur(14px)",
                border: "0.5px solid rgba(255,255,255,0.15)",
                boxShadow: "0 16px 32px -14px rgba(20,10,35,0.4)",
              }}
            >
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
                style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}
              >
                <f.icon size={22} className="text-[#3A1F0A]" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide mb-1.5" style={{ color: "#F0B87A" }}>
                  {f.tag}
                </p>
                <h2 className="text-2xl font-semibold tracking-tight mb-3 text-white">{f.title}</h2>
                <p className="text-white/65 leading-relaxed">{f.body}</p>
              </div>
            </div>
          </FadeUp>
        ))}
      </section>

      <section className="relative overflow-hidden py-24">
        <div className="relative max-w-2xl mx-auto text-center px-6">
          <FadeUp>
            <h2 className="text-3xl font-semibold text-white mb-6">Try it yourself</h2>
            <Link href="/plan" className="inline-flex items-center gap-2 font-medium px-7 py-3.5 rounded-full hover:opacity-90 transition text-[#3A1F0A]" style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}>
              Plan a trip <ArrowRight size={18} />
            </Link>
          </FadeUp>
        </div>
      </section>
    </main>
  );
}