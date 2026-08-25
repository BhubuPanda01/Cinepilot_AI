"""Storyboard Agent: breaks each scene into key storyboard frames (shot type, angle, description)."""

from typing import List, Optional

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class StoryboardFrame(BaseModel):
    scene_number: int = Field(description="Matches the scene_number from the Parser Agent output")
    frame_number: int = Field(description="Frame order within the scene, starting at 1")
    shot_type: str = Field(
        description="e.g. Establishing Wide Shot, Medium Shot, Close-Up, Over-the-Shoulder, POV, Aerial"
    )
    camera_angle: str = Field(description="e.g. Eye-level, Low angle, High angle, Dutch tilt, Bird's-eye")
    camera_movement: Optional[str] = Field(
        default=None, description="e.g. Static, Pan, Dolly-in, Handheld, Tracking shot, or None"
    )
    description: str = Field(
        description="What is visually depicted in this frame: subjects, action, composition"
    )


class StoryboardResult(BaseModel):
    frames: List[StoryboardFrame]


storyboard_agent = LlmAgent(
    name="storyboard_agent",
    model="gemini-2.5-flash",
    description="Breaks each parsed scene into 2-4 key storyboard frames with shot type and camera angle.",
    instruction=(
        "You are the Storyboard Agent in a film pre-production pipeline. "
        "You will receive a JSON object containing parsed screenplay scenes "
        "(each with scene_number, heading, location, time_of_day, characters, action, dialogue, "
        "and an analysis of emotion/action_level/complexity/risk). "
        "For every scene, break it down into 2 to 4 key storyboard frames that capture the essential "
        "visual beats -- typically an establishing shot, then the key action or emotional beat(s), "
        "and a closing/reaction shot where relevant. Fewer frames for simple/low-action scenes, "
        "more frames for high-action or emotionally complex scenes. "
        "For each frame, choose an appropriate shot_type, camera_angle, and camera_movement that "
        "fits the scene's emotion and action_level, and write a concise visual description of what "
        "is depicted. Number frames sequentially within each scene starting at 1. "
        "Return frames for every scene in the input, in scene order."
    ),
    output_schema=StoryboardResult,
    output_key="storyboard_frames",
)
