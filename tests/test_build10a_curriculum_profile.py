
from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
    CurriculumSource,
)


def test_curriculum_profile_supports_different_hierarchies():
    mathematics = CurriculumProfile(
        profile_id="test-mathematics-grade-7",
        education_stage="Junior School",
        grade="7",
        learning_area="Mathematics",
        hierarchy_labels=["topic", "subtopic"],
        content_nodes=[
            CurriculumContentNode(
                code="M1",
                title="Numbers",
                node_type="topic",
                children=[
                    CurriculumContentNode(
                        code="M1.1",
                        title="Example subtopic",
                        node_type="subtopic",
                        parent_code="M1",
                    )
                ],
            )
        ],
    )

    assert mathematics.learning_area == "Mathematics"
    assert mathematics.content_nodes[0].title == "Numbers"
    assert mathematics.content_nodes[0].children[0].node_type == "subtopic"


def test_curriculum_profile_supports_subject_specific_planning():
    science = CurriculumProfile(
        profile_id="test-integrated-science-grade-7",
        education_stage="Junior School",
        grade="7",
        learning_area="Integrated Science",
        hierarchy_labels=["strand", "sub_strand"],
        learning_experience_types=["investigation"],
        assessment_methods=["observation"],
    )

    assert science.learning_area == "Integrated Science"
    assert "investigation" in science.learning_experience_types
    assert "observation" in science.assessment_methods


def test_curriculum_profile_preserves_source_references():
    source = CurriculumSource(
        authority="KICD",
        document_title="Test curriculum design",
        curriculum_version="test",
        pages=[12, 13],
    )

    profile = CurriculumProfile(
        profile_id="test-profile",
        education_stage="Junior School",
        grade="7",
        learning_area="Agriculture",
        sources=[source],
    )

    assert profile.sources[0].authority == "KICD"
    assert profile.sources[0].pages == [12, 13]


def test_unverified_profile_is_not_marked_verified_by_default():
    profile = CurriculumProfile(
        profile_id="draft-profile",
        education_stage="Junior School",
        grade="7",
        learning_area="Kiswahili",
    )

    assert profile.source_verified is False
    assert profile.content_nodes == []

def test_content_node_stores_its_own_curriculum_requirements():
    node = CurriculumContentNode(
        code="M1.1",
        title="Example Mathematics topic",
        node_type="subtopic",
        specific_learning_outcomes=[
            "Verified outcome for this topic"
        ],
        suggested_learning_experiences=[
            "Verified learning experience for this topic"
        ],
        key_inquiry_questions=[
            "Verified inquiry question for this topic"
        ],
        source_pages=[12],
    )

    assert node.specific_learning_outcomes == [
        "Verified outcome for this topic"
    ]
    assert node.suggested_learning_experiences == [
        "Verified learning experience for this topic"
    ]
    assert node.key_inquiry_questions == [
        "Verified inquiry question for this topic"
    ]
    assert node.source_pages == [12]
