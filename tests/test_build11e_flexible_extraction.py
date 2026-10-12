
"""BUILD 11E-1 — Requirements for flexible curriculum extraction.

Science examples are synthetic fixtures based on excerpts supplied
by the developer, not verified extraction of a complete KICD PDF.
"""

from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
)


def make_science_profile():
    """Represent Strand -> Sub-strand without inventing a Theme."""
    science_strand = CurriculumContentNode(
        code="1.0",
        title="Scientific Investigation",
        node_type="strand",
        children=[
            CurriculumContentNode(
                code="1.1",
                title="Introduction to Integrated Science",
                node_type="sub_strand",
                parent_code="1.0",
                lessons=12,
                specific_learning_outcomes=[
                    "Explain the meaning of Integrated Science."
                ],
                suggested_learning_experiences=[
                    "Discuss examples of Integrated Science."
                ],
                key_inquiry_questions=[
                    "What is Integrated Science?"
                ],
                source_pages=[12],
            ),
            CurriculumContentNode(
                code="1.2",
                title="Laboratory Safety",
                node_type="sub_strand",
                parent_code="1.0",
                lessons=14,
                source_pages=[13],
            ),
            CurriculumContentNode(
                code="1.3",
                title="Laboratory apparatus and instruments",
                node_type="sub_strand",
                parent_code="1.0",
                lessons=16,
                source_pages=[14],
            ),
        ],
    )

    mixtures_strand = CurriculumContentNode(
        code="2.0",
        title="Mixtures, Elements and Compounds",
        node_type="strand",
        children=[
            CurriculumContentNode(
                code="2.1",
                title="Mixtures",
                node_type="sub_strand",
                parent_code="2.0",
                lessons=18,
                source_pages=[20],
            ),
            CurriculumContentNode(
                code="2.2",
                title="Acids, bases and indicators",
                node_type="sub_strand",
                parent_code="2.0",
                lessons=22,
                source_pages=[22],
            ),
        ],
    )

    return CurriculumProfile(
        profile_id="fixture-grade-7-integrated-science",
        source_verified=False,
        education_stage="Junior School",
        grade="Grade 7",
        learning_area="Integrated Science",
        hierarchy_labels=["Strand", "Sub-strand"],
        content_nodes=[science_strand, mixtures_strand],
        notes=[
            "Synthetic test fixture based on supplied excerpts."
        ],
    )


def test_science_hierarchy_does_not_invent_theme():
    profile = make_science_profile()

    assert profile.hierarchy_labels == ["Strand", "Sub-strand"]
    assert [node.node_type for node in profile.content_nodes] == [
        "strand",
        "strand",
    ]
    assert all(
        child.node_type == "sub_strand"
        for strand in profile.content_nodes
        for child in strand.children
    )


def test_science_lesson_allocations_are_preserved():
    profile = make_science_profile()

    lessons = [
        child.lessons
        for strand in profile.content_nodes
        for child in strand.children
    ]

    assert lessons == [12, 14, 16, 18, 22]


def test_science_content_stays_attached_to_its_sub_strand():
    profile = make_science_profile()
    introduction = profile.content_nodes[0].children[0]

    assert introduction.code == "1.1"
    assert introduction.parent_code == "1.0"
    assert introduction.specific_learning_outcomes == [
        "Explain the meaning of Integrated Science."
    ]
    assert introduction.suggested_learning_experiences == [
        "Discuss examples of Integrated Science."
    ]
    assert introduction.key_inquiry_questions == [
        "What is Integrated Science?"
    ]
    assert introduction.source_pages == [12]


def test_science_fixture_is_not_marked_as_verified():
    profile = make_science_profile()

    assert profile.source_verified is False
    assert any("Synthetic test fixture" in note for note in profile.notes)


def test_existing_three_level_hierarchy_remains_representable():
    profile = CurriculumProfile(
        profile_id="fixture-grade-9-english",
        source_verified=False,
        education_stage="Junior School",
        grade="Grade 9",
        learning_area="English",
        hierarchy_labels=["Theme", "Strand", "Sub-strand"],
        content_nodes=[
            CurriculumContentNode(
                code="1.0",
                title="Citizenship",
                node_type="theme",
                children=[
                    CurriculumContentNode(
                        code="1.1",
                        title="Listening and Speaking",
                        node_type="strand",
                        parent_code="1.0",
                        children=[
                            CurriculumContentNode(
                                code="1.1.1",
                                title="Polite Language",
                                node_type="sub_strand",
                                parent_code="1.1",
                                lessons=2,
                                source_pages=[10],
                            )
                        ],
                    )
                ],
            )
        ],
    )

    theme = profile.content_nodes[0]
    strand = theme.children[0]
    sub_strand = strand.children[0]

    assert [theme.node_type, strand.node_type, sub_strand.node_type] == [
        "theme",
        "strand",
        "sub_strand",
    ]
    assert sub_strand.lessons == 2
    assert sub_strand.source_pages == [10]
