from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile

from database import CANDIDATE_STATUS, complete_candidate_test, create_application, create_candidate_test, get_applied_job_ids, get_applications, get_candidate_test, get_candidate_test_summaries, get_job_posting, get_job_postings, get_shortlisted_applications, get_started_test, start_candidate_test
from schemas.interview import InterviewStatusOut
from schemas.job import ApplicationDetailOut, ApplicationOut, JobPostingOut
from schemas.test import CandidateTestOut, CandidateTestSummaryOut, TestSubmission
from resume_checker.services.document_parser import EmptyDocumentError, UnsupportedFileError, parse_document
from resume_checker.services.resume_parser import ResumeData
from resume_checker.services.resume_scorer import score_resume

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
MAX_RESUME_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
from auth_utils.dependencies import require_role

router = APIRouter()


@router.get("/candidate/status", response_model=InterviewStatusOut)
def candidate_status(user=Depends(require_role("candidate"))):
    return CANDIDATE_STATUS


@router.get("/candidate/jobs", response_model=list[JobPostingOut])
def candidate_jobs(user=Depends(require_role("candidate"))):
    return get_job_postings()


@router.get("/candidate/applications", response_model=list[int])
def candidate_applications(user=Depends(require_role("candidate"))):
    username, _ = user
    return get_applied_job_ids(username)


@router.get("/candidate/my-applications", response_model=list[ApplicationDetailOut])
def candidate_my_applications(user=Depends(require_role("candidate"))):
    username, _ = user
    return get_applications(username)


@router.get("/candidate/tests", response_model=list[CandidateTestSummaryOut])
def candidate_tests(user=Depends(require_role("candidate"))):
    """Return one generated test for every shortlisted application."""
    username, _ = user
    shortlisted_applications = get_shortlisted_applications(username)
    if not shortlisted_applications:
        return []

    from questions_generator.rag_pipeline import generate_interview

    tests = []
    for application in shortlisted_applications:
        existing_test = get_candidate_test(application["application_id"])
        if existing_test:
            tests.append(existing_test)
            continue

        resume_path = UPLOAD_DIR / application["resume_path"]
        if not resume_path.exists():
            raise HTTPException(status_code=404, detail="The shortlisted resume file could not be found")
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
        create_candidate_test(application["application_id"], generated.get("questions", []))
    return get_candidate_test_summaries(username)


@router.post("/candidate/tests/{test_id}/start", response_model=CandidateTestOut)
def candidate_start_test(test_id: int, user=Depends(require_role("candidate"))):
    username, _ = user
    test = start_candidate_test(username, test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    if test is False:
        raise HTTPException(status_code=409, detail="This test has already been opened")
    return test


@router.post("/candidate/tests/{test_id}/submit", response_model=CandidateTestOut)
def candidate_submit_test(test_id: int, body: TestSubmission, user=Depends(require_role("candidate"))):
    username, _ = user
    questions = get_started_test(username, test_id)
    if questions is None:
        raise HTTPException(status_code=404, detail="Test not found")
    if questions is False:
        raise HTTPException(status_code=409, detail="This test is not available for submission")
    try:
        from questions_generator.rag_pipeline import evaluate_descriptive_answer

        earned = 0.0
        maximum = 0.0
        evaluations = []
        for question in questions:
            marks = float(question.get("marks", 0))
            maximum += marks
            answer = body.answers.get(str(question.get("id")), "")
            if question.get("type") == "MCQ":
                correct = answer == question.get("correct_answer")
                question_score = marks if correct else 0.0
                evaluation = {"score": question_score, "max_score": marks, "correct": correct}
            else:
                evaluation = evaluate_descriptive_answer(question, answer)
                question_score = float(evaluation.get("score", 0))
            earned += question_score
            evaluations.append({"question_id": question.get("id"), "score": question_score, "max_score": marks, "feedback": evaluation.get("feedback", "")})
        score = round((earned / maximum) * 100, 2) if maximum else 0
        performance = {"score": score, "earned_marks": round(earned, 2), "maximum_marks": round(maximum, 2), "evaluations": evaluations}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Performance evaluation failed: {error}") from error
    result = complete_candidate_test(username, test_id, body.answers, score, performance)
    return result


@router.post("/candidate/generate-test")
def candidate_generate_test(payload: dict = Body(...), user=Depends(require_role("candidate"))):
    """Generate an interview test using the existing question generator logic."""
    required = [
        "resume_path",
        "job_description",
        "mode",
        "total_questions",
        "easy_questions",
        "medium_questions",
        "hard_questions",
    ]

    missing = [key for key in required if key not in payload]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")

    from questions_generator.rag_pipeline import generate_interview

    try:
        return generate_interview(
            resume_path=payload["resume_path"],
            job_description=payload["job_description"],
            mode=payload["mode"],
            total_questions=int(payload["total_questions"]),
            easy_questions=int(payload["easy_questions"]),
            medium_questions=int(payload["medium_questions"]),
            hard_questions=int(payload["hard_questions"]),
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Test generation failed: {error}") from error


@router.post("/candidate/jobs/{job_id}/apply", response_model=ApplicationOut)
async def candidate_apply(job_id: int, resume: UploadFile = File(...), user=Depends(require_role("candidate"))):
    username, _ = user
    extension = Path(resume.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Upload a PDF, DOC, or DOCX resume")
    content = await resume.read(MAX_RESUME_SIZE + 1)
    if len(content) > MAX_RESUME_SIZE:
        raise HTTPException(status_code=400, detail="Resume must be smaller than 5 MB")

    stored_name = f"{uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(exist_ok=True)
    resume_path = UPLOAD_DIR / stored_name
    job = get_job_posting(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job posting not found")

    resume_path.write_bytes(content)
    try:
        resume_text = parse_document(str(resume_path))
        checker_job = {
            "title": job["title"],
            "summary": job["description"],
            "location": job["location"],
            "experience_years": job["experience_years"],
            "education": job["education"],
            "must_have": job["must_have"],
            "nice_to_have": job["nice_to_have"],
        }
        score_result = score_resume(
            checker_job,
            ResumeData(
                name=username,
                email="",
                experience_years=0,
                education="",
                location="",
                skills=[],
                resume_text=resume_text,
            ),
        )
        score = score_result["score"]
    except (UnsupportedFileError, EmptyDocumentError, ValueError) as error:
        resume_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        resume_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Resume scoring failed")

    application = create_application(username, job_id, resume.filename, stored_name, score)
    if application is False:
        resume_path.unlink(missing_ok=True)
        raise HTTPException(status_code=409, detail="You have already applied for this role")
    return application
