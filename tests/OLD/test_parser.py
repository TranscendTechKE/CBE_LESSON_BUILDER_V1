from app.services.curriculum_parser import parse_curriculum


def test_parse_basic_curriculum():
    extracted = {
        "source_file": "test.pdf",
        "page_count": 1,
        "text": """
        Learning Area: Integrated Science
        Grade: Grade 7
        Strand: Living Things
        Sub-strand: Cells
        Specific Learning Outcomes
        1. Identify cell structures
        2. Describe cell functions
        """
    }

    data = parse_curriculum(extracted)

    assert data.learning_area == "Integrated Science"
    assert data.grade == "Grade 7"
    assert data.strand == "Living Things"
    assert data.sub_strand == "Cells"
