"""
Photo lookup backed by Unsplash's free API.

Used for two things: destination hero photos (WhereToStay — "what does
Madikeri look like") and a generic scenic background photo for the plan
page's atmosphere. Never used for individual hotels — showing a generic
stock photo next to a specific hotel name would misleadingly imply it's a
real photo of that building.

Best-effort: any failure (no key, rate limit, no results) returns None
rather than raising, so a missing photo never breaks the page.
"""

from __future__ import annotations

import os

import httpx

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


async def search_photo(query: str) -> str | None:
    """Return a landscape photo URL matching a search query, or None if
    unavailable."""
    api_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                UNSPLASH_SEARCH_URL,
                params={
                    "query": query,
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


async def get_destination_photo(destination: str) -> str | None:
    """Return a photo URL for a destination, or None if unavailable."""
    return await search_photo(f"{destination} India travel")