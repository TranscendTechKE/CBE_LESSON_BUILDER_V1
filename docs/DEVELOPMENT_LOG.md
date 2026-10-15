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

Documentation and institutional handover checkpoint

Date: 2026-10-15

Purpose: bring project documentation into line with the implementation
history before connecting the local repository to the TranscendTech
institutional GitHub repository.

Repository evidence reviewed

The local repository history includes these checkpoints:

9ee3049 — BUILD 10: add flexible curriculum profile API.

c2290eb — BUILD 11D: integrate profile-driven curriculum navigation.

a055a47 — BUILD 11E: add flexible curriculum text extraction.

3e444bb — checkpoint: flexible curriculum support.

b21fc7f — checkpoint with Word export and branding.

989c981 — prepare CBE lesson builder for Render deployment.

The current branch is master, at 989c981 when this checkpoint
was prepared. Existing tags include BUILD-08-working and
BUILD-09-english-working.

Documentation changes

Replaced the outdated BUILD 01–06 overview in README.md with a
project description reflecting the later curriculum-profile work,
Word export, tests and deployment configuration.

Updated docs/ARCHITECTURE.md to describe the original curriculum
workflow alongside flexible profiles, document adapters, extraction,
lesson generation, export and deployment considerations.

Preserved the existing BUILD 10 and BUILD 11A history in this log.

Important limitations retained

Flexible hierarchy support does not prove accurate extraction for
every learning area or curriculum PDF.

The original workflow uses an in-memory document registry.

Persistent storage, user authentication and production operational
readiness require separate verification.

Render configuration alone does not establish successful or
production-ready deployment.

Verification status

This checkpoint records documentation changes and the repository
history inspected while preparing the handover. It does not claim that
the full automated test suite was rerun as part of this documentation
edit.

Repository state and handover precautions

At the time of inspection, the working tree also showed deleted
BUILD_09_CHANGE_MAP.md and READMEbuild9.md, plus untracked
app/static/css/curriculum-explorer.css.bak, diagnostics/ and
scripts/ content.

These files require a deliberate inclusion, restoration or exclusion
decision. They must not be silently discarded or automatically
included in the institutional handover.

No Git remote was configured at the time of inspection. The destination
institutional repository must be confirmed before adding a remote or
pushing commits.

Next steps

Review the documentation diff for factual accuracy.

Inspect the deleted BUILD 09 notes and untracked diagnostic files.

Review .gitignore, generated files and secret handling.

Run or confirm the intended verification checks and record actual
results.

Commit the approved documentation changes separately.

Confirm the institutional GitHub repository and its existing
history before connecting or pushing.




## Documentation and Institutional Handover Checkpoint

**Date:** 15 October 2026

### Goal

Bring the project documentation up to date before preparing the repository for inclusion in the TranscendTech institutional GitHub repository.

### Scope

- Update the README to reflect the current application direction and development history.
- Update the architecture document to describe the major components and data flow.
- Preserve the existing BUILD history.
- Document limitations and repository handover precautions.
- Keep this checkpoint separate from application-code changes.

### Architecture and Design Decisions

The application retains the established Grade 9 English workflow while introducing flexible curriculum profiles, document adapters, and curriculum text extraction components.

The application uses FastAPI, Python data models, PyMuPDF, browser-based curriculum exploration, lesson-plan generation, and Word export.

The exact active route and service should be verified before assuming a capability is used throughout the application.

### Important Limitations

- Extraction accuracy has not been established for every KICD learning area or PDF layout.
- Complex tables, unusual headings, and multi-line cells may require additional handling.
- The original curriculum workflow uses an in-memory document registry.
- In-memory state is not durable storage and may be lost after a process restart.
- Profile API support does not automatically establish persistent profile storage.
- Authentication, user accounts, and access controls require separate verification.
- A deployment configuration file does not establish production readiness.

### Verification Status

This checkpoint records documentation work, not a new automated test run.

The full test suite must not be described as passing unless it has actually been executed against the relevant working tree. Record the commands and actual results when testing is performed.

### Repository State and Handover Precautions

Earlier Git inspection identified:

- Deleted `BUILD_09_CHANGE_MAP.md`.
- Deleted `READMEbuild9.md`.
- Untracked `app/static/css/curriculum-explorer.css.bak`.
- Untracked content under `diagnostics/`.
- Untracked content under `scripts/`.

Inspect these items before deciding whether to restore, retain, ignore, or commit them. Do not discard or stage them automatically.

No Git remote was configured during the earlier inspection. Confirm the destination institutional repository and review its existing history before connecting or pushing.

### Next Steps

1. Review the formatting and factual accuracy of all three documentation files.
2. Inspect the deleted BUILD 09 notes and untracked files.
3. Review `.gitignore`, environment files, backups, generated data, and secret handling.
4. Run relevant tests and record actual results.
5. Review the full diff and run `git diff --check`.
6. Stage only approved documentation files.
7. Commit the documentation checkpoint separately.
8. Confirm the institutional GitHub destination and its existing history.
9. Agree on the integration strategy before pushing.
