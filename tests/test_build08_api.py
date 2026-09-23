def test_build08_files_exist():
    from pathlib import Path
    root = Path(__file__).parents[1]
    assert (root / "app/routes/curriculum.py").exists()
    assert (root / "app/services/lesson_plan_generator.py").exists()
    assert (root / "app/templates/dashboard.html").exists()
    assert (root / "app/static/js/curriculum-explorer.js").exists()
    assert (root / "app/static/css/curriculum-explorer.css").exists()
