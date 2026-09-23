"""
BUILD 07E - Curriculum extraction validation.
"""

from app.models.curriculum import CurriculumDocument


def validate_curriculum(document: CurriculumDocument) -> list[str]:
    warnings: list[str] = []

    if not document.themes:
        warnings.append("No curriculum themes were extracted.")

    for theme in document.themes:
        for unit in theme.units:
            prefix = f"{unit.sub_strand_code} {unit.sub_strand}"

            if not unit.strand:
                warnings.append(f"{prefix}: strand name is missing.")

            if not unit.specific_learning_outcomes:
                warnings.append(f"{prefix}: no Specific Learning Outcomes extracted.")

            if not unit.suggested_learning_experiences:
                warnings.append(f"{prefix}: no Suggested Learning Experiences extracted.")

            if not unit.key_inquiry_questions:
                warnings.append(f"{prefix}: no Key Inquiry Questions extracted.")

            if not unit.core_competencies:
                warnings.append(f"{prefix}: no Core Competencies extracted.")

            if not unit.pertinent_and_contemporary_issues:
                warnings.append(f"{prefix}: no PCIs extracted.")

            if not unit.values:
                warnings.append(f"{prefix}: no Values extracted.")

            if not unit.links_to_other_subjects:
                warnings.append(f"{prefix}: no Links to Other Subjects extracted.")

            if not unit.source_pdf_pages:
                warnings.append(f"{prefix}: source PDF page provenance is missing.")

    return warnings
