"""
Destination hero photos, backed by Unsplash's free API.

This is intentionally NOT used for individual hotels — showing a generic
stock photo next to a specific hotel name would misleadingly imply it's a
real photo of that building. It's honest and useful for a destination
("what does Madikeri look like"), which is what this is scoped to.

Best-effort: any failure (no key, rate limit, no results) returns None
rather than raising, so a photo being unavailable never breaks the plan.
"""

from __future__ import annotations

import os

import httpx

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


async def get_destination_photo(destination: str) -> str | None:
    """Return a photo URL for a destination, or None if unavailable."""
    api_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                UNSPLASH_SEARCH_URL,
                params={
                    "query": f"{destination} India travel",
                    "per_page": 1,
                    "orientation": "landscape",
                },
                headers={"Authorization": f"Client-ID {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return None

    results = data.get("results", [])
    if not results:
        return None

    urls = results[0].get("urls", {})
    return urls.get("regular") or urls.get("small")