from fastapi.testclient import TestClient

from app.main import app
from app.models.curriculum import CurriculumDocument, CurriculumTheme, CurriculumUnit
from app.routes import curriculum as curriculum_routes


client = TestClient(app)


def test_uploaded_document_profile_endpoint(monkeypatch):
    document = CurriculumDocument(
        source_file="sample-english.pdf",
        title="Sample English Curriculum",
        page_count=10,
        grade="Grade 9",
        learning_area="English",
        warnings=["Some content may require manual review."],
        themes=[
            CurriculumTheme(
                code="1.0",
                title="Citizenship",
                start_pdf_page=3,
                end_pdf_page=5,
                units=[
                    CurriculumUnit(
                        theme_code="1.0",
                        theme_title="Citizenship",
                        strand_code="1.1",
                        strand="Listening and Speaking",
                        sub_strand_code="1.1.1",
                        sub_strand="Polite Language",
                        lessons=2,
                        specific_learning_outcomes=[
                            "Use polite language appropriately."
                        ],
                        source_pdf_pages=[4],
                    )
                ],
            )
        ],
    )

    monkeypatch.setitem(
        curriculum_routes.DOCUMENTS,
        "test-document",
        document,
    )

    response = client.get(
        "/api/curriculum/test-document/profile"
    )

    assert response.status_code == 200
    profile = response.json()

    assert profile["profile_id"] == "uploaded-test-document"
    assert profile["source_verified"] is False
    assert profile["learning_area"] == "English"
    assert profile["grade"] == "Grade 9"

    theme = profile["content_nodes"][0]
    strand = theme["children"][0]
    unit = strand["children"][0]

    assert theme["title"] == "Citizenship"
    assert strand["title"] == "Listening and Speaking"
    assert unit["title"] == "Polite Language"
    assert unit["source_pages"] == [4]
    assert any(
        "manual review" in note
        for note in profile["notes"]
    )


def test_unknown_document_profile_returns_404():
    response = client.get(
        "/api/curriculum/document-does-not-exist/profile"
    )

    assert response.status_code == 404
