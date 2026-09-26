from typing import Any
from pydantic import BaseModel, Field

from .llm_client import llm_client

# ---------------------------------------------------------
# Pydantic Schemas for Semantic Analysis
# ---------------------------------------------------------

class Match(BaseModel):
    requirement: str = Field(..., description="The original requirement from the JD")
    matched: bool = Field(..., description="Whether the candidate satisfies the requirement")
    evidence: str = Field(..., description="Evidence from the resume, if matched")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence value between 0 and 1")

class Gap(BaseModel):
    requirement: str = Field(..., description="The requirement that was not met")
    reason: str = Field(..., description="Reason why the requirement is a gap")

class SemanticMatchResponse(BaseModel):
    matches: list[Match]
    gaps: list[Gap]
    summary: str = Field(..., description="A concise summary of the candidate's fit")


# ---------------------------------------------------------
# Semantic matching
# ---------------------------------------------------------

def analyze_semantic_matches(
    job: dict[str, Any],
    resume_text: str,
    resume_skills: list[str],
) -> dict[str, Any]:
    """
    Use configured LLM to semantically compare a job description
    against a candidate resume.

    The LLM provides:
        - matched requirements
        - evidence
        - confidence
        - missing requirements
        - summary

    The LLM does NOT determine the final 100-point score.
    """

    must_have = job.get("must_have", [])
    nice_to_have = job.get("nice_to_have", [])

    candidate_text = (
        f"Candidate Skills:\n"
        f"{', '.join(resume_skills)}\n\n"
        f"Resume:\n"
        f"{resume_text}"
    )

    job_text = (
        f"Job Title: {job.get('title', '')}\n"
        f"Job Summary: {job.get('summary', '')}\n\n"
        f"Must-Have Requirements:\n"
        f"{chr(10).join('- ' + skill for skill in must_have)}\n\n"
        f"Nice-to-Have Requirements:\n"
        f"{chr(10).join('- ' + skill for skill in nice_to_have)}"
    )

    prompt = f"""You are an expert technical recruitment assistant.

Your task is to compare a candidate resume against a job description.

For every MUST-HAVE requirement:

1. Decide whether the candidate satisfies it.
2. Use only evidence actually present in the resume.
3. If matched, provide concise evidence from the resume.
4. Give a confidence value between 0 and 1.
5. If there is insufficient evidence, mark it as a gap.
6. Do not assume skills that are not supported by the resume.

Important rules:

- Understand semantic meaning, not just exact keywords.
- "Built REST APIs using FastAPI" can support "REST API design".
- "Django" satisfies a requirement such as "FastAPI or Flask or Django".
- "Django ORM" can satisfy "SQLAlchemy or Django ORM".
- "pytest" can provide evidence for "Unit Testing (pytest)".
- Do not treat unrelated skills as matches.
- Do not invent experience, skills, education, or projects.
- Do NOT automatically assume Tailwind CSS means proven Responsive Design unless there is evidence.
- Do NOT automatically assume React means TypeScript unless there is evidence for TypeScript.
- Do NOT automatically assume FastAPI means SQLAlchemy unless there is evidence for SQLAlchemy.
- Distinguish direct evidence from weak inference.
- Identify genuine gaps if evidence is weak or absent.
- Do not assign the candidate's final overall score.
- Do not make an overall hiring decision.
- Be conservative and evidence-based when evidence is weak.

JOB DESCRIPTION
---------------
{job_text}

CANDIDATE
---------
{candidate_text}

Analyze the candidate against the job description based strictly on the evidence above.
"""

    result_model = llm_client.call(prompt, SemanticMatchResponse)
    
    # Return as dict to remain compatible with existing callers
    return result_model.model_dump()