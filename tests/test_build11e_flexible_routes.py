
from fastapi.testclient import TestClient

from app.main import app
from app.models.curriculum_profile import (
    CurriculumContentNode,
    CurriculumProfile,
)
from app.routes import curriculum as curriculum_routes


client = TestClient(app)


def make_science_profile():
    unit = CurriculumContentNode(
        code="1.1",
        title="Classification of Living Things",
        node_type="sub_strand",
        specific_learning_outcomes=[
            "Classify living things using observable characteristics."
        ],
        suggested_learning_experiences=[
            "Learners observe and group specimens by shared characteristics."
        ],
        key_inquiry_questions=[
            "How can living things be classified?"
        ],
        core_competencies=["Critical thinking and problem solving"],
        source_pages=[5],
    )

    strand = CurriculumContentNode(
        code="1.0",
        title="Living Things and Their Environment",
        node_type="strand",
        children=[unit],
        source_pages=[4, 5],
    )

    return CurriculumProfile(
        profile_id="test-science-grade-7",
        authority="KICD",
        source_verified=False,
        education_stage="Junior School",
        grade="Grade 7",
        learning_area="Science",
        hierarchy_labels=["Strand", "Sub-strand"],
        content_nodes=[strand],
    )


def test_flexible_profile_unit_endpoint_returns_real_content(monkeypatch):
    profile = make_science_profile()

    monkeypatch.setitem(
        curriculum_routes.PROFILES,
        "test-science-document",
        profile,
    )

    response = client.get(
        "/api/curriculum/test-science-document/unit/1.1"
    )

    assert response.status_code == 200
    unit = response.json()

    assert unit["code"] == "1.1"
    assert unit["sub_strand"] == "Classification of Living Things"
    assert unit["learning_area"] == "Science"
    assert unit["grade"] == "Grade 7"
    assert unit["specific_learning_outcomes"] == [
        "Classify living things using observable characteristics."
    ]
    assert unit["source_pages"] == [5]
    assert unit["source_verified"] is False


def test_flexible_profile_theme_endpoint_returns_root(monkeypatch):
    monkeypatch.setitem(
        curriculum_routes.PROFILES,
        "test-science-document",
        make_science_profile(),
    )

    response = client.get(
        "/api/curriculum/test-science-document/themes"
    )

    assert response.status_code == 200
    sections = response.json()

    assert len(sections) == 1
    assert sections[0]["code"] == "1.0"
    assert sections[0]["title"] == "Living Things and Their Environment"
    assert sections[0]["unit_count"] == 1


def test_flexible_profile_lesson_plan_uses_selected_unit(monkeypatch):
    monkeypatch.setitem(
        curriculum_routes.PROFILES,
        "test-science-document",
        make_science_profile(),
    )

    response = client.post(
        "/api/curriculum/lesson-plan",
        json={
            "document_id": "test-science-document",
            "sub_strand_code": "1.1",
            "teacher_name": "Test Teacher",
            "school_name": "Test School",
            "duration_minutes": 40,
            "lesson_number": 1,
        },
    )

    assert response.status_code == 200
    plan = response.json()

    assert isinstance(plan, dict)
    assert plan
