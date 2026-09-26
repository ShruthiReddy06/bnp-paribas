from pydantic import BaseModel
from typing import Optional


class InterviewStatusOut(BaseModel):
    status: str
    jd: str
    interviewer_name: Optional[str] = None
    interview_date: Optional[str] = None


class DecisionRequest(BaseModel):
    interview_id: int
    decision: str
    feedback: str = ''


class ScheduleRequest(BaseModel):
    application_id: int
    scheduled_at: str


class InterviewOut(BaseModel):
    interview_id: int
    application_id: int
    job_title: str
    interviewer_username: Optional[str] = None
    scheduled_at: Optional[str] = None
    candidate_confirmed: bool
    interviewer_confirmed: bool
    decision: Optional[str] = None
    feedback: Optional[str] = None
