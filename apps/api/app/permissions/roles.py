"""Permission validation utilities."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.models.base import RoleEnum


def require_roles(*roles: RoleEnum):
    """Dependency factory: validate current user role is within allowed roles."""

    def _check(user) -> object:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        if RoleEnum(user.role) not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return _check
