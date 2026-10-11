import pytest

from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
    CurriculumSource,
)
from app.services.curriculum_profile_adapter import (
    CurriculumProfileAdapterError,
    adapt_profile_node,
)
from app.services.lesson_plan_generator import generate_lesson_plan


def make_profile(source_verified=True):
    return CurriculumProfile(
        profile_id="test-maths-grade-7",
        source_verified=source_verified,
        education_stage="Junior School",
        grade="7",
        learning_area="Mathematics",
        sources=[
            CurriculumSource(
                document_title="Test curriculum document",
                pages=[12],
            )
        ],
        content_nodes=[
            CurriculumContentNode(
                code="M1",
                title="Numbers",
                node_type="strand",
                source_pages=[12],
                children=[
                    CurriculumContentNode(
                        code="M1.1",
                        title="Example topic",
                        node_type="sub_strand",
                        specific_learning_outcomes=[
                            "Verified test outcome"
                        ],
                        suggested_learning_experiences=[
                            "Verified test learning experience"
                        ],
                        key_inquiry_questions=[
                            "Test inquiry question?"
                        ],
                        source_pages=[13],
                    )
                ],
            )
        ],
    )


def test_adapter_maps_selected_node_and_parent_context():
    profile = make_profile()

    result = adapt_profile_node(profile, "M1.1")

    assert result["grade"] == "7"
    assert result["learning_area"] == "Mathematics"
    assert result["strand"] == "Numbers"
    assert result["sub_strand"] == "Example topic"
    assert result["specific_learning_outcomes"] == [
        "Verified test outcome"
    ]
    assert result["suggested_learning_experiences"] == [
        "Verified test learning experience"
    ]


def test_adapter_preserves_source_page_traceability():
    result = adapt_profile_node(make_profile(), "M1.1")

    assert result["source_pages"] == [12, 13]
    assert result["source_document"] == "Test curriculum document"


def test_adapter_rejects_unverified_profile_by_default():
    with pytest.raises(CurriculumProfileAdapterError):
        adapt_profile_node(
            make_profile(source_verified=False),
            "M1.1",
        )


def test_adapter_can_be_used_for_unverified_development_data():
    result = adapt_profile_node(
        make_profile(source_verified=False),
        "M1.1",
        allow_unverified=True,
    )

    assert result["source_verified"] is False


def test_adapter_rejects_unknown_node_code():
    with pytest.raises(CurriculumProfileAdapterError):
        adapt_profile_node(make_profile(), "UNKNOWN")


def test_adapter_output_works_with_existing_lesson_generator():
    profile = make_profile()

    adapted_unit = adapt_profile_node(profile, "M1.1")
    plan = generate_lesson_plan(adapted_unit)

    assert plan["learning_area"] == "Mathematics"
    assert plan["grade"] == "7"
    assert plan["sub_strand"] == "Example topic"
    assert plan["specific_learning_outcomes"] == [
        "Verified test outcome"
    ]
    assert plan["source_pages"] == [12, 13]
    assert plan["source_document"] == "Test curriculum document"
    assert plan["duration_minutes"] == 40
    assert len(plan["lesson_development"]["steps"]) == 4
