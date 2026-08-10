import base64
import re

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.dependencies import CurrentUser, DBSession
from app.config import settings
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
    extraction_method = "pdf_text"
    # Some generated transcripts contain a text layer, but lay out the final
    # score in a way that a text pattern cannot reliably identify.  In that
    # case, use vision as a fallback as well as for fully scanned documents.
    if cgpa is None and settings.GEMINI_API_KEY:
        cgpa = _find_cgpa_with_gemini(document)
        extraction_method = "gemini_vision" if cgpa is not None else "unavailable"
    transcript = Transcript(user_id=user.id, filename=file.filename or "transcript.pdf", extracted_text=text, detected_cgpa=cgpa)
    db.add(transcript)
    if cgpa is not None:
        user.cgpa = cgpa
    db.commit()
    return {"id": transcript.id, "filename": transcript.filename, "detected_cgpa": cgpa, "extracted_characters": len(text), "extraction_method": extraction_method}


def _find_cgpa(text: str) -> float | None:
    """Return a final cumulative GPA, without confusing it with term GPAs."""
    normalized = re.sub(r"\s+", " ", text)
    labels = (
        r"(?:final\s+)?(?:cumulative|overall)\s+(?:c\.?(?:g\.?(?:p\.?(?:a\.?)?)?)?|g\.?(?:p\.?(?:a\.?)?)?)",
        r"(?:final\s+)?c\.?(?:g\.?(?:p\.?(?:a\.?)?)?)",
        r"(?:final\s+)?g\.?(?:p\.?(?:a\.?)?)",
    )
    value = r"([0-4](?:[\.,]\d{1,2})?)"

    for label in labels:
        matches = re.finditer(rf"\b{label}\b\s*(?:is|=|:|\-|/)?\s*{value}\b", normalized, re.IGNORECASE)
        for match in matches:
            # A bare "GPA" label can occur inside "semester GPA" or "term
            # GPA".  Those values are not an applicant's final result.
            preceding_text = normalized[max(0, match.start() - 24):match.start()]
            if re.search(r"(?:semester|term|session)\s+$", preceding_text, re.IGNORECASE):
                continue
            cgpa = float(match.group(1).replace(",", "."))
            if 0 <= cgpa <= 4:
                return cgpa
    return None


def _find_cgpa_with_gemini(document: fitz.Document) -> float | None:
    """Use Gemini vision when text extraction cannot identify a final CGPA."""
    try:
        import requests

        parts = [
            {
                "text": (
                    "Read these academic transcript pages. Return only the final cumulative GPA or CGPA "
                    "as a number from 0 to 4.0. Do not return semester GPA, marks, explanations, or other text."
                )
            }
        ]
        for page_number in range(min(3, document.page_count)):
            page = document[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(pix.tobytes("png")).decode("ascii"),
                    }
                }
            )
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
            params={"key": settings.GEMINI_API_KEY},
            json={"contents": [{"parts": parts}]},
            timeout=45,
        )
        response.raise_for_status()
        result = response.json()
        answer = result["candidates"][0]["content"]["parts"][0].get("text", "")
        match = re.search(r"\b([0-4](?:\.\d{1,2})?)\b", answer)
        return float(match.group(1)) if match else None
    except Exception:
        return None
