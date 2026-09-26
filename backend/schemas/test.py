from typing import Any, Optional

from pydantic import BaseModel


class CandidateTestOut(BaseModel):
    id: int
    status: str
    score: Optional[float] = None
    questions: list[dict[str, Any]]


class CandidateTestSummaryOut(BaseModel):
    id: int
    status: str
    score: Optional[float] = None
    question_count: int


class TestSubmission(BaseModel):
    answers: dict[str, str]