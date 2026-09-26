from pathlib import Path
import json
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import shutil
import os
from services.resume_parser import ResumeData
from services.resume_scorer import score_resume
from services.semantic_matcher import analyze_semantic_matches
from pydantic import BaseModel
from services.document_parser import parse_document, UnsupportedFileError, EmptyDocumentError

app = FastAPI(title="Resume Scoring API")


# Input_Data.json is one level above the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "Input_Data.json"

UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# Temporary storage for JDs created through the API
created_jobs = {}


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# -----------------------------
# Request model for creating JD
# -----------------------------

class JobDescription(BaseModel):
    title: str
    location: str
    experience_years: float
    education: str
    must_have: list[str]
    nice_to_have: list[str] = []
    summary: str = ""


# -----------------------------
# Request model for resume scoring
# -----------------------------

class ResumeScoreRequest(BaseModel):
    job_id: str
    resume: ResumeData


# -----------------------------
# Root endpoint
# -----------------------------

@app.get("/")
def root():
    return {
        "message": "Resume Scoring API is running"
    }


# -----------------------------
# Get sample JD from JSON
# -----------------------------

@app.get("/jd/{jd_id}")
def get_job_description(jd_id: str):
    data = load_data()

    for jd in data["job_descriptions"]:
        if jd["id"] == jd_id:
            return jd

    raise HTTPException(
        status_code=404,
        detail=f"Job description '{jd_id}' not found"
    )


# -----------------------------
# Create a new JD
# -----------------------------

@app.post("/jobs")
def create_job(job: JobDescription):

    job_id = f"job-{uuid.uuid4().hex[:8]}"

    new_job = {
        "id": job_id,
        "title": job.title,
        "location": job.location,
        "experience_years": job.experience_years,
        "education": job.education,
        "must_have": job.must_have,
        "nice_to_have": job.nice_to_have,
        "summary": job.summary
    }

    created_jobs[job_id] = new_job

    return new_job


# -----------------------------
# Get a newly created JD
# -----------------------------

@app.get("/jobs/{job_id}")
def get_created_job(job_id: str):

    if job_id not in created_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )

    return created_jobs[job_id]


# -----------------------------
# Submit a manual resume
# -----------------------------

@app.post("/resume")
def submit_resume(resume: ResumeData):
    return {
        "message": "Resume received successfully",
        "resume": resume
    }


# -----------------------------
# Score a resume against a JD
# -----------------------------

@app.post("/score")
def score_candidate(request: ResumeScoreRequest):

    # Check dynamically created jobs first
    if request.job_id in created_jobs:
        job = created_jobs[request.job_id]

    else:
        # Check sample JDs from Input_Data.json
        data = load_data()

        job = None

        for jd in data["job_descriptions"]:
            if jd["id"] == request.job_id:
                job = jd
                break

        if job is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job '{request.job_id}' not found"
            )

    result = score_resume(
        job=job,
        resume=request.resume
    )

    semantic_analysis = analyze_semantic_matches(
        job=job,
        resume_text=request.resume.resume_text,
        resume_skills=request.resume.skills
    )

    result["semantic_analysis"] = semantic_analysis

    return {
        "job_id": request.job_id,
        "candidate": request.resume.name,
        "result": result
    }

# -----------------------------
# Upload a resume document
# -----------------------------

@app.post("/resume/upload")
def upload_resume(job_id: str = Form(...), file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
        
    file_path = UPLOADS_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        text = parse_document(str(file_path))
    except UnsupportedFileError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    resume_data = ResumeData(
        name=file.filename,
        email="uploaded@example.com",
        experience_years=0.0,
        education="Extracted from document",
        location="Unknown",
        skills=[],
        resume_text=text
    )
    
    request = ResumeScoreRequest(job_id=job_id, resume=resume_data)
    return score_candidate(request)