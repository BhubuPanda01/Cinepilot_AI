"""Review Agent: critiques the pre-production package for pacing, camera coverage, risk, and consistency."""

from typing import List

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class ReviewFinding(BaseModel):
    category: str = Field(
        description="One of: Pacing, Camera Coverage, Risk Concentration, Character Consistency, Dialogue, Emotional Arc"
    )
    severity: str = Field(description="One of: Low, Medium, High")
    note: str = Field(description="Specific, actionable observation -- reference scene numbers where relevant")


class ReviewResult(BaseModel):
    overall_assessment: str = Field(
        description="2-3 sentence summary of the screenplay's pre-production readiness"
    )
    strengths: List[str] = Field(description="What's working well across the package")
    findings: List[ReviewFinding] = Field(description="Specific concerns or gaps to address")


review_agent = LlmAgent(
    name="review_agent",
    model="gemini-2.5-flash",
    description="Critiques the full pre-production package: pacing, camera variety, risk load, character/emotional consistency.",
    instruction=(
        "You are the Review Agent in a film pre-production pipeline, acting as an experienced script "
        "supervisor and previsualization reviewer. You will receive a JSON object with the full package: "
        "title, scenes (each with heading, action, dialogue, analysis of emotion/action_level/complexity/risk_level, "
        "and storyboard frames with shot_type/camera_angle/camera_movement), and character profiles. "
        "Critique the package as a whole across these dimensions:\n"
        "- Pacing: does emotional intensity and action_level escalate/vary sensibly across the scene order, "
        "or are there dead zones / abrupt tonal whiplash?\n"
        "- Camera Coverage: is there repetitive over-reliance on the same shot_type/camera_angle across scenes, "
        "or good variety appropriate to each scene's tone?\n"
        "- Risk Concentration: are High-risk scenes clustered in a way that could strain a single shoot day/location, "
        "or reasonably spread out?\n"
        "- Character Consistency: do character arcs (from their profiles) track logically through the scenes "
        "they appear in?\n"
        "- Dialogue: is dialogue sparse/absent in scenes where it would help, or overused where action should carry it?\n"
        "Cite specific scene_numbers in your findings. Be concrete and constructive, not generic. "
        "List genuine strengths too, not only problems."
    ),
    output_schema=ReviewResult,
    output_key="review",
)
