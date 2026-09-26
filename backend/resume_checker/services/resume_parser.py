from pydantic import BaseModel
from typing import List


class ResumeData(BaseModel):
    name: str
    email: str
    experience_years: float
    education: str
    location: str
    skills: List[str]
    resume_text: str