"""
BUILD 07A - Section detection.

Kept separate from curriculum_parser.py so the application can later support
other KICD designs without hard-coding Grade 9 English page numbers.
"""

import re


THEME_RE = re.compile(
    r"^\s*THEME\s+(\d+(?:\.\d+)?)\s*[:.]?\s*(.+?)\s*$",
    re.IGNORECASE,
)


def detect_first_theme_page(pages: list[dict]) -> int | None:
    for page in pages:
        for line in page.get("text", "").splitlines():
            if THEME_RE.match(line.strip()):
                return page["pdf_page"]
    return None


def detect_theme_boundaries(pages: list[dict]) -> list[dict]:
    themes = []

    for page in pages:
        for line in page.get("text", "").splitlines():
            match = THEME_RE.match(line.strip())
            if match:
                themes.append(
                    {
                        "code": match.group(1),
                        "title": match.group(2).strip(),
                        "start_pdf_page": page["pdf_page"],
                    }
                )
                break

    for index, theme in enumerate(themes):
        theme["end_pdf_page"] = (
            themes[index + 1]["start_pdf_page"] - 1
            if index + 1 < len(themes)
            else pages[-1]["pdf_page"] if pages else None
        )

    return themes
