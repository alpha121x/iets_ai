from fastapi import APIRouter

from app.dependencies import CurrentUser, DBSession
from app.schemas import ProfileUpdate, UserProfile

router = APIRouter(prefix="/api/profile", tags=["Student profile"])


@router.get("/me", response_model=UserProfile)
def get_profile(user: CurrentUser) -> CurrentUser:
    return user


@router.put("/me", response_model=UserProfile)
def update_profile(payload: ProfileUpdate, user: CurrentUser, db: DBSession) -> CurrentUser:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
