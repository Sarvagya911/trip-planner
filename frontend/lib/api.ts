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
  destination_info: DestinationInfo[];
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8002";

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

// --- Conversation ---
// Mirrors backend/app/models/conversation.py

export interface BriefLeg {
  mode: TravelMode;
  origin: string;
  destination: string;
}

export interface TripBrief {
  origin: string | null;
  depart_date: string | null;
  return_date: string | null;
  adults: number;
  children: number;
  elders: number;
  has_pets: boolean;
  budget_inr: number | null;
  preferences: string[];
  destinations: string[];
  proposed_legs: BriefLeg[];
  ready: boolean;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ConversationRequest {
  messages: ConversationMessage[];
  brief: TripBrief;
}

export interface ConversationResponse {
  reply: string;
  brief: TripBrief;
}

export function emptyBrief(): TripBrief {
  return {
    origin: null,
    depart_date: null,
    return_date: null,
    adults: 1,
    children: 0,
    elders: 0,
    has_pets: false,
    budget_inr: null,
    preferences: [],
    destinations: [],
    proposed_legs: [],
    ready: false,
  };
}

export async function converse(req: ConversationRequest): Promise<ConversationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/conversation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(`Conversation failed (${res.status}): ${body}`, res.status);
  }

  return res.json();
}

// --- Destination enrichment (hotels + photo) ---
// Mirrors backend/app/models/places.py

export interface Place {
  name: string;
  category: string;
  rating: number | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  why: string | null;
  book_external_url: string | null;
}

export interface DestinationInfo {
  destination: string;
  hotels: Place[];
  photo_url: string | null;
}

// A suggested rest stop on a long driving leg (rides in segment.provider_data.stop)
export interface RestStop {
  label: string;
  near_latitude: number;
  near_longitude: number;
  fuel: Place | null;
  food: Place | null;
}

// --- Journey hero video ---
export async function getJourneyVideo(mode: TravelMode): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/journey-video?mode=${mode}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.url ?? null;
  } catch {
    return null;
  }
}