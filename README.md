# CBE Lesson Builder V1

A local-first Kenyan CBE curriculum document processor and lesson-plan builder.

## V1 pipeline

1. Upload a curriculum-design PDF.
2. Extract text with PyMuPDF.
3. Parse common CBE headings into structured curriculum JSON.
4. Review/edit the extracted curriculum.
5. Generate a lesson plan from the structured curriculum.
6. Edit the lesson plan in the browser.
7. Print/save the lesson plan as PDF from the browser.

## Important

This V1 deliberately keeps curriculum extraction deterministic and transparent. It does not claim that every PDF layout will parse perfectly. Always verify extracted curriculum data against the source PDF before using a generated lesson plan.

## Requirements

- Windows 10/11
- Python 3.11+ (Python 3.13 is expected to work)
- VS Code

## Setup in Windows CMD

```cmd
cd C:\Users\Loitah\Documents\01_IDEAS_LAB
python -m venv .venv
.venv\Scripts\activate
cd CBE_LESSON_BUILDER_V1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you already have a compatible project virtual environment, activate it and install the requirements there.

## Run

```cmd
python -m uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000

## First test

Use a text-based (not scanned-image-only) Kenyan CBE curriculum-design PDF.

Upload it, process it, inspect the extracted fields, then generate a lesson.

## Project stages included

BUILD 01 PDF ingestion
BUILD 02 curriculum parser
BUILD 03 curriculum explorer
BUILD 04 lesson generator
BUILD 05 teacher editor
BUILD 06 print/export

## Future upgrades

- OCR for scanned PDFs
- Better curriculum-table extraction
- SQLite/PostgreSQL persistence
- DOCX generation
- AI provider adapter
- authentication and teacher accounts
- curriculum source/page citations
- richer CBE-specific validation
