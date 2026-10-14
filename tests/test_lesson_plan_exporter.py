from io import BytesIO

from docx import Document

from app.services.lesson_plan_exporter import export_lesson_plan_docx


def test_export_creates_editable_word_document():
    plan = {
        "school": "Sample School",
        "teacher": "Test Teacher",
        "grade": "Grade 9",
        "learning_area": "English",
        "duration_minutes": 40,
        "theme": "Citizenship",
        "strand": "Listening and Speaking",
        "sub_strand": "Oral Communication",
        "specific_learning_outcomes": ["Communicate clearly"],
        "key_inquiry_questions": ["How do we communicate effectively?"],
        "introduction": {
            "duration_minutes": 5,
            "activities": ["Review prior learning"],
        },
        "lesson_development": {
            "duration_minutes": 30,
            "steps": [{
                "number": 1,
                "title": "Guided Exploration",
                "duration_minutes": 8,
                "activities": ["Practise oral communication"],
            }],
        },
        "conclusion": {
            "duration_minutes": 5,
            "activities": ["Summarise the lesson"],
        },
        "assessment": ["Check learner understanding"],
        "reflection": ["Review learner progress"],
        "source_pages": [12, 13],
        "source_document": "Grade 9 English Curriculum",
    }

    output = export_lesson_plan_docx(plan)
    document = Document(BytesIO(output.getvalue()))
    text = "\n".join(p.text for p in document.paragraphs)

    assert "COMPETENCY-BASED EDUCATION LESSON PLAN" in text
    assert "Sample School" in text
    assert "Communicate clearly" in text
    assert "Practise oral communication" in text
    assert "Check learner understanding" in text
    assert "Grade 9 English Curriculum" in text
