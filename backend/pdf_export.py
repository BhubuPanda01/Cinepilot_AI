"""Builds a downloadable production package PDF from a project's pipeline data."""

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
    PageBreak,
)

import storage

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="H1", fontSize=20, spaceAfter=14, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="H2", fontSize=14, spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="H3", fontSize=11, spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Body", fontSize=9.5, leading=13))
styles.add(ParagraphStyle(name="Meta", fontSize=8.5, textColor=colors.grey, leading=12))


def _badge_row(badges: list[str]) -> str:
    return " &nbsp;&middot;&nbsp; ".join(badges)


def build_production_pdf(name: str, data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
    )
    story = []

    # --- Title page ---
    story.append(Paragraph(data.get("title") or name, styles["H1"]))
    story.append(Paragraph("CinePilot AI &mdash; Pre-Production Package", styles["Meta"]))
    story.append(Spacer(1, 0.3 * inch))

    # --- Characters ---
    characters = data.get("characters", [])
    if characters:
        story.append(Paragraph("Character Sheets", styles["H2"]))
        for c in characters:
            story.append(Paragraph(f"{c['name']} &mdash; {c.get('role', '')}", styles["H3"]))
            story.append(Paragraph(f"<b>Occupation:</b> {c.get('occupation', '')}", styles["Body"]))
            story.append(Paragraph(f"<b>Description:</b> {c.get('physical_description', '')}", styles["Body"]))
            story.append(Paragraph(f"<b>Personality:</b> {c.get('personality', '')}", styles["Body"]))
            story.append(Paragraph(f"<b>Wardrobe:</b> {c.get('wardrobe_style', '')}", styles["Body"]))
            story.append(Paragraph(f"<i>{c.get('arc_summary', '')}</i>", styles["Body"]))
            story.append(Spacer(1, 0.15 * inch))
        story.append(PageBreak())

    # --- Scenes / Storyboard / Shot list ---
    scenes = data.get("scenes", [])
    if scenes:
        story.append(Paragraph("Scenes &amp; Storyboard", styles["H2"]))
        for scene in scenes:
            story.append(
                Paragraph(f"Scene {scene['scene_number']}: {scene['heading']}", styles["H3"])
            )
            story.append(
                Paragraph(f"{scene.get('location', '')} &middot; {scene.get('time_of_day', '')}", styles["Meta"])
            )
            analysis = scene.get("analysis") or {}
            if analysis:
                badges = _badge_row([
                    analysis.get("emotion", ""),
                    f"Action: {analysis.get('action_level', '')}",
                    f"Complexity: {analysis.get('complexity', '')}",
                    f"Risk: {analysis.get('risk_level', '')}",
                ])
                story.append(Paragraph(badges, styles["Meta"]))
            story.append(Paragraph(scene.get("action", ""), styles["Body"]))
            if analysis.get("risk_notes") and analysis["risk_notes"].lower() != "none":
                story.append(Paragraph(f"<i>Risk note: {analysis['risk_notes']}</i>", styles["Meta"]))

            for frame in scene.get("storyboard", []):
                story.append(Spacer(1, 0.08 * inch))
                frame_label = _badge_row([
                    f"Frame {frame['frame_number']}",
                    frame.get("shot_type", ""),
                    frame.get("camera_angle", ""),
                    frame.get("camera_movement") or "",
                ])
                story.append(Paragraph(frame_label, styles["Meta"]))
                story.append(Paragraph(frame.get("description", ""), styles["Body"]))
                if frame.get("prompt"):
                    story.append(Paragraph(f"<i>Prompt: {frame['prompt']}</i>", styles["Meta"]))

                image_path = frame.get("image_path")
                if image_path:
                    # image_path is an API route ("/api/media/<uid>/<project>/<file>");
                    # strip the route prefix to get the storage object path.
                    object_path = image_path.removeprefix("/api/media/").removeprefix("/images/")
                    image_bytes = storage.read_media(object_path)
                    if image_bytes:
                        story.append(Spacer(1, 0.05 * inch))
                        story.append(
                            RLImage(
                                io.BytesIO(image_bytes),
                                width=3.2 * inch,
                                height=3.2 * inch,
                                kind="proportional",
                            )
                        )

            story.append(Spacer(1, 0.2 * inch))
        story.append(PageBreak())

    # --- Shot list table ---
    shot_rows = [["Scene", "Frame", "Shot Type", "Angle", "Movement"]]
    for scene in scenes:
        for frame in scene.get("storyboard", []):
            shot_rows.append([
                str(scene["scene_number"]),
                str(frame["frame_number"]),
                frame.get("shot_type", ""),
                frame.get("camera_angle", ""),
                frame.get("camera_movement") or "-",
            ])
    if len(shot_rows) > 1:
        story.append(Paragraph("Shot List", styles["H2"]))
        table = Table(shot_rows, repeatRows=1, colWidths=[0.6 * inch, 0.6 * inch, 1.8 * inch, 1.5 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4e4e7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d4d4d8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(PageBreak())

    # --- Location intelligence (web-grounded) ---
    location_scout = data.get("location_scout") or []
    grounded_locations = [loc for loc in location_scout if loc.get("grounded")]
    if grounded_locations:
        story.append(Paragraph("Location Intelligence", styles["H2"]))
        story.append(
            Paragraph(
                "Researched from live web sources via Parallel Search. Locations without "
                "reliable sources are omitted rather than inferred.",
                styles["Meta"],
            )
        )
        for loc in grounded_locations:
            scenes_label = ", ".join(str(n) for n in loc.get("scene_numbers", []))
            story.append(
                Paragraph(f"{loc['location']} &mdash; Scene(s) {scenes_label}", styles["H3"])
            )
            story.append(Paragraph(f"<b>Permits:</b> {loc.get('permit_notes', '')}", styles["Body"]))
            story.append(
                Paragraph(f"<b>Constraints:</b> {loc.get('logistical_challenges', '')}", styles["Body"])
            )
            story.append(
                Paragraph(
                    f"<b>Recommendations:</b> {loc.get('practical_recommendations', '')}",
                    styles["Body"],
                )
            )
            for url in loc.get("sources", []):
                story.append(Paragraph(f"Source: {url}", styles["Meta"]))
            story.append(Spacer(1, 0.12 * inch))
        story.append(PageBreak())

    # --- Review ---
    review = data.get("review")
    if review:
        story.append(Paragraph("Review", styles["H2"]))
        story.append(Paragraph(review.get("overall_assessment", ""), styles["Body"]))
        if review.get("strengths"):
            story.append(Paragraph("Strengths", styles["H3"]))
            for s in review["strengths"]:
                story.append(Paragraph(f"&bull; {s}", styles["Body"]))
        if review.get("findings"):
            story.append(Paragraph("Findings", styles["H3"]))
            for f in review["findings"]:
                story.append(Paragraph(f"<b>[{f['severity']}] {f['category']}:</b> {f['note']}", styles["Body"]))
        story.append(Spacer(1, 0.2 * inch))

    # --- Director Report ---
    report = data.get("director_report")
    if report:
        story.append(Paragraph("Director Report", styles["H2"]))
        story.append(Paragraph(report.get("executive_summary", ""), styles["Body"]))
        if report.get("key_recommendations"):
            story.append(Paragraph("Key Recommendations", styles["H3"]))
            for r in report["key_recommendations"]:
                story.append(Paragraph(f"&bull; {r}", styles["Body"]))
        if report.get("production_notes"):
            story.append(Paragraph("Production Notes", styles["H3"]))
            for n in report["production_notes"]:
                story.append(Paragraph(f"&bull; {n}", styles["Body"]))
        if report.get("budget_risk_summary"):
            story.append(Paragraph("Budget / Risk Summary", styles["H3"]))
            story.append(Paragraph(report["budget_risk_summary"], styles["Body"]))

    doc.build(story)
    return buffer.getvalue()
