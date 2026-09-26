from fastapi import APIRouter, HTTPException

from database import create_user, get_user, verify_password
from schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from auth_utils.token import create_token

router = APIRouter()


@router.post("/register", response_model=LoginResponse)
def register(body: RegisterRequest):
    if body.role not in {"candidate", "interviewer"}:
        raise HTTPException(status_code=400, detail="Choose candidate or interviewer")
    if not create_user(body.username, body.password, body.role):
        raise HTTPException(status_code=409, detail="Username is already registered")

    token = create_token(body.username)
    return LoginResponse(token=token, role=body.role, username=body.username)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = get_user(body.username)
    if not user or not verify_password(body.password, user):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(body.username)
    return LoginResponse(token=token, role=user["role"], username=body.username)
