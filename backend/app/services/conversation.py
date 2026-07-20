"""
Conversation service — the LLM layer.

Gemini does two things each turn: (1) writes a natural reply that moves the
conversation forward (asking what's still missing, suggesting destinations
when the user is unsure), and (2) updates the structured TripBrief with
whatever new information the latest user message revealed.

We get both in one call by asking Gemini to return JSON with a `reply`
string and a `brief` object. This keeps the LLM in its lane: it decides
intent, destinations, and modes, but the brief's legs are later priced by
the deterministic orchestrator — the model never states a distance or fare.
"""

from __future__ import annotations

import json
import os

from google import genai
from google.genai import types

from app.models.conversation import ConversationMessage, TripBrief

MODEL = "gemini-flash-latest"

SYSTEM_INSTRUCTION = """You are a friendly, concise travel planning assistant for an app that plans \
multi-mode trips across India (driving, flights, trains, buses) — and can mix them in one trip.

Your job each turn:
1. Reply naturally and briefly (1-3 sentences). Ask for the single most important missing piece \
of information, not everything at once.
2. If the user is unsure where to go, suggest 2-3 concrete destinations that fit what they've said \
(vibe, budget, who's travelling), and ask which appeals.
3. Update the structured trip brief with anything new the user told you.

Information you're trying to gather, roughly in priority order: where they're starting from, \
rough dates, how many people (adults/children/elders) and whether pets, budget, and preferences/vibe.

Once you know the origin, at least one destination, and roughly who is travelling, propose concrete \
legs (mode + origin + destination for each hop) and set ready=true. Choose sensible modes: flights \
for long distances, driving/train/bus for shorter hops. You decide destinations and modes; you do NOT \
state distances, durations, or prices — the app calculates those separately.

Always respond with ONLY a JSON object, no markdown, in exactly this shape:
{
  "reply": "<your natural reply to the user>",
  "brief": {
    "origin": <string or null>,
    "depart_date": <"YYYY-MM-DD" or null>,
    "return_date": <"YYYY-MM-DD" or null>,
    "adults": <int>,
    "children": <int>,
    "elders": <int>,
    "has_pets": <bool>,
    "budget_inr": <int or null>,
    "preferences": [<string>, ...],
    "destinations": [<string>, ...],
    "proposed_legs": [{"mode": "flight|train|bus|driving", "origin": <string>, "destination": <string>}, ...],
    "ready": <bool>
  }
}

Carry forward everything already known in the brief you're given — only add or refine, never drop \
information the user already provided."""


class ConversationService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._client = genai.Client(api_key=self.api_key)

    async def respond(
        self,
        messages: list[ConversationMessage],
        brief: TripBrief,
    ) -> tuple[str, TripBrief]:
        # Give the model the running brief plus the conversation so far.
        convo = "\n".join(f"{m.role}: {m.content}" for m in messages)
        prompt = (
            f"Current trip brief (JSON):\n{brief.model_dump_json()}\n\n"
            f"Conversation so far:\n{convo}\n\n"
            f"Produce your JSON response now."
        )

        response = self._client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.6,
            ),
        )

        raw = (response.text or "").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Model didn't return clean JSON — degrade gracefully rather than
            # 500. Keep the old brief, surface the raw text as the reply.
            return (raw or "Sorry, could you say that another way?", brief)

        reply = data.get("reply", "")
        brief_data = data.get("brief", {})
        try:
            updated_brief = TripBrief.model_validate(brief_data)
        except Exception:
            # Malformed brief — keep the previous one, still return the reply.
            updated_brief = brief

        return reply, updated_brief