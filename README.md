# SmartHire

SmartHire is a role-based hiring platform prototype designed to streamline recruitment operations across three user roles: admin, candidate, and interviewer. The application supports job posting, resume-based screening, AI-assisted assessment generation, test execution, and interviewer review in a single workflow.

## Overview

The project is split into two main parts:

- Backend: FastAPI service with SQLite persistence and AI-driven hiring logic
- Frontend: React + Vite single-page app for candidate, admin, and interviewer workflows

This project is intended as a practical prototype for hiring automation and talent operations.

## Key Features

- Candidate registration and login
- Admin job posting and role management
- Resume upload and submission for job applications
- Automatic resume scoring against a job requirement model
- Shortlist threshold configuration
- AI-generated technical assessments using candidate resume context
- Standard fallback assessment generation when AI is unavailable
- Candidate test start/submit flow
- Interviewer assignment and interview scheduling
- Interview decision and feedback workflow
- Role-based route protection for admin, candidate, and interviewer views

## User Roles

### Admin
- Manage job openings
- View candidate pipeline
- Configure shortlist threshold
- Assign interviewers
- Assign tests to shortlisted candidates
- Review application statuses and scores
- Manage user accounts

### Candidate
- Sign up / sign in
- Browse available jobs
- Upload resume
- Track application status
- Start and complete assigned tests
- View results and progression

### Interviewer
- View assigned candidates
- Schedule interviews
- Review candidate evaluation
- Accept or reject candidates with feedback

## Tech Stack

### Backend
- Python
- FastAPI
- SQLite
- Pydantic
- LangChain
- Groq
- FAISS
- sentence-transformers
- PyPDF and python-docx for document parsing

### Frontend
- React
- Vite
- React Router DOM

## Project Structure

```text
bnp-paribas/
├── backend/
│   ├── auth_utils/
│   │   ├── dependencies.py
│   │   └── token.py
│   ├── models/
│   │   ├── candidate.py
│   │   ├── interview.py
│   │   └── user.py
│   ├── questions_generator/
│   │   ├── app.py
│   │   ├── app_backup.py
│   │   ├── offline_assessment.py
│   │   └── rag_pipeline.py
│   ├── resume_checker/
│   │   ├── main.py
│   │   └── services/
│   ├── routers/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── candidate.py
│   │   ├── candidate_interviews.py
│   │   └── interviewer.py
│   ├── schemas/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── candidate.py
│   │   ├── interview.py
│   │   ├── job.py
│   │   └── test.py
│   ├── database.py
│   ├── main.py
│   ├── README.md
│   ├── requirements.txt
│   └── uploads/
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── README.md
│   └── vite.config.js
├── README.md
└── .gitignore
```

## Backend Architecture

The backend is centered around a FastAPI application that exposes role-specific routes:

- `main.py` initializes the app and includes each router
- `database.py` contains the SQLite schema, seed data, and database logic
- `routers/` contains the API endpoints by role
- `auth_utils/` handles token validation and role enforcement
- `resume_checker/` performs resume parsing and matching
- `questions_generator/` creates AI-powered interview questions and evaluates descriptive answers

## Frontend Architecture

The frontend uses route-based role access:

- `App.jsx` defines protected routes for admin, candidate, and interviewer screens
- `LoginPage.jsx` handles sign in and sign up
- `AuthContext` stores the active user session and token
- Dashboard pages are separated by role and organized in `pages/`
- Shared components live in `components/`

## Default Accounts

The application seeds demo users on first run:

| Username | Password | Role |
| --- | --- | --- |
| admin1 | admin123 | admin |
| candidate1 | cand123 | candidate |
| interviewer1 | int123 | interviewer |
| interviewer2 | int123 | interviewer |

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd bnp-paribas
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will run on:

```text
http://localhost:8000
```

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

## Environment Variables

For AI-based test generation, create a `backend/.env` file if needed:

```env
GROQ_API_KEY=your_key_here
```

When a Groq API key is present, the platform can generate AI interview questions; otherwise, it falls back to a standard assessment.

## Resume Upload Rules

Candidates can upload resumes in the following formats:

- PDF
- DOC
- DOCX

Maximum file size: 5 MB

## AI Question Generation

The question generation pipeline in `backend/questions_generator/rag_pipeline.py`:

- loads the resume document
- creates a vector store from resume content
- retrieves relevant context based on the job description
- generates personalized interview questions with a required difficulty mix
- validates JSON output for question structure and counts
- evaluates descriptive answers using an LLM-based rubric

## Notes and Limitations

This is a prototype application intended for demonstration and local development. Some simplifications are present, including:

- lightweight token handling rather than full production JWT management
- SQLite instead of a full enterprise database setup
- minimal frontend styling and limited production polish
- route logic and data access still combined in parts of the backend

## Suggested Next Enhancements

- Add proper JWT authentication and refresh tokens
- Introduce a dedicated service layer for business logic
- Add unit and integration testing
- Expand analytics dashboards for recruiters
- Add improved admin reporting and audit control
- Add notifications and email workflows
- Improve resume parsing and scoring accuracy

## License

This project is provided for educational and prototype use.

## Contributing

Contributions are welcome. For improvements, create a feature branch, make your changes, and open a pull request with a clear summary of the update.
