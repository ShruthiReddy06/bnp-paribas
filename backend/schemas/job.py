from pydantic import BaseModel


class JobPostingCreate(BaseModel):
    title: str
    description: str
    location: str
    type: str
    experience_years: float = 0
    education: str = ''
    must_have: list[str] = []
    nice_to_have: list[str] = []


class JobPostingOut(JobPostingCreate):
    id: int


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    resume_filename: str
    score: float | None = None


class ApplicationDetailOut(ApplicationOut):
    job_title: str
    location: str
    type: str