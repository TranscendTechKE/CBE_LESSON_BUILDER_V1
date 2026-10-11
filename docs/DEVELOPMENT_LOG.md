# CBE Lesson Builder — Development Log

## BUILD 10 — Flexible Curriculum Profiles

Status: committed and regression-tested.

- Added flexible curriculum profile models.
- Added a profile adapter to map selected profile nodes into the existing lesson generator's input structure.
- Added profile API endpoints and tests.
- Profile registration and approval remain in-memory; this is not production-ready persistence or authentication.

## BUILD 11A — Existing Workflow Inspection

Status: inspection complete; no application code changed.

### Confirmed live workflow

1. `POST /api/curriculum/upload` receives a PDF.
2. `app/services/curriculum_parser.py` extracts the document into `CurriculumDocument`.
3. `app/routes/curriculum.py` stores parsed documents in the in-memory `DOCUMENTS` dictionary.
4. The browser loads themes, filters strands, and selects sub-strands.
5. `POST /api/curriculum/lesson-plan` passes the selected `CurriculumUnit` to `generate_lesson_plan()`.

### Confirmed limitations

- `app/models/curriculum.py` requires theme, strand, and sub-strand fields.
- `app/services/curriculum_parser.py` was designed around Grade 9 English.
- `app/services/curriculum_detector.py` detects theme headings only.
- `app/static/js/curriculum-explorer.js` hard-codes the three selector levels.
- `app/templates/dashboard.html` hard-codes their labels.
- BUILD 10's flexible profile API is not yet connected to the PDF upload/explorer workflow.

### Regression baseline

`tests/test_curriculum_real_pdf.py` checks the real Grade 9 English PDF when the fixture is available. Preserve the existing English parsing and lesson-generation behaviour while introducing flexible hierarchy support.

The BUILD 10 suite previously passed: 21 tests passed. This records the last known result; it does not assert that tests have been rerun during BUILD 11A.

## BUILD 11 — Objective and acceptance criteria

Objective: connect curriculum PDF upload, structural selection, source evidence, and lesson generation through a hierarchy-aware workflow.

Acceptance criteria:

1. The explorer does not require every learning area to use Theme > Strand > Sub-strand.
2. Selector labels and levels reflect the extracted curriculum structure.
3. The selected node retains its identity and source-page provenance.
4. The selected node reaches the lesson generator through an explicit adapter.
5. Existing Grade 9 English regression tests remain passing.
6. Unsupported or ambiguous PDF structures are reported honestly rather than presented as verified data.
7. Each checkpoint records changed files, commands, test results, limitations, and the next step.

### Implementation boundary

Do not rewrite the proven English parser wholesale. Reuse BUILD 10's generic profile structures where appropriate, and integrate incrementally with the existing upload and lesson-planning workflow.

Generic hierarchy support does not by itself prove accurate extraction for every KICD learning area. Additional real-PDF fixtures and subject-specific validation will be needed.
