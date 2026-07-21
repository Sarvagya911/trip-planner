"""
Scenic background video per travel mode, backed by Pixabay's free Video API.

Used only for the immersive journey-progress hero — a generic "view from
the road/window" clip that matches the current leg's mode. This is stock
footage, not a real photo/video of the user's specific route, same honesty
principle as the destination hero photos (Unsplash): atmosphere, not a
factual claim about the actual trip.

Best-effort: any failure (no key, no results, rate limit) returns None
rather than raising, so a missing video never breaks the page.
"""

from __future__ import annotations

import os

import httpx

PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"

# Search terms tuned per mode for a scenic, road/window-view feel.
# No category filter — Pixabay's "places" category skews toward landmarks
# and buildings, which crowds out transport-specific footage.
MODE_QUERIES = {
    "driving": "scenic road drive mountain",
    "bus": "bus window road travel",
    "flight": "airplane window clouds",
    "train": "train window countryside",
}


async def get_mode_video(mode: str) -> str | None:
    """Return a looping video URL (medium quality) for a travel mode, or
    None if unavailable."""
    api_key = os.environ.get("PIXABAY_API_KEY", "")
    if not api_key:
        return None

    query = MODE_QUERIES.get(mode, "scenic travel road")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                PIXABAY_VIDEO_URL,
                params={
                    "key": api_key,
                    "q": query,
                    "video_type": "film",
                    "safesearch": "true",
                    "per_page": 5,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return None

    hits = data.get("hits", [])
    if not hits:
        return None

    # "medium" balances quality and file size for a looping background clip.
    videos = hits[0].get("videos", {})
    medium = videos.get("medium", {}) or videos.get("small", {})
    return medium.get("url")