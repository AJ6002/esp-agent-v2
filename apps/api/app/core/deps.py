"""FastAPI dependencies: database session and current user resolution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.demo import is_demo_account
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.base import RoleEnum
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials not provided"
        )
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials invalid or expired"
        ) from None
    subject = payload.get("sub")
    if (
        not isinstance(subject, str)
        or not subject.isascii()
        or not subject.isdecimal()
        or len(subject) > 19
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
        )
    user_id = int(subject)
    if not 1 <= user_id <= 2**63 - 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
        )
    user = db.get(User, user_id)
    if (
        not user
        or not user.is_active
        or (not settings.is_development and is_demo_account(user.email))
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist or is disabled"
        )
    return user


def require_role(*roles: RoleEnum) -> Callable:
    """Dependency factory: restrict accessible roles."""

    def _dep(user: Annotated[User, Depends(get_current_user)]) -> User:
        if RoleEnum(user.role) not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return _dep


# Common role dependencies
admin_only = require_role(RoleEnum.admin)
supervisor_or_admin = require_role(RoleEnum.admin, RoleEnum.supervisor)
technician_or_above = require_role(
    RoleEnum.admin, RoleEnum.supervisor, RoleEnum.technician
)
