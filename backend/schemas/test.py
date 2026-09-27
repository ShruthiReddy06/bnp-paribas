from typing import Any, Optional

from pydantic import BaseModel


class CandidateTestOut(BaseModel):
    id: int
    status: str
    score: Optional[float] = None
    generation_mode: str = 'ai'
    questions: list[dict[str, Any]]


class CandidateTestSummaryOut(BaseModel):
    id: int
    status: str
    score: Optional[float] = None
    question_count: int
    generation_mode: str = 'ai'
    application_status: Optional[str] = None


class TestSubmission(BaseModel):
    answers: dict[str, str]