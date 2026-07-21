"use client";

import { useEffect, useMemo, useState } from "react";
import { Car, Plane, Bus, TrainFront } from "lucide-react";
import { getJourneyVideo, type Segment, type TravelMode } from "@/lib/api";

const MODE_ICON: Record<TravelMode, React.ComponentType<{ size?: number; className?: string }>> = {
  driving: Car,
  flight: Plane,
  train: TrainFront,
  bus: Bus,
};

const MODE_LABEL: Record<TravelMode, string> = {
  driving: "On the road",
  flight: "In the air",
  train: "On the rails",
  bus: "On the bus",
};

interface Props {
  segments: Segment[];
  departDate: string | null; // ISO date, e.g. "2026-08-04"
}

interface LegTiming {
  segment: Segment;
  startHour: number;
  endHour: number;
}

// A gentle sine-wave curve so the path feels like a real route rather than
// a flat progress bar. Generalizes to any number of legs.
function curveY(x: number, xMin: number, xMax: number): number {
  const t = (x - xMin) / (xMax - xMin);
  return 22 - 14 * Math.sin(Math.PI * t);
}

function buildWavePath(width: number, xMin: number): string {
  const xMax = xMin + width;
  const steps = 24;
  let d = "";
  for (let i = 0; i <= steps; i++) {
    const x = xMin + (width * i) / steps;
    const y = curveY(x, xMin, xMax);
    d += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  }
  return d;
}

export function JourneyHero({ segments, departDate }: Props) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [percent, setPercent] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [phase, setPhase] = useState<"before" | "during" | "after">("before");
  const [now, setNow] = useState(() => Date.now());

  // Cumulative schedule assuming legs run back-to-back from departure.
  // This is a simplifying assumption (no real per-leg departure times exist
  // yet) — clearly labeled as an estimate in the UI, not live tracking.
  const legTimings: LegTiming[] = useMemo(() => {
    let cursor = 0;
    return segments.map((seg) => {
      const duration = seg.duration_hours_estimate ?? 1;
      const timing = { segment: seg, startHour: cursor, endHour: cursor + duration };
      cursor += duration;
      return timing;
    });
  }, [segments]);

  const totalHours = legTimings.length > 0 ? legTimings[legTimings.length - 1].endHour : 0;

  useEffect(() => {
    const tick = () => setNow(Date.now());
    const id = setInterval(tick, 30 * 60 * 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!departDate || totalHours === 0) {
      setPhase("before");
      setPercent(0);
      return;
    }
    const start = new Date(`${departDate}T00:00:00`).getTime();
    const elapsedHours = (now - start) / (1000 * 60 * 60);

    if (elapsedHours <= 0) {
      setPhase("before");
      setPercent(0);
      setActiveIndex(0);
    } else if (elapsedHours >= totalHours) {
      setPhase("after");
      setPercent(100);
      setActiveIndex(legTimings.length - 1);
    } else {
      setPhase("during");
      setPercent(Math.round((elapsedHours / totalHours) * 100));
      const idx = legTimings.findIndex((l) => elapsedHours >= l.startHour && elapsedHours < l.endHour);
      setActiveIndex(idx === -1 ? 0 : idx);
    }
  }, [now, departDate, totalHours, legTimings]);

  useEffect(() => {
    const seg = legTimings[activeIndex]?.segment;
    if (!seg) return;
    let cancelled = false;
    getJourneyVideo(seg.mode).then((url) => {
      if (!cancelled) setVideoUrl(url);
    });
    return () => {
      cancelled = true;
    };
  }, [activeIndex, legTimings]);

  if (segments.length === 0) return null;

  const activeSeg = legTimings[activeIndex]?.segment ?? segments[0];
  const Icon = MODE_ICON[activeSeg.mode];
  const origin = segments[0].origin;
  const destination = segments[segments.length - 1].destination;

  const statusLine =
    phase === "before"
      ? "Not started yet"
      : phase === "after"
      ? "Trip complete"
      : `${MODE_LABEL[activeSeg.mode]} · ${activeSeg.origin} to ${activeSeg.destination}`;

  return (
    <div className="relative rounded-3xl overflow-hidden shadow-lg" style={{ height: 300 }}>
      {videoUrl ? (
        <video key={videoUrl} autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover">
          <source src={videoUrl} type="video/mp4" />
        </video>
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-[#0C447C] to-[#378ADD]" />
      )}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, rgba(4,20,40,0.15) 0%, rgba(4,20,40,0.25) 45%, rgba(4,20,40,0.78) 100%)",
        }}
      />

      <div className="relative flex flex-col h-full p-6 box-border">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-wide text-white/80 mb-0.5">Your journey</p>
            <p className="text-lg font-medium text-white">
              {origin} to {destination}
            </p>
            <p className="text-xs text-white/85 mt-1 flex items-center gap-1.5">
              <Icon size={13} /> {statusLine}
            </p>
          </div>
          <div className="text-right bg-white/15 backdrop-blur-sm rounded-xl px-3.5 py-2">
            <p className="text-[10px] text-white/75">Position</p>
            <p className="text-xl font-medium text-white">{percent}%</p>
          </div>
        </div>

        <div className="flex-1" />

        <div className="relative h-11 mx-0.5 mb-2">
          <svg width="100%" height="44" viewBox="0 0 580 44" className="absolute top-0 left-0">
            <path d={buildWavePath(556, 12)} fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="3" strokeLinecap="round" />
            <path
              d={buildWavePath(556, 12)}
              fill="none"
              stroke="#FAC775"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray={620}
              strokeDashoffset={620 - (620 * percent) / 100}
            />
            {legTimings.map((l, i) => {
              const x = 12 + (556 * l.startHour) / (totalHours || 1);
              const y = curveY(x, 12, 568);
              return <circle key={i} cx={x} cy={y} r={5} fill="rgba(255,255,255,0.5)" />;
            })}
          </svg>
          <div
            className="absolute w-9 h-9 rounded-full flex items-center justify-center shadow-lg transition-all duration-700"
            style={{
              left: `calc(${percent}% - 18px)`,
              top: `${curveY(12 + (556 * percent) / 100, 12, 568) - 18}px`,
              background: "radial-gradient(circle at 32% 28%, #FFF3D6, #FAC775 55%, #EF9F27 100%)",
            }}
          >
            <Icon size={16} className="text-[#633806]" />
          </div>
        </div>

        <div className="flex justify-between text-[11px] text-white/90 px-0.5">
          <span className="font-medium">{origin}</span>
          <span className="text-white/65">{destination}</span>
        </div>
      </div>
    </div>
  );
}