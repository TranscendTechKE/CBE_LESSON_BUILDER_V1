
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.curriculum_profiles import PROFILES, VERIFIED_PROFILE_IDS


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_profiles():
    PROFILES.clear()
    VERIFIED_PROFILE_IDS.clear()
    yield
    PROFILES.clear()
    VERIFIED_PROFILE_IDS.clear()


def sample_profile(source_verified=True):
    return {
        "profile_id": "test-science-grade-7",
        "source_verified": source_verified,
        "education_stage": "Junior School",
        "grade": "7",
        "learning_area": "Integrated Science",
        "sources": [
            {
                "authority": "KICD",
                "document_title": "Test curriculum document",
                "pages": [10],
            }
        ],
        "content_nodes": [
            {
                "code": "S1",
                "title": "Example strand",
                "node_type": "strand",
                "source_pages": [10],
                "children": [
                    {
                        "code": "S1.1",
                        "title": "Example topic",
                        "node_type": "sub_strand",
                        "specific_learning_outcomes": [
                            "Test learning outcome"
                        ],
                        "suggested_learning_experiences": [
                            "Test learning experience"
                        ],
                        "key_inquiry_questions": [
                            "Test inquiry question?"
                        ],
                        "source_pages": [11],
                    }
                ],
            }
        ],
    }


def test_register_profile():
    response = client.post(
        "/api/curriculum-profiles",
        json=sample_profile(),
    )

    assert response.status_code == 200
    assert response.json()["profile_id"] == "test-science-grade-7"
    assert response.json()["node_count"] == 2


def test_duplicate_profile_id_is_rejected():
    payload = sample_profile()

    first = client.post("/api/curriculum-profiles", json=payload)
    second = client.post("/api/curriculum-profiles", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409


def test_list_and_retrieve_profiles():
    client.post(
        "/api/curriculum-profiles",
        json=sample_profile(),
    )

    listed = client.get("/api/curriculum-profiles")
    retrieved = client.get(
        "/api/curriculum-profiles/test-science-grade-7"
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert retrieved.status_code == 200
    assert retrieved.json()["learning_area"] == "Integrated Science"


def test_retrieve_profile_nodes():
    client.post(
        "/api/curriculum-profiles",
        json=sample_profile(),
    )

    response = client.get(
        "/api/curriculum-profiles/test-science-grade-7/nodes"
    )

    assert response.status_code == 200
    assert response.json()["nodes"][0]["children"][0]["code"] == "S1.1"


def test_unverified_profile_cannot_generate_lesson_plan():
    client.post(
        "/api/curriculum-profiles",
        json=sample_profile(source_verified=False),
    )

    response = client.post(
        "/api/curriculum-profiles/test-science-grade-7/lesson-plan",
        json={"selected_node_code": "S1.1"},
    )

    assert response.status_code == 403
    assert "not been approved" in response.json()["detail"].lower()


def test_submitted_verification_claim_is_not_enough():
    response = client.post(
        "/api/curriculum-profiles",
        json=sample_profile(source_verified=True),
    )

    assert response.status_code == 200
    assert response.json()["source_verified"] is False

    plan_response = client.post(
        "/api/curriculum-profiles/test-science-grade-7/lesson-plan",
        json={
            "selected_node_code": "S1.1",
            "duration_minutes": 40,
        },
    )

    assert plan_response.status_code == 403


def test_server_approved_profile_generates_lesson_plan():
    client.post(
        "/api/curriculum-profiles",
        json=sample_profile(source_verified=True),
    )

    VERIFIED_PROFILE_IDS.add("test-science-grade-7")

    response = client.post(
        "/api/curriculum-profiles/test-science-grade-7/lesson-plan",
        json={
            "selected_node_code": "S1.1",
            "duration_minutes": 40,
        },
    )

    assert response.status_code == 200

    plan = response.json()
    assert plan["learning_area"] == "Integrated Science"
    assert plan["grade"] == "7"
    assert plan["sub_strand"] == "Example topic"
    assert plan["source_pages"] == [10, 11]
    assert len(plan["lesson_development"]["steps"]) == 4


def test_unknown_profile_returns_404():
    response = client.get(
        "/api/curriculum-profiles/does-not-exist"
    )

    assert response.status_code == 404