"""Director Report Agent: synthesizes the full package + review into director-facing recommendations."""

from typing import List

from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent


class DirectorReport(BaseModel):
    executive_summary: str = Field(
        description="3-5 sentence summary a director/producer could read in under a minute"
    )
    key_recommendations: List[str] = Field(
        description="Concrete, prioritized directives -- e.g. scheduling, casting emphasis, shot planning"
    )
    production_notes: List[str] = Field(
        description=(
            "Logistics call-outs derived from scene risk/complexity: permits, stunt coordination, "
            "VFX/practical effects needs, crowd control, night shoots, weather-dependent scenes, etc. "
            "Reference scene_numbers where relevant."
        )
    )
    budget_risk_summary: str = Field(
        description="Overall assessment of the shoot's budget/risk profile based on the scene-level risk and complexity ratings"
    )


director_report_agent = LlmAgent(
    name="director_report_agent",
    model="gemini-2.5-flash",
    description="Synthesizes the full pre-production package and review findings into a director-facing report.",
    instruction=(
        "You are the Director Report Agent, the final synthesis step in a film pre-production pipeline. "
        "You will receive a JSON object with: title, scenes (with analysis and storyboard data), "
        "character profiles, the Review Agent's findings (overall_assessment, strengths, findings), "
        "and 'location_scout' -- web-grounded location intelligence with real permit_notes, "
        "logistical_challenges, and source URLs for each filming location. "
        "When a location_scout entry has grounded=true, prefer its sourced facts over your own "
        "assumptions when writing production_notes for scenes at that location, and reflect any "
        "real permit or access constraints it surfaced. Do not repeat facts from entries where "
        "grounded=false. "
        "Write a concise, actionable report for a director or producer who has not yet read the other agents' "
        "raw output. Do not just repeat the review findings verbatim -- synthesize them into: "
        "an executive summary, prioritized key_recommendations (what to actually do about the review findings), "
        "production_notes (concrete logistics call-outs derived from scene risk/complexity ratings -- permits, "
        "stunts, VFX, crowds, night shoots, weather dependency), and a budget_risk_summary assessing the "
        "overall shoot based on how many scenes are High complexity/risk versus Low."
    ),
    output_schema=DirectorReport,
    output_key="director_report",
)
