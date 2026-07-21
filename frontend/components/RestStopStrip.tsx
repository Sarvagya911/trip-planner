import { Fuel, Utensils, MapPin, ExternalLink } from "lucide-react";
import type { RestStop } from "@/lib/api";

export function RestStopStrip({ stop }: { stop: RestStop }) {
  if (!stop.fuel && !stop.food) return null;

  return (
    <div className="ml-12 mt-1 mb-1 flex items-start gap-2 rounded-lg bg-route-soft/50 border border-line px-3 py-2.5">
      <MapPin size={15} className="text-route shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-route mb-1.5">
          Suggested break · {stop.label}
        </p>
        <div className="flex flex-col sm:flex-row sm:gap-6 gap-1.5">
          {stop.fuel && (
            <div className="flex items-center gap-1.5 text-sm min-w-0">
              <Fuel size={14} className="text-ink-soft shrink-0" />
              <span className="truncate">{stop.fuel.name}</span>
              {stop.fuel.book_external_url && (
                <a href={stop.fuel.book_external_url} target="_blank" rel="noopener noreferrer" className="text-route shrink-0" aria-label="Find fuel stop on map">
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
          )}
          {stop.food && (
            <div className="flex items-center gap-1.5 text-sm min-w-0">
              <Utensils size={14} className="text-ink-soft shrink-0" />
              <span className="truncate">{stop.food.name}</span>
              {stop.food.book_external_url && (
                <a href={stop.food.book_external_url} target="_blank" rel="noopener noreferrer" className="text-route shrink-0" aria-label="Find food stop on map">
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}