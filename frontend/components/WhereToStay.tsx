import { Building2, ExternalLink, Info } from "lucide-react";
import type { DestinationInfo } from "@/lib/api";

export function WhereToStay({ destinations }: { destinations: DestinationInfo[] }) {
  const withHotels = destinations.filter((d) => d.hotels.length > 0);
  if (withHotels.length === 0) return null;

  return (
    <div className="mt-8">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft mb-1">
        Where to stay
      </h2>
      <p className="flex items-center gap-1.5 text-xs text-ink-soft mb-4">
        <Info size={13} className="shrink-0" />
        Ratings aren&apos;t shown here — check reviews on the booking site before you book.
      </p>

      <div className="space-y-6">
        {withHotels.map((dest) => (
          <div key={dest.destination}>
            <p className="text-sm font-medium mb-2">{dest.destination}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {dest.hotels.map((hotel, i) => (
                <div key={i} className="flex flex-col bg-card border border-line rounded-xl p-4">
                  <div className="flex items-start gap-2.5 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-route-soft flex items-center justify-center shrink-0">
                      <Building2 size={16} className="text-route" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-sm leading-tight">{hotel.name}</p>
                      {hotel.address && (
                        <p className="text-xs text-ink-soft truncate mt-0.5">{hotel.address}</p>
                      )}
                    </div>
                  </div>

                  {hotel.why && <p className="text-sm text-ink-soft flex-1">{hotel.why}</p>}

                  {hotel.book_external_url && (
                    <a href={hotel.book_external_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-route hover:underline mt-3 self-start">
                      Find &amp; book <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}