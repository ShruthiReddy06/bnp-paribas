from dataclasses import dataclass
from typing import Optional


@dataclass
class InterviewStatus:
    status: str
    jd: str
    interviewer_name: Optional[str] = None
    interview_date: Optional[str] = None
