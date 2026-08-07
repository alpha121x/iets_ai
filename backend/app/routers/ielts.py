from fastapi import APIRouter, HTTPException
from sqlalchemy import desc

from app.dependencies import CurrentUser, DBSession
from app.models.ielts import IELTSLesson, IELTSResult, PracticeAttempt, WritingSubmission
from app.schemas import AttemptCreate, IELTSResultCreate, IELTSResultOut, LessonOut, SpeakingCreate, WritingCreate, WritingOut
from app.services import overall_band, speaking_feedback, writing_feedback

router = APIRouter(prefix="/api/ielts", tags=["IELTS coach"])


@router.get("/lessons", response_model=list[LessonOut])
def list_lessons(db: DBSession, module: str | None = None):
    query = db.query(IELTSLesson)
    if module:
        query = query.filter(IELTSLesson.module.ilike(module))
    return query.order_by(IELTSLesson.id).all()


@router.post("/results", response_model=IELTSResultOut)
def save_result(payload: IELTSResultCreate, user: CurrentUser, db: DBSession) -> IELTSResult:
    result = IELTSResult(user_id=user.id, overall=overall_band(**payload.model_dump(exclude={"test_type", "source"})), **payload.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("/results/latest", response_model=IELTSResultOut)
def latest_result(user: CurrentUser, db: DBSession) -> IELTSResult:
    result = db.query(IELTSResult).filter_by(user_id=user.id).order_by(desc(IELTSResult.created_at)).first()
    if not result:
        raise HTTPException(status_code=404, detail="No IELTS result has been recorded yet")
    return result


@router.post("/writing", response_model=WritingOut)
def evaluate_writing(payload: WritingCreate, user: CurrentUser, db: DBSession) -> WritingSubmission:
    band, feedback = writing_feedback(payload.answer, payload.task_type)
    submission = WritingSubmission(user_id=user.id, estimated_band=band, feedback=feedback, **payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.post("/speaking")
def evaluate_speaking(payload: SpeakingCreate, user: CurrentUser) -> dict:
    """Evaluate an already transcribed response; connect speech-to-text in the client or AI layer."""
    band, feedback = speaking_feedback(payload.transcript)
    return {"estimated_band": band, "feedback": feedback, "prompt": payload.prompt}


@router.get("/coach-tip")
def coach_tip(module: str = "Writing") -> dict:
    tips = {
        "Reading": "Underline keywords, then locate their paraphrases in the passage before choosing an answer.",
        "Listening": "Use the pauses to read ahead and predict whether you need a number, name, or noun.",
        "Writing": "Plan for two minutes: position, two main ideas, and one specific example for each body paragraph.",
        "Speaking": "Avoid one-word answers: answer directly, explain why, and give a personal example.",
    }
    return {"module": module, "tip": tips.get(module.title(), tips["Writing"])}


@router.post("/practice")
def save_attempt(payload: AttemptCreate, user: CurrentUser, db: DBSession) -> dict:
    if payload.correct_answers > payload.total_questions:
        raise HTTPException(status_code=422, detail="Correct answers cannot exceed total questions")
    score = round((payload.correct_answers / payload.total_questions) * 100, 1)
    attempt = PracticeAttempt(user_id=user.id, score=score, **payload.model_dump())
    db.add(attempt)
    db.commit()
    return {"module": payload.module, "percentage": score, "message": "Practice attempt saved"}
