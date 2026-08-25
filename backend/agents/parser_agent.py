"""Parser Agent: extracts structured scenes from raw screenplay text using Gemini via Vertex AI."""

from typing import List, Optional

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class Scene(BaseModel):
    scene_number: int = Field(description="Sequential scene number, starting at 1")
    heading: str = Field(description="Original slugline, e.g. 'INT. WAREHOUSE - NIGHT'")
    location: str = Field(description="Location name extracted from the heading")
    time_of_day: str = Field(description="DAY, NIGHT, DAWN, DUSK, or CONTINUOUS")
    characters: List[str] = Field(description="Characters present in the scene")
    action: str = Field(description="Summary of the action/description lines")
    dialogue: List[str] = Field(
        default_factory=list,
        description="Dialogue lines formatted as 'CHARACTER: line'",
    )


class ScreenplayParseResult(BaseModel):
    title: Optional[str] = Field(default=None, description="Screenplay title if identifiable")
    scenes: List[Scene]


parser_agent = LlmAgent(
    name="parser_agent",
    model="gemini-2.5-flash",
    description="Extracts structured scene data from raw screenplay text.",
    instruction=(
        "You are the Parser Agent in a film pre-production pipeline. "
        "You will receive raw text extracted from a screenplay PDF. "
        "Split it into scenes based on sluglines (INT./EXT. headings). "
        "For each scene, extract the location, time of day, characters present, "
        "a concise action summary, and dialogue lines. "
        "Preserve scene order exactly as it appears in the text. "
        "If a field cannot be determined, use your best inference from context."
    ),
    output_schema=ScreenplayParseResult,
    output_key="parsed_screenplay",
)
