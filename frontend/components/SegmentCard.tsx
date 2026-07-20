import { Car, Plane, TrainFront, Bus, ExternalLink } from "lucide-react";
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

const STATUS_META: Record<SegmentStatus, { label: string; color: string; bg: string }> = {
  rough_estimate: { label: "Estimate", color: "var(--amber)", bg: "var(--amber-soft)" },
  static_timetable: { label: "Scheduled", color: "var(--route)", bg: "var(--route-soft)" },
  live_suggested: { label: "Live option", color: "var(--signal)", bg: "var(--signal-soft)" },
  live_tracked: { label: "Live tracked", color: "var(--signal)", bg: "var(--signal-soft)" },
  live_booked: { label: "Booked", color: "var(--signal)", bg: "var(--signal-soft)" },
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

export function SegmentCard({ segment }: { segment: Segment }) {
  const Icon = MODE_ICON[segment.mode];
  const status = STATUS_META[segment.status];
  const dep = formatTime(segment.departure);
  const arr = formatTime(segment.arrival);
  const trainInfo = segment.mode === "train" ? (segment.provider_data as { train_name?: string; train_number?: string }) : null;

  return (
    <div className="flex rounded-xl overflow-hidden border border-line bg-card shadow-sm">
      <div className="flex flex-col items-center justify-center w-12 shrink-0 bg-ink text-paper font-mono text-sm font-semibold">
        {String(segment.order).padStart(2, "0")}
      </div>

      <div className="flex flex-1 flex-col sm:flex-row">
        <div className="flex-1 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon size={18} className="text-route" />
            <span className="font-semibold text-sm">{MODE_LABEL[segment.mode]}</span>
            <span
              className="text-xs font-mono px-2 py-0.5 rounded-full"
              style={{ color: status.color, background: status.bg }}
            >
              {status.label}
            </span>
          </div>

          <div className="flex items-baseline gap-2 text-base font-medium">
            <span>{segment.origin}</span>
            <span className="text-ink-soft">&rarr;</span>
            <span>{segment.destination}</span>
          </div>

          {trainInfo?.train_name && (
            <p className="text-xs text-ink-soft mt-1 font-mono">
              {trainInfo.train_name} · #{trainInfo.train_number}
            </p>
          )}

          <div className="flex items-center gap-4 mt-2 text-sm text-ink-soft font-mono">
            {dep && arr ? (
              <span>{dep} &ndash; {arr}</span>
            ) : (
              <span>~{formatDuration(segment.duration_hours_estimate)}</span>
            )}
          </div>
        </div>

        <div className="ticket-notch w-px hidden sm:block" />
        <div className="ticket-notch h-px sm:hidden" />

        <div className="p-4 sm:w-48 shrink-0 flex sm:flex-col justify-between items-center sm:items-start gap-2">
          <div>
            <p className="text-xs text-ink-soft uppercase tracking-wide">Est. cost</p>
            <p className="font-mono font-semibold">
              {segment.cost.currency} {Math.round(segment.cost.low)}
              {segment.cost.high !== segment.cost.low && `–${Math.round(segment.cost.high)}`}
            </p>
          </div>
          {segment.book_external_url && (
            <a href={segment.book_external_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-route hover:underline">
              Book <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}