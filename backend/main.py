"""Pipeline entrypoint: runs the full multi-agent pre-production pipeline on a screenplay PDF.

Usage:
    python main.py path/to/screenplay.pdf
"""

import asyncio
import io
import json
import logging
import sys
from pathlib import Path
from typing import Awaitable, Callable, Optional

from dotenv import load_dotenv
from pypdf import PdfReader
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ClientError

from agents.parser_agent import parser_agent
from agents.scene_analysis_agent import scene_analysis_agent
from agents.character_agent import character_agent
from agents.storyboard_agent import storyboard_agent
from agents.prompt_agent import prompt_agent
from agents.review_agent import review_agent
from agents.director_report_agent import director_report_agent
from agents.location_scout_agent import location_scout_agent
from parallel_search import search_location_intel

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

APP_NAME = "cinepilot"
USER_ID = "local_user"

# Locations with no real-world referent aren't worth a web lookup.
UNRESEARCHABLE_LOCATIONS = {"unknown", "unspecified", "n/a", "", "unspecified location"}


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


async def run_agent(
    agent: LlmAgent, input_text: str, output_key: str, max_retries: int = 3
) -> dict:
    for attempt in range(max_retries):
        try:
            runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
            session = await runner.session_service.create_session(
                app_name=APP_NAME, user_id=USER_ID
            )

            message = types.Content(role="user", parts=[types.Part(text=input_text)])

            async for event in runner.run_async(
                user_id=USER_ID, session_id=session.id, new_message=message
            ):
                pass  # drain events; final state is read from the session below

            updated_session = await runner.session_service.get_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=session.id
            )
            return updated_session.state.get(output_key)
        except ClientError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_seconds = 15 * (attempt + 1)
                logger.warning(
                    "Quota exhausted for %s; retrying in %ss (attempt %s/%s)",
                    agent.name,
                    wait_seconds,
                    attempt + 1,
                    max_retries,
                    extra={
                        "agent": agent.name,
                        "event": "quota_retry",
                        "attempt": attempt + 1,
                        "wait_seconds": wait_seconds,
                    },
                )
                await asyncio.sleep(wait_seconds)
                continue
            logger.error(
                "Agent %s failed: %s",
                agent.name,
                e,
                extra={"agent": agent.name, "event": "agent_failed"},
            )
            raise


async def run_parser(screenplay_text: str) -> dict:
    return await run_agent(parser_agent, screenplay_text, "parsed_screenplay")


async def run_scene_analysis(parsed_screenplay: dict) -> dict:
    return await run_agent(
        scene_analysis_agent, json.dumps(parsed_screenplay), "scene_analysis"
    )


async def run_character_agent(screenplay_text: str) -> dict:
    return await run_agent(character_agent, screenplay_text, "character_profiles")


async def run_storyboard_agent(merged_screenplay: dict) -> dict:
    payload = {"title": merged_screenplay.get("title"), "scenes": merged_screenplay["scenes"]}
    return await run_agent(storyboard_agent, json.dumps(payload), "storyboard_frames")


async def run_prompt_agent(storyboard: dict, characters: list) -> dict:
    payload = {"frames": storyboard.get("frames", []), "characters": characters}
    return await run_agent(prompt_agent, json.dumps(payload), "cinematic_prompts")


async def run_review_agent(merged_screenplay: dict) -> dict:
    return await run_agent(review_agent, json.dumps(merged_screenplay), "review")


async def run_director_report_agent(merged_screenplay: dict, review: dict) -> dict:
    payload = {**merged_screenplay, "review": review}
    return await run_agent(
        director_report_agent, json.dumps(payload), "director_report"
    )


def collect_researchable_locations(merged_screenplay: dict) -> list[dict]:
    """Group scenes by location so each real place is researched once, not per scene."""
    by_location: dict[str, dict] = {}
    for scene in merged_screenplay.get("scenes", []):
        location = (scene.get("location") or "").strip()
        if location.lower() in UNRESEARCHABLE_LOCATIONS:
            continue

        entry = by_location.setdefault(
            location,
            {"location": location, "scene_numbers": [], "scenes_context": []},
        )
        analysis = scene.get("analysis") or {}
        entry["scene_numbers"].append(scene["scene_number"])
        entry["scenes_context"].append(
            {
                "scene_number": scene["scene_number"],
                "time_of_day": scene.get("time_of_day"),
                "action": scene.get("action"),
                "complexity": analysis.get("complexity"),
                "risk_level": analysis.get("risk_level"),
                "risk_notes": analysis.get("risk_notes"),
            }
        )
    return list(by_location.values())


async def run_location_scout_agent(merged_screenplay: dict) -> dict:
    """Ground each location in live web data (Parallel Search), then synthesize."""
    locations = collect_researchable_locations(merged_screenplay)
    if not locations:
        logger.info("No researchable locations found; skipping location scout")
        return {"locations": []}

    # Searches are independent and hit Parallel (not the constrained Vertex quota),
    # so they can safely run concurrently.
    search_results = await asyncio.gather(
        *(search_location_intel(loc["location"]) for loc in locations)
    )

    for loc, search in zip(locations, search_results):
        loc["web_results"] = search.get("results", [])

    with_results = sum(1 for loc in locations if loc["web_results"])
    logger.info(
        "Web search returned results for %s/%s locations",
        with_results,
        len(locations),
        extra={"event": "location_search", "locations_with_results": with_results},
    )

    result = await run_agent(
        location_scout_agent, json.dumps({"locations": locations}), "location_scout"
    )

    # The agent decides what is actually usable -- raw hits are not the same as
    # sourced findings, so report its verdict rather than the search count.
    grounded = sum(1 for loc in result.get("locations", []) if loc.get("grounded"))
    logger.info(
        "Location scout grounded %s/%s locations in real sources",
        grounded,
        len(locations),
        extra={"event": "location_grounded", "grounded": grounded},
    )
    return result


def merge_analysis(parsed_screenplay: dict, scene_analysis: dict) -> dict:
    analyses_by_scene = {
        a["scene_number"]: a for a in scene_analysis.get("analyses", [])
    }
    merged_scenes = []
    for scene in parsed_screenplay.get("scenes", []):
        analysis = analyses_by_scene.get(scene["scene_number"], {})
        merged_scenes.append({**scene, "analysis": analysis})
    return {"title": parsed_screenplay.get("title"), "scenes": merged_scenes}


def merge_storyboard(merged: dict, storyboard: dict, prompts: dict) -> dict:
    prompts_by_key = {
        (p["scene_number"], p["frame_number"]): p for p in prompts.get("prompts", [])
    }
    frames_by_scene: dict = {}
    for frame in storyboard.get("frames", []):
        key = (frame["scene_number"], frame["frame_number"])
        prompt_data = prompts_by_key.get(key, {})
        frames_by_scene.setdefault(frame["scene_number"], []).append(
            {
                **frame,
                "prompt": prompt_data.get("prompt"),
                "negative_prompt": prompt_data.get("negative_prompt"),
            }
        )
    for scene in merged["scenes"]:
        scene["storyboard"] = frames_by_scene.get(scene["scene_number"], [])
    return merged


PIPELINE_STEPS = [
    "Parsing screenplay",
    "Analyzing scenes",
    "Extracting characters",
    "Building storyboard",
    "Writing cinematic prompts",
    "Scouting locations on the web",
    "Reviewing package",
    "Compiling director report",
]


async def run_pipeline(
    screenplay_text: str,
    on_progress: Optional[Callable[[int, str], Awaitable[None]]] = None,
) -> dict:
    async def step_done(index: int):
        if on_progress:
            await on_progress(index + 1, PIPELINE_STEPS[index])

    parsed = await run_parser(screenplay_text)
    await step_done(0)

    analysis = await run_scene_analysis(parsed)
    await step_done(1)

    characters = await run_character_agent(screenplay_text)
    await step_done(2)

    merged = merge_analysis(parsed, analysis)
    merged["characters"] = characters.get("characters", [])

    storyboard = await run_storyboard_agent(merged)
    await step_done(3)

    prompts = await run_prompt_agent(storyboard, merged["characters"])
    await step_done(4)

    merged = merge_storyboard(merged, storyboard, prompts)

    # Web-grounded location research runs before the review/report steps so the
    # final director report can cite real permit and logistics data.
    location_scout = await run_location_scout_agent(merged)
    merged["location_scout"] = location_scout.get("locations", [])
    await step_done(5)

    review = await run_review_agent(merged)
    await step_done(6)

    director_report = await run_director_report_agent(merged, review)
    await step_done(7)

    merged["review"] = review
    merged["director_report"] = director_report
    return merged


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if len(sys.argv) != 2:
        print("Usage: python main.py path/to/screenplay.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Extracting text from {pdf_path.name}...")
    text = extract_text(pdf_path)

    async def report(step: int, name: str):
        print(f"  [{step}/{len(PIPELINE_STEPS)}] {name}")

    print(f"Running {len(PIPELINE_STEPS)}-agent pipeline...")
    result = asyncio.run(run_pipeline(text, on_progress=report))

    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{pdf_path.stem}_parsed.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(f"Done. Parsed + analyzed scenes written to {output_path}")


if __name__ == "__main__":
    main()
