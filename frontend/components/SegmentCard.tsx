import { Car, Plane, TrainFront, Bus, ExternalLink, Navigation, ArrowRight } from "lucide-react";
import type { Segment, TravelMode, SegmentStatus } from "@/lib/api";

const MODE_ICON: Record<TravelMode, React.ComponentType<{ size?: number; className?: string }>> = {
  driving: Car,
  flight: Plane,
  train: TrainFront,
  bus: Bus,
};

const MODE_LABEL: Record<TravelMode, string> = {
  driving: "Drive",
  flight: "Flight",
  train: "Train",
  bus: "Bus",
};

const STATUS_META: Record<SegmentStatus, string> = {
  rough_estimate: "Estimate",
  static_timetable: "Scheduled",
  live_suggested: "Live option",
  live_tracked: "Live tracked",
  live_booked: "Booked",
};

function formatTime(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(hours: number | null): string {
  if (hours == null) return "—";
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function navigationLink(origin: string, destination: string): string {
  const o = encodeURIComponent(origin);
  const d = encodeURIComponent(destination);
  return `https://www.google.com/maps/dir/?api=1&origin=${o}&destination=${d}&travelmode=driving`;
}

export function SegmentCard({ segment }: { segment: Segment }) {
  const Icon = MODE_ICON[segment.mode];
  const statusLabel = STATUS_META[segment.status];
  const dep = formatTime(segment.departure);
  const arr = formatTime(segment.arrival);
  const trainInfo = segment.mode === "train" ? (segment.provider_data as { train_name?: string; train_number?: string }) : null;

  return (
    <div
      className="relative rounded-3xl p-6 overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.09)",
        backdropFilter: "blur(16px)",
        border: "0.5px solid rgba(255,255,255,0.16)",
        boxShadow: "0 24px 48px -16px rgba(20,10,35,0.5), inset 0 1px 0 rgba(255,255,255,0.1)",
      }}
    >
      <div className="flex items-center gap-3.5 mb-4">
        <div
          className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0"
          style={{
            background: "linear-gradient(135deg, #F0B87A, #D97A4A)",
            boxShadow: "0 8px 18px rgba(217,122,74,0.4)",
          }}
        >
          <Icon size={20} className="text-[#3A1F0A]" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-base font-medium text-white">{segment.origin}</span>
            <ArrowRight size={14} className="text-white/45 shrink-0" />
            <span className="text-base font-medium text-white">{segment.destination}</span>
          </div>
          <p className="text-xs text-white/60 mt-0.5">
            {MODE_LABEL[segment.mode]} &middot; {statusLabel}
          </p>
          {trainInfo?.train_name && (
            <p className="text-xs text-white/50 mt-0.5 font-mono">
              {trainInfo.train_name} &middot; #{trainInfo.train_number}
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-7 gap-y-3 pt-4" style={{ borderTop: "0.5px solid rgba(255,255,255,0.14)" }}>
        <div>
          <p className="text-[10px] uppercase tracking-wide text-white/50 mb-0.5">Duration</p>
          <p className="text-base font-medium text-white">
            {dep && arr ? `${dep} \u2013 ${arr}` : `~${formatDuration(segment.duration_hours_estimate)}`}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wide text-white/50 mb-0.5">Est. cost</p>
          <p className="text-base font-medium text-white">
            {segment.cost.currency} {Math.round(segment.cost.low)}
            {segment.cost.high !== segment.cost.low && `\u2013${Math.round(segment.cost.high)}`}
          </p>
        </div>

        <div className="flex items-center gap-4 ml-auto">
          {segment.mode === "driving" && (
            <a href={navigationLink(segment.origin, segment.destination)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs font-medium hover:opacity-80" style={{ color: "#F0B87A" }}>
              <Navigation size={13} /> Navigate
            </a>
          )}
          {segment.book_external_url && (
            <a href={segment.book_external_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs font-medium hover:opacity-80" style={{ color: "#F0B87A" }}>
              Book <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}