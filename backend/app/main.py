"""
FastAPI entrypoint.
"""

from __future__ import annotations

from datetime import date

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models.segment import Segment, TravelMode, TripSegments
from app.providers.base import PartyComposition
from app.providers.registry import build_default_registry
from app.services.orchestrator import LegRequest, TripOrchestrator

app = FastAPI(title="Trip Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = build_default_registry()
orchestrator = TripOrchestrator(registry)


class SegmentSearchRequest(BaseModel):
    mode: TravelMode
    origin: str
    destination: str
    depart_date: date
    adults: int = 1
    children: int = 0
    elders: int = 0
    has_pets: bool = False


@app.post("/api/v1/segment/search", response_model=list[Segment])
async def search_segment(req: SegmentSearchRequest) -> list[Segment]:
    """Search a single segment/leg for one mode. This is the building block
    the orchestrator calls once per leg in /trip/plan below."""
    try:
        provider = registry.get(req.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    party = PartyComposition(
        adults=req.adults,
        children=req.children,
        elders=req.elders,
        has_pets=req.has_pets,
    )

    try:
        return await provider.search(req.origin, req.destination, req.depart_date, party)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


class LegIn(BaseModel):
    mode: TravelMode
    origin: str
    destination: str


class TripPlanRequest(BaseModel):
    legs: list[LegIn]
    depart_date: date
    adults: int = 1
    children: int = 0
    elders: int = 0
    has_pets: bool = False


class TripPlanResponse(BaseModel):
    trip: TripSegments
    warnings: list[str]


@app.post("/api/v1/trip/plan", response_model=TripPlanResponse)
async def plan_trip(req: TripPlanRequest) -> TripPlanResponse:
    """Plan a full multi-mode trip: one leg per entry in `legs`, stitched
    into an ordered TripSegments. This is the mixed-mode endpoint —
    e.g. a flight leg followed by a driving leg followed by a train leg,
    all in one request."""
    party = PartyComposition(
        adults=req.adults,
        children=req.children,
        elders=req.elders,
        has_pets=req.has_pets,
    )
    legs = [LegRequest(mode=leg.mode, origin=leg.origin, destination=leg.destination) for leg in req.legs]

    try:
        result = await orchestrator.plan_trip(legs, req.depart_date, party)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TripPlanResponse(trip=result.trip, warnings=result.warnings)


@app.get("/api/v1/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "modes_available": [m.value for m in registry.all_modes()]}