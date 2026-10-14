
"""BUILD 11E-2 — Flexible, page-aware curriculum text extraction.

This service interprets already-extracted page text. It does not
verify official sources or guarantee complete extraction from every PDF.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
    CurriculumSource,
)


THEME_RE = re.compile(
    r"^\s*THEME\s+(\d+(?:\.\d+)?)\s*[:.]?\s*(.+?)\s*$",
    re.IGNORECASE,
)

EXPLICIT_STRAND_RE = re.compile(
    r"^\s*STRAND\s+(\d+(?:\.\d+)?)\s*[:.]?\s*(.+?)\s*$",
    re.IGNORECASE,
)

EXPLICIT_SUB_STRAND_RE = re.compile(
    r"^\s*SUB[\s-]*STRAND\s*:?\s*"
    r"(\d+(?:\.\d+)+)\s+(.+?)\s*$",
    re.IGNORECASE,
)

NUMBERED_SUB_STRAND_RE = re.compile(
    r"^\s*(\d+\.\d+\.\d+)\s+(.+?)\s*$"
)

NUMBERED_HEADING_RE = re.compile(
    r"^\s*(\d+\.\d+)\s+(.+?)\s*$"
)

LESSON_SUFFIX_RE = re.compile(
    r"\s*\(\s*(\d+)\s+lessons?\s*\)\s*$",
    re.IGNORECASE,
)

SECTION_PATTERNS = [
    (
        "specific_learning_outcomes",
        re.compile(
            r"^(?:specific learning outcomes|"
            r"by the end of the sub[\s-]*strand)"
            r"\b",
            re.IGNORECASE,
        ),
    ),
    (
        "suggested_learning_experiences",
        re.compile(
            r"^(?:suggested learning experiences|"
            r"the learner is guided to)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "key_inquiry_questions",
        re.compile(
            r"^(?:suggested\s+)?key inquiry question"
            r"(?:s|\s*\(s\))?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "core_competencies",
        re.compile(r"^core competencies\b", re.IGNORECASE),
    ),
    (
        "values",
        re.compile(r"^values\b", re.IGNORECASE),
    ),
    (
        "pertinent_and_contemporary_issues",
        re.compile(
            r"^(?:pertinent and contemporary issues|PCIs?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "links_to_other_learning_areas",
        re.compile(
            r"^(?:links? to other subjects?|"
            r"links? to other learning areas?|"
            r"links? to other learning area)\b",
            re.IGNORECASE,
        ),
    ),
]


def _clean_line(value: str) -> str:
    """Normalize whitespace and common extracted bullet glyphs."""
    value = value.replace("\u2022", "•").replace("\uf0b7", "•")
    return re.sub(r"\s+", " ", value).strip()


def _content_line(value: str) -> str:
    """Remove a list marker without changing the content itself."""
    return re.sub(
        r"^(?:[•●▪◦]|[-–—]|[a-z]\)|\d+[.)])\s*",
        "",
        value,
        flags=re.IGNORECASE,
    ).strip()


def _section_for_heading(line: str) -> str | None:
    normalized = _clean_line(line).rstrip(":").strip()

    for field, pattern in SECTION_PATTERNS:
        if pattern.match(normalized):
            return field

    return None


def _split_lessons(title: str) -> tuple[str, int | None]:
    match = LESSON_SUFFIX_RE.search(title)
    if not match:
        return title.strip(), None

    clean_title = title[: match.start()].strip()
    return clean_title, int(match.group(1))


def _add_page(node: CurriculumContentNode, page: int) -> None:
    if page not in node.source_pages:
        node.source_pages.append(page)


def _append_content(
    node: CurriculumContentNode,
    section: str,
    line: str,
) -> None:
    value = _content_line(line)
    if not value:
        return

    target = getattr(node, section)
    if value not in target:
        target.append(value)



def parse_curriculum_pages(
    pages: Sequence[dict],
    *,
    grade: str,
    learning_area: str,
    document_title: str,
) -> CurriculumProfile:
    """Build a flexible profile from page-indexed extracted text.

    PDF page positions and likely printed footer numbers are stored
    separately. Printed-page detection is heuristic and must be verified
    against real source documents.
    """
    roots: list[CurriculumContentNode] = []
    current_theme: CurriculumContentNode | None = None
    current_strand: CurriculumContentNode | None = None
    current_unit: CurriculumContentNode | None = None
    current_section: str | None = None

    has_theme = False
    has_strand = False
    has_sub_strand = False
    warnings: list[str] = []
    observed_pages: set[int] = set()
    curriculum_ended = False
    in_rubric = False

    for page in pages:
        pdf_page = page.get("pdf_page")
        text = page.get("text", "")

        if not isinstance(pdf_page, int) or isinstance(pdf_page, bool) or pdf_page < 1:
            warnings.append("A page has a missing or invalid PDF page number.")
            continue

        observed_pages.add(pdf_page)

        # The table of contents is not the curriculum body.
        if "TABLE OF CONTENTS" in text.upper():
            continue

        # The appendix has its own numbering and must not be
        # parsed as the teaching hierarchy.
        if curriculum_ended:
            continue

        if re.search(r"\bAPPENDIX\s*:", text, re.IGNORECASE):
            curriculum_ended = True
            continue

        if not isinstance(text, str) or not text.strip():
            warnings.append(
                f"PDF page {pdf_page} contains no extractable text."
            )
            continue

        raw_lines = text.splitlines()
        nonempty_indexes = [
            i for i, value in enumerate(raw_lines) if value.strip()
        ]

        footer_index = None
        printed_page = None

        if nonempty_indexes:
            last_index = nonempty_indexes[-1]
            last_line = raw_lines[last_index].strip()
            if re.fullmatch(r"\d{1,3}", last_line):
                footer_index = last_index
                printed_page = int(last_line)

        for line_index, raw_line in enumerate(raw_lines):
            if line_index == footer_index:
                continue

            line = _clean_line(raw_line)
            if not line:
                continue

            if re.fullmatch(r"\d{1,3}", line):
                continue

            theme_match = THEME_RE.match(line)
            explicit_strand_match = EXPLICIT_STRAND_RE.match(line)
            explicit_sub_match = EXPLICIT_SUB_STRAND_RE.match(line)
            numbered_sub_match = NUMBERED_SUB_STRAND_RE.match(line)
            numbered_match = NUMBERED_HEADING_RE.match(line)

            # Assessment rubrics are supplementary, not sub-strand content.
            if in_rubric:
                if explicit_strand_match:
                    in_rubric = False
                else:
                    continue

            if re.match(
                r"^(?:suggested\s+)?assessment\s+rubrics?\b",
                line,
                re.IGNORECASE,
            ):
                in_rubric = True
                current_section = None
                continue

            if theme_match:
                code, title = theme_match.groups()
                title, _ = _split_lessons(title)
                current_theme = CurriculumContentNode(
                    code=code,
                    title=title,
                    node_type="theme",
                    source_pages=[pdf_page],
                )
                roots.append(current_theme)
                current_strand = None
                current_unit = None
                current_section = None
                has_theme = True
                continue

            if explicit_strand_match:
                code, title = explicit_strand_match.groups()
                title, _ = _split_lessons(title)

                siblings = (
                    current_theme.children if current_theme else roots
                )

                existing = next(
                    (
                        node for node in siblings
                        if node.node_type == "strand"
                        and node.code == code
                    ),
                    None,
                )

                if existing is not None:
                    current_strand = existing

                    if len(title) > len(existing.title):
                        existing.title = title

                    if pdf_page not in existing.source_pages:
                        existing.source_pages.append(pdf_page)
                else:
                    current_strand = CurriculumContentNode(
                        code=code,
                        title=title,
                        node_type="strand",
                        parent_code=current_theme.code if current_theme else None,
                        source_pages=[pdf_page],
                    )

                    if current_theme:
                        current_theme.children.append(current_strand)
                    else:
                        roots.append(current_strand)

                current_unit = None
                current_section = None
                has_strand = True
                continue

            if explicit_sub_match:
                code, title = explicit_sub_match.groups()
                title, lessons = _split_lessons(title)
                current_unit = CurriculumContentNode(
                    code=code,
                    title=title,
                    node_type="sub_strand",
                    parent_code=current_strand.code if current_strand else None,
                    lessons=lessons,
                    source_pages=[pdf_page],
                )
                if current_strand:
                    current_strand.children.append(current_unit)
                else:
                    warnings.append(
                        f"PDF page {pdf_page}: sub-strand {code} "
                        "appears before a recognizable strand."
                    )
                    roots.append(current_unit)

                current_section = None
                has_sub_strand = True
                continue

            if numbered_sub_match:
                code, title = numbered_sub_match.groups()
                title, lessons = _split_lessons(title)
                current_unit = CurriculumContentNode(
                    code=code,
                    title=title,
                    node_type="sub_strand",
                    parent_code=current_strand.code if current_strand else None,
                    lessons=lessons,
                    source_pages=[pdf_page],
                )
                if current_strand:
                    current_strand.children.append(current_unit)
                elif current_theme:
                    warnings.append(
                        f"PDF page {pdf_page}: sub-strand {code} "
                        "appears without a recognizable strand."
                    )
                    current_theme.children.append(current_unit)
                else:
                    warnings.append(
                        f"PDF page {pdf_page}: sub-strand {code} "
                        "appears without a recognizable parent."
                    )
                    roots.append(current_unit)

                current_section = None
                has_sub_strand = True
                continue

            if numbered_match:
                code, title = numbered_match.groups()
                title, lessons = _split_lessons(title)

                # Repeated 1.0 / 2.0 / 3.0 / 4.0 headings
                # are strand labels, not child sub-strands.
                if (
                    current_strand is not None
                    and current_theme is None
                    and code == current_strand.code
                ):
                    current_unit = None
                    current_section = None
                    continue

                # In a strand-only structure, 1.1 is a sub-strand.
                # Within a theme, 1.1 is treated as a strand.
                if current_strand is not None and current_theme is None:
                    current_unit = CurriculumContentNode(
                        code=code,
                        title=title,
                        node_type="sub_strand",
                        parent_code=current_strand.code,
                        lessons=lessons,
                        source_pages=[pdf_page],
                    )
                    current_strand.children.append(current_unit)
                    has_sub_strand = True
                else:
                    current_strand = CurriculumContentNode(
                        code=code,
                        title=title,
                        node_type="strand",
                        parent_code=current_theme.code if current_theme else None,
                        source_pages=[pdf_page],
                    )
                    if current_theme:
                        current_theme.children.append(current_strand)
                    else:
                        roots.append(current_strand)

                    current_unit = None
                    has_strand = True

                current_section = None
                continue

            section = _section_for_heading(line)
            if section:
                current_section = section
                continue

            if current_unit is not None and current_section is not None:
                _append_content(current_unit, current_section, line)
                _add_page(current_unit, pdf_page)

        # Attach a likely printed footer to the unit active on this page.
        # Keep it distinct from source_pages, which stores PDF page indexes.
        if (
            printed_page is not None
            and current_unit is not None
            and pdf_page in current_unit.source_pages
        ):
            printed_pages = current_unit.metadata.setdefault(
                "printed_pages", []
            )
            if printed_page not in printed_pages:
                printed_pages.append(printed_page)

    if not roots:
        warnings.append(
            "No recognizable curriculum hierarchy was found; "
            "review the extracted text and heading patterns."
        )

    if has_theme and has_strand and has_sub_strand:
        hierarchy_labels = ["Theme", "Strand", "Sub-strand"]
    elif has_strand and has_sub_strand:
        hierarchy_labels = ["Strand", "Sub-strand"]
    elif has_theme:
        hierarchy_labels = ["Theme"]
    elif has_strand:
        hierarchy_labels = ["Strand"]
    else:
        hierarchy_labels = []

    return CurriculumProfile(
        profile_id="extracted-curriculum",
        authority="KICD",
        source_verified=False,
        sources=[
            CurriculumSource(
                authority="KICD",
                document_title=document_title,
                pages=sorted(observed_pages),
            )
        ],
        education_stage="Junior School",
        grade=grade,
        learning_area=learning_area,
        hierarchy_labels=hierarchy_labels,
        content_nodes=roots,
        notes=[
            "Generated from extracted page text; source verification "
            "has not been established.",
            *[f"Warning: {warning}" for warning in warnings],
        ],
    )
