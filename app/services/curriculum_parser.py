"""
BUILD 07B-07E - Real KICD curriculum parser.

This parser was designed against the uploaded:
    GRADE.9.ENGLISH.pdf

It does NOT assume that "page 10" is always the starting page.
Instead it detects the first THEME <number>.0 heading and then uses
the curriculum's own strand/sub-strand codes and section headings.

The parser is deliberately tolerant of PDF line wrapping because the
source PDF frequently splits headings and sentences over multiple lines.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from app.models.curriculum import CurriculumDocument, CurriculumTheme, CurriculumUnit
from app.services.pdf_processor import extract_pdf_pages


THEME_RE = re.compile(
    r"^\s*THEME\s+(\d+(?:\.\d+)?)\s*[:.]?\s*(.+?)\s*$",
    re.IGNORECASE,
)
STRAND_RE = re.compile(
    r"^\s*(\d+)\.(\d+)\s+(.+?)\s*$",
)
SUB_STRAND_RE = re.compile(
    r"^\s*(\d+)\.(\d+)\.(\d+)\s+(.+?)\s*$",
)
LESSON_RE = re.compile(r"\(\s*(\d+)\s+lessons?\s*\)", re.IGNORECASE)
PRINTED_PAGE_RE = re.compile(r"(?<!\d)(\d{1,3})\s*$")

SECTION_HEADINGS = {
    "outcomes": "outcomes",
    "experiences": "experiences",
    "inquiry": "inquiry",
    "competencies": "competencies",
    "pcis": "pcis",
    "values": "values",
    "links": "links",
}

HEADER_WORDS = {
    "strand",
    "sub strand",
    "sub-strand",
    "specific learning outcomes",
    "suggested learning experiences",
    "key inquiry question (s)",
    "key inquiry questions",
}


def _clean_line(line: str) -> str:
    line = line.replace("\u2022", "")
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^(?:|[-–—]|o)\s+", line))


def _strip_bullet(line: str) -> str:
    return re.sub(r"^(?:|[-–—]|o)\s+", "", line).strip()


def _is_letter_item(line: str) -> bool:
    return bool(re.match(r"^[a-z]\)\s+", line, re.IGNORECASE))


def _is_number_item(line: str) -> bool:
    return bool(re.match(r"^\d+[.)]\s+", line))


def _is_section_heading(line: str) -> str | None:
    n = re.sub(r"\s+", " ", line.strip().lower())
    if n.startswith("core competencies to be developed"):
        return "competencies"
    if n.startswith("pertinent and contemporary issues"):
        return "pcis"
    if n.startswith("values"):
        return "values"
    if n.startswith("link to other subject"):
        return "links"
    if n.startswith("links to other subject"):
        return "links"
    if n.startswith("by the end of the sub strand"):
        return "outcomes"
    if n.startswith("the learner is guided to"):
        return "experiences"
    return None


def _looks_like_table_header(line: str) -> bool:
    n = re.sub(r"\s+", " ", line.lower()).strip()
    return n in HEADER_WORDS or n.startswith("key inquiry question")


def _normalise_heading_fragments(lines: list[str]) -> list[str]:
    """
    Remove repeated table headers and obvious page-number-only lines.
    Keep content lines intact otherwise.
    """
    output: list[str] = []
    for raw in lines:
        line = _clean_line(raw)
        if not line:
            continue

        # PyMuPDF sometimes places a new structural heading on the same
        # extracted line as the previous cell/page content, for example:
        #   "1.2 Reading 1.2.1 Independent Reading - Grade Appropriate Text"
        # or:
        #   "... Link to other subjects THEME 14.0: SPORTS ..."
        # Split those structural boundaries before parsing.
        line = re.sub(r"(?<!^)\s+(?=\d+\.\d+\.\d+(?:\s|$))", "\n", line)
        line = re.sub(r"(?<!^)\s+(?=THEME\s+\d+(?:\.\d+)?\s*[:.])", "\n", line, flags=re.I)
        line = re.sub(r"(?<!^)\s+(?=(?:Specific Learning Outcomes|Suggested Learning Experiences|Key Inquiry Question(?:\(s\))?|Core Competencies to be Developed|Pertinent and Contemporary Issues \(PCIs\)|Values|Links? to other subjects))", "\n", line, flags=re.I)

        for fragment in line.split("\n"):
            fragment = _clean_line(fragment)
            if not fragment:
                continue
            if _looks_like_table_header(fragment):
                continue
            if re.fullmatch(r"\d{1,3}", fragment):
                # Printed page numbers occur at page ends. They are stored separately.
                continue
            output.append(fragment)
    return output


def _parse_printed_page(lines: list[str]) -> int | None:
    # In this KICD PDF, printed page numbers appear as a standalone line,
    # usually at the end of a page's extracted text.
    for line in reversed(lines):
        line = _clean_line(line)
        if re.fullmatch(r"\d{1,3}", line):
            return int(line)
    return None


def detect_theme_pages(pages: list[dict]) -> list[CurriculumTheme]:
    themes: list[CurriculumTheme] = []
    for page in pages:
        lines = [_clean_line(x) for x in page["text"].splitlines()]
        for line in lines:
            match = THEME_RE.match(line)
            if match:
                themes.append(
                    CurriculumTheme(
                        code=match.group(1),
                        title=match.group(2).strip(),
                        start_pdf_page=page["pdf_page"],
                    )
                )
                break

    for index, theme in enumerate(themes):
        if index + 1 < len(themes):
            theme.end_pdf_page = themes[index + 1].start_pdf_page - 1
        else:
            theme.end_pdf_page = pages[-1]["pdf_page"] if pages else None

    return themes


def _parse_list_section(lines: list[str], mode: str) -> list[str]:
    """
    Parse wrapped bullet/letter/number items.

    KICD uses bullets for experiences/competencies/PCIs/values/links,
    letters for outcomes and numbers for inquiry questions.
    """
    items: list[str] = []
    current: str | None = None

    for line in lines:
        line = _clean_line(line)
        if not line:
            continue

        starts = (
            _is_bullet(line)
            if mode in {"experiences", "competencies", "pcis", "values", "links"}
            else _is_letter_item(line)
            if mode == "outcomes"
            else _is_number_item(line)
        )

        if starts:
            if current:
                items.append(current.strip())
            if mode in {"experiences", "competencies", "pcis", "values", "links"}:
                current = _strip_bullet(line)
            else:
                current = re.sub(r"^[a-z]\)\s+", "", line, flags=re.I)
                if mode == "inquiry":
                    current = re.sub(r"^\d+[.)]\s+", "", current)
        else:
            if current:
                current += " " + line
            elif mode == "inquiry" and line:
                # Some inquiry questions are extracted without their numeric
                # prefix on a continuation line.
                current = line

    if current:
        items.append(current.strip())

    return [x for x in items if x]


def _split_unit_header(text: str) -> tuple[str, str, int | None]:
    """
    Split e.g.
        1.1.1 Polite Language (2 Lessons)
    """
    text = re.sub(r"\s+", " ", text).strip()
    match = SUB_STRAND_RE.match(text)
    if not match:
        raise ValueError(f"Invalid sub-strand header: {text}")

    code = ".".join(match.group(i) for i in (1, 2, 3))
    remainder = match.group(4).strip()
    lesson_match = LESSON_RE.search(remainder)
    lessons = int(lesson_match.group(1)) if lesson_match else None
    title = LESSON_RE.sub("", remainder).strip(" -")
    return code, title, lessons


def _collect_header(lines: list[str], index: int) -> tuple[str, str, int | None, int]:
    """
    Collect a possibly wrapped sub-strand heading.

    Example in the PDF:
        1.2.1 Independent
        Reading - Grade
        Appropriate Text
        (2 Lessons)
    """
    first = _clean_line(lines[index])
    code_match = SUB_STRAND_RE.match(first)
    code_only = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)\s*$", first)
    if not code_match and not code_only:
        raise ValueError(first)

    collected = [first]
    j = index + 1

    while j < len(lines):
        line = _clean_line(lines[j])
        if not line:
            j += 1
            continue

        if _is_section_heading(line):
            break
        if SUB_STRAND_RE.match(line) or THEME_RE.match(line):
            break
        if STRAND_RE.match(line):
            break

        collected.append(line)
        if LESSON_RE.search(line):
            j += 1
            break

        # Stop if we have reached the first prose heading.
        if line.lower().startswith("by the end of the sub strand"):
            break

        j += 1

    header = " ".join(collected)
    code, title, lessons = _split_unit_header(header)
    return code, title, lessons, j


def _find_theme_for_page(page_number: int, themes: list[CurriculumTheme]) -> CurriculumTheme | None:
    for theme in themes:
        if theme.start_pdf_page <= page_number <= (theme.end_pdf_page or page_number):
            return theme
    return None



def _extract_metadata(pages: list[dict]) -> tuple[str | None, str | None, str | None]:
    first_text = "\n".join(page["text"] for page in pages[:9])
    title = "Junior School Curriculum Design"

    # Prefer explicit subject headings over incidental mentions.
    subject_patterns = [
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+ENGLISH\b", "English"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+KISWAHILI\b", "Kiswahili"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+MATHEMATICS\b", "Mathematics"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+INTEGRATED SCIENCE\b", "Integrated Science"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+AGRICULTURE\b", "Agriculture"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+SOCIAL STUDIES\b", "Social Studies"),
        (r"\bGENERAL LEARNING OUTCOMES FOR\s+INDIGENOUS LANGUAGES\b", "Indigenous Languages"),
    ]

    learning_area = None
    for pattern, area in subject_patterns:
        if re.search(pattern, first_text, re.IGNORECASE):
            learning_area = area
            break

    # Fallback: inspect short, standalone title-page lines only.
    if learning_area is None:
        title_lines = [
            re.sub(r"\s+", " ", line).strip().upper()
            for page in pages[:3]
            for line in page["text"].splitlines()
        ]
        title_aliases = {
            "ENGLISH": "English",
            "KISWAHILI": "Kiswahili",
            "MATHEMATICS": "Mathematics",
            "INTEGRATED SCIENCE": "Integrated Science",
            "SCIENCE": "Integrated Science",
            "AGRICULTURE": "Agriculture",
            "SOCIAL STUDIES": "Social Studies",
        }
        for line in title_lines:
            if line in title_aliases:
                learning_area = title_aliases[line]
                break

    grade_match = re.search(r"\bGrade\s+(\d+)\b", first_text, re.IGNORECASE)
    grade = f"Grade {grade_match.group(1)}" if grade_match else None

    return title, grade, learning_area


def _extract_general_outcomes(pages: list[dict]) -> list[str]:
    text = "\n".join(page["text"] for page in pages[:9])
    marker = re.search(
        r"GENERAL LEARNING OUTCOMES FOR ENGLISH(.*?)(?:SUMMARY OF STRANDS AND SUBSTRANDS)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not marker:
        return []

    lines = [x.strip() for x in marker.group(1).splitlines() if x.strip()]
    return _parse_list_section(lines, "outcomes")


def _extract_strands_summary(pages: list[dict]) -> dict[str, list[str]]:
    text = "\n".join(page["text"] for page in pages[:9])
    marker = re.search(
        r"SUMMARY OF STRANDS AND SUBSTRANDS(.*?)(?:THEME\s+1\.0\s*:)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not marker:
        return {}

    lines = [_clean_line(x) for x in marker.group(1).splitlines() if _clean_line(x)]
    result: dict[str, list[str]] = {}
    current_strand: str | None = None

    # The real document uses a two-column table. PyMuPDF text order makes
    # each strand heading followed by its sub-strand descriptions.
    known_strands = {"Listening", "Speaking", "Reading", "Grammar", "Writing"}
    for line in lines:
        if line in known_strands:
            current_strand = line
            result.setdefault(current_strand, [])
            continue
        if current_strand and line.lower() not in {"strand", "sub strand"}:
            result[current_strand].append(line)

    return result


def _parse_theme_units(
    theme: CurriculumTheme,
    pages: list[dict],
) -> list[CurriculumUnit]:
    theme_pages = [
        page for page in pages
        if theme.start_pdf_page <= page["pdf_page"] <= (theme.end_pdf_page or page["pdf_page"])
    ]

    units: list[CurriculumUnit] = []
    current_strand_code: str | None = None
    current_strand_name: str | None = None

    current_unit: CurriculumUnit | None = None
    section: str | None = None

    for page in theme_pages:
        raw_lines = page["text"].splitlines()
        lines = _normalise_heading_fragments(raw_lines)
        printed_page = _parse_printed_page(raw_lines)

        i = 0
        while i < len(lines):
            line = lines[i]

            theme_match = THEME_RE.match(line)
            if theme_match and theme_match.group(1) != theme.code:
                i += 1
                continue

            # A strand may be extracted as several lines by PyMuPDF:
            #   1.1
            #   Listening
            #   and
            #   Speaking
            # or as one line:
            #   1.1 Listening and Speaking
            strand_match = STRAND_RE.match(line)
            if strand_match and not SUB_STRAND_RE.match(line):
                current_strand_code = f"{strand_match.group(1)}.{strand_match.group(2)}"
                current_strand_name = strand_match.group(3).strip()
                section = None
                i += 1
                continue

            strand_code_only = re.match(r"^\s*(\d+)\.(\d+)\s*$", line)
            if strand_code_only:
                current_strand_code = f"{strand_code_only.group(1)}.{strand_code_only.group(2)}"
                name_parts: list[str] = []
                j = i + 1
                while j < len(lines):
                    candidate = _clean_line(lines[j])
                    if not candidate:
                        j += 1
                        continue
                    if SUB_STRAND_RE.match(candidate) or THEME_RE.match(candidate):
                        break
                    if re.match(r"^\s*\d+\.\d+\s*$", candidate):
                        break
                    if _is_section_heading(candidate) or _looks_like_table_header(candidate):
                        break
                    # The table header can be split across lines. Stop rather
                    # than swallowing it into the strand name.
                    if candidate.lower() in {"listening", "speaking", "reading", "grammar", "writing"}:
                        name_parts.append(candidate)
                        j += 1
                        # Continue collecting because "Listening and Speaking"
                        # is itself wrapped in the real PDF.
                        continue
                    name_parts.append(candidate)
                    j += 1
                    if j < len(lines) and SUB_STRAND_RE.match(_clean_line(lines[j])):
                        break
                    if len(name_parts) >= 4:
                        break

                current_strand_name = " ".join(name_parts).strip()
                # The real PDF has "Listening / and / Speaking" on separate
                # lines; normalise that into the actual strand name.
                current_strand_name = re.sub(r"\s+", " ", current_strand_name)
                section = None
                i = j
                continue

            if SUB_STRAND_RE.match(line) or re.match(r"^\s*\d+\.\d+\.\d+\s*$", line):
                if current_unit:
                    units.append(current_unit)

                sub_code, sub_title, lessons, next_i = _collect_header(lines, i)

                if current_strand_code is None or current_strand_name is None:
                    # Recover strand code/name from the sub-strand prefix.
                    parts = sub_code.split(".")
                    current_strand_code = ".".join(parts[:2])
                    current_strand_name = ""

                current_unit = CurriculumUnit(
                    theme_code=theme.code,
                    theme_title=theme.title,
                    strand_code=current_strand_code,
                    strand=current_strand_name,
                    sub_strand_code=sub_code,
                    sub_strand=sub_title,
                    lessons=lessons,
                    source_pdf_pages=[page["pdf_page"]],
                    source_printed_pages=[printed_page] if printed_page else [],
                )
                section = None
                i = next_i
                continue

            if current_unit is None:
                i += 1
                continue

            # Keep provenance as the unit crosses page boundaries.
            if page["pdf_page"] not in current_unit.source_pdf_pages:
                current_unit.source_pdf_pages.append(page["pdf_page"])
            if printed_page and printed_page not in current_unit.source_printed_pages:
                current_unit.source_printed_pages.append(printed_page)

            section_name = _is_section_heading(line)
            if section_name:
                section = section_name
                i += 1
                continue

            if section == "outcomes" and line.lower().startswith("by the end of the sub strand"):
                i += 1
                continue
            if section == "experiences" and line.lower().startswith("the learner is guided to"):
                i += 1
                continue

            # The first section can be inferred from its prose marker even if
            # the marker was separated from the heading by PDF line wrapping.
            if line.lower().startswith("by the end of the sub strand"):
                section = "outcomes"
                i += 1
                continue
            if line.lower().startswith("the learner is guided to"):
                section = "experiences"
                i += 1
                continue

            # In the real PDF the "Key Inquiry Question(s)" table heading
            # can be extracted separately from the numbered questions. When
            # those numbered questions arrive after the experience list, use
            # them as the section boundary.
            if section == "experiences" and _is_number_item(line):
                section = "inquiry"

            if section == "outcomes":
                target = current_unit.specific_learning_outcomes
            elif section == "experiences":
                target = current_unit.suggested_learning_experiences
            elif section == "inquiry":
                target = current_unit.key_inquiry_questions
            elif section == "competencies":
                target = current_unit.core_competencies
            elif section == "pcis":
                target = current_unit.pertinent_and_contemporary_issues
            elif section == "values":
                target = current_unit.values
            elif section == "links":
                target = current_unit.links_to_other_subjects
            else:
                i += 1
                continue

            # Accumulate using the same parser rules, but one line at a time.
            if section == "outcomes" and _is_letter_item(line):
                target.append(re.sub(r"^[a-z]\)\s+", "", line, flags=re.I))
            elif section == "inquiry" and _is_number_item(line):
                target.append(re.sub(r"^\d+[.)]\s+", "", line))
            elif section in {"experiences", "competencies", "pcis", "values", "links"} and _is_bullet(line):
                target.append(_strip_bullet(line))
            elif target:
                # PDF wraps frequently split one item over several lines.
                target[-1] = f"{target[-1]} {line}".strip()

            i += 1

    if current_unit:
        units.append(current_unit)

    return units


def _deduplicate(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def clean_document(document: CurriculumDocument) -> CurriculumDocument:
    for theme in document.themes:
        for unit in theme.units:
            unit.specific_learning_outcomes = _deduplicate(unit.specific_learning_outcomes)
            unit.suggested_learning_experiences = _deduplicate(unit.suggested_learning_experiences)
            unit.key_inquiry_questions = _deduplicate(unit.key_inquiry_questions)
            unit.core_competencies = _deduplicate(unit.core_competencies)
            unit.pertinent_and_contemporary_issues = _deduplicate(
                unit.pertinent_and_contemporary_issues
            )
            unit.values = _deduplicate(unit.values)
            unit.links_to_other_subjects = _deduplicate(unit.links_to_other_subjects)
    return document


def parse_curriculum_pdf(path: str | Path) -> CurriculumDocument:
    path = Path(path)
    pages = extract_pdf_pages(path)

    themes = detect_theme_pages(pages)
    title, grade, learning_area = _extract_metadata(pages)

    document = CurriculumDocument(
        source_file=path.name,
        page_count=len(pages),
        title=title,
        grade=grade,
        learning_area=learning_area,
        general_learning_outcomes=_extract_general_outcomes(pages),
        strands_summary=_extract_strands_summary(pages),
        themes=themes,
        extraction_start_page=themes[0].start_pdf_page if themes else None,
        extraction_end_page=themes[-1].end_pdf_page if themes else None,
    )

    if not themes:
        document.warnings.append(
            "No THEME <number>.0 heading was detected. Detailed curriculum extraction was not started."
        )
        return document

    for theme in document.themes:
        theme.units = _parse_theme_units(theme, pages)

    # Validate against the structure actually expected by the lesson builder.
    for theme in document.themes:
        if not theme.units:
            document.warnings.append(
                f"Theme {theme.code} {theme.title} contains no parsed sub-strand units "
                f"(PDF page {theme.start_pdf_page})."
            )

    return clean_document(document)
