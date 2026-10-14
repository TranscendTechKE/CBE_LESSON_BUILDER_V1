"""
BUILD 08 - Curriculum Explorer + Lesson Plan API.

This router sits between the BUILD 07 parser and the teacher interface.

Flow:
PDF upload -> parse -> store in memory -> Theme -> Strand -> Sub-strand
-> verified curriculum unit -> lesson-plan generator.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.curriculum_parser import parse_curriculum_pdf
from app.services.lesson_plan_generator import generate_lesson_plan
from app.services.curriculum_document_adapter import (
    adapt_curriculum_document,
)
from app.services.pdf_processor import extract_pdf_pages
from app.services.flexible_curriculum_extractor import (
    parse_curriculum_pages,
)
from app.models.curriculum_profile import CurriculumProfile
from app.models.curriculum import CurriculumDocument

router = APIRouter(prefix="/api/curriculum", tags=["CBE Curriculum"])

# V1 deliberately uses an in-process store.
# Replace this with the project's DB/repository in the next persistence build.
DOCUMENTS: dict[str, CurriculumDocument] = {}
PROFILES = {}

def _walk_profile_nodes(nodes, ancestors=()):
    for node in nodes:
        yield node, ancestors
        yield from _walk_profile_nodes(
            node.children,
            ancestors + (node,),
        )


def _profile_leaf_nodes(profile, root=None):
    nodes = [root] if root is not None else profile.content_nodes

    for node, ancestors in _walk_profile_nodes(nodes):
        if not node.children and node.code:
            yield node, ancestors


def _profile_unit_payload(profile, node, ancestors):
    path = ancestors + (node,)

    theme = next(
        (item for item in path if item.node_type == "theme"),
        None,
    )
    strand = next(
        (item for item in reversed(path[:-1])
         if item.node_type == "strand"),
        None,
    )

    if strand is None and path and path[0].node_type != "theme":
        strand = path[0] if len(path) > 1 else None

    metadata = node.metadata or {}

    return {
        "code": node.code,
        "title": node.title,
        "node_type": node.node_type,
        "theme_code": theme.code if theme else "",
        "theme_title": theme.title if theme else "",
        "strand_code": strand.code if strand else "",
        "strand": strand.title if strand else "",
        "sub_strand_code": node.code,
        "sub_strand": node.title,
        "lessons": node.lessons,
        "specific_learning_outcomes": node.specific_learning_outcomes,
        "suggested_learning_experiences": node.suggested_learning_experiences,
        "key_inquiry_questions": node.key_inquiry_questions,
        "core_competencies": node.core_competencies,
        "pertinent_and_contemporary_issues": node.pertinent_and_contemporary_issues,
        "values": node.values,
        "links_to_other_subjects": node.links_to_other_learning_areas,
        "source_pages": node.source_pages,
        "source_pdf_pages": node.source_pages,
        "source_printed_pages": metadata.get("printed_pages", []),
        "grade": profile.grade,
        "learning_area": profile.learning_area,
        "source_verified": profile.source_verified,
    }


def _find_profile_unit(profile, code):
    for node, ancestors in _profile_leaf_nodes(profile):
        if node.code == code:
            return _profile_unit_payload(profile, node, ancestors)

    return None


def _document_summary(doc: CurriculumDocument) -> dict[str, Any]:
    return {
        "source_file": doc.source_file,
        "page_count": doc.page_count,
        "grade": doc.grade,
        "learning_area": doc.learning_area,
        "theme_count": len(doc.themes),
        "unit_count": doc.unit_count,
        "extraction_start_page": doc.extraction_start_page,
        "extraction_end_page": doc.extraction_end_page,
        "warnings": doc.warnings,
        "themes": [
            {
                "code": theme.code,
                "title": theme.title,
                "start_pdf_page": theme.start_pdf_page,
                "end_pdf_page": theme.end_pdf_page,
                "unit_count": len(theme.units),
            }
            for theme in doc.themes
        ],
    }


@router.post("/upload")
async def upload_curriculum(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF curriculum design.")

    content = await file.read()
    if not content:
        raise HTTPException(400, "The uploaded PDF is empty.")

    suffix = Path(file.filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        temp_path = Path(tmp.name)

    try:
        document = parse_curriculum_pdf(temp_path)
        profile = None

        # Preserve the legacy parser whenever it extracts usable units.
        if document.unit_count == 0:
            pages = extract_pdf_pages(temp_path)

            first_text = "\n".join(
                page["text"] for page in pages[:9]
            )

            grade_match = __import__("re").search(
                r"\bGrade\s+(\d+)\b",
                first_text,
                __import__("re").IGNORECASE,
            )
            grade = (
                f"Grade {grade_match.group(1)}"
                if grade_match
                else "Unknown"
            )

            # Use a conservative label; do not assume every document
            # without the word English is Science.
            learning_area = "Unknown"
            filename_upper = file.filename.upper()
            for area in (
                "SCIENCE",
                "MATHEMATICS",
                "KISWAHILI",
                "ENGLISH",
                "AGRICULTURE",
                "SOCIAL STUDIES",
            ):
                if area in filename_upper or area in first_text.upper():
                    learning_area = area.title()
                    break

            profile = parse_curriculum_pages(
                pages,
                grade=grade,
                learning_area=learning_area,
                document_title=file.filename,
            )

            # Do not accept a profile that found no usable hierarchy.
            if not profile.content_nodes or not profile.hierarchy_labels:
                raise HTTPException(
                    422,
                    "No recognizable curriculum hierarchy was extracted. "
                    "Check that this PDF contains selectable text and "
                    "review the extraction warnings.",
                )

    finally:
        temp_path.unlink(missing_ok=True)

    import hashlib

    document_id = hashlib.sha256(content).hexdigest()[:16]
    DOCUMENTS[document_id] = document

    if profile is not None:
        profile.profile_id = f"uploaded-{document_id}"
        PROFILES[document_id] = profile
    else:
        PROFILES.pop(document_id, None)

    summary = _document_summary(document)

    if profile is not None:
        summary.update(
            {
                "grade": profile.grade,
                "learning_area": profile.learning_area,
                "theme_count": sum(
                    1 for node in profile.content_nodes
                    if node.node_type == "theme"
                ),
                "unit_count": sum(
                    1 for node in profile.content_nodes
                    for child in node.children
                    for _ in (
                        child.children
                        if child.children
                        else [child]
                    )
                    if _.node_type in ("sub_strand", "unit", "topic")
                ),
                "hierarchy_labels": profile.hierarchy_labels,
                "warnings": profile.notes,
                "themes": [],
            }
        )

    return {
        "document_id": document_id,
        "summary": summary,
    }


@router.get("/{document_id}")
def get_curriculum(document_id: str):
    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found. Upload it again.")
    return doc.model_dump()



@router.get("/{document_id}/profile")
async def get_curriculum_profile(document_id: str):
    profile = PROFILES.get(document_id)

    if profile is None:
        document = DOCUMENTS.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Curriculum document not found.",
            )

        profile = adapt_curriculum_document(document)
        profile.profile_id = f"uploaded-{document_id}"

    return profile.model_dump()



@router.get("/{document_id}/themes")
def get_themes(document_id: str):
    profile = PROFILES.get(document_id)

    if profile is not None:
        result = []

        for root in profile.content_nodes:
            descendants = list(_profile_leaf_nodes(profile, root))
            result.append({
                "code": root.code,
                "title": root.title,
                "start_pdf_page": min(root.source_pages)
                if root.source_pages else None,
                "end_pdf_page": max(root.source_pages)
                if root.source_pages else None,
                "unit_count": len(descendants),
            })

        return result

    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found.")

    return [
        {
            "code": theme.code,
            "title": theme.title,
            "start_pdf_page": theme.start_pdf_page,
            "end_pdf_page": theme.end_pdf_page,
            "unit_count": len(theme.units),
        }
        for theme in doc.themes
    ]


@router.get("/{document_id}/themes/{theme_code}/units")
def get_theme_units(document_id: str, theme_code: str):
    profile = PROFILES.get(document_id)

    if profile is not None:
        root = next(
            (node for node in profile.content_nodes
             if node.code == theme_code),
            None,
        )
        if root is None:
            raise HTTPException(404, "Curriculum section not found.")

        return [
            _profile_unit_payload(profile, node, ancestors)
            for node, ancestors in _profile_leaf_nodes(profile, root)
        ]

    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found.")

    theme = next((x for x in doc.themes if x.code == theme_code), None)
    if not theme:
        raise HTTPException(404, "Theme not found.")

    return [
        {
            "strand_code": unit.strand_code,
            "strand": unit.strand,
            "sub_strand_code": unit.sub_strand_code,
            "sub_strand": unit.sub_strand,
            "lessons": unit.lessons,
            "source_pdf_pages": unit.source_pdf_pages,
        }
        for unit in theme.units
    ]


@router.get("/{document_id}/unit/{sub_strand_code}")
def get_unit(document_id: str, sub_strand_code: str):
    profile = PROFILES.get(document_id)

    if profile is not None:
        unit = _find_profile_unit(profile, sub_strand_code)
        if unit is not None:
            return unit

        raise HTTPException(404, "Curriculum unit not found.")

    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found.")

    for theme in doc.themes:
        for unit in theme.units:
            if unit.sub_strand_code == sub_strand_code:
                return unit.model_dump()

    raise HTTPException(404, "Sub-strand not found.")


class LessonPlanRequest(BaseModel):
    document_id: str
    sub_strand_code: str
    teacher_name: str = ""
    school_name: str = ""
    lesson_date: str = ""
    duration_minutes: int = Field(default=40, ge=20, le=180)
    class_size: int | None = Field(default=None, ge=1, le=200)
    lesson_number: int = Field(default=1, ge=1)



@router.post("/lesson-plan")
def create_lesson_plan(request: LessonPlanRequest):
    profile = PROFILES.get(request.document_id)

    if profile is not None:
        unit = _find_profile_unit(
            profile,
            request.sub_strand_code,
        )
    else:
        doc = DOCUMENTS.get(request.document_id)
        if not doc:
            raise HTTPException(
                404,
                "Curriculum document not found. Upload it again.",
            )

        unit = None
        for theme in doc.themes:
            for candidate in theme.units:
                if candidate.sub_strand_code == request.sub_strand_code:
                    unit = candidate
                    break
            if unit is not None:
                break

    if unit is None:
        raise HTTPException(404, "Selected curriculum unit not found.")

    lesson_plan = generate_lesson_plan(
        unit,
        teacher_name=request.teacher_name,
        school_name=request.school_name,
        lesson_date=request.lesson_date,
        duration_minutes=request.duration_minutes,
        class_size=request.class_size,
        lesson_number=request.lesson_number,
    )

    return JSONResponse(lesson_plan)
