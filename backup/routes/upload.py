from pathlib import Path
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.pdf_processor import extract_pdf

from app.services.validator import validate_curriculum

router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "uploads"
EXTRACTED_DIR = ROOT / "app" / "data" / "extracted"
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-curriculum")
async def upload_curriculum(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    destination = UPLOAD_DIR / safe_name

    content = await file.read()
    destination.write_bytes(content)

    try:
        extracted = extract_pdf(destination)
        curriculum = parse_curriculum(extracted)
        warnings = validate_curriculum(curriculum)

        return JSONResponse({
            "ok": True,
            "file": safe_name,
            "curriculum": curriculum.model_dump(),
            "warnings": warnings,
        })
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {exc}")
