from app.models.curriculum import (
    CurriculumDocument,
    CurriculumTheme,
    CurriculumUnit,
)
from app.services.curriculum_document_adapter import (
    adapt_curriculum_document,
)


def test_document_adapter_preserves_hierarchy_content_and_pages():
    document = CurriculumDocument(
        source_file="sample-english.pdf",
        title="Sample English Curriculum",
        page_count=20,
        grade="Grade 9",
        learning_area="English",
        themes=[
            CurriculumTheme(
                code="1.0",
                title="Citizenship",
                start_pdf_page=5,
                end_pdf_page=8,
                units=[
                    CurriculumUnit(
                        theme_code="1.0",
                        theme_title="Citizenship",
                        strand_code="1.1",
                        strand="Listening and Speaking",
                        sub_strand_code="1.1.1",
                        sub_strand="Polite Language",
                        lessons=2,
                        specific_learning_outcomes=[
                            "Use polite language appropriately."
                        ],
                        suggested_learning_experiences=[
                            "Practise polite expressions in pairs."
                        ],
                        key_inquiry_questions=[
                            "Why is polite language important?"
                        ],
                        source_pdf_pages=[6, 7],
                        source_printed_pages=[12, 13],
                    )
                ],
            )
        ],
    )

    profile = adapt_curriculum_document(document)

    theme = profile.content_nodes[0]
    strand = theme.children[0]
    unit = strand.children[0]

    assert profile.source_verified is False
    assert profile.learning_area == "English"
    assert theme.node_type == "theme"
    assert strand.node_type == "strand"
    assert unit.code == "1.1.1"
    assert unit.title == "Polite Language"
    assert unit.lessons == 2
    assert unit.specific_learning_outcomes == [
        "Use polite language appropriately."
    ]
    assert unit.source_pages == [6, 7]
    assert profile.sources[0].document_title == "Sample English Curriculum"
    assert profile.sources[0].pages == [5, 6, 7, 8]
