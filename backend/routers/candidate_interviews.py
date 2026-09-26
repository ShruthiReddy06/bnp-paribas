from fastapi import APIRouter, Depends, HTTPException

from auth_utils.dependencies import require_role
from database import confirm_interview, get_candidate_interviews

router = APIRouter()


@router.get("/candidate/interviews")
def candidate_interviews(user=Depends(require_role("candidate"))):
    username, _ = user
    return get_candidate_interviews(username)


@router.post("/candidate/interviews/{interview_id}/confirm")
def candidate_confirm_interview(interview_id: int, user=Depends(require_role("candidate"))):
    username, _ = user
    if not confirm_interview(username, interview_id):
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"ok": True, "interview_id": interview_id, "candidate_confirmed": True}