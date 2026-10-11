
"""BUILD 10D — Flexible curriculum profile API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.curriculum_profile import CurriculumProfile
from app.services.curriculum_profile_adapter import (
    CurriculumProfileAdapterError,
    adapt_profile_node,
)
from app.services.lesson_plan_generator import generate_lesson_plan


router = APIRouter(
    prefix="/api/curriculum-profiles",
    tags=["Flexible Curriculum Profiles"],
)

# Temporary in-memory registry, consistent with the current BUILD 08 API.
PROFILES: dict[str, CurriculumProfile] = {}

# Server-controlled approval registry.
# Registration alone never authorizes curriculum use.
VERIFIED_PROFILE_IDS: set[str] = set()


class GenerateProfileLessonRequest(BaseModel):
    selected_node_code: str
    teacher_name: str = ""
    school_name: str = ""
    lesson_date: str = ""
    lesson_time: str = ""
    duration_minutes: int = Field(default=40, ge=20, le=180)
    class_size: int | None = Field(default=None, ge=1, le=200)
    lesson_number: int = Field(default=1, ge=1)


@router.post("")
def register_profile(profile: CurriculumProfile):
    """Register a profile, without claiming that it has been verified."""
    if profile.profile_id in PROFILES:
        raise HTTPException(
            status_code=409,
            detail="A profile with this profile_id is already registered.",
        )

    profile.source_verified = False
    PROFILES[profile.profile_id] = profile

    return {
        "profile_id": profile.profile_id,
        "source_verified": profile.source_verified,
        "node_count": sum(
            count_nodes(node)
            for node in profile.content_nodes
        ),
        "message": "Profile registered as unverified. Approval is required before lesson-plan generation.",
    }


def count_nodes(node) -> int:
    """Count a node and all its descendants."""
    return 1 + sum(count_nodes(child) for child in node.children)


@router.get("")
def list_profiles():
    """List registered profile summaries."""
    return [
        {
            "profile_id": profile.profile_id,
            "grade": profile.grade,
            "learning_area": profile.learning_area,
            "education_stage": profile.education_stage,
            "source_verified": profile.source_verified,
            "node_count": sum(
                count_nodes(node)
                for node in profile.content_nodes
            ),
        }
        for profile in PROFILES.values()
    ]


@router.get("/{profile_id}")
def get_profile(profile_id: str):
    profile = PROFILES.get(profile_id)

    if profile is None:
        raise HTTPException(404, "Curriculum profile not found.")

    return profile.model_dump()


@router.get("/{profile_id}/nodes")
def get_profile_nodes(profile_id: str):
    profile = PROFILES.get(profile_id)

    if profile is None:
        raise HTTPException(404, "Curriculum profile not found.")

    def serialize_node(node):
        return {
            "code": node.code,
            "title": node.title,
            "node_type": node.node_type,
            "source_pages": node.source_pages,
            "children": [
                serialize_node(child) for child in node.children
            ],
        }

    return {
        "profile_id": profile.profile_id,
        "source_verified": profile.source_verified,
        "nodes": [
            serialize_node(node) for node in profile.content_nodes
        ],
    }


@router.post("/{profile_id}/lesson-plan")
def create_profile_lesson_plan(
    profile_id: str,
    request: GenerateProfileLessonRequest,
):
    profile = PROFILES.get(profile_id)

    if profile is None:
        raise HTTPException(404, "Curriculum profile not found.")
    if profile_id not in VERIFIED_PROFILE_IDS:
        raise HTTPException(
            status_code=403,
            detail="Curriculum profile has not been approved by the server.",
        )

    # Only the approved server-side copy is passed to the adapter.
    approved_profile = profile.model_copy(
        update={"source_verified": True}
    )

    try:
        unit = adapt_profile_node(
            approved_profile,
            request.selected_node_code,
        )
    except CurriculumProfileAdapterError as exc:
        raise HTTPException(400, str(exc)) from exc

    plan = generate_lesson_plan(
        unit,
        teacher_name=request.teacher_name,
        school_name=request.school_name,
        lesson_date=request.lesson_date,
        lesson_time=request.lesson_time,
        duration_minutes=request.duration_minutes,
        class_size=request.class_size,
        lesson_number=request.lesson_number,
    )

    return plan
