"""
BUILD 09 - Standardized CBE Lesson Plan Generator

Purpose:
    Convert a verified CurriculumUnit extracted from the real KICD curriculum
    PDF into a structured CBE lesson plan matching the organization seen in
    the supplied Grade 9 English lesson-plan reference document.

BUILD 09 deliberately leaves curriculum loading, unit selection, and lesson
plan details outside this service. It only upgrades the lesson-plan output
layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LessonStep:
    number: int
    title: str
    duration_minutes: int
    activities: list[str] = field(default_factory=list)


@dataclass
class LessonPlan:
    # Header
    school: str = ""
    teacher: str = ""
    grade: str = ""
    learning_area: str = ""
    date: str = ""
    time: str = ""
    duration_minutes: int = 40
    roll: str = ""

    # Curriculum alignment
    theme: str = ""
    strand: str = ""
    sub_strand: str = ""
    specific_learning_outcomes: list[str] = field(default_factory=list)
    key_inquiry_questions: list[str] = field(default_factory=list)
    core_competencies: list[str] = field(default_factory=list)
    pcis: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    links_to_other_subjects: list[str] = field(default_factory=list)

    # Lesson resources and flow
    learning_resources: list[str] = field(default_factory=list)
    introduction: dict[str, Any] = field(default_factory=dict)
    lesson_development: dict[str, Any] = field(default_factory=dict)
    conclusion: dict[str, Any] = field(default_factory=dict)

    # Follow-up / evaluation
    assessment: list[str] = field(default_factory=list)
    assessment_approaches: list[str] = field(default_factory=list)
    extended_activities: list[str] = field(default_factory=list)
    reflection: list[str] = field(default_factory=list)
    teacher_self_evaluation: dict[str, str] = field(default_factory=dict)

    # Traceability
    lesson_number: int = 1
    source_pages: list[int] = field(default_factory=list)
    source_document: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_list(value: Any) -> list[str]:
    """Normalize model fields without changing their meaning."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _field(unit: Any, *names: str, default: Any = None) -> Any:
    """Read a field from either a Pydantic model or a plain object."""
    for name in names:
        if hasattr(unit, name):
            value = getattr(unit, name)
            if value is not None:
                return value
        if isinstance(unit, dict) and name in unit and unit[name] is not None:
            return unit[name]
    return default


def _lesson_time(duration: int) -> tuple[int, int, int]:
    """Return introduction, development and conclusion minutes.

    The supplied reference examples commonly use 5/30/5 for a 40-minute
    lesson. BUILD 09 preserves that structure when duration is 40 and scales
    it proportionally for other durations.
    """
    duration = max(15, int(duration or 40))
    intro = max(3, round(duration * 0.125))
    conclusion = max(3, round(duration * 0.125))
    development = duration - intro - conclusion
    return intro, development, max(3, conclusion)


def _split_step_times(development: int, count: int = 4) -> list[int]:
    """Distribute development time across four classroom steps."""
    count = max(1, count)
    base = development // count
    remainder = development % count
    return [base + (1 if i < remainder else 0) for i in range(count)]


def _default_resources(unit: Any) -> list[str]:
    resources = _clean_list(_field(unit, "learning_resources", "resources"))
    return resources or [
        "Curriculum Design",
        "Teacher's Guide",
        "Lesson notes",
    ]


def _build_steps(unit: Any, outcomes: list[str], questions: list[str], times: list[int]) -> list[LessonStep]:
    """Create a generic but curriculum-grounded four-step lesson sequence.

    The reference document demonstrates four-step development in many lessons,
    but also shows variation. Four steps are therefore the default V1 shape;
    the API remains data-driven so a future AI/activity planner can replace it.
    """
    focus = _field(unit, "sub_strand", "sub_strand_title", default="the lesson focus")
    outcome_focus = outcomes[0] if outcomes else f"understand {focus}"
    inquiry = questions[0] if questions else "What have we learned about this topic?"

    return [
        LessonStep(
            1,
            "Introduction and Prior Knowledge",
            times[0],
            [
                "Review relevant prior learning and introduce the lesson focus.",
                f"Guide learners to consider the lesson focus: {focus}.",
                f"Introduce the key inquiry question: {inquiry}",
            ],
        ),
        LessonStep(
            2,
            "Guided Exploration",
            times[1],
            [
                f"Guide learners through an activity directly related to: {outcome_focus}.",
                "Learners work individually, in pairs, or in groups as appropriate.",
                "Teacher observes, questions and provides support where needed.",
            ],
        ),
        LessonStep(
            3,
            "Application and Practice",
            times[2],
            [
                "Learners apply the concept or skill through a structured task.",
                "Learners share responses, examples, performances or written work.",
                "Teacher gives immediate formative feedback and addresses misconceptions.",
            ],
        ),
        LessonStep(
            4,
            "Sharing and Consolidation",
            times[3],
            [
                "Learners present or compare their work with peers.",
                "Class discusses key findings and connects them to the lesson outcomes.",
                "Teacher checks understanding using brief oral or written questions.",
            ],
        ),
    ]


def _extended_activities(unit: Any, outcomes: list[str]) -> list[str]:
    focus = _field(unit, "sub_strand", "sub_strand_title", default="the lesson topic")
    outcome = outcomes[0] if outcomes else f"the skills developed under {focus}"
    return [
        f"Creative/Application Task: Learners complete a short task at home or in a learning group applying {outcome.lower()}.",
        f"Research/Reading Task: Learners find an additional example related to {focus} and prepare a brief report or class sharing.",
        "Peer Extension: Learners exchange their work with a peer and give feedback using the lesson criteria.",
    ]


def _assessment(unit: Any, outcomes: list[str]) -> tuple[list[str], list[str]]:
    items = []
    for outcome in outcomes[:3]:
        items.append(f"Check learner achievement of the outcome: {outcome}")
    if not items:
        items = ["Oral questioning", "Observation of learner participation", "Review of learner work"]
    approaches = [
        "Observation",
        "Oral questioning",
        "Individual or group task",
        "Peer assessment where appropriate",
        "Review of learner written/performed work",
    ]
    return items, approaches


def generate_lesson_plan(
    unit: Any,
    teacher_name: str = "",
    school_name: str = "",
    lesson_date: str = "",
    duration_minutes: int = 40,
    class_size: int | None = None,
    lesson_number: int = 1,
    lesson_time: str = "",
) -> dict[str, Any]:
    """Generate BUILD 09 standardized lesson-plan data from a verified unit."""

    duration = int(duration_minutes or 40)
    intro_minutes, development_minutes, conclusion_minutes = _lesson_time(duration)
    step_times = _split_step_times(development_minutes, 4)

    outcomes = _clean_list(_field(unit, "specific_learning_outcomes", "learning_outcomes", "slos"))
    questions = _clean_list(_field(unit, "key_inquiry_questions", "key_inquiry_question", "kiqs"))
    competencies = _clean_list(_field(unit, "core_competencies", "core_competency", "competencies"))
    pcis = _clean_list(_field(unit, "pcis", "pertinent_and_contemporary_issues"))
    values = _clean_list(_field(unit, "values", "values_"))
    links = _clean_list(_field(unit, "links_to_other_subjects", "links_to_subjects", "other_subjects"))
    source_pages = _clean_list(_field(unit, "source_pages", "pages"))

    assessment, approaches = _assessment(unit, outcomes)
    steps = _build_steps(unit, outcomes, questions, step_times)
    resources = _default_resources(unit)
    focus = _field(unit, "sub_strand", "sub_strand_title", default="the lesson topic")

    plan = LessonPlan(
        school=school_name,
        teacher=teacher_name,
        grade=_field(unit, "grade", "grade_level", default="Grade 9"),
        learning_area=_field(unit, "learning_area", "subject", default="English"),
        date=lesson_date,
        time=lesson_time,
        duration_minutes=duration,
        roll=str(class_size) if class_size is not None else "",
        theme=_field(unit, "theme", "theme_title", default=""),
        strand=_field(unit, "strand", "strand_title", default=""),
        sub_strand=focus,
        specific_learning_outcomes=outcomes,
        key_inquiry_questions=questions,
        core_competencies=competencies,
        pcis=pcis,
        values=values,
        links_to_other_subjects=links,
        learning_resources=resources,
        introduction={
            "duration_minutes": intro_minutes,
            "activities": [
                "Review relevant prior learning.",
                "Introduce the lesson focus and key inquiry question(s).",
                "Link the lesson to learners' prior knowledge and experience.",
            ],
        },
        lesson_development={
            "duration_minutes": development_minutes,
            "steps": [asdict(step) for step in steps],
        },
        conclusion={
            "duration_minutes": conclusion_minutes,
            "activities": [
                "Summarize the key points and learning achieved.",
                "Use a brief formative check such as oral questions, a quiz, or an exit response.",
                "Preview the next lesson or follow-up learning where appropriate.",
            ],
        },
        assessment=assessment,
        assessment_approaches=approaches,
        extended_activities=_extended_activities(unit, outcomes),
        reflection=[
            "What did learners understand well?",
            "Which activity or explanation was most effective?",
            "What needs reinforcement in the next lesson?",
        ],
        teacher_self_evaluation={
            "what_went_well": "",
            "areas_for_improvement": "",
            "learners_needing_support": "",
            "action_for_next_lesson": "",
            "teacher_signature": "",
            "date": "",
        },
        lesson_number=int(lesson_number or 1),
        source_pages=[int(p) for p in source_pages if str(p).isdigit()],
        source_document=str(_field(unit, "source_document", "document_name", default="")),
    )

    return plan.to_dict()
