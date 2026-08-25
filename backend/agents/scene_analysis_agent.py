"""Scene Analysis Agent: classifies emotion, action level, complexity, and risk per scene."""

from typing import List, Optional

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class SceneAnalysis(BaseModel):
    scene_number: int = Field(description="Matches the scene_number from the Parser Agent output")
    emotion: str = Field(
        description="Primary emotional tone, e.g. Joy, Tension, Fear, Romance, Grief, Triumph, Suspense"
    )
    action_level: str = Field(description="One of: Low, Medium, High")
    complexity: str = Field(
        description=(
            "Production complexity: Low, Medium, or High. Consider number of characters, "
            "VFX/stunts, crowd scenes, night shoots, special props, or multiple locations."
        )
    )
    risk_level: str = Field(
        description="Physical/safety risk on set: Low, Medium, or High"
    )
    risk_notes: str = Field(
        description="Brief note on what drives the risk/complexity rating, or 'None' if low risk"
    )


class ScreenplayAnalysisResult(BaseModel):
    analyses: List[SceneAnalysis]


scene_analysis_agent = LlmAgent(
    name="scene_analysis_agent",
    model="gemini-2.5-flash",
    description="Classifies emotion, action level, complexity, and risk for each parsed scene.",
    instruction=(
        "You are the Scene Analysis Agent in a film pre-production pipeline. "
        "You will receive a JSON object containing a list of parsed screenplay scenes "
        "(each with scene_number, heading, location, time_of_day, characters, action, dialogue). "
        "For every scene in the input, produce one analysis entry with the same scene_number. "
        "Classify: emotion (primary emotional tone), action_level (Low/Medium/High), "
        "complexity (Low/Medium/High production complexity), risk_level (Low/Medium/High safety risk), "
        "and a short risk_notes explaining the rating. "
        "Base your judgment only on the action, dialogue, and heading text provided. "
        "Return exactly one analysis per input scene, in the same order."
    ),
    output_schema=ScreenplayAnalysisResult,
    output_key="scene_analysis",
)
