"""Export generated CBE lesson plans as editable Word documents."""

from io import BytesIO
from typing import Any

from docx import Document
from docx.shared import Inches


def export_lesson_plan_docx(plan: dict[str, Any]) -> BytesIO:
    """Build an editable .docx document from lesson-plan data."""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    title = plan.get("sub_strand") or "CBE Lesson Plan"
    doc.add_heading("COMPETENCY-BASED EDUCATION LESSON PLAN", 0)
    doc.add_heading(str(title), 1)

    def field(label: str, value: Any) -> None:
        if value is not None and str(value).strip():
            p = doc.add_paragraph()
            p.add_run(f"{label}: ").bold = True
            p.add_run(str(value))

    def items(heading: str, values: Any) -> None:
        if not isinstance(values, list) or not values:
            return
        doc.add_heading(heading, 2)
        for value in values:
            if isinstance(value, dict):
                value = value.get("objective") or str(value)
            doc.add_paragraph(str(value), style="List Bullet")

    def stage(heading: str, data: Any) -> None:
        if not isinstance(data, dict):
            return
        doc.add_heading(heading, 2)
        field("Duration", f"{data.get('duration_minutes', 0)} minutes")
        items("Activities", data.get("activities", []))

    doc.add_heading("1. Lesson Information", 1)
    for label, key in [
        ("School", "school"),
        ("Teacher", "teacher"),
        ("Grade", "grade"),
        ("Learning Area", "learning_area"),
        ("Date", "date"),
        ("Time", "time"),
        ("Duration", "duration_minutes"),
        ("Class Size", "roll"),
        ("Lesson Number", "lesson_number"),
    ]:
        value = plan.get(key)
        if key == "duration_minutes" and value is not None:
            value = f"{value} minutes"
        field(label, value)

    doc.add_heading("2. Curriculum Alignment", 1)
    for label, key in [
        ("Theme", "theme"),
        ("Strand", "strand"),
        ("Sub-strand", "sub_strand"),
        ("Source Document", "source_document"),
        ("Source PDF Pages", "source_pages"),
    ]:
        value = plan.get(key)
        if key == "source_pages" and isinstance(value, list):
            value = ", ".join(map(str, value))
        field(label, value)

    items("Specific Learning Outcomes",
          plan.get("specific_learning_outcomes"))
    items("Key Inquiry Questions", plan.get("key_inquiry_questions"))
    items("Core Competencies", plan.get("core_competencies"))
    items("Pertinent and Contemporary Issues", plan.get("pcis"))
    items("Values", plan.get("values"))
    items("Links to Other Subjects", plan.get("links_to_other_subjects"))
    items("Learning Resources", plan.get("learning_resources"))

    doc.add_heading("3. Lesson Flow", 1)
    stage("Introduction", plan.get("introduction"))

    development = plan.get("lesson_development")
    if isinstance(development, dict):
        doc.add_heading("Lesson Development", 2)
        field("Duration",
              f"{development.get('duration_minutes', 0)} minutes")
        for step in development.get("steps", []):
            if not isinstance(step, dict):
                continue
            doc.add_heading(
                f"Step {step.get('number', '')}: {step.get('title', '')}",
                3,
            )
            field("Duration", f"{step.get('duration_minutes', 0)} minutes")
            items("Activities", step.get("activities", []))

    stage("Conclusion", plan.get("conclusion"))

    doc.add_heading("4. Assessment and Follow-up", 1)
    items("Assessment", plan.get("assessment"))
    items("Assessment Approaches", plan.get("assessment_approaches"))
    items("Extended Activities", plan.get("extended_activities"))
    items("Reflection", plan.get("reflection"))

    doc.add_heading("5. Teacher Self-Evaluation", 1)

    evaluation = plan.get("teacher_self_evaluation") or {}

    evaluation_fields = [
        ("What went well", "what_went_well"),
        ("Areas for improvement", "areas_for_improvement"),
        ("Learners needing support", "learners_needing_support"),
        ("Action for next lesson", "action_for_next_lesson"),
        ("Teacher signature", "teacher_signature"),
    ]

    for label, key in evaluation_fields:
        paragraph = doc.add_paragraph()
        paragraph.add_run(f"{label}: ").bold = True
        value = evaluation.get(key, "")
        paragraph.add_run(str(value) if value else " ")
        if not value:
            doc.add_paragraph(" ")

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output
