from app.services.lesson_plan_generator import generate_lesson_plan


class Unit:
    grade = "Grade 9"
    learning_area = "English"
    theme = "1.0: Citizenship"
    strand = "Listening and Speaking"
    sub_strand = "1.1.1 Polite Language"
    specific_learning_outcomes = [
        "Use polite language in appropriate situations.",
        "Demonstrate appropriate language in conversations.",
    ]
    key_inquiry_questions = ["Why is polite language important?"]
    learning_resources = ["Skills in English", "Teacher's Guide"]
    core_competencies = ["Communication and collaboration"]
    pcis = ["Social cohesion"]
    values = ["Respect"]
    links_to_other_subjects = ["Social Studies"]
    source_pages = [10, 11]
    source_document = "GRADE.9.ENGLISH.pdf"


def test_build09_standard_structure():
    plan = generate_lesson_plan(
        Unit(),
        teacher_name="Teacher",
        school_name="School",
        lesson_date="2026-09-23",
        duration_minutes=40,
        class_size=35,
        lesson_number=1,
    )

    assert plan["theme"] == "1.0: Citizenship"
    assert plan["strand"] == "Listening and Speaking"
    assert plan["sub_strand"] == "1.1.1 Polite Language"

    assert plan["introduction"]["duration_minutes"] == 5
    assert plan["lesson_development"]["duration_minutes"] == 30
    assert plan["conclusion"]["duration_minutes"] == 5

    steps = plan["lesson_development"]["steps"]
    assert len(steps) == 4
    assert sum(step["duration_minutes"] for step in steps) == 30

    assert plan["learning_resources"] == ["Skills in English", "Teacher's Guide"]
    assert plan["assessment"]
    assert plan["assessment_approaches"]
    assert plan["extended_activities"]
    assert plan["reflection"]
    assert plan["teacher_self_evaluation"]["what_went_well"] == ""
    assert plan["source_pages"] == [10, 11]
