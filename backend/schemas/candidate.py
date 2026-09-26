from pydantic import BaseModel
from typing import Optional


class CandidateOut(BaseModel):
    id: int
    name: str
    jd: str
    status: str
    score: float
    decision: Optional[str] = None
