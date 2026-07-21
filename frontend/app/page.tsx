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
} from "lucide-react";

const FEATURES = [
  {
    icon: MessageSquare,
    title: "Just describe your trip",
    body: "Tell it where you're starting from, who's coming, and the kind of place you want. It asks the right follow-ups and suggests destinations if you're not sure.",
  },
  {
    icon: MapIcon,
    title: "See the whole route",
    body: "A real map of your driving route, plus a cinematic journey view that tracks your progress and shifts scenery to match your mode of travel.",
  },
  {
    icon: Building2,
    title: "Hotels, sorted",
    body: "Real nearby hotels for every destination, with an honest note on each and a one-tap link to book — no invented ratings, just what's actually there.",
  },
  {
    icon: Fuel,
    title: "Built-in rest stops",
    body: "Long drive? It finds a fuel stop and a place to eat around the halfway point, so the whole trip is planned — not just the destination.",
  },
  {
    icon: Wand2,
    title: "Change your mind anytime",
    body: "\"Make it cheaper.\" \"Avoid flights.\" \"I have a dog.\" Keep talking after the plan exists and it adjusts — and tells you exactly what changed.",
  },
  {
    icon: Navigation,
    title: "One tap to go",
    body: "When it's time to leave, a single tap opens turn-by-turn navigation in Google or Apple Maps — no re-typing your route anywhere else.",
  },
];

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

export default function HomePage() {
  return (
    <main className="flex-1">
      {/* Hero */}
      <section className="relative h-screen min-h-[640px] w-full overflow-hidden">
        <video autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover">
          <source src="https://cdn.pixabay.com/video/2022/10/05/133699-757782422_medium.mp4" type="video/mp4" />
        </video>
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(4,20,40,0.55) 0%, rgba(4,20,40,0.35) 45%, rgba(4,20,40,0.85) 100%)",
          }}
        />

        <div className="relative h-full flex flex-col items-center justify-center text-center px-6">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-white/80 text-sm uppercase tracking-[0.2em] mb-4"
          >
            Every trip, one place
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-white text-5xl sm:text-6xl md:text-7xl font-semibold tracking-tight max-w-3xl leading-[1.05]"
          >
            Plan it. Watch it come together.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-white/85 text-lg mt-6 max-w-xl"
          >
            Describe a trip in plain language and get a full itinerary — driving,
            flights, and buses, mixed as needed — with hotels, rest stops, and a
            map, all in one place.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="mt-9"
          >
            <Link href="/plan" className="inline-flex items-center gap-2 bg-white text-ink font-medium px-7 py-3.5 rounded-full hover:bg-white/90 transition">
              Start planning <ArrowRight size={18} />
            </Link>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/70 text-xs uppercase tracking-widest"
        >
          Scroll
        </motion.div>
      </section>

      {/* Feature grid */}
      <section
        className="relative overflow-hidden py-28"
        style={{ background: "linear-gradient(180deg, #2D1F4A 0%, #4A2F5C 55%, #6B3A52 100%)" }}
      >
        <div className="absolute rounded-full pointer-events-none" style={{ top: -100, right: -80, width: 320, height: 320, background: "radial-gradient(circle, rgba(240,184,122,0.12) 0%, transparent 70%)" }} />
        <div className="absolute rounded-full pointer-events-none" style={{ bottom: -120, left: -70, width: 300, height: 300, background: "radial-gradient(circle, rgba(201,166,232,0.10) 0%, transparent 70%)" }} />

        <div className="relative max-w-6xl mx-auto px-6">
          <FadeUp>
            <p className="font-medium text-sm uppercase tracking-wide mb-3" style={{ color: "#F0B87A" }}>
              What it does
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight max-w-xl mb-16 text-white">
              Everything a trip needs, worked out before you leave.
            </h2>
          </FadeUp>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <FadeUp key={f.title} delay={i * 0.08}>
                <div
                  className="rounded-2xl p-6 h-full"
                  style={{
                    background: "rgba(255,255,255,0.08)",
                    backdropFilter: "blur(14px)",
                    border: "0.5px solid rgba(255,255,255,0.15)",
                    boxShadow: "0 16px 32px -14px rgba(20,10,35,0.4)",
                  }}
                >
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center mb-5"
                    style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}
                  >
                    <f.icon size={20} className="text-[#3A1F0A]" />
                  </div>
                  <h3 className="font-medium text-lg mb-2 text-white">{f.title}</h3>
                  <p className="text-white/65 text-sm leading-relaxed">{f.body}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* CTA band */}
      <section className="relative overflow-hidden py-28">
        <div className="absolute inset-0" style={{ background: "linear-gradient(135deg, #6B3A52 0%, #8C4A4A 100%)" }} />
        <div className="relative max-w-2xl mx-auto text-center px-6">
          <FadeUp>
            <h2 className="text-3xl sm:text-4xl font-semibold text-white mb-5">
              Where to next?
            </h2>
            <p className="text-white/85 mb-9">
              Tell it where you&apos;re starting from — the rest comes together as you talk.
            </p>
            <Link href="/plan" className="inline-flex items-center gap-2 font-medium px-7 py-3.5 rounded-full hover:opacity-90 transition text-[#3A1F0A]" style={{ background: "linear-gradient(135deg, #F0B87A, #D97A4A)" }}>
              Plan a trip <ArrowRight size={18} />
            </Link>
          </FadeUp>
        </div>
      </section>
    </main>
  );
}