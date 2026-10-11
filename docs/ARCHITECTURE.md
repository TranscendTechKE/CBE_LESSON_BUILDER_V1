# Architecture — CBE Lesson Builder V1

## Current workflow

Browser dashboard
-> POST /api/curriculum/upload
-> curriculum_parser.parse_curriculum_pdf()
-> CurriculumDocument / CurriculumTheme / CurriculumUnit
-> In-memory document registry
-> Theme > Strand > Sub-strand selectors
-> POST /api/curriculum/lesson-plan
-> Lesson generator
-> Lesson plan displayed in browser

## BUILD 10 profile workflow

The flexible curriculum profile API and adapter exist, but are not yet connected to the PDF upload and explorer workflow.

## Target workflow

PDF upload
-> curriculum extraction with source-page evidence
-> hierarchy-aware curriculum representation
-> selectors based on extracted structure
-> explicit selected-node identity
-> adapter to the existing lesson generator
-> generated plan with source evidence

## Design constraints

- Preserve the working Grade 9 English workflow.
- Prefer deterministic extraction and visible warnings over guessed content.
- Reuse existing profile structures where suitable.
- Do not claim a curriculum is verified simply because its PDF was parsed.
- Defer authentication and persistent administrative approval.
- Test each integration step before proceeding.
