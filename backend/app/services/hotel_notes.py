"""
Batched "why stay here" note generator.

Takes all the hotels across all destinations and writes a short one-line
"why" for each — in a SINGLE Groq call, not one per hotel. Keeps LLM usage
to exactly one extra call per trip plan regardless of hotel count, which is
both fast and quota-light.

Degrades gracefully: if the call fails or the key is missing, hotels simply
come back without a `why` line — the feature still works, just less flavored.
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from app.models.places import Place

MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM = """You write very short, appealing one-line descriptions of hotels for a travel app.
For each hotel given, write a single sentence (max ~15 words) on why a traveler might like staying there,
based on its name and location. Be concrete and warm, never generic filler like "great choice".
If the name suggests something (heritage, homestay, comforts, resort), lean into it.
Respond with ONLY a JSON object mapping each hotel name exactly to its one-line description:
{"Hotel Name": "why line", ...}"""


async def annotate_hotels(hotels_by_destination: dict[str, list[Place]]) -> None:
    """Fill each Place.why in-place. Best-effort; silently skips on failure."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return

    # Flatten to (destination, hotel) so the prompt has context.
    lines = []
    for dest, hotels in hotels_by_destination.items():
        for h in hotels:
            lines.append(f"- {h.name} (in {dest})")
    if not lines:
        return

    prompt = "Hotels:\n" + "\n".join(lines) + "\n\nWrite the JSON now."

    try:
        client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        raw = (completion.choices[0].message.content or "").strip()
        notes = json.loads(raw)
    except Exception:
        return  # best-effort; leave why=None

    for hotels in hotels_by_destination.values():
        for h in hotels:
            note = notes.get(h.name)
            if isinstance(note, str) and note.strip():
                h.why = note.strip()