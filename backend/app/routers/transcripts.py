import re

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.dependencies import CurrentUser, DBSession
from app.models.transcript import Transcript

router = APIRouter(prefix="/api/transcripts", tags=["Academic transcripts"])


@router.post("/upload")
async def upload_transcript(
    user: CurrentUser, db: DBSession, file: UploadFile = File(...)
) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF transcripts are accepted")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Transcript must be smaller than 10 MB")
    try:
        document = fitz.open(stream=content, filetype="pdf")
        text = "\n".join(page.get_text() for page in document).strip()
    except Exception as error:
        raise HTTPException(status_code=422, detail="The PDF could not be read") from error
    cgpa = _find_cgpa(text)
    transcript = Transcript(user_id=user.id, filename=file.filename or "transcript.pdf", extracted_text=text, detected_cgpa=cgpa)
    db.add(transcript)
    if cgpa is not None:
        user.cgpa = cgpa
    db.commit()
    return {"id": transcript.id, "filename": transcript.filename, "detected_cgpa": cgpa, "extracted_characters": len(text)}


def _find_cgpa(text: str) -> float | None:
    match = re.search(r"(?:CGPA|GPA)\s*[:\-]?\s*([0-4](?:\.\d{1,2})?)", text, re.IGNORECASE)
    return float(match.group(1)) if match else None
