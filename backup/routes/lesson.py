from fastapi import APIRouter, HTTPException
from app.models.curriculum import CurriculumData
from app.services.lesson_generator import generate_lesson

router = APIRouter(prefix="/api")


@router.post("/generate-lesson")
def generate(curriculum: CurriculumData):
    try:
        lesson = generate_lesson(curriculum)
        return {"ok": True, "lesson": lesson.model_dump()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lesson generation failed: {exc}")
