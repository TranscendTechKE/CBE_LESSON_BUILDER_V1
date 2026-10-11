from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.curriculum import router as curriculum_router
from app.routes.curriculum_profiles import router as curriculum_profiles_router

from app.config import settings


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_name)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(curriculum_router)
app.include_router(curriculum_profiles_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )

