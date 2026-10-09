# BUILD 09 — Standardized CBE Lesson Plan Structure

## Target

`Verified KICD curriculum → CBE lesson-plan structure → timed Organisation of Learning → assessment → assessment approaches → reflection → extended activities → teacher self-evaluation`

BUILD 09 modifies the **lesson-plan generation/output layer** from BUILD 08. The existing three-step workflow remains unchanged:

1. Load Curriculum Design
2. Select Curriculum Unit
3. Lesson Plan Details

The selected unit remains the source of the curriculum-aligned fields.

## Source-grounded structure

The supplied Grade 9 English lesson-plan reference repeatedly uses:

- Strand
- Sub Strand
- Specific Learning Outcomes
- Key Inquiry Question(s)
- Learning Resources
- Organisation of Learning
  - Introduction
  - Lesson Development
  - Step 1, Step 2, Step 3, Step 4 where used
  - Conclusion
- Extended Activities
- Teacher Self-Evaluation

The reference also demonstrates that lesson-development step timings can vary. BUILD 09 therefore stores each step as data rather than hard-coding four equal blocks.

## BUILD 09 additions/changes

- Structured `LessonPlan` data model.
- Timed Introduction, Lesson Development and Conclusion.
- Data-driven development steps with individual durations.
- Learning Resources as a first-class section.
- Assessment and Assessment Approaches retained.
- Reflection retained as teacher prompts.
- Extended Activities generated as concrete follow-up tasks.
- Teacher Self-Evaluation remains blank for teacher completion; the system does not fabricate teacher reflection.
- Curriculum traceability through source pages/document where available.
- Compatibility helpers accept common BUILD 07/08 field names.

## Timing

For the common 40-minute lesson, the generator produces:

- Introduction: 5 minutes
- Lesson Development: 30 minutes
- Conclusion: 5 minutes

For another duration, the generator proportionally adjusts the three sections and distributes development time across four steps. This preserves the reference document's structure while avoiding a fixed 40-minute assumption.

## Deliberately unchanged

BUILD 09 does **not** introduce:

- DOCX generation
- AI provider calls
- authentication/teacher accounts
- payment integration
- database persistence

Those are subsequent integration layers. The standardized lesson-plan core should be stable before adding them.
