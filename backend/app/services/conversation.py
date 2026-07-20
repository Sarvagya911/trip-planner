# """
# Conversation service — the LLM layer.
#
# Gemini does two things each turn: (1) writes a natural reply that moves the
# conversation forward (asking what's still missing, suggesting destinations
# when the user is unsure), and (2) updates the structured TripBrief with
# whatever new information the latest user message revealed.
#
# We get both in one call by asking Gemini to return JSON with a `reply`
# string and a `brief` object. This keeps the LLM in its lane: it decides
# intent, destinations, and modes, but the brief's legs are later priced by
# the deterministic orchestrator — the model never states a distance or fare.
#
# Free-tier Gemini returns transient 503 "high demand" errors fairly often,
# so we retry a few times with a short backoff before giving up. That keeps
# those spikes from ever reaching the user.
# """
#
# from __future__ import annotations
#
# import asyncio
# import json
# import os
# from datetime import date
#
# from google import genai
# from google.genai import types
#
# from app.models.conversation import ConversationMessage, TripBrief
#
# MODEL = "gemini-2.0-flash"
# MAX_RETRIES = 4
# RETRY_BACKOFF_SECONDS = 1.5
#
# SYSTEM_INSTRUCTION = """You are a friendly, concise travel planning assistant for an app that plans \
# multi-mode trips across India (driving, flights, trains, buses) — and can mix them in one trip.
#
# Your job each turn:
# 1. Reply naturally and briefly (1-3 sentences). Ask for the single most important missing piece \
# of information, not everything at once.
# 2. If the user is unsure where to go, suggest 2-3 concrete destinations that fit what they've said \
# (vibe, budget, who's travelling), and ask which appeals.
# 3. Update the structured trip brief with anything new the user told you.
#
# Information you're trying to gather, roughly in priority order: where they're starting from, \
# rough dates, how many people (adults/children/elders) and whether pets, budget, and preferences/vibe.
#
# Once you know the origin, at least one destination, and roughly who is travelling, propose concrete \
# legs (mode + origin + destination for each hop) and set ready=true. Choose sensible modes: flights \
# for long distances, driving/train/bus for shorter hops. You decide destinations and modes; you do NOT \
# state distances, durations, or prices — the app calculates those separately.
#
# IMPORTANT: for each leg's origin and destination, use a specific, routable town or city name — never \
# a broad region, district, or area. For example use "Madikeri" not "Coorg", "Manali" not "Himachal", \
# "Gangtok" not "Sikkim". A named town routes correctly; a region does not. When suggesting a \
# destination in conversation you may use the familiar name, but in proposed_legs always use the \
# specific town.
#
# Always respond with ONLY a JSON object, no markdown, in exactly this shape:
# {
#   "reply": "<your natural reply to the user>",
#   "brief": {
#     "origin": <string or null>,
#     "depart_date": <"YYYY-MM-DD" or null>,
#     "return_date": <"YYYY-MM-DD" or null>,
#     "adults": <int>,
#     "children": <int>,
#     "elders": <int>,
#     "has_pets": <bool>,
#     "budget_inr": <int or null>,
#     "preferences": [<string>, ...],
#     "destinations": [<string>, ...],
#     "proposed_legs": [{"mode": "flight|train|bus|driving", "origin": <string>, "destination": <string>}, ...],
#     "ready": <bool>
#   }
# }
#
# Carry forward everything already known in the brief you're given — only add or refine, never drop \
# information the user already provided."""
#
#
# class ConversationService:
#     def __init__(self, api_key: str | None = None) -> None:
#         self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
#         self._client = genai.Client(api_key=self.api_key)
#
#     async def respond(
#         self,
#         messages: list[ConversationMessage],
#         brief: TripBrief,
#     ) -> tuple[str, TripBrief]:
#         convo = "\n".join(f"{m.role}: {m.content}" for m in messages)
#         today = date.today().isoformat()
#         prompt = (
#             f"Today's date is {today}. Resolve any relative dates the user "
#             f"mentions (e.g. 'next Friday', 'in two weeks') against this, and "
#             f"always output dates as future dates in YYYY-MM-DD form.\n\n"
#             f"Current trip brief (JSON):\n{brief.model_dump_json()}\n\n"
#             f"Conversation so far:\n{convo}\n\n"
#             f"Produce your JSON response now."
#         )
#
#         response = await self._generate_with_retry(prompt)
#
#         raw = (response.text or "").strip()
#         try:
#             data = json.loads(raw)
#         except json.JSONDecodeError:
#             return (raw or "Sorry, could you say that another way?", brief)
#
#         reply = data.get("reply", "")
#         brief_data = data.get("brief", {})
#         try:
#             updated_brief = TripBrief.model_validate(brief_data)
#         except Exception:
#             updated_brief = brief
#
#         return reply, updated_brief
#
#     async def _generate_with_retry(self, prompt: str):
#         """Call Gemini, retrying on transient 503 'high demand' errors."""
#         last_exc = None
#         for attempt in range(MAX_RETRIES):
#             try:
#                 return self._client.models.generate_content(
#                     model=MODEL,
#                     contents=prompt,
#                     config=types.GenerateContentConfig(
#                         system_instruction=SYSTEM_INSTRUCTION,
#                         response_mime_type="application/json",
#                         temperature=0.6,
#                     ),
#                 )
#             except Exception as exc:
#                 last_exc = exc
#                 # Retry only on transient overload; fail fast on real errors
#                 # (bad key, invalid model, etc.).
#                 if "503" in str(exc) or "UNAVAILABLE" in str(exc):
#                     await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
#                     continue
#                 raise
#         raise last_exc

"""
Conversation service — the LLM layer (Groq via the OpenAI-compatible SDK).

Groq's free tier is far more generous than Gemini's, and it's OpenAI-SDK
compatible, so we point the OpenAI client at Groq's base URL. Each turn the
model (1) writes a natural reply and (2) updates the structured TripBrief,
returned together as one JSON object. The LLM decides intent, destinations,
and modes; the brief's legs are priced later by the deterministic
orchestrator — the model never states a distance or fare.

Free-tier Gemini/Groq can return transient 5xx/429 errors, so we retry a few
times with a short backoff before giving up.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import date

from openai import OpenAI

from app.models.conversation import ConversationMessage, TripBrief

MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 1.5

SYSTEM_INSTRUCTION = """You are a friendly, concise travel planning assistant for an app that plans \
multi-mode trips across India (driving, flights, buses) — and can mix them in one trip.

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
for long distances, driving/bus for shorter hops. You decide destinations and modes; you do NOT \
state distances, durations, or prices — the app calculates those separately.

IMPORTANT: for each leg's origin and destination, use a specific, routable town or city name — never \
a broad region, district, or area. For example use "Madikeri" not "Coorg", "Manali" not "Himachal", \
"Gangtok" not "Sikkim". A named town routes correctly; a region does not. When suggesting a \
destination in conversation you may use the familiar name, but in proposed_legs always use the \
specific town.

Do NOT propose train legs — train scheduling data isn't available yet, so a train leg cannot be \
planned and will fail. Prefer driving, flights, or buses. If the user asks to avoid flights, use \
bus or driving instead of train.

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
    "proposed_legs": [{"mode": "flight|bus|driving", "origin": <string>, "destination": <string>}, ...],
    "ready": <bool>
  }
}

Carry forward everything already known in the brief you're given — only add or refine, never drop \
information the user already provided.

If the brief already has proposed_legs (the user is REFINING an existing plan, not starting fresh), \
treat their message as an edit to that plan: adjust only what they ask for and keep the rest. When you \
change something (swap a flight for a bus to save money, remove a leg, add a destination), say clearly \
in your reply what you changed and why, in one short sentence. Keep ready=true when a valid plan still \
exists after the edit."""


class ConversationService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self._client = OpenAI(api_key=self.api_key, base_url=GROQ_BASE_URL)

    async def respond(
        self,
        messages: list[ConversationMessage],
        brief: TripBrief,
    ) -> tuple[str, TripBrief]:
        convo = "\n".join(f"{m.role}: {m.content}" for m in messages)
        today = date.today().isoformat()
        user_prompt = (
            f"Today's date is {today}. Resolve any relative dates the user "
            f"mentions (e.g. 'next Friday', 'in two weeks') against this, and "
            f"always output dates as future dates in YYYY-MM-DD form.\n\n"
            f"Current trip brief (JSON):\n{brief.model_dump_json()}\n\n"
            f"Conversation so far:\n{convo}\n\n"
            f"Produce your JSON response now."
        )

        raw = await self._generate_with_retry(user_prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return (raw or "Sorry, could you say that another way?", brief)

        reply = data.get("reply", "")
        brief_data = data.get("brief", {})
        try:
            updated_brief = TripBrief.model_validate(brief_data)
        except Exception:
            updated_brief = brief

        return reply, updated_brief

    async def _generate_with_retry(self, user_prompt: str) -> str:
        """Call Groq, retrying on transient 429/5xx errors."""
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                completion = self._client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.6,
                    response_format={"type": "json_object"},
                )
                return (completion.choices[0].message.content or "").strip()
            except Exception as exc:
                last_exc = exc
                msg = str(exc)
                if "429" in msg or "503" in msg or "500" in msg:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue
                raise
        raise last_exc