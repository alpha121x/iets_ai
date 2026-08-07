from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.models import (  # Import models before metadata is created.
    IELTSResult,
    University,
    UniversityProgram,
    User,
    WritingSubmission,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Coach API is running", "status": "success"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
