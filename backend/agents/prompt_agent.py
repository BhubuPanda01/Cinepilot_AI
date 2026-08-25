"""Prompt Engineering Agent: turns storyboard frames into detailed cinematic prompts for image/video generation."""

from typing import List, Optional

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class CinematicPrompt(BaseModel):
    scene_number: int = Field(description="Matches the scene_number from the Storyboard Agent output")
    frame_number: int = Field(description="Matches the frame_number from the Storyboard Agent output")
    prompt: str = Field(
        description=(
            "A single detailed cinematic text-to-image/video prompt: subjects with consistent "
            "physical/wardrobe description, setting, lighting, mood, color palette, shot type, "
            "camera angle/movement, and visual style (e.g. 'cinematic, 35mm film, Bollywood drama')."
        )
    )
    negative_prompt: Optional[str] = Field(
        default=None, description="Elements to avoid in generation, if relevant, else None"
    )


class PromptResult(BaseModel):
    prompts: List[CinematicPrompt]


prompt_agent = LlmAgent(
    name="prompt_agent",
    model="gemini-2.5-flash",
    description="Generates detailed cinematic image/video generation prompts for each storyboard frame.",
    instruction=(
        "You are the Prompt Engineering Agent in a film pre-production pipeline. "
        "You will receive a JSON object with two parts: 'frames' (storyboard frames with scene_number, "
        "frame_number, shot_type, camera_angle, camera_movement, description) and 'characters' "
        "(character profiles with name, physical_description, wardrobe_style) for visual consistency. "
        "For every frame, write one detailed cinematic prompt suitable for an AI image/video generator. "
        "Whenever a frame includes a named character, incorporate that character's physical_description "
        "and wardrobe_style from the characters list so their appearance stays consistent across frames. "
        "Include setting, lighting (matching time_of_day/mood implied by the frame), color palette, "
        "the frame's shot_type and camera_angle/movement, and an overall visual style descriptor "
        "appropriate to the screenplay's genre. Keep each prompt to 2-4 sentences. "
        "Return exactly one prompt per input frame, matching scene_number and frame_number."
    ),
    output_schema=PromptResult,
    output_key="cinematic_prompts",
)
