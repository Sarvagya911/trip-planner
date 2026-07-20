"""
The TripBrief is the structured bridge between free-form conversation and
the deterministic trip planner. The conversation's whole job is to fill
this in. Once it's complete enough, its suggested legs feed straight into
the existing orchestrator (/trip/plan) — which is what actually prices and
routes them. The LLM proposes destinations and modes; it never invents
distances or fares.

Everything here is Optional because a brief is built up gradually over a
multi-turn conversation — early on most fields are still unknown.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.segment import TravelMode


class BriefLeg(BaseModel):
    """One proposed leg. Mirrors what the orchestrator needs, so a complete
    brief converts directly into a trip plan request."""
    mode: TravelMode
    origin: str
    destination: str


class TripBrief(BaseModel):
    origin: str | None = Field(None, description="Where the trip starts from")
    depart_date: str | None = Field(None, description="ISO date YYYY-MM-DD if known")
    return_date: str | None = Field(None, description="ISO date YYYY-MM-DD if known")

    adults: int = 1
    children: int = 0
    elders: int = 0
    has_pets: bool = False

    budget_inr: int | None = Field(None, description="Total rough budget in INR if the user gave one")
    preferences: list[str] = Field(default_factory=list, description="Free-form vibe/interest tags, e.g. 'beach', 'quiet', 'kid-friendly'")

    # Destinations the user has settled on, or the AI has suggested and the
    # user accepted. May be empty early in the conversation.
    destinations: list[str] = Field(default_factory=list)

    # Concrete legs, once enough is known to propose a route. When this is
    # populated and `ready` is true, it can be handed to /trip/plan.
    proposed_legs: list[BriefLeg] = Field(default_factory=list)

    # The model's own assessment: does it have enough to propose a trip?
    ready: bool = Field(False, description="True when enough info exists to propose concrete legs")


class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ConversationRequest(BaseModel):
    """Stateless: the frontend sends the whole history each turn, so the
    backend needs no session store yet. `brief` carries the structured
    state extracted so far, also round-tripped by the client."""
    messages: list[ConversationMessage]
    brief: TripBrief = Field(default_factory=TripBrief)


class ConversationResponse(BaseModel):
    reply: str  # what the assistant says back to the user
    brief: TripBrief  # updated structured state