from fastapi import APIRouter, Depends, HTTPException
from typing import List

from database import get_interviewer_candidates, schedule_interview, submit_interview_decision
from schemas.interview import DecisionRequest, ScheduleRequest
from auth_utils.dependencies import require_role

router = APIRouter()


@router.get("/interviewer/candidates")
def interviewer_candidates(user=Depends(require_role("interviewer"))):
    username, _ = user
    return get_interviewer_candidates(username)


@router.post("/interviewer/schedule")
def interviewer_schedule(body: ScheduleRequest, user=Depends(require_role("interviewer"))):
    username, _ = user
    interview = schedule_interview(body.application_id, username, body.scheduled_at)
    if not interview:
        raise HTTPException(status_code=404, detail="Candidate is not assigned to you or is no longer eligible")
    return interview


@router.post("/interviewer/decision")
def interviewer_decision(body: DecisionRequest, user=Depends(require_role("interviewer"))):
    if body.decision not in {"Accepted", "Rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be Accepted or Rejected")
    username, _ = user
    result = submit_interview_decision(body.interview_id, username, body.decision, body.feedback)
    if result is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    if result is False:
        raise HTTPException(status_code=409, detail="Schedule the interview before submitting a review")
    return {"ok": True, "interview_id": body.interview_id, "decision": body.decision}
