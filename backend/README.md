# SmartHire Backend (basic, modular — no services layer)

Same endpoints and behavior as the single-file version, split into modules
for readability. Business logic still lives directly in the routers since
there's no scoring/LLM logic yet — that's what a `services/` layer would be
for, added later.

## Structure
```
backend/
├── main.py                  # creates app, mounts routers, CORS
├── database.py               # SQLite users table plus prototype candidate data
├── models/                   # plain dataclasses describing each record
│   ├── user.py
│   ├── candidate.py
│   └── interview.py
├── schemas/                  # Pydantic request/response validation
│   ├── auth.py
│   ├── candidate.py
│   └── interview.py
├── auth_utils/
│   ├── token.py               # create_token / resolve_token (fake session)
│   └── dependencies.py        # get_current_user, require_role("admin") etc.
└── routers/
    ├── auth.py                # POST /login, POST /register
    ├── admin.py               # candidates and job posting management
    ├── candidate.py           # status and available job postings
    └── interviewer.py          # GET /interviewer/candidates, POST /interviewer/decision
```

## Setup
```
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on http://localhost:8000

## Test logins
| username     | password  | role        |
|--------------|-----------|-------------|
| admin1       | admin123  | admin       |
| candidate1   | cand123   | candidate   |
| interviewer1 | int123    | interviewer |

New accounts created through `POST /register` are stored in `smarthire.db` beside
this README and remain available after a backend restart. Passwords are stored
as salted PBKDF2 hashes. The built-in demo accounts are seeded on first startup.

Admins can create postings with `POST /admin/jobs`. Candidates receive all
postings from `GET /candidate/jobs` after signing in.

Candidates apply with a PDF, DOC, or DOCX resume smaller than 5 MB. Resume
files are stored in `backend/uploads` and their metadata is saved with the
application record.

## Not included (add later)
- `services/` — resume scoring, answer scoring, LLM client, combined-score logic
- Real JWT (the current token store is still in-memory)
- Audit log
- JD CRUD, Q&A flow
