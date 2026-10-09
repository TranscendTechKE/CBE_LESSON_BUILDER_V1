"""
BUILD 08 - CBE lesson-plan generator.

The generator is deliberately curriculum-grounded:
it cannot generate a lesson plan from a free-text topic alone.
It requires a selected CurriculumUnit and copies its verified fields
into the lesson plan before adding teacher-editable pedagogical details.
"""

from __future__ import annotations
from datetime import date
from typing import Any

from app.models.curriculum import CurriculumUnit


def _dedupe(values: list[str]) -> list[str]:
    out, seen = [], set()
    for value in values:
        v = " ".join(value.split()).strip()
        if v and v.casefold() not in seen:
            seen.add(v.casefold())
            out.append(v)
    return out


def generate_lesson_plan(
    unit: CurriculumUnit,
    *,
    teacher_name: str = "",
    school_name: str = "",
    lesson_date: str = "",
    duration_minutes: int = 40,
    class_size: int | None = None,
    lesson_number: int = 1,
) -> dict[str, Any]:
    """Generate a CBE-aligned lesson-plan draft from one verified unit."""

    outcomes = _dedupe(unit.specific_learning_outcomes)
    experiences = _dedupe(unit.suggested_learning_experiences)
    inquiries = _dedupe(unit.key_inquiry_questions)

    # Keep lesson objectives traceable to the curriculum outcomes.
    objectives = [
        {
            "objective": outcome,
            "source": "Specific Learning Outcome",
            "source_pdf_pages": unit.source_pdf_pages,
        }
        for outcome in outcomes
    ]

    # Suggested experiences become candidate classroom activities, not
    # invented curriculum requirements.
    activities = []
    for index, experience in enumerate(experiences, start=1):
        activities.append(
            {
                "step": index,
                "activity": experience,
                "teacher_role": "Facilitate, question, model and provide feedback.",
                "learner_role": "Participate actively and demonstrate evidence of learning.",
            }
        )

    if not activities:
        activities = [
            {
                "step": 1,
                "activity": "Teacher-guided exploration of the selected curriculum outcome.",
                "teacher_role": "Facilitate learning and provide feedback.",
                "learner_role": "Participate and demonstrate learning.",
            }
        ]

    return {
        "document_type": "CBE Lesson Plan",
        "generated_on": date.today().isoformat(),
        "teacher": teacher_name,
        "school": school_name,
        "lesson_date": lesson_date,
        "duration_minutes": duration_minutes,
        "class_size": class_size,
        "lesson_number": lesson_number,

        "curriculum": {
            "grade": "Grade 9",
            "learning_area": "English",
            "theme_code": unit.theme_code,
            "theme": unit.theme_title,
            "strand_code": unit.strand_code,
            "strand": unit.strand,
            "sub_strand_code": unit.sub_strand_code,
            "sub_strand": unit.sub_strand,
            "lessons_allocated": unit.lessons,
            "source_pdf_pages": unit.source_pdf_pages,
            "source_printed_pages": unit.source_printed_pages,
        },

        "specific_learning_outcomes": outcomes,
        "lesson_objectives": objectives,
        "key_inquiry_questions": inquiries,
        "suggested_learning_experiences": experiences,

        "core_competencies": _dedupe(unit.core_competencies),
        "pertinent_and_contemporary_issues": _dedupe(
            unit.pertinent_and_contemporary_issues
        ),
        "values": _dedupe(unit.values),
        "links_to_other_subjects": _dedupe(unit.links_to_other_subjects),

        "lesson_flow": {
            "introduction": {
                "suggested_minutes": min(5, max(3, duration_minutes // 8)),
                "activity": "Activate prior knowledge and introduce the selected sub-strand.",
            },
            "development": {
                "suggested_minutes": max(20, duration_minutes - 15),
                "activities": activities,
            },
            "assessment": {
                "suggested_minutes": 5,
                "activity": "Use questioning, observation, learner work and/or performance evidence aligned to the selected outcome.",
            },
            "reflection": {
                "suggested_minutes": 5,
                "teacher_prompt": "What evidence showed that the learners achieved the selected outcome? What needs reinforcement?",
                "learner_prompt": "What did I learn, practise or improve?",
            },
        },

        "assessment": {
            "approaches": [
                "Question and answer",
                "Observation",
                "Learner performance/work",
                "Peer/self assessment where appropriate",
            ],
            "alignment_note": "Assessment evidence should be matched to the selected Specific Learning Outcome(s).",
        },

        "resources": [
            "Relevant curriculum-approved/non-digital resources available at the school",
            "Relevant digital resources where available",
            "Learner exercise books/materials",
        ],

        "teacher_notes": "",
        "adaptations": "",
    }
