"""
CBE Lesson Builder V1
BUILD 07 - Curriculum-aware data models.

These models mirror the structure found in the real Grade 9 English
KICD curriculum design PDF rather than assuming a flat curriculum record.
"""

from pydantic import BaseModel, Field


class CurriculumPage(BaseModel):
    pdf_page: int
    printed_page: int | None = None
    text: str = ""


class CurriculumUnit(BaseModel):
    theme_code: str
    theme_title: str
    strand_code: str
    strand: str
    sub_strand_code: str
    sub_strand: str
    lessons: int | None = None
    specific_learning_outcomes: list[str] = Field(default_factory=list)
    suggested_learning_experiences: list[str] = Field(default_factory=list)
    key_inquiry_questions: list[str] = Field(default_factory=list)
    core_competencies: list[str] = Field(default_factory=list)
    pertinent_and_contemporary_issues: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    links_to_other_subjects: list[str] = Field(default_factory=list)
    source_pdf_pages: list[int] = Field(default_factory=list)
    source_printed_pages: list[int] = Field(default_factory=list)


class CurriculumTheme(BaseModel):
    code: str
    title: str
    start_pdf_page: int
    end_pdf_page: int | None = None
    units: list[CurriculumUnit] = Field(default_factory=list)


class CurriculumDocument(BaseModel):
    source_file: str
    page_count: int
    title: str | None = None
    grade: str | None = None
    learning_area: str | None = None
    general_learning_outcomes: list[str] = Field(default_factory=list)
    strands_summary: dict[str, list[str]] = Field(default_factory=dict)
    themes: list[CurriculumTheme] = Field(default_factory=list)
    extraction_start_page: int | None = None
    extraction_end_page: int | None = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def unit_count(self) -> int:
        return sum(len(theme.units) for theme in self.themes)
