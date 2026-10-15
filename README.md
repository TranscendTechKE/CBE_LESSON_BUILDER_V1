
# CBE Lesson Builder V1

A local-first Kenyan Competency-Based Education (CBE) curriculum document processor and lesson-planning application.

The project is being developed to help teachers inspect curriculum-design PDFs, explore extracted curriculum structures, prepare lesson plans, and export teaching documents. The design prioritises transparent extraction, source verification, and teacher review rather than unverified automation.

## Project Status

The repository contains an established Grade 9 English lesson-planning workflow and subsequent development toward flexible curriculum support.

Development milestones include:

- **BUILD 08–09:** API and lesson-plan generation checkpoints.
- **BUILD 10:** Flexible curriculum profiles, adapters, and profile API.
- **BUILD 11C–11E:** Document adapters, profile-driven navigation, flexible curriculum text extraction, and related routes.
- **Later checkpoints:** Lesson-plan Word export, interface branding, and Render deployment configuration.

These milestones describe development history. They do not mean that every curriculum PDF, learning area, or extraction pathway has been fully validated.

## Current Capabilities

The repository includes implementation for:

- Uploading and processing curriculum-design PDFs.
- Extracting PDF text using PyMuPDF.
- Representing curriculum information using structured models.
- Exploring curriculum structures through a browser interface.
- Supporting flexible curriculum profiles and document adapters.
- Generating lesson plans from selected curriculum information.
- Exporting lesson plans to Microsoft Word documents.
- Serving the application through FastAPI.
- Providing a health endpoint at `/health`.
- Preparing deployment configuration through `render.yaml`.

The quality of extracted information depends on the source document, its layout, and the extraction pathway used. Review the relevant implementation and tests before relying on a particular workflow.

## Technology Stack

- Python
- FastAPI and Uvicorn
- Pydantic and pydantic-settings
- PyMuPDF
- Jinja2
- HTML, CSS, and JavaScript
- python-docx
- pytest

## Requirements

- Windows 10/11 or another compatible Python environment
- Python compatible with the installed dependencies
- Git
- VS Code or another code editor

## Local Setup — Windows

Open a terminal in the project directory.

Create a virtual environment if one does not already exist:

```cmd
python -m venv .venv
```

Activate it:

```cmd
.venv\Scripts\activate
```

Install the dependencies:

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the project virtual environment already exists, activate it rather than creating another one.

## Run the Application

With the virtual environment activated, run:

```bash
python -m uvicorn app.main:app --reload
```

Open the application:

`http://127.0.0.1:8000`

Health endpoint:

`http://127.0.0.1:8000/health`

## Run Automated Tests

Run the full test suite from the project root:

```bash
python -m pytest -q
```

Run individual test modules when investigating a specific component:

```bash
python -m pytest tests/test_build09_lesson_plan.py -q
python -m pytest tests/test_build10a_curriculum_profile.py -q
python -m pytest tests/test_build11e_flexible_extraction.py -q
python -m pytest tests/test_lesson_plan_exporter.py -q
```

Record actual test results in the development log. A previous passing test result is not proof that subsequent changes pass.

## Curriculum Verification

Before using extracted curriculum information for teaching:

1. Compare the extracted information with the original KICD curriculum-design document.
2. Confirm that headings and hierarchy levels were identified correctly.
3. Review the selected theme, strand, sub-strand, or equivalent curriculum node.
4. Check learning outcomes and other extracted information.
5. Review the generated lesson plan against the source.
6. Treat ambiguous layouts or unsupported structures as requiring manual review.

Flexible hierarchy support does not establish accurate extraction for every KICD learning area.

## Project Documentation

- `docs/ARCHITECTURE.md` — application components, data flow, design constraints, and deployment considerations.
- `docs/DEVELOPMENT_LOG.md` — development checkpoints, decisions, verification records, limitations, and next steps.
- `tests/` — automated tests and test fixtures, including the Grade 9 English curriculum PDF.
- `scripts/` — supporting scripts, where retained.
- `diagnostics/` — curriculum investigation outputs, where retained.

## Known Limitations and Further Work

The following areas require continued validation or development:

- Extraction accuracy across different curriculum PDFs and learning areas.
- Handling of complex tables, multi-line cells, and unusual page layouts.
- Validation against additional real curriculum-design documents.
- Source-page evidence and traceability throughout the workflow.
- Persistent storage for uploaded documents, extracted data, and generated plans.
- Authentication, user accounts, and access control.
- Production deployment verification and operational monitoring.
- OCR support for scanned-image-only PDFs, where needed.

Do not assume a capability is complete merely because a related module, configuration file, or roadmap entry exists.

## Deployment

A `render.yaml` file is present for Render deployment configuration.

Deployment configuration alone does not establish production readiness. Before using a hosted instance with real users, verify data persistence, file storage, configuration secrets, access controls, logging, and behaviour after restarts and redeployments.

## Institutional Repository Handover

The project is being prepared for inclusion in the TranscendTech institutional GitHub repository.

Before publishing:

- Review the Git working tree and the exact files intended for publication.
- Inspect environment files and ensure that secrets are not committed.
- Review test results and update the development log.
- Decide whether diagnostic scripts, fixtures, backups, and generated files belong in the repository.
- Confirm the destination repository and inspect its existing history.
- Agree on the integration strategy before pushing.

Do not force-push or overwrite an existing institutional repository without reviewing its contents and agreeing on the integration strategy.

## Development Principle

Preserve working functionality, make changes incrementally, verify behaviour with relevant tests, and document each checkpoint before proceeding to the next major change.
