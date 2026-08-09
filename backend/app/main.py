from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.models import (  # Import models before metadata is created.
    IELTSResult,
    University,
    UniversityProgram,
    User,
    WritingSubmission,
)
from app.routers import auth, dashboard, ielts, profile, transcripts, universities
from app.seed import seed_initial_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal

    with SessionLocal() as db:
        seed_initial_data(db)
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(ielts.router)
app.include_router(transcripts.router)
app.include_router(universities.router)
app.include_router(dashboard.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Coach API is running", "status": "success"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


react_build_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
static_dir = react_build_dir if react_build_dir.exists() else Path(__file__).parent / "static"
app.mount("/app", StaticFiles(directory=static_dir, html=True), name="frontend")
