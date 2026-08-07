from fastapi import APIRouter
from sqlalchemy import desc

from app.dependencies import CurrentUser, DBSession
from app.models.ielts import IELTSResult, WritingSubmission
from app.models.university import University, UniversityProgram
from app.services import university_match

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard(user: CurrentUser, db: DBSession) -> dict:
    result = db.query(IELTSResult).filter_by(user_id=user.id).order_by(desc(IELTSResult.created_at)).first()
    submissions = db.query(WritingSubmission).filter_by(user_id=user.id).count()
    strong_matches = 0
    if result:
        programs = db.query(UniversityProgram, University).join(University)
        if user.target_country:
            programs = programs.filter(University.country.ilike(user.target_country))
        for program, _ in programs.all():
            if university_match(program, result, user)["status"] == "Strong match":
                strong_matches += 1
    weakest = None
    if result:
        scores = {"Reading": result.reading, "Listening": result.listening, "Writing": result.writing, "Speaking": result.speaking}
        weakest = min(scores, key=scores.get)
    ielts = None
    if result:
        ielts = {
            "reading": result.reading,
            "listening": result.listening,
            "writing": result.writing,
            "speaking": result.speaking,
            "overall": result.overall,
            "created_at": result.created_at.isoformat(),
        }
    return {"student": user.full_name, "ielts": ielts, "weakest_module": weakest, "writing_submissions": submissions, "strong_matches": strong_matches}
