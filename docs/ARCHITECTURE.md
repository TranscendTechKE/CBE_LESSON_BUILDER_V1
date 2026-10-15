# Architecture — CBE Lesson Builder V1

## 1. Purpose

CBE Lesson Builder processes Kenyan curriculum-design PDFs and supports curriculum exploration and lesson-plan preparation.

The architecture combines an established Grade 9 English workflow with newer components intended to support different curriculum hierarchies. Extraction should remain transparent, and teacher review is essential.

This document describes the major components and design considerations. For implementation details, consult the source code and the development log.

## 2. Application Entry Point

The main application entry point is:

`app/main.py`

It creates the FastAPI application, configures static-file serving, registers the curriculum and curriculum-profile routers, and exposes a health endpoint.

The health endpoint is:

`GET /health`

Relevant components include:

- `app/config.py` — application configuration.
- `app/routes/curriculum.py` — original curriculum upload, extraction, navigation, and lesson-planning workflow.
- `app/routes/curriculum_profiles.py` — curriculum-profile API.
- `app/models/` — curriculum, profile, and lesson data models.
- `app/services/` — extraction, document adaptation, lesson generation, validation, and export.
- `app/templates/` — browser templates.
- `app/static/` — frontend JavaScript and CSS.

## 3. Curriculum Processing Workflow

The intended high-level workflow is:

1. A user uploads a curriculum-design PDF.
2. The application extracts available document text.
3. Curriculum extraction and document-adapter components transform supported information into structured representations.
4. The browser presents curriculum information for exploration.
5. The user selects curriculum content for lesson planning.
6. The selected information is passed through the relevant model, adapter, or generator.
7. The user reviews the generated lesson plan.
8. The user may export the plan as a Word document.

The exact path depends on the endpoint and extraction route used. Consult `app/routes/curriculum.py`, `app/routes/curriculum_profiles.py`, and their associated services before changing the workflow.

The intended architecture must preserve the working English workflow while allowing other curriculum structures to be introduced incrementally.

## 4. Core Curriculum Components

### 4.1 Original Curriculum Representation

The original curriculum workflow uses:

- `app/models/curriculum.py`
- `app/services/curriculum_parser.py`
- `app/services/curriculum_detector.py`

The original Grade 9 English workflow was designed around a hierarchy of:

**Theme → Strand → Sub-strand**

This hierarchy should not be assumed to apply to every learning area. Different curriculum documents may use different headings, levels, and organisational structures.

### 4.2 Flexible Curriculum Profiles

Flexible curriculum support includes:

- `app/models/curriculum_profile.py`
- `app/routes/curriculum_profiles.py`
- `app/services/curriculum_profile_adapter.py`

These components provide profile models, profile-related API operations, and an adapter for translating supported profile content into lesson-generator inputs.

The existence of profile models or endpoints does not, by itself, prove that every profile is persisted, that every hierarchy is supported, or that every learning area produces accurate lesson plans.

### 4.3 Document Adaptation and Flexible Extraction

Relevant components include:

- `app/services/curriculum_document_adapter.py`
- `app/services/flexible_curriculum_extractor.py`

These components support document adaptation and flexible curriculum text extraction.

Extraction quality depends on the source PDF and its layout. Unusual headings, complex tables, multi-line cells, and scanned pages may require additional processing or manual review.

The extracted representation should be checked against the original document before being used for lesson preparation.

## 5. Lesson-Plan Generation and Export

Relevant components include:

- `app/models/lesson.py`
- `app/services/lesson_generator.py`
- `app/services/lesson_plan_generator.py`
- `app/services/lesson_plan_exporter.py`
- `app/services/validator.py`

The project contains lesson-generation code and a Word-export service implemented with `python-docx`.

Before changing generation or export behaviour, inspect the active API route and its service calls. Multiple generator or adapter modules do not necessarily mean that every workflow uses all of them.

Generated lesson plans must be reviewed against the selected curriculum source before classroom use.

## 6. Frontend

The browser interface uses HTML templates, JavaScript, and CSS.

Relevant files include:

- `app/templates/base.html`
- `app/templates/dashboard.html`
- `app/static/js/curriculum-explorer.js`
- `app/static/css/curriculum-explorer.css`

The frontend supports curriculum exploration and interaction with the application's API.

Changes to hierarchy handling should preserve the existing English workflow and be tested against the relevant frontend and API behaviour.

## 7. State and Persistence

The original curriculum upload workflow uses an in-memory document registry in `app/routes/curriculum.py`.

In-memory state is not durable storage. It may be lost when the application process restarts, and it is not automatically shared across independent application instances.

Before describing profile registration, extracted documents, or generated plans as persistent, verify that the current implementation explicitly stores them in durable storage.

Before production use, evaluate storage for:

- Uploaded curriculum PDFs.
- Extracted curriculum data.
- Generated lesson plans.
- User and administrative records, if introduced.

## 8. Deployment

The repository includes `render.yaml` and deployment-related configuration.

These files support deployment preparation but do not independently prove that a production deployment has been fully validated.

Deployment review should cover:

- Environment variables and secret handling.
- Upload and generated-file storage.
- Persistence across process restarts and redeployments.
- Behaviour with multiple application instances.
- Health checks, logging, and error handling.
- Authentication and access controls if user accounts are introduced.

Deployment status should be recorded separately from application feature status.

## 9. Testing Strategy

The test suite includes modules covering the original API and lesson generator, curriculum profiles, document adapters, flexible extraction, routes, real-PDF behaviour, and lesson-plan export.

Important test files include:

- `tests/test_build08_api.py`
- `tests/test_build09_lesson_plan.py`
- `tests/test_build10a_curriculum_profile.py`
- `tests/test_build10b_curriculum_profile_adapter.py`
- `tests/test_build10d_curriculum_profiles_api.py`
- `tests/test_build11c_document_adapter.py`
- `tests/test_build11d_document_profile_endpoint.py`
- `tests/test_build11e_flexible_extraction.py`
- `tests/test_build11e_flexible_routes.py`
- `tests/test_build11e_text_extraction.py`
- `tests/test_curriculum_real_pdf.py`
- `tests/test_lesson_plan_exporter.py`

The Grade 9 English curriculum fixture is located under `tests/fixtures/`.

Run relevant tests after code changes and record the actual results in `docs/DEVELOPMENT_LOG.md`. Historical results must not be presented as the result of a later test run.

A passing automated test suite does not replace manual verification against representative curriculum PDFs.

## 10. Design Constraints

Development should follow these constraints:

1. Preserve the working Grade 9 English workflow.
2. Prefer transparent extraction and visible warnings to guessed data.
3. Use adapters to isolate differences between curriculum structures.
4. Validate extracted information against the source PDF.
5. Avoid claiming universal KICD curriculum compatibility without evidence from representative documents.
6. Keep changes incremental and regression-tested.
7. Separate implemented capabilities from planned work.
8. Do not treat deployment configuration as proof of production readiness.

## 11. Recommended Development Sequence

For each new development checkpoint:

1. Define the specific objective and acceptance criteria.
2. Inspect the current implementation before editing.
3. Make the smallest change that meets the objective.
4. Run relevant tests and record their actual results.
5. Compare extraction results against source curriculum documents where applicable.
6. Update the development log and relevant documentation.
7. Review the Git diff before committing.
8. Preserve a known-working checkpoint before beginning a larger chang

Architecture — CBE Lesson Builder V1

1. Purpose

CBE Lesson Builder processes Kenyan curriculum-design PDFs and supports
curriculum exploration and lesson-plan preparation.

The architecture combines an established Grade 9 English workflow
with newer components intended to support different curriculum
hierarchies. Extraction is deterministic where implemented, and
teacher review remains essential.

2. Application entry point

app/main.py creates the FastAPI application, configures static-file
serving, and registers the curriculum and curriculum-profile routers.

The application exposes /health for a basic health check.

Relevant components include:

app/config.py — application configuration.

app/routes/curriculum.py — curriculum upload, extraction,
navigation and lesson-planning endpoints.

app/routes/curriculum_profiles.py — curriculum-profile API.

app/models/ — curriculum, profile and lesson data models.

app/services/ — extraction, adapters, generation and export.

app/templates/ — browser templates.

app/static/ — frontend JavaScript and CSS.

3. Curriculum processing workflow

The principal workflow is intended to follow this sequence:

A user uploads a curriculum-design PDF.

The application extracts text from the document.

Curriculum extraction and document-adapter components transform
available information into structured representations.

The browser presents curriculum information for exploration.

The user selects curriculum content for lesson planning.

The selected information is passed through the relevant model or
adapter to lesson-plan generation.

The user reviews the generated plan and may export it.

The exact path depends on the endpoint and extraction route used.
Consult app/routes/curriculum.py and the associated services for the
current implementation details.

4. Core curriculum components

Original curriculum representation

app/models/curriculum.py

app/services/curriculum_parser.py

app/services/curriculum_detector.py

The original workflow was designed around Grade 9 English and a
Theme → Strand → Sub-strand hierarchy.

It remains important to preserve this workflow while improving
support for other curriculum structures.

Flexible curriculum profiles

app/models/curriculum_profile.py

app/routes/curriculum_profiles.py

app/services/curriculum_profile_adapter.py

These components provide profile models, profile-related API
operations and an adapter for translating selected profile content
into lesson-generator inputs.

Document adaptation and flexible extraction

app/services/curriculum_document_adapter.py

app/services/flexible_curriculum_extractor.py

These components support the newer hierarchy-aware workflow and
flexible curriculum text extraction.

Their existence does not establish that every learning area's
curriculum structure or PDF layout is handled accurately.

5. Lesson-plan generation and export

Relevant components include:

app/models/lesson.py

app/services/lesson_generator.py

app/services/lesson_plan_generator.py

app/services/lesson_plan_exporter.py

app/services/validator.py

The project contains lesson-generation code and a Word-export service
implemented with python-docx.

Review the current route and service implementations before assuming
that every generator, validation rule or export option is used by
every user workflow.

Generated lesson plans must be checked against the selected
curriculum source before classroom use.

6. Frontend

The browser interface uses HTML templates, JavaScript and CSS.

Relevant files include:

app/templates/base.html

app/templates/dashboard.html

app/static/js/curriculum-explorer.js

app/static/css/curriculum-explorer.css

The frontend supports curriculum exploration and interaction with the
application's API. Changes to curriculum hierarchy handling should
preserve the existing English workflow and be tested against the
relevant frontend and API behaviour.

7. State and persistence

The original curriculum upload workflow uses an in-memory document
registry in app/routes/curriculum.py. In-memory state is not durable
storage: it may be lost when the application process restarts, and it
is not shared automatically across independent application instances.

Profile registration or approval must not be described as persistent
unless the current implementation explicitly provides durable storage.

Before production use, evaluate storage for uploaded PDFs, extracted
curriculum data, generated lesson plans and user-related records.

8. Deployment

The repository includes render.yaml and deployment-related
configuration changes.

The configuration supports deployment preparation, but it does not
prove that a production deployment has been fully validated.

Deployment review should cover:

Environment-variable configuration and secret handling.

Upload and generated-file storage.

Persistence across process restarts and redeployments.

Behaviour when multiple application instances are used.

Health checks, logging and error handling.

Authentication and access controls if user accounts are introduced.

9. Testing strategy

The test suite includes modules covering the original API and lesson
generator, curriculum profiles, document adapters, flexible extraction,
routes, real-PDF behaviour and lesson-plan export.

Important test files include:

tests/test_build08_api.py

tests/test_build09_lesson_plan.py

tests/test_build10a_curriculum_profile.py

tests/test_build10b_curriculum_profile_adapter.py

tests/test_build10d_curriculum_profiles_api.py

tests/test_build11c_document_adapter.py

tests/test_build11d_document_profile_endpoint.py

tests/test_build11e_flexible_extraction.py

tests/test_build11e_flexible_routes.py

tests/test_build11e_text_extraction.py

tests/test_curriculum_real_pdf.py

tests/test_lesson_plan_exporter.py

The Grade 9 English fixture is located under tests/fixtures/.

Run the relevant tests after code changes and record actual results.
Historical test results must not be presented as the result of a later
test run.

10. Design constraints

Preserve the working Grade 9 English workflow.

Prefer transparent extraction and visible warnings to guessed data.

Use adapters to isolate differences between curriculum structures.

Validate extracted information against the source PDF.

Avoid claiming universal KICD curriculum compatibility without
evidence from representative documents.

Keep changes incremental and regression-tested.

Do not treat deployment configuration as proof of production
readiness.
