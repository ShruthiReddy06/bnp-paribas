from dataclasses import dataclass
from typing import Optional


@dataclass
class Candidate:
    id: int
    name: str
    jd: str
    status: str
    score: int
    decision: Optional[str] = None
