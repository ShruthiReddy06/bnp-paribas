from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    access_scope: Literal['admin', 'standard'] = 'standard'


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
