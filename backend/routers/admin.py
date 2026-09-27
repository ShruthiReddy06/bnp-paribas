import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from dotenv import load_dotenv

from database import assign_interviewer, create_candidate_test, create_job_posting, delete_job_posting, delete_user, get_admin_applications, get_admin_candidate_pipeline, get_admin_users, get_candidate_test, get_job_postings, get_shortlist_threshold, get_shortlisted_application, set_shortlist_threshold
from schemas.candidate import CandidateOut
from schemas.admin import AdminApplicationOut, AdminUserOut, ThresholdOut, ThresholdUpdate
from schemas.interview import InterviewAssignmentRequest
from schemas.job import JobPostingCreate, JobPostingOut
from auth_utils.dependencies import require_role

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"


@router.get("/admin/candidates", response_model=List[CandidateOut])
def admin_candidates(user=Depends(require_role("admin"))):
    return get_admin_candidate_pipeline()


@router.get("/admin/jobs", response_model=List[JobPostingOut])
def admin_jobs(user=Depends(require_role("admin"))):
    return get_job_postings()


@router.post("/admin/jobs", response_model=JobPostingOut)
def admin_create_job(body: JobPostingCreate, user=Depends(require_role("admin"))):
    return create_job_posting(body.title, body.description, body.location, body.type, body.experience_years, body.education, body.must_have, body.nice_to_have)


@router.delete("/admin/jobs/{job_id}")
def admin_delete_job(job_id: int, user=Depends(require_role("admin"))):
    if not delete_job_posting(job_id):
        raise HTTPException(status_code=404, detail="Job posting not found")
    return {"ok": True, "job_id": job_id}


@router.get("/admin/users", response_model=List[AdminUserOut])
def admin_users(user=Depends(require_role("admin"))):
    return get_admin_users()


@router.delete("/admin/users/{username}")
def admin_delete_user(username: str, user=Depends(require_role("admin"))):
    deleted_role = delete_user(username)
    if deleted_role is None:
        raise HTTPException(status_code=404, detail="User not found")
    if deleted_role == "admin":
        raise HTTPException(status_code=403, detail="Administrator accounts cannot be deleted")
    return {"ok": True, "username": username, "role": deleted_role}


@router.get("/admin/applications", response_model=List[AdminApplicationOut])
def admin_applications(user=Depends(require_role("admin"))):
    return get_admin_applications()


@router.post("/admin/applications/{application_id}/assign-test")
def admin_assign_test(application_id: int, user=Depends(require_role("admin"))):
    application = get_shortlisted_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Tests can only be assigned to shortlisted applications")

    existing_test = get_candidate_test(application_id)
    if existing_test:
        return {
            "id": existing_test["id"], "status": existing_test["status"],
            "question_count": len(existing_test["questions"]),
            "generation_mode": existing_test["generation_mode"],
        }

    resume_path = UPLOAD_DIR / application["resume_path"]
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="The shortlisted resume file could not be found")

    load_dotenv(UPLOAD_DIR.parent / ".env")
    generation_mode = "ai"
    if os.getenv("GROQ_API_KEY"):
        from questions_generator.rag_pipeline import generate_interview

        job_description = (
            f"Job title: {application['job_title']}\n"
            f"Job description: {application['job_description']}\n"
            f"Required skills: {', '.join(application['must_have'])}\n"
            f"Nice-to-have skills: {', '.join(application['nice_to_have'])}"
        )
        try:
            generated = generate_interview(
                resume_path=str(resume_path),
                job_description=job_description,
                mode="3",
                total_questions=6,
                easy_questions=2,
                medium_questions=2,
                hard_questions=2,
            )
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"Test generation failed: {error}") from error
        questions = generated.get("questions", [])
    else:
        from questions_generator.offline_assessment import create_standard_assessment

        questions = create_standard_assessment()
        generation_mode = "standard"
    if not questions:
        raise HTTPException(status_code=502, detail="Test generation returned no questions")
    test = create_candidate_test(application_id, questions, generation_mode)
    return {
        "id": test["id"], "status": test["status"],
        "question_count": len(questions), "generation_mode": generation_mode,
    }


@router.post("/admin/interviews/assign")
def admin_assign_interviewer(body: InterviewAssignmentRequest, user=Depends(require_role("admin"))):
    assignment = assign_interviewer(body.application_id, body.interviewer_username)
    if assignment is False:
        raise HTTPException(status_code=400, detail="Selected user is not an interviewer")
    if assignment is None:
        raise HTTPException(status_code=404, detail="Eligible interview application not found")
    return assignment


@router.get("/admin/settings/threshold", response_model=ThresholdOut)
def admin_get_threshold(user=Depends(require_role("admin"))):
    return {"threshold": get_shortlist_threshold()}


@router.put("/admin/settings/threshold", response_model=ThresholdOut)
def admin_update_threshold(body: ThresholdUpdate, user=Depends(require_role("admin"))):
    if not 0 <= body.threshold <= 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
    return {"threshold": set_shortlist_threshold(body.threshold)}
