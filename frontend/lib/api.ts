// Types mirror backend/app/models/segment.py exactly. If that schema
// changes, update here too — this is the one place the frontend
// depends on the backend's shape.

export type TravelMode = "driving" | "flight" | "train" | "bus";

export type SegmentStatus =
  | "rough_estimate"
  | "static_timetable"
  | "live_suggested"
  | "live_tracked"
  | "live_booked";

export interface CostEstimate {
  low: number;
  high: number;
  currency: string;
}

export interface Segment {
  segment_id: string;
  order: number;
  mode: TravelMode;
  status: SegmentStatus;
  provider: string;
  origin: string;
  destination: string;
  departure: string | null;
  arrival: string | null;
  duration_hours_estimate: number | null;
  cost: CostEstimate;
  book_external_url: string | null;
  provider_data: Record<string, unknown>;
}

export interface TripSegments {
  segments: Segment[];
}

export interface TripPlanResponse {
  trip: TripSegments;
  warnings: string[];
}

export interface LegInput {
  mode: TravelMode;
  origin: string;
  destination: string;
}

export interface TripPlanRequest {
  legs: LegInput[];
  depart_date: string; // YYYY-MM-DD
  adults: number;
  children: number;
  elders: number;
  has_pets: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function planTrip(req: TripPlanRequest): Promise<TripPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/trip/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(`Trip planning failed (${res.status}): ${body}`, res.status);
  }

  return res.json();
}