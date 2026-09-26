from fastapi import Header, HTTPException, Depends
from typing import Optional

from database import get_user
from auth_utils.token import resolve_token


def get_current_user(authorization: Optional[str] = Header(None)):
    """Returns (username, role) for a valid Bearer token, else raises 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ")[1]
    username = resolve_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return username, user["role"]


def require_role(role: str):
    """Use as a dependency to restrict a route to one role, e.g.:
    def route(user=Depends(require_role("admin"))): ...
    """
    def checker(user=Depends(get_current_user)):
        username, user_role = user
        if user_role != role:
            raise HTTPException(status_code=403, detail=f"{role.title()} only")
        return username, user_role
    return checker
