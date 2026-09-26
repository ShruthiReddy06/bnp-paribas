from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, admin, candidate, candidate_interviews, interviewer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://[::1]:5174",
        "null",
    ],
     allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(candidate.router)
app.include_router(candidate_interviews.router)
app.include_router(interviewer.router)
