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
from app.models.curriculum import CurriculumDocument

router = APIRouter(prefix="/api/curriculum", tags=["CBE Curriculum"])

# V1 deliberately uses an in-process store.
# Replace this with the project's DB/repository in the next persistence build.
DOCUMENTS: dict[str, CurriculumDocument] = {}


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
    finally:
        temp_path.unlink(missing_ok=True)

    # Simple stable ID for the browser session.
    import hashlib
    document_id = hashlib.sha256(content).hexdigest()[:16]
    DOCUMENTS[document_id] = document

    return {
        "document_id": document_id,
        "summary": _document_summary(document),
    }


@router.get("/{document_id}")
def get_curriculum(document_id: str):
    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found. Upload it again.")
    return doc.model_dump()


@router.get("/{document_id}/profile")
def get_curriculum_profile(document_id: str):
    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(
            404,
            "Curriculum document not found. Upload it again.",
        )

    profile = adapt_curriculum_document(doc)
    profile.profile_id = f"uploaded-{document_id}"

    return profile.model_dump()


@router.get("/{document_id}/themes")
def get_themes(document_id: str):
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
    doc = DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found.")

    theme = next((x for x in doc.themes if x.code == theme_code), None)
    if not theme:
        raise HTTPException(404, "Theme not found.")

    return [
        {
            "strand_code": u.strand_code,
            "strand": u.strand,
            "sub_strand_code": u.sub_strand_code,
            "sub_strand": u.sub_strand,
            "lessons": u.lessons,
            "source_pdf_pages": u.source_pdf_pages,
        }
        for u in theme.units
    ]


@router.get("/{document_id}/unit/{sub_strand_code}")
def get_unit(document_id: str, sub_strand_code: str):
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
    doc = DOCUMENTS.get(request.document_id)
    if not doc:
        raise HTTPException(404, "Curriculum document not found. Upload it again.")

    unit = None
    for theme in doc.themes:
        for candidate in theme.units:
            if candidate.sub_strand_code == request.sub_strand_code:
                unit = candidate
                break
        if unit:
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
