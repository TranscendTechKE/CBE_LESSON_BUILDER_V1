
"""
BUILD 10A — Flexible curriculum profile models.

Purpose:
- Support different curriculum hierarchies across learning areas.
- Preserve curriculum source references.
- Describe subject-specific lesson-planning requirements.
- Avoid changing the existing English curriculum models.
"""

from pydantic import BaseModel, Field


class CurriculumSource(BaseModel):
    """Reference to an official curriculum document."""

    authority: str = "KICD"
    document_title: str
    url: str | None = None
    curriculum_version: str | None = None
    pages: list[int] = Field(default_factory=list)



class CurriculumContentNode(BaseModel):
    """
    A flexible curriculum content item.

    Examples include theme, strand, sub_strand, topic,
    subtopic, unit, and competency.
    """

    code: str | None = None
    title: str
    node_type: str
    parent_code: str | None = None

    children: list["CurriculumContentNode"] = Field(
        default_factory=list
    )

    # Curriculum content specific to this node.
    specific_learning_outcomes: list[str] = Field(
        default_factory=list
    )
    suggested_learning_experiences: list[str] = Field(
        default_factory=list
    )
    key_inquiry_questions: list[str] = Field(
        default_factory=list
    )

    core_competencies: list[str] = Field(
        default_factory=list
    )
    pertinent_and_contemporary_issues: list[str] = Field(
        default_factory=list
    )
    values: list[str] = Field(default_factory=list)
    links_to_other_learning_areas: list[str] = Field(
        default_factory=list
    )

    lessons: int | None = None
    source_pages: list[int] = Field(default_factory=list)

    # Additional structured metadata where necessary.
    metadata: dict[
        str,
        str | int | float | bool | list[int] | None,
    ] = Field(default_factory=dict)


class CurriculumProfile(BaseModel):
    """
    Describes how a particular learning area's curriculum is organized.

    A profile must be grounded in a verified curriculum design
    before it is used to generate official curriculum-aligned plans.
    """

    profile_id: str
    authority: str = "KICD"

    curriculum_version: str | None = None
    source_verified: bool = False
    sources: list[CurriculumSource] = Field(default_factory=list)

    education_stage: str
    grade: str
    learning_area: str

    # Allows different curriculum structures.
    hierarchy_labels: list[str] = Field(default_factory=list)
    content_nodes: list[CurriculumContentNode] = Field(
        default_factory=list
    )

    # Curriculum content captured from the source design.
    general_learning_outcomes: list[str] = Field(
        default_factory=list
    )
    core_competencies: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    pertinent_and_contemporary_issues: list[str] = Field(
        default_factory=list
    )
    links_to_other_learning_areas: list[str] = Field(
        default_factory=list
    )

    # Planning guidance, to be populated from verified sources
    # and tested subject-specific rules.
    required_lesson_fields: list[str] = Field(default_factory=list)
    learning_experience_types: list[str] = Field(
        default_factory=list
    )
    assessment_methods: list[str] = Field(default_factory=list)

    notes: list[str] = Field(default_factory=list)