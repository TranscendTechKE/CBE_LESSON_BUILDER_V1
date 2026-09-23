from app.models.curriculum import CurriculumData
from app.services.lesson_generator import generate_lesson


def test_generate_lesson():
    data = CurriculumData(
        learning_area="English",
        grade="Grade 7",
        strand="Reading",
        sub_strand="Comprehension",
        learning_outcomes=["Identify the main idea."]
    )

    lesson = generate_lesson(data)

    assert lesson.learning_area == "English"
    assert lesson.specific_learning_outcomes == ["Identify the main idea."]
