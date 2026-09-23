"""
BUILD 07A - PDF page extraction.

The extractor intentionally works page-by-page.  BUILD 07 needs page
boundaries because KICD curriculum units often continue onto the next
PDF page while retaining the same sub-strand.
"""

from pathlib import Path
import re
import pymupdf


_SOFT_HYPHEN_ARTIFACTS = (
    "\u00ad",   # soft hyphen
    "\ufffe",   # observed PDF extraction artifact
)


def normalize_pdf_text(text: str) -> str:
    """Normalise extraction artefacts without rewriting curriculum content."""
    for artifact in _SOFT_HYPHEN_ARTIFACTS:
        text = text.replace(artifact, "-")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Join words split only by a PDF line-break hyphen:
    # "embarrassi-\nng" -> "embarrassing".
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    # Preserve line structure, but collapse horizontal whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_pdf_pages(path: str | Path) -> list[dict]:
    path = Path(path)
    document = pymupdf.open(path)
    pages: list[dict] = []

    try:
        for pdf_page, page in enumerate(document, start=1):
            text = normalize_pdf_text(page.get_text("text"))
            pages.append(
                {
                    "pdf_page": pdf_page,
                    "text": text,
                }
            )
    finally:
        document.close()

    return pages


def extract_pdf(path: str | Path) -> dict:
    """Backward-compatible wrapper used by the existing BUILD 01 upload flow."""
    path = Path(path)
    pages = extract_pdf_pages(path)

    return {
        "source_file": path.name,
        "page_count": len(pages),
        "pages": pages,
        "text": "\n\n".join(page["text"] for page in pages),
    }
