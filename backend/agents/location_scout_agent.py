"""Location Scout Agent: turns real web search results into practical location notes.

Unlike the other agents, this one is grounded -- it receives actual web excerpts
(permit rules, local regulations, cost references) retrieved via Parallel's Search
API, and must base its findings on those rather than on prior assumptions.
"""

from typing import List

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class LocationIntel(BaseModel):
    location: str = Field(description="Location name, matching the input location exactly")
    scene_numbers: List[int] = Field(description="Scene numbers shot at this location")
    permit_notes: str = Field(
        description=(
            "Who issues filming permits here and what the process/requirements are, "
            "based ONLY on the supplied web excerpts. If the excerpts don't cover it, "
            "say so plainly rather than guessing."
        )
    )
    logistical_challenges: str = Field(
        description="Access, crowd, traffic, timing, or seasonal constraints indicated by the sources"
    )
    practical_recommendations: str = Field(
        description="Concrete actions for the production team, tied to this screenplay's scenes"
    )
    sources: List[str] = Field(
        description="URLs actually used to support the findings above. Empty if no useful sources were supplied."
    )
    grounded: bool = Field(
        description="True if findings are supported by the supplied web excerpts; False if no usable sources were available"
    )


class LocationScoutResult(BaseModel):
    locations: List[LocationIntel]


location_scout_agent = LlmAgent(
    name="location_scout_agent",
    model="gemini-2.5-flash",
    description="Produces web-grounded filming location intelligence: permits, constraints, recommendations.",
    instruction=(
        "You are the Location Scout Agent in a film pre-production pipeline. "
        "You will receive a JSON object with a 'locations' list. Each entry has the location "
        "name, the scene_numbers shot there, the scenes' risk/complexity context, and "
        "'web_results' -- real search results (title, url, excerpts) retrieved from the live web.\n\n"
        "CRITICAL GROUNDING RULE: base permit_notes and logistical_challenges strictly on the "
        "supplied web_results. Do NOT invent permit authorities, fees, or regulations that do not "
        "appear in the excerpts. If the excerpts for a location contain nothing useful, set "
        "grounded=false, leave sources empty, and state plainly that no reliable source was found "
        "-- do not fill the gap with plausible-sounding guesses.\n\n"
        "In 'sources', list only URLs you actually drew information from. "
        "practical_recommendations may connect the sourced facts to this screenplay's specific "
        "scenes (their action, risk level, and time of day). "
        "Produce exactly one entry per input location, preserving the location name verbatim."
    ),
    output_schema=LocationScoutResult,
    output_key="location_scout",
)
