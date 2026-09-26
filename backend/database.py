"""Small SQLite-backed data store for the SmartHire prototype."""

import hashlib
import json
import secrets
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("smarthire.db")

DEFAULT_USERS = {
    "team06": {"password": "06", "role": "admin"},
    "candidate1": {"password": "cand123", "role": "candidate"},
    "interviewer1": {"password": "int123", "role": "interviewer"},
}

DEFAULT_JOB_POSTINGS = [
    {"title": "Frontend Developer", "description": "Build thoughtful interfaces for our next generation of products.", "location": "Bengaluru", "type": "Full-time"},
    {"title": "Python Developer", "description": "Design reliable services and APIs that power the hiring platform.", "location": "Hyderabad", "type": "Full-time"},
    {"title": "Product Designer", "description": "Shape simple, human workflows for candidates and hiring teams.", "location": "Remote", "type": "Full-time"},
]


def _password_hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()


def initialize_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'candidate', 'interviewer'))
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_postings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                type TEXT NOT NULL,
                experience_years REAL NOT NULL DEFAULT 0,
                education TEXT NOT NULL DEFAULT '',
                must_have TEXT NOT NULL DEFAULT '[]',
                nice_to_have TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                job_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                UNIQUE(username, job_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'Ready',
                score REAL,
                answers TEXT,
                performance TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL UNIQUE,
                interviewer_username TEXT NOT NULL,
                scheduled_at TEXT,
                candidate_confirmed INTEGER NOT NULL DEFAULT 0,
                interviewer_confirmed INTEGER NOT NULL DEFAULT 0,
                decision TEXT,
                feedback TEXT
            )
            """
        )
        test_columns = {row[1] for row in connection.execute("PRAGMA table_info(candidate_tests)")}
        if "answers" not in test_columns:
            connection.execute("ALTER TABLE candidate_tests ADD COLUMN answers TEXT")
        if "performance" not in test_columns:
            connection.execute("ALTER TABLE candidate_tests ADD COLUMN performance TEXT")
        connection.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES ('shortlist_threshold', '70')"
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(applications)")}
        if "resume_filename" not in columns:
            connection.execute("ALTER TABLE applications ADD COLUMN resume_filename TEXT")
        if "resume_path" not in columns:
            connection.execute("ALTER TABLE applications ADD COLUMN resume_path TEXT")
        if "score" not in columns:
            connection.execute("ALTER TABLE applications ADD COLUMN score REAL")
        job_columns = {row[1] for row in connection.execute("PRAGMA table_info(job_postings)")}
        if "experience_years" not in job_columns:
            connection.execute("ALTER TABLE job_postings ADD COLUMN experience_years REAL NOT NULL DEFAULT 0")
        if "education" not in job_columns:
            connection.execute("ALTER TABLE job_postings ADD COLUMN education TEXT NOT NULL DEFAULT ''")
        if "must_have" not in job_columns:
            connection.execute("ALTER TABLE job_postings ADD COLUMN must_have TEXT NOT NULL DEFAULT '[]'")
        if "nice_to_have" not in job_columns:
            connection.execute("ALTER TABLE job_postings ADD COLUMN nice_to_have TEXT NOT NULL DEFAULT '[]'")
        for username, user in DEFAULT_USERS.items():
            salt = secrets.token_hex(16)
            connection.execute(
                """
                INSERT OR IGNORE INTO users
                    (username, password_hash, password_salt, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, _password_hash(user["password"], salt), salt, user["role"]),
            )
        if connection.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO job_postings (title, description, location, type) VALUES (?, ?, ?, ?)",
                [(job["title"], job["description"], job["location"], job["type"]) for job in DEFAULT_JOB_POSTINGS],
            )


def get_user(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT username, password_hash, password_salt, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        return None
    return {
        "username": row[0],
        "password_hash": row[1],
        "password_salt": row[2],
        "role": row[3],
    }


def verify_password(password: str, user: dict) -> bool:
    expected = _password_hash(password, user["password_salt"])
    return secrets.compare_digest(expected, user["password_hash"])


def create_user(username: str, password: str, role: str) -> bool:
    salt = secrets.token_hex(16)
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, password_salt, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, _password_hash(password, salt), salt, role),
            )
    except sqlite3.IntegrityError:
        return False
    return True


def delete_user(username: str):
    upload_dir = Path(__file__).with_name("uploads")
    with sqlite3.connect(DB_PATH) as connection:
        user = connection.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            return None
        if user[0] == "admin":
            return "admin"
        resume_paths = [row[0] for row in connection.execute(
            "SELECT resume_path FROM applications WHERE username = ? AND resume_path IS NOT NULL",
            (username,),
        ).fetchall()]
        connection.execute("DELETE FROM applications WHERE username = ?", (username,))
        connection.execute("DELETE FROM users WHERE username = ?", (username,))

    for resume_path in resume_paths:
        stored_file = (upload_dir / resume_path).resolve()
        if stored_file.parent == upload_dir.resolve():
            stored_file.unlink(missing_ok=True)
    return user[0]


def get_shortlist_threshold():
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = 'shortlist_threshold'"
        ).fetchone()
    return float(row[0]) if row else 70.0


def set_shortlist_threshold(threshold: float):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('shortlist_threshold', ?)",
            (str(threshold),),
        )
        connection.execute(
            """
            UPDATE applications
            SET status = CASE WHEN score >= ? THEN 'Shortlisted' ELSE 'Not shortlisted' END
            WHERE score IS NOT NULL
            """,
            (threshold,),
        )
    return threshold


def get_job_postings():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT id, title, description, location, type, experience_years, education, must_have, nice_to_have FROM job_postings ORDER BY id DESC"
        ).fetchall()
    return [
        {"id": row[0], "title": row[1], "description": row[2], "location": row[3], "type": row[4],
         "experience_years": row[5], "education": row[6], "must_have": json.loads(row[7]), "nice_to_have": json.loads(row[8])}
        for row in rows
    ]


def get_job_posting(job_id: int):
    return next((job for job in get_job_postings() if job["id"] == job_id), None)


def create_job_posting(title: str, description: str, location: str, job_type: str, experience_years: float, education: str, must_have: list[str], nice_to_have: list[str]):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO job_postings (title, description, location, type, experience_years, education, must_have, nice_to_have) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (title, description, location, job_type, experience_years, education, json.dumps(must_have), json.dumps(nice_to_have)),
        )
        posting_id = cursor.lastrowid
    return {"id": posting_id, "title": title, "description": description, "location": location, "type": job_type,
            "experience_years": experience_years, "education": education, "must_have": must_have, "nice_to_have": nice_to_have}


def delete_job_posting(job_id: int):
    upload_dir = Path(__file__).with_name("uploads")
    with sqlite3.connect(DB_PATH) as connection:
        job = connection.execute("SELECT id FROM job_postings WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return False
        resume_paths = [row[0] for row in connection.execute(
            "SELECT resume_path FROM applications WHERE job_id = ? AND resume_path IS NOT NULL",
            (job_id,),
        ).fetchall()]
        connection.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        connection.execute("DELETE FROM job_postings WHERE id = ?", (job_id,))

    for resume_path in resume_paths:
        stored_file = (upload_dir / resume_path).resolve()
        if stored_file.parent == upload_dir.resolve():
            stored_file.unlink(missing_ok=True)
    return True


def create_application(username: str, job_id: int, resume_filename: str, resume_path: str, score: float):
    status = "Shortlisted" if score >= get_shortlist_threshold() else "Not shortlisted"
    with sqlite3.connect(DB_PATH) as connection:
        job = connection.execute("SELECT id FROM job_postings WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return None
        try:
            cursor = connection.execute(
                "INSERT INTO applications (username, job_id, resume_filename, resume_path, score, status) VALUES (?, ?, ?, ?, ?, ?)",
                (username, job_id, resume_filename, resume_path, score, status),
            )
        except sqlite3.IntegrityError:
            return False
    return {"id": cursor.lastrowid, "job_id": job_id, "status": status, "resume_filename": resume_filename, "score": score}


def get_applied_job_ids(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT job_id FROM applications WHERE username = ? ORDER BY job_id",
            (username,),
        ).fetchall()
    return [row[0] for row in rows]


def get_applications(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT applications.id, applications.job_id, job_postings.title,
                   job_postings.location, job_postings.type, applications.status,
                   applications.resume_filename, applications.score
            FROM applications
            JOIN job_postings ON job_postings.id = applications.job_id
            WHERE applications.username = ?
            ORDER BY applications.id DESC
            """,
            (username,),
        ).fetchall()
    return [
        {"id": row[0], "job_id": row[1], "job_title": row[2], "location": row[3],
         "type": row[4], "status": row[5], "resume_filename": row[6], "score": row[7]}
        for row in rows
    ]


def get_admin_users():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT username, role FROM users ORDER BY role, username"
        ).fetchall()
    return [{"username": row[0], "role": row[1]} for row in rows]


def get_admin_candidate_pipeline():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT applications.id, applications.username, job_postings.title,
                   applications.status, applications.score
            FROM applications
            JOIN job_postings ON job_postings.id = applications.job_id
            JOIN users ON users.username = applications.username
            WHERE users.role = 'candidate'
            ORDER BY applications.id DESC
            """
        ).fetchall()
    return [
        {"id": row[0], "name": row[1], "jd": row[2], "status": row[3],
         "score": row[4] if row[4] is not None else 0, "decision": None}
        for row in rows
    ]


def get_admin_applications():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT applications.id, applications.username, job_postings.title,
                                     applications.status, applications.resume_filename, applications.score,
                                     candidate_tests.status, candidate_tests.score, candidate_tests.performance,
                                     interviews.id, interviews.interviewer_username, interviews.scheduled_at,
                                     interviews.candidate_confirmed, interviews.interviewer_confirmed,
                                     interviews.decision, interviews.feedback
            FROM applications
            JOIN job_postings ON job_postings.id = applications.job_id
                 LEFT JOIN candidate_tests ON candidate_tests.application_id = applications.id
                                 LEFT JOIN interviews ON interviews.application_id = applications.id
            ORDER BY applications.id DESC
            """
        ).fetchall()
    return [
        {"id": row[0], "username": row[1], "job_title": row[2],
         "status": row[3], "resume_filename": row[4], "score": row[5],
         "test_status": row[6], "test_score": row[7],
         "performance": json.loads(row[8]) if row[8] else None,
         "interview_id": row[9], "interviewer_username": row[10], "scheduled_at": row[11],
         "candidate_confirmed": bool(row[12]) if row[12] is not None else None,
         "interviewer_confirmed": bool(row[13]) if row[13] is not None else None,
         "interview_decision": row[14], "interview_feedback": row[15]}
        for row in rows
    ]


def get_shortlisted_applications(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT applications.id, applications.resume_path, job_postings.title,
                   job_postings.description, job_postings.must_have,
                   job_postings.nice_to_have
            FROM applications
            JOIN job_postings ON job_postings.id = applications.job_id
            WHERE applications.username = ? AND applications.status = 'Shortlisted'
            ORDER BY applications.id DESC
            """,
            (username,),
        ).fetchall()
    return [
        {"application_id": row[0], "resume_path": row[1], "job_title": row[2],
         "job_description": row[3], "must_have": json.loads(row[4]),
         "nice_to_have": json.loads(row[5])}
        for row in rows
    ]


def get_candidate_test(application_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        test = connection.execute(
            "SELECT id, status, score FROM candidate_tests WHERE application_id = ?",
            (application_id,),
        ).fetchone()
        if not test:
            return None
        questions = connection.execute(
            "SELECT payload FROM test_questions WHERE test_id = ? ORDER BY position",
            (test[0],),
        ).fetchall()
    return {"id": test[0], "status": test[1], "score": test[2],
            "questions": [json.loads(row[0]) for row in questions]}


def get_candidate_test_summaries(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT candidate_tests.id, candidate_tests.status, candidate_tests.score,
                   COUNT(test_questions.id)
            FROM candidate_tests
            JOIN applications ON applications.id = candidate_tests.application_id
            LEFT JOIN test_questions ON test_questions.test_id = candidate_tests.id
            WHERE applications.username = ?
            GROUP BY candidate_tests.id
            ORDER BY candidate_tests.id DESC
            """,
            (username,),
        ).fetchall()
    return [{"id": row[0], "status": row[1], "score": row[2], "question_count": row[3]} for row in rows]


def start_candidate_test(username: str, test_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT candidate_tests.id, candidate_tests.status, candidate_tests.score
            FROM candidate_tests
            JOIN applications ON applications.id = candidate_tests.application_id
            WHERE candidate_tests.id = ? AND applications.username = ?
                  AND applications.status = 'Shortlisted'
            """,
            (test_id, username),
        ).fetchone()
        if not row:
            return None
        if row[1] != "Ready":
            return False
        connection.execute("UPDATE candidate_tests SET status = 'Started' WHERE id = ?", (test_id,))
        questions = connection.execute(
            "SELECT payload FROM test_questions WHERE test_id = ? ORDER BY position",
            (test_id,),
        ).fetchall()
    return {"id": row[0], "status": "Started", "score": row[2],
            "questions": [json.loads(question[0]) for question in questions]}


def submit_candidate_test(username: str, test_id: int, answers: dict[str, str]):
    with sqlite3.connect(DB_PATH) as connection:
        test = connection.execute(
            """
            SELECT candidate_tests.id, candidate_tests.status
            FROM candidate_tests
            JOIN applications ON applications.id = candidate_tests.application_id
            WHERE candidate_tests.id = ? AND applications.username = ?
            """,
            (test_id, username),
        ).fetchone()
        if not test:
            return None
        if test[1] != "Started":
            return False
        rows = connection.execute(
            "SELECT payload FROM test_questions WHERE test_id = ? ORDER BY position",
            (test_id,),
        ).fetchall()
        questions = [json.loads(row[0]) for row in rows]
        earned = 0
        maximum = 0
        for question in questions:
            marks = float(question.get("marks", 0))
            maximum += marks
            if question.get("type") == "MCQ" and answers.get(str(question.get("id"))) == question.get("correct_answer"):
                earned += marks
        score = round((earned / maximum) * 100, 2) if maximum else 0
        connection.execute(
            "UPDATE candidate_tests SET status = 'Completed', score = ?, answers = ? WHERE id = ?",
            (score, json.dumps(answers), test_id),
        )
    return {"id": test_id, "status": "Completed", "score": score, "questions": []}


def get_started_test(username: str, test_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT candidate_tests.id, candidate_tests.status
            FROM candidate_tests
            JOIN applications ON applications.id = candidate_tests.application_id
            WHERE candidate_tests.id = ? AND applications.username = ?
            """,
            (test_id, username),
        ).fetchone()
        if not row:
            return None
        if row[1] != "Started":
            return False
        questions = connection.execute(
            "SELECT payload FROM test_questions WHERE test_id = ? ORDER BY position",
            (test_id,),
        ).fetchall()
    return [json.loads(question[0]) for question in questions]


def complete_candidate_test(username: str, test_id: int, answers: dict[str, str], score: float, performance: dict):
    with sqlite3.connect(DB_PATH) as connection:
        owned = connection.execute(
            """
            SELECT candidate_tests.id, candidate_tests.application_id FROM candidate_tests
            JOIN applications ON applications.id = candidate_tests.application_id
            WHERE candidate_tests.id = ? AND applications.username = ? AND candidate_tests.status = 'Started'
            """,
            (test_id, username),
        ).fetchone()
        if not owned:
            return False
        application_status = "Interview" if score > 70 else "Test completed"
        connection.execute(
            "UPDATE candidate_tests SET status = 'Completed', score = ?, answers = ?, performance = ? WHERE id = ?",
            (score, json.dumps(answers), json.dumps(performance), test_id),
        )
        connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (application_status, owned[1]),
        )
    return {"id": test_id, "status": "Completed", "score": score, "questions": []}


def get_interviewer_candidates(interviewer_username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT applications.id, applications.username, job_postings.title,
                   applications.score, interviews.id, interviews.scheduled_at,
                   interviews.candidate_confirmed, interviews.interviewer_confirmed,
                   interviews.decision, interviews.feedback
            FROM applications
            JOIN job_postings ON job_postings.id = applications.job_id
            LEFT JOIN interviews ON interviews.application_id = applications.id
            WHERE applications.status = 'Interview'
              AND (interviews.interviewer_username IS NULL OR interviews.interviewer_username = ?)
            ORDER BY applications.id DESC
            """,
            (interviewer_username,),
        ).fetchall()
    return [
        {"application_id": row[0], "candidate_username": row[1], "job_title": row[2], "resume_score": row[3],
         "interview_id": row[4], "scheduled_at": row[5], "candidate_confirmed": bool(row[6]),
         "interviewer_confirmed": bool(row[7]), "decision": row[8], "feedback": row[9]}
        for row in rows
    ]


def schedule_interview(application_id: int, interviewer_username: str, scheduled_at: str):
    with sqlite3.connect(DB_PATH) as connection:
        eligible = connection.execute(
            "SELECT id FROM applications WHERE id = ? AND status = 'Interview'",
            (application_id,),
        ).fetchone()
        if not eligible:
            return None
        connection.execute(
            """
            INSERT INTO interviews (application_id, interviewer_username, scheduled_at, interviewer_confirmed)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(application_id) DO UPDATE SET
                interviewer_username = excluded.interviewer_username,
                scheduled_at = excluded.scheduled_at,
                interviewer_confirmed = 1,
                candidate_confirmed = 0
            """,
            (application_id, interviewer_username, scheduled_at),
        )
        row = connection.execute(
            "SELECT id, scheduled_at, candidate_confirmed, interviewer_confirmed, decision, feedback FROM interviews WHERE application_id = ?",
            (application_id,),
        ).fetchone()
    return {"interview_id": row[0], "application_id": application_id, "scheduled_at": row[1],
            "candidate_confirmed": bool(row[2]), "interviewer_confirmed": bool(row[3]),
            "decision": row[4], "feedback": row[5]}


def get_candidate_interviews(username: str):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT interviews.id, applications.id, job_postings.title, interviews.interviewer_username,
                   interviews.scheduled_at, interviews.candidate_confirmed, interviews.interviewer_confirmed,
                   interviews.decision, interviews.feedback
            FROM interviews
            JOIN applications ON applications.id = interviews.application_id
            JOIN job_postings ON job_postings.id = applications.job_id
            WHERE applications.username = ?
            ORDER BY interviews.id DESC
            """,
            (username,),
        ).fetchall()
    return [
        {"interview_id": row[0], "application_id": row[1], "job_title": row[2], "interviewer_username": row[3],
         "scheduled_at": row[4], "candidate_confirmed": bool(row[5]), "interviewer_confirmed": bool(row[6]),
         "decision": row[7], "feedback": row[8]}
        for row in rows
    ]


def confirm_interview(username: str, interview_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT interviews.id FROM interviews
            JOIN applications ON applications.id = interviews.application_id
            WHERE interviews.id = ? AND applications.username = ?
            """,
            (interview_id, username),
        ).fetchone()
        if not row:
            return None
        connection.execute("UPDATE interviews SET candidate_confirmed = 1 WHERE id = ?", (interview_id,))
    return True


def submit_interview_decision(interview_id: int, interviewer_username: str, decision: str, feedback: str):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT application_id FROM interviews WHERE id = ? AND interviewer_username = ?",
            (interview_id, interviewer_username),
        ).fetchone()
        if not row:
            return None
        connection.execute(
            "UPDATE interviews SET decision = ?, feedback = ? WHERE id = ?",
            (decision, feedback, interview_id),
        )
        connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (decision, row[0]),
        )
    return True


def create_candidate_test(application_id: int, questions: list[dict]):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO candidate_tests (application_id) VALUES (?)",
            (application_id,),
        )
        test_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO test_questions (test_id, position, payload) VALUES (?, ?, ?)",
            [(test_id, position, json.dumps(question)) for position, question in enumerate(questions)],
        )
    return {"id": test_id, "status": "Ready", "score": None, "questions": questions}


initialize_database()

CANDIDATES = [
    {"id": 1, "name": "Asha Rao", "jd": "Frontend Developer", "status": "Screening", "score": 82, "decision": None},
    {"id": 2, "name": "Vikram Shah", "jd": "Python Developer", "status": "Passed", "score": 91, "decision": None},
    {"id": 3, "name": "Meera Iyer", "jd": "Java Backend Developer", "status": "Hold", "score": 68, "decision": None},
]

# The logged-in candidate's own status (hardcoded for "candidate1")
CANDIDATE_STATUS = {
    "status": "Interview-Scheduled",
    "jd": "Frontend Developer",
    "interviewer_name": "Rahul Mehta",
    "interview_date": "2026-10-02",
}

# token -> username (fake session store, not real JWT)
SESSIONS = {}
