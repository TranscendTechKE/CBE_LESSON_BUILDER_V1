
"""BUILD 10B — Adapt flexible curriculum profiles for lesson generation.

This adapter translates a selected CurriculumContentNode and its parent
context into the dictionary format expected by the BUILD 09 generator.

It does not verify curriculum sources or invent official curriculum content.
"""

from typing import Any

from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
)


class CurriculumProfileAdapterError(ValueError):
    """Raised when a profile cannot safely be adapted."""


def _node_dict(node: CurriculumContentNode) -> dict[str, Any]:
    """Return a node as a plain dictionary."""
    return node.model_dump()


def _find_node_path(
    nodes: list[CurriculumContentNode],
    target_code: str,
    ancestors: list[CurriculumContentNode] | None = None,
) -> list[CurriculumContentNode] | None:
    """Find a node by code and return its root-to-node path."""
    ancestors = ancestors or []

    for node in nodes:
        path = ancestors + [node]

        if node.code == target_code:
            return path

        result = _find_node_path(node.children, target_code, path)
        if result is not None:
            return result

    return None


def adapt_profile_node(
    profile: CurriculumProfile,
    selected_node_code: str,
    *,
    allow_unverified: bool = False,
) -> dict[str, Any]:
    """Map a selected profile node into the BUILD 09 input structure.

    Unverified profiles are rejected by default. The explicit override is
    intended for testing and development, not for claiming KICD verification.
    """
    if not profile.source_verified and not allow_unverified:
        raise CurriculumProfileAdapterError(
            "Curriculum profile is not verified. "
            "Verify its official source before generating an aligned plan."
        )

    path = _find_node_path(
        profile.content_nodes,
        selected_node_code,
    )

    if path is None:
        raise CurriculumProfileAdapterError(
            f"Curriculum node code not found: {selected_node_code}"
        )

    selected = path[-1]

    # Use the nearest matching ancestor for theme/strand context.
    theme = ""
    strand = ""
    for node in path:
        if node.node_type.lower() in {"theme", "unit"}:
            theme = node.title
        elif node.node_type.lower() == "strand":
            strand = node.title

    # Keep curriculum statements attached to the selected node.
    # Do not silently substitute ancestor outcomes for missing outcomes.
    return {
        "grade": profile.grade,
        "learning_area": profile.learning_area,
        "theme": theme,
        "strand": strand,
        "sub_strand": selected.title,
        "specific_learning_outcomes": list(
            selected.specific_learning_outcomes
        ),
        "suggested_learning_experiences": list(
            selected.suggested_learning_experiences
        ),
        "key_inquiry_questions": list(
            selected.key_inquiry_questions
        ),
        "core_competencies": list(
            selected.core_competencies
            or profile.core_competencies
        ),
        "pertinent_and_contemporary_issues": list(
            selected.pertinent_and_contemporary_issues
            or profile.pertinent_and_contemporary_issues
        ),
        "values": list(selected.values or profile.values),
        "links_to_other_subjects": list(
            selected.links_to_other_learning_areas
            or profile.links_to_other_learning_areas
        ),
        "source_pages": sorted(
            {
                page
                for node in path
                for page in node.source_pages
            }
        ),
        "source_document": "; ".join(
            source.document_title for source in profile.sources
        ),
        "selected_node_code": selected.code,
        "selected_node_type": selected.node_type,
        "ancestor_path": [
            {
                "code": node.code,
                "title": node.title,
                "node_type": node.node_type,
            }
            for node in path[:-1]
        ],
        "profile_id": profile.profile_id,
        "source_verified": profile.source_verified,
    }