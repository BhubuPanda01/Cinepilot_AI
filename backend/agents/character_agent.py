"""Character Agent: extracts character profiles with concept descriptions from parsed scenes."""

from typing import List

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class CharacterProfile(BaseModel):
    name: str = Field(description="Character name as it appears in the screenplay")
    occupation: str = Field(
        description=(
            "The character's stated occupation/role in the story (e.g. 'Honest IPS officer', "
            "'Investigative journalist'). Use the exact wording from an explicit character list "
            "or bio in the source text if one exists; otherwise infer from context."
        )
    )
    role: str = Field(description="One of: Protagonist, Antagonist, Supporting, Minor")
    physical_description: str = Field(
        description="Concept-art-ready physical description: age range, build, notable features"
    )
    personality: str = Field(description="Key personality traits inferred from dialogue and action")
    wardrobe_style: str = Field(
        description="Suggested wardrobe/costume style fitting the character and genre"
    )
    arc_summary: str = Field(
        description="One or two sentences summarizing the character's journey across the screenplay"
    )


class CharacterListResult(BaseModel):
    characters: List[CharacterProfile]


character_agent = LlmAgent(
    name="character_agent",
    model="gemini-2.5-flash",
    description="Extracts character profiles and concept descriptions from the raw screenplay text.",
    instruction=(
        "You are the Character Agent in a film pre-production pipeline. "
        "You will receive the RAW text extracted from a screenplay PDF -- this may include a "
        "'Main Characters' or cast list section with explicit occupation/role descriptions "
        "(e.g. 'Aarav Sharma - Honest IPS officer'), in addition to scene headings, action lines, and dialogue. "
        "ALWAYS check for and prioritize any explicit character list or bio text first -- use that "
        "exact information for occupation, and let it strongly inform personality and role. "
        "Only fall back to inferring from action/dialogue when no explicit bio exists for a character, "
        "and mark inferred fields with '(Inferred)'. "
        "Identify every distinct named character across the whole document and produce one profile per character. "
        "Determine role (Protagonist/Antagonist/Supporting/Minor) from how central they are to the story. "
        "Summarize each character's arc based on the full document. "
        "Do not invent characters that are not mentioned in the input."
    ),
    output_schema=CharacterListResult,
    output_key="character_profiles",
)
