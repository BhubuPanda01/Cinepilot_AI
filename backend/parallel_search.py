"""Parallel Search API client -- grounds location scouting in real web data.

Used by the Location Scout Agent to research actual filming permits, costs, and
logistics for a screenplay's locations, instead of relying on the model's own
(often outdated or invented) assumptions.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from parallel import Parallel

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

# 'turbo' is the low-latency/low-cost tier -- appropriate here because we issue
# one search per distinct location and don't need exhaustive research depth.
SEARCH_MODE = "turbo"
MAX_CHARS_TOTAL = 4000

_client: Optional[Parallel] = None


def _get_client() -> Parallel:
    global _client
    if _client is None:
        api_key = os.environ.get("PARALLEL_API_KEY")
        if not api_key:
            raise RuntimeError("PARALLEL_API_KEY is not set")
        _client = Parallel(api_key=api_key)
    return _client


def _search_sync(location: str) -> dict:
    client = _get_client()

    # NOTE: deliberately do NOT mix the screenplay title into these queries --
    # a fictional title (e.g. "SAFAR") derails the search toward unrelated pages.
    # Only the real-world location name should drive the lookup.
    response = client.search(
        objective=(
            f"Find practical film production information for shooting on location at "
            f"{location}: which government body or authority issues filming permits, the "
            f"application process, permit fees, access restrictions, and crowd or traffic "
            f"constraints a production crew should plan for."
        ),
        search_queries=[
            f"film shooting permit application authority {location}",
            f"government permission rules filming {location}",
            f"{location} filming restrictions crew access",
        ],
        mode=SEARCH_MODE,
        max_chars_total=MAX_CHARS_TOTAL,
    )

    return {
        "location": location,
        "results": [
            {
                "title": r.title,
                "url": r.url,
                "excerpts": list(r.excerpts or [])[:2],
            }
            for r in response.results[:5]
        ],
    }


async def search_location_intel(location: str) -> dict:
    """Research one location. Returns empty results rather than raising, so a
    single failed lookup never takes down the whole pipeline."""
    try:
        return await asyncio.to_thread(_search_sync, location)
    except Exception as e:
        logger.warning(
            "parallel_search_failed", extra={"location": location, "error": str(e)}
        )
        return {"location": location, "results": [], "error": str(e)}
