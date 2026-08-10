from fastapi import APIRouter
from sqlalchemy import desc

from app.dependencies import CurrentUser, DBSession
from app.models.chat import ChatMessage
from app.schemas import CoachChatRequest
from app.services import coach_reply

router = APIRouter(prefix="/api/coach", tags=["AI Coach"])


@router.get("/messages")
def messages(user: CurrentUser, db: DBSession) -> list[dict]:
    rows = db.query(ChatMessage).filter_by(user_id=user.id).order_by(desc(ChatMessage.created_at)).limit(30).all()
    return [{"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()} for row in reversed(rows)]


@router.post("/chat")
def chat(payload: CoachChatRequest, user: CurrentUser, db: DBSession) -> dict:
    db.add(ChatMessage(user_id=user.id, role="user", content=payload.message))
    reply = coach_reply(payload.message, user.target_program, user.target_country)
    db.add(ChatMessage(user_id=user.id, role="assistant", content=reply))
    db.commit()
    return {"role": "assistant", "content": reply}
