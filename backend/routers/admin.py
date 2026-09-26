from fastapi import APIRouter, Depends, HTTPException
from typing import List

from database import create_job_posting, delete_job_posting, delete_user, get_admin_applications, get_admin_candidate_pipeline, get_admin_users, get_job_postings, get_shortlist_threshold, set_shortlist_threshold
from schemas.candidate import CandidateOut
from schemas.admin import AdminApplicationOut, AdminUserOut, ThresholdOut, ThresholdUpdate
from schemas.job import JobPostingCreate, JobPostingOut
from auth_utils.dependencies import require_role

router = APIRouter()


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


@router.get("/admin/settings/threshold", response_model=ThresholdOut)
def admin_get_threshold(user=Depends(require_role("admin"))):
    return {"threshold": get_shortlist_threshold()}


@router.put("/admin/settings/threshold", response_model=ThresholdOut)
def admin_update_threshold(body: ThresholdUpdate, user=Depends(require_role("admin"))):
    if not 0 <= body.threshold <= 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
    return {"threshold": set_shortlist_threshold(body.threshold)}
