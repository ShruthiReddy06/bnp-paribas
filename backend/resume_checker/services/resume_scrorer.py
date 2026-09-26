from typing import Any

from .resume_parser import ResumeData


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def normalize(value: str) -> str:
    """
    Normalize text so comparisons are case-insensitive
    and punctuation differences are less important.
    """
    value = value.lower().strip()

    replacements = {
        "-": " ",
        "_": " ",
        "/": " ",
        "(": " ",
        ")": " ",
        ",": " ",
        ".": " ",
        "+": " plus ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return " ".join(value.split())


# ---------------------------------------------------------
# Requirement parsing
# ---------------------------------------------------------

def extract_alternatives(requirement: str) -> list[str]:
    """
    Extract alternative skills from requirements such as:

        FastAPI or Flask or Django

    and:

        SQL (PostgreSQL / MySQL)

    Returns the actual alternatives that can satisfy the
    requirement.
    """

    text = requirement.strip()

    # Example:
    # SQL (PostgreSQL / MySQL)
    if "(" in text and ")" in text:
        prefix = text.split("(", 1)[0].strip()
        inside = text.split("(", 1)[1].split(")", 1)[0]

        alternatives = []

        if prefix:
            alternatives.append(prefix)

        for part in inside.replace("/", "|").split("|"):
            part = part.strip()
            if part:
                alternatives.append(part)

        return alternatives

    # Example:
    # FastAPI or Flask or Django
    if " or " in text.lower():
        return [
            part.strip()
            for part in text.lower().split(" or ")
            if part.strip()
        ]

    # Example:
    # JUnit / pytest
    if "/" in text:
        return [
            part.strip()
            for part in text.split("/")
            if part.strip()
        ]

    return [text]


# ---------------------------------------------------------
# Version-aware matching
# ---------------------------------------------------------

def matches_python_version(required: str, resume_text: str) -> bool:
    """
    Handle requirements such as Python 3.9+.

    A resume mentioning Python without a specific version is
    accepted as evidence of Python. If a version is present,
    known Python 3.x versions are checked.
    """
    required_normalized = normalize(required)
    resume_normalized = normalize(resume_text)

    if "python 3 9 plus" not in required_normalized:
        return False

    if "python" not in resume_normalized:
        return False

    # Python is mentioned without a version.
    if "python 3" not in resume_normalized:
        return True

    versions = [
        "python 3 9",
        "python 3 10",
        "python 3 11",
        "python 3 12",
        "python 3 13",
        "python 3 14",
    ]

    return any(version in resume_normalized for version in versions)


# ---------------------------------------------------------
# Related technical terminology
# ---------------------------------------------------------

SKILL_EQUIVALENTS = {
    "rest api design": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "restful web services",
        "building rest apis",
        "developing rest apis",
    ],
    "unit testing": [
        "unit testing",
        "unit tests",
        "pytest",
        "unittest",
    ],
    "object oriented programming": [
        "object oriented programming",
        "object oriented design",
        "object oriented development",
        "oop",
    ],
    "continuous integration": [
        "continuous integration",
        "ci cd",
        "github actions",
        "jenkins",
    ],
}


def related_skill_matches(
    required_skill: str,
    resume_skills: list[str],
    resume_text: str,
) -> bool:
    """
    Match a requirement against related technical terminology.

    This is still a deterministic terminology layer.
    It is not an LLM or embedding model.
    """

    required = normalize(required_skill)

    candidate_text = normalize(
        " ".join(resume_skills) + " " + resume_text
    )

    alternatives = SKILL_EQUIVALENTS.get(required, [])

    return any(
        normalize(term) in candidate_text
        for term in alternatives
    )


# ---------------------------------------------------------
# Single skill matching
# ---------------------------------------------------------

def single_skill_matches(
    required_skill: str,
    resume_skills: list[str],
    resume_text: str,
) -> bool:

    required = normalize(required_skill)

    normalized_resume_skills = [
        normalize(skill)
        for skill in resume_skills
    ]

    normalized_resume_text = normalize(resume_text)

    # Version-aware requirement
    if matches_python_version(
        required_skill,
        resume_text,
    ):
        return True

    # Direct structured-skill match
    for skill in normalized_resume_skills:
        if required == skill:
            return True

        if required in skill:
            return True

        if skill in required:
            return True

    # Direct resume-text match
    if required in normalized_resume_text:
        return True

    # Related terminology match
    if related_skill_matches(
        required_skill,
        resume_skills,
        resume_text,
    ):
        return True

    return False


# ---------------------------------------------------------
# Requirement matching
# ---------------------------------------------------------

def skill_matches(
    required_skill: str,
    resume_skills: list[str],
    resume_text: str,
) -> bool:
    """
    Determine whether a JD requirement is satisfied.

    Supports:
    - Direct skills
    - OR requirements
    - Slash-separated alternatives
    - Parenthesized alternatives
    - Version-aware requirements
    - Related technical terminology
    """

    alternatives = extract_alternatives(required_skill)

    for alternative in alternatives:
        if single_skill_matches(
            alternative,
            resume_skills,
            resume_text,
        ):
            return True

    # Check the complete requirement for terminology matches.
    if related_skill_matches(
        required_skill,
        resume_skills,
        resume_text,
    ):
        return True

    return False


# ---------------------------------------------------------
# Skill scoring
# ---------------------------------------------------------

def calculate_skill_score(
    must_have: list[str],
    nice_to_have: list[str],
    resume: ResumeData,
) -> tuple[float, list[str], list[str], list[str]]:
    """
    Calculate skill matching score.

    Must-have requirements: 70 points
    Nice-to-have requirements: 30 points
    """

    matched_must_have = []
    missing_must_have = []

    for requirement in must_have:
        if skill_matches(
            requirement,
            resume.skills,
            resume.resume_text,
        ):
            matched_must_have.append(requirement)
        else:
            missing_must_have.append(requirement)

    matched_nice_to_have = []

    for requirement in nice_to_have:
        if skill_matches(
            requirement,
            resume.skills,
            resume.resume_text,
        ):
            matched_nice_to_have.append(requirement)

    if must_have:
        must_have_score = (
            len(matched_must_have) / len(must_have)
        ) * 70
    else:
        must_have_score = 70

    if nice_to_have:
        nice_to_have_score = (
            len(matched_nice_to_have) / len(nice_to_have)
        ) * 30
    else:
        nice_to_have_score = 30

    skill_score = must_have_score + nice_to_have_score

    return (
        skill_score,
        matched_must_have,
        missing_must_have,
        matched_nice_to_have,
    )


# ---------------------------------------------------------
# Experience scoring
# ---------------------------------------------------------

def calculate_experience_score(
    required_experience: float,
    candidate_experience: float,
) -> tuple[float, bool]:

    if required_experience <= 0:
        return 15.0, True

    if candidate_experience >= required_experience:
        return 15.0, True

    experience_ratio = (
        candidate_experience / required_experience
    )

    score = experience_ratio * 15

    return score, False


# ---------------------------------------------------------
# Education scoring
# ---------------------------------------------------------

def calculate_education_score(
    required_education: str,
    candidate_education: str,
) -> tuple[float, bool]:

    required = normalize(required_education)
    candidate = normalize(candidate_education)

    education_keywords = [
        "b e",
        "b tech",
        "mca",
        "m tech",
        "b sc",
        "m sc",
    ]

    candidate_has_degree = any(
        keyword in candidate
        for keyword in education_keywords
    )

    related_field = (
        "computer science" in candidate
        or "computer engineering" in candidate
        or "information technology" in candidate
    )

    if (
        (
            "computer science" in required
            or "related field" in required
        )
        and candidate_has_degree
        and related_field
    ):
        return 10.0, True

    return 0.0, False


# ---------------------------------------------------------
# Location scoring
# ---------------------------------------------------------

def calculate_location_score(
    required_location: str,
    candidate_location: str,
) -> tuple[float, bool]:

    if not required_location:
        return 5.0, True

    matched = (
        normalize(required_location)
        == normalize(candidate_location)
    )

    return (
        5.0 if matched else 0.0,
        matched,
    )


# ---------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------

def score_resume(
    job: dict[str, Any],
    resume: ResumeData,
) -> dict[str, Any]:
    """
    Main resume scoring function.

    Current baseline scoring:
        Skills       -> 70 points
        Experience   -> 15 points
        Education    -> 10 points
        Location     -> 5 points

    This is the deterministic baseline. A true semantic/LLM
    layer can be added later without changing the API contract.
    """

    (
        skill_score,
        matched_must_have,
        missing_must_have,
        matched_nice_to_have,
    ) = calculate_skill_score(
        job.get("must_have", []),
        job.get("nice_to_have", []),
        resume,
    )

    experience_score, experience_match = (
        calculate_experience_score(
            job.get("experience_years", 0),
            resume.experience_years,
        )
    )

    education_score, education_match = (
        calculate_education_score(
            job.get("education", ""),
            resume.education,
        )
    )

    location_score, location_match = (
        calculate_location_score(
            job.get("location", ""),
            resume.location,
        )
    )

    total_score = (
        skill_score
        + experience_score
        + education_score
        + location_score
    )

    total_score = round(
        min(total_score, 100),
        2,
    )

    return {
        "score": total_score,
        "matched_skills": matched_must_have,
        "missing_skills": missing_must_have,
        "nice_to_have_matches": matched_nice_to_have,
        "experience_match": experience_match,
        "education_match": education_match,
        "location_match": location_match,
        "breakdown": {
            "skills": round(skill_score, 2),
            "experience": round(experience_score, 2),
            "education": round(education_score, 2),
            "location": round(location_score, 2),
        },
    }