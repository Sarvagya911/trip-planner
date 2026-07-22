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
from app.models.conversation import (
    ConversationRequest,
    ConversationResponse,
)
from app.models.places import DestinationInfo
from app.services.journey_videos import get_mode_video
from app.services.destination_photos import search_photo
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

# Conversation service is created lazily so the app still boots (and the
# trip-planning endpoints still work) even if no GROQ_API_KEY is set yet.
_conversation_service = None


def get_conversation_service():
    global _conversation_service
    if _conversation_service is None:
        from app.services.conversation import ConversationService
        _conversation_service = ConversationService()
    return _conversation_service


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
    budget_inr: int | None = None


class TripPlanResponse(BaseModel):
    trip: TripSegments
    warnings: list[str]
    destination_info: list[DestinationInfo] = []


@app.post("/api/v1/trip/plan", response_model=TripPlanResponse)
async def plan_trip(req: TripPlanRequest) -> TripPlanResponse:
    """Plan a full multi-mode trip: one leg per entry in `legs`, stitched
    into an ordered TripSegments, with hotel suggestions per destination."""
    party = PartyComposition(
        adults=req.adults,
        children=req.children,
        elders=req.elders,
        has_pets=req.has_pets,
    )
    legs = [LegRequest(mode=leg.mode, origin=leg.origin, destination=leg.destination) for leg in req.legs]

    try:
        result = await orchestrator.plan_trip(legs, req.depart_date, party, budget_inr=req.budget_inr)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TripPlanResponse(
        trip=result.trip,
        warnings=result.warnings,
        destination_info=result.destination_info,
    )


@app.post("/api/v1/conversation", response_model=ConversationResponse)
async def conversation(req: ConversationRequest) -> ConversationResponse:
    """Hold a planning conversation. The frontend sends the full message
    history plus the structured brief so far; we return the assistant's
    reply and an updated brief. Stateless — no server-side session store."""
    try:
        service = get_conversation_service()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"conversation service unavailable: {exc}") from exc

    try:
        reply, brief = await service.respond(req.messages, req.brief)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"conversation failed: {exc}") from exc

    return ConversationResponse(reply=reply, brief=brief)


@app.get("/api/v1/journey-video")
async def journey_video(mode: str) -> dict[str, str | None]:
    """Returns a scenic background video URL for a travel mode (driving,
    bus, flight, train), used for the immersive journey-progress hero.
    Best-effort — returns {"url": null} if unavailable rather than erroring."""
    url = await get_mode_video(mode)
    return {"url": url}


@app.get("/api/v1/scenic-photo")
async def scenic_photo(query: str = "mountains scenic landscape") -> dict[str, str | None]:
    """Returns a generic scenic photo URL for page-background atmosphere
    (not tied to a specific trip destination). Best-effort — returns
    {"url": null} if unavailable rather than erroring."""
    url = await search_photo(query)
    return {"url": url}


@app.get("/api/v1/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "modes_available": [m.value for m in registry.all_modes()]}