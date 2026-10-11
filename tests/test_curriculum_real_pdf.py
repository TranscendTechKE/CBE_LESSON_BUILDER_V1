"""
BUILD 07F - Regression test against the REAL uploaded Grade 9 English PDF.

This test is intentionally data-specific. It is not a hypothetical curriculum
fixture. Copy GRADE.9.ENGLISH.pdf into tests/fixtures/ before running locally,
or pass its real path through the test helper.
"""

from pathlib import Path

from app.services.curriculum_parser import parse_curriculum_pdf
from app.services.validator import validate_curriculum
from app.services.curriculum_document_adapter import (
    adapt_curriculum_document,
)


FIXTURE = Path(__file__).parent / "fixtures" / "GRADE.9.ENGLISH.pdf"


def test_real_grade_9_english_structure():
    if not FIXTURE.exists():
        return

    document = parse_curriculum_pdf(FIXTURE)

    assert document.page_count == 152
    assert document.learning_area == "English"
    assert document.grade == "Grade 9"

    assert document.extraction_start_page == 10
    assert document.themes

    first = document.themes[0]
    assert first.code == "1.0"
    assert first.title.upper() == "CITIZENSHIP"
    assert first.start_pdf_page == 10

    first_unit = first.units[0]
    assert first_unit.strand_code == "1.1"
    assert first_unit.strand == "Listening and Speaking"
    assert first_unit.sub_strand_code == "1.1.1"
    assert first_unit.sub_strand == "Polite Language"
    assert first_unit.lessons == 2

    assert any("euphemism" in x.lower() for x in first_unit.specific_learning_outcomes)
    assert any("define the term euphemism" in x.lower() for x in first_unit.suggested_learning_experiences)
    assert first_unit.key_inquiry_questions
    assert first_unit.core_competencies
    assert first_unit.pertinent_and_contemporary_issues
    assert first_unit.values
    assert first_unit.links_to_other_subjects

    warnings = validate_curriculum(document)
    # We permit warnings elsewhere in the 152-page document; the regression
    # test only requires the first real unit to be structurally complete.
    assert not any(warning.startswith("1.1.1 ") for warning in warnings)


def test_real_document_has_multiple_themes():
    if not FIXTURE.exists():
        return

    document = parse_curriculum_pdf(FIXTURE)

    assert len(document.themes) >= 14
    assert document.themes[0].code == "1.0"
    assert document.themes[1].code == "2.0"


def test_real_grade_9_english_adapts_to_profile():
    if not FIXTURE.exists():
        return

    document = parse_curriculum_pdf(FIXTURE)
    profile = adapt_curriculum_document(document)

    assert profile.source_verified is False
    assert profile.learning_area == "English"
    assert profile.grade == "Grade 9"
    assert profile.content_nodes

    # Preserve the first theme and its hierarchy.
    theme = profile.content_nodes[0]
    assert theme.code == document.themes[0].code
    assert theme.title == document.themes[0].title
    assert theme.node_type == "theme"
    assert theme.children

    strand = theme.children[0]
    assert strand.node_type == "strand"
    assert strand.children

    # Preserve the first actual curriculum unit.
    unit = strand.children[0]
    original_unit = document.themes[0].units[0]

    assert unit.code == original_unit.sub_strand_code
    assert unit.title == original_unit.sub_strand
    assert unit.node_type == "sub_strand"
    assert unit.lessons == original_unit.lessons
    assert unit.specific_learning_outcomes == (
        original_unit.specific_learning_outcomes
    )
    assert unit.source_pages == original_unit.source_pdf_pages

    # Every parsed unit should remain represented in the profile.
    original_count = sum(
        len(theme.units) for theme in document.themes
    )
    adapted_count = sum(
        len(strand.children)
        for theme in profile.content_nodes
        for strand in theme.children
    )
    assert adapted_count == original_count