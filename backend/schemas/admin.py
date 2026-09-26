from typing import Optional

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    username: str
    role: str


class AdminApplicationOut(BaseModel):
    id: int
    username: str
    job_title: str
    status: str
    resume_filename: Optional[str] = None
    score: Optional[float] = None
    test_status: Optional[str] = None
    test_score: Optional[float] = None
    performance: Optional[dict] = None
    interview_id: Optional[int] = None
    interviewer_username: Optional[str] = None
    scheduled_at: Optional[str] = None
    candidate_confirmed: Optional[bool] = None
    interviewer_confirmed: Optional[bool] = None
    interview_decision: Optional[str] = None
    interview_feedback: Optional[str] = None


class ThresholdOut(BaseModel):
    threshold: float


class ThresholdUpdate(BaseModel):
    threshold: float