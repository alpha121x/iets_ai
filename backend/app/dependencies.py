from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.security import credentials_exception

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
DBSession = Annotated[Session, Depends(get_db)]


def current_user(db: DBSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        email = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]).get("sub")
    except JWTError as error:
        raise credentials_exception() from error
    if not email:
        raise credentials_exception()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception()
    return user


CurrentUser = Annotated[User, Depends(current_user)]
