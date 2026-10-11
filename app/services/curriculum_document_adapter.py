"""BUILD 11C — Adapt parsed curriculum documents to flexible profiles.

This adapter reshapes existing extracted records. It does not verify the
official source or claim that the parser extracted every item correctly.
"""

from app.models.curriculum import CurriculumDocument
from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
    CurriculumSource,
)


def adapt_curriculum_document(
    document: CurriculumDocument,
) -> CurriculumProfile:
    """Convert the existing theme/unit representation into a nested profile."""

    theme_nodes: list[CurriculumContentNode] = []
    source_pages: set[int] = set()

    for theme in document.themes:
        strand_nodes: dict[str, CurriculumContentNode] = {}

        for unit in theme.units:
            source_pages.update(unit.source_pdf_pages)

            strand_key = unit.strand_code
            if strand_key not in strand_nodes:
                strand_nodes[strand_key] = CurriculumContentNode(
                    code=unit.strand_code,
                    title=unit.strand,
                    node_type="strand",
                    parent_code=theme.code,
                )

            strand_nodes[strand_key].children.append(
                CurriculumContentNode(
                    code=unit.sub_strand_code,
                    title=unit.sub_strand,
                    node_type="sub_strand",
                    parent_code=unit.strand_code,
                    specific_learning_outcomes=list(
                        unit.specific_learning_outcomes
                    ),
                    suggested_learning_experiences=list(
                        unit.suggested_learning_experiences
                    ),
                    key_inquiry_questions=list(
                        unit.key_inquiry_questions
                    ),
                    core_competencies=list(unit.core_competencies),
                    pertinent_and_contemporary_issues=list(
                        unit.pertinent_and_contemporary_issues
                    ),
                    values=list(unit.values),
                    links_to_other_learning_areas=list(
                        unit.links_to_other_subjects
                    ),
                    lessons=unit.lessons,
                    source_pages=list(unit.source_pdf_pages),
                    metadata={
                        "source_printed_pages": ", ".join(
                            str(page)
                            for page in unit.source_printed_pages
                        )
                    },
                )
            )

        theme_pages = [theme.start_pdf_page]
        if theme.end_pdf_page is not None:
            theme_pages.append(theme.end_pdf_page)
        source_pages.update(theme_pages)

        theme_nodes.append(
            CurriculumContentNode(
                code=theme.code,
                title=theme.title,
                node_type="theme",
                source_pages=theme_pages,
                children=list(strand_nodes.values()),
            )
        )

    return CurriculumProfile(
        profile_id=f"uploaded-{document.learning_area or 'unknown'}-"
        f"{document.grade or 'unknown'}",
        authority="KICD",
        source_verified=False,
        sources=[
            CurriculumSource(
                authority="KICD",
                document_title=document.title or document.source_file,
                pages=sorted(source_pages),
            )
        ],
        education_stage="",
        grade=document.grade or "Unknown",
        learning_area=document.learning_area or "Unknown",
        hierarchy_labels=["Theme", "Strand", "Sub-strand"],
        content_nodes=theme_nodes,
        general_learning_outcomes=list(
            document.general_learning_outcomes
        ),
        notes=[
            "Adapted from the existing PDF parser output.",
            "Source verification has not been established by this adapter.",
            *[f"Parser warning: {warning}" for warning in document.warnings],
        ],
    )
