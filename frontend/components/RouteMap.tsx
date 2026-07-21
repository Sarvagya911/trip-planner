"use client";

import { useEffect, useRef } from "react";
import type { Segment, RestStop } from "@/lib/api";

// Decodes an ORS/Google-style encoded polyline into [lat, lon] pairs.
// ORS returns this format in provider_data.route_polyline.
function decodePolyline(encoded: string): [number, number][] {
  const points: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let b: number;
    let shift = 0;
    let result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push([lat / 1e5, lng / 1e5]);
  }
  return points;
}

export function RouteMap({ segments }: { segments: Segment[] }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<import("leaflet").Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");
      if (cancelled || !mapRef.current) return;

      const map = L.map(mapRef.current, { scrollWheelZoom: false });
      mapInstance.current = map;

      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
  attribution: '&copy; OpenStreetMap contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  maxZoom: 19,
}).addTo(map);


      const bounds: [number, number][] = [];
      const driveIcon = L.divIcon({
        className: "",
        html: `<div style="width:12px;height:12px;border-radius:50%;background:#0F6E56;border:2px solid white;box-shadow:0 0 0 1px #0F6E56;"></div>`,
        iconSize: [12, 12],
      });
      const stopIcon = L.divIcon({
        className: "",
        html: `<div style="width:10px;height:10px;border-radius:50%;background:#B45309;border:2px solid white;box-shadow:0 0 0 1px #B45309;"></div>`,
        iconSize: [10, 10],
      });

      for (const seg of segments) {
        if (seg.mode !== "driving") continue;
        const polyline = (seg.provider_data as { route_polyline?: string })?.route_polyline;
        if (!polyline) continue;

        const points = decodePolyline(polyline);
        if (points.length === 0) continue;

        L.polyline(points, { color: "#0F6E56", weight: 4, opacity: 0.85 }).addTo(map);
        bounds.push(...points);

        const start = points[0];
        const end = points[points.length - 1];
        L.marker(start, { icon: driveIcon }).addTo(map).bindPopup(seg.origin);
        L.marker(end, { icon: driveIcon }).addTo(map).bindPopup(seg.destination);

        const stop = (seg.provider_data as { stop?: RestStop })?.stop;
        if (stop) {
          L.marker([stop.near_latitude, stop.near_longitude], { icon: stopIcon })
            .addTo(map)
            .bindPopup(`Suggested stop: ${stop.fuel?.name ?? stop.food?.name ?? "rest point"}`);
        }
      }

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [24, 24] });
      } else {
        map.setView([20.5937, 78.9629], 5); // fallback: India center
      }
    })();

    return () => {
      cancelled = true;
      mapInstance.current?.remove();
      mapInstance.current = null;
    };
  }, [segments]);

  const hasDrivingLeg = segments.some((s) => s.mode === "driving");
  if (!hasDrivingLeg) return null;

  return (
    <div className="mt-6">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-soft mb-3">
        Route map
      </h2>
      <div
        ref={mapRef}
        className="w-full h-72 sm:h-96 rounded-xl border border-line overflow-hidden"
        style={{ background: "var(--card)" }}
      />
    </div>
  );
}