
"""BUILD 11E-2 — Flexible curriculum text extraction tests.

Science input is synthetic and based on supplied excerpts.
It is not a substitute for testing the complete source PDF.
"""

from app.services.flexible_curriculum_extractor import (
    parse_curriculum_pages,
)


def test_science_extraction_supports_two_level_hierarchy():
    pages = [
        {
            "pdf_page": 10,
            "text": """
STRAND 1.0: SCIENTIFIC INVESTIGATION
Sub Strand: 1.1 Introduction to Integrated Science (12 lessons)
Specific Learning Outcomes
a) Explain the meaning of Integrated Science.
Suggested Learning Experiences
- Discuss examples of Integrated Science.
Suggested Key Inquiry Question(s)
1. What is Integrated Science?
Core competencies to be developed
- Communication and collaboration
Values
- Responsibility
Pertinent and Contemporary Issues (PCIs)
- Safety awareness
Link to other learning area
- Mathematics
10
""",
        },
        {
            "pdf_page": 11,
            "text": """
Sub Strand: 1.2 Laboratory Safety (14 lessons)
Specific Learning Outcomes
a) Identify basic laboratory safety practices.
11
""",
        },
    ]

    profile = parse_curriculum_pages(
        pages,
        grade="Grade 7",
        learning_area="Integrated Science",
        document_title="Synthetic Grade 7 Science",
    )

    assert profile.hierarchy_labels == ["Strand", "Sub-strand"]
    assert len(profile.content_nodes) == 1

    strand = profile.content_nodes[0]
    assert strand.code == "1.0"
    assert strand.title == "SCIENTIFIC INVESTIGATION"
    assert strand.node_type == "strand"

    introduction, safety = strand.children
    assert introduction.code == "1.1"
    assert introduction.lessons == 12
    assert safety.code == "1.2"
    assert safety.lessons == 14

    assert introduction.specific_learning_outcomes == [
        "Explain the meaning of Integrated Science."
    ]
    assert introduction.suggested_learning_experiences == [
        "Discuss examples of Integrated Science."
    ]
    assert introduction.key_inquiry_questions == [
        "What is Integrated Science?"
    ]
    assert introduction.core_competencies == [
        "Communication and collaboration"
    ]
    assert introduction.values == ["Responsibility"]
    assert introduction.pertinent_and_contemporary_issues == [
        "Safety awareness"
    ]
    assert introduction.links_to_other_learning_areas == ["Mathematics"]

    assert introduction.source_pages == [10]
    assert safety.source_pages == [11]
    assert profile.source_verified is False


def test_english_extraction_supports_three_level_hierarchy():
    pages = [
        {
            "pdf_page": 10,
            "text": """
THEME 1.0: CITIZENSHIP
1.1 Listening and Speaking
1.1.1 Polite Language (2 lessons)
By the end of the sub strand, the learner should be able to:
a) Use polite language appropriately.
The learner is guided to:
- Practise polite expressions in pairs.
Key Inquiry Question(s)
1. Why is polite language important?
10
""",
        }
    ]

    profile = parse_curriculum_pages(
        pages,
        grade="Grade 9",
        learning_area="English",
        document_title="Synthetic Grade 9 English",
    )

    assert profile.hierarchy_labels == [
        "Theme",
        "Strand",
        "Sub-strand",
    ]

    theme = profile.content_nodes[0]
    strand = theme.children[0]
    sub_strand = strand.children[0]

    assert theme.title == "CITIZENSHIP"
    assert strand.title == "Listening and Speaking"
    assert sub_strand.title == "Polite Language"
    assert sub_strand.lessons == 2
    assert sub_strand.specific_learning_outcomes == [
        "Use polite language appropriately."
    ]
    assert sub_strand.suggested_learning_experiences == [
        "Practise polite expressions in pairs."
    ]
    assert sub_strand.key_inquiry_questions == [
        "Why is polite language important?"
    ]


def test_unknown_input_is_not_marked_verified_or_silently_accepted():
    pages = [
        {
            "pdf_page": 4,
            "text": """
UNRECOGNIZED CURRICULUM HEADING
Some text whose structural role is unknown.
4
""",
        }
    ]

    profile = parse_curriculum_pages(
        pages,
        grade="Grade 7",
        learning_area="Unknown",
        document_title="Synthetic unknown document",
    )

    assert profile.source_verified is False
    assert profile.content_nodes == []
    assert profile.notes
    assert any("warning" in note.lower() for note in profile.notes)


def test_new_sub_strand_ends_previous_content_section():
    pages = [
        {
            "pdf_page": 10,
            "text": """
STRAND 1.0: SCIENTIFIC INVESTIGATION
Sub Strand: 1.1 Introduction to Integrated Science (12 lessons)
Specific Learning Outcomes
a) Explain Integrated Science.
Sub Strand: 1.2 Laboratory Safety (14 lessons)
Specific Learning Outcomes
a) Identify laboratory safety practices.
10
""",
        }
    ]

    profile = parse_curriculum_pages(
        pages,
        grade="Grade 7",
        learning_area="Integrated Science",
        document_title="Synthetic Science",
    )

    first, second = profile.content_nodes[0].children

    assert first.specific_learning_outcomes == [
        "Explain Integrated Science."
    ]
    assert second.specific_learning_outcomes == [
        "Identify laboratory safety practices."
    ]


def test_printed_page_number_is_not_used_as_pdf_page_number():
    pages = [
        {
            "pdf_page": 10,
            "text": """
STRAND 1.0: SCIENTIFIC INVESTIGATION
Sub Strand: 1.1 Introduction to Integrated Science (12 lessons)
Specific Learning Outcomes
a) Explain Integrated Science.
8
""",
        }
    ]

    profile = parse_curriculum_pages(
        pages,
        grade="Grade 7",
        learning_area="Integrated Science",
        document_title="Synthetic Science",
    )

    unit = profile.content_nodes[0].children[0]

    # The PDF page is known from the extraction input.
    assert unit.source_pages == [10]

    # Printed-page metadata is a separate concern. This assertion
    # documents the desired behavior for the next implementation step.
    assert unit.metadata.get("printed_pages") == [8]
