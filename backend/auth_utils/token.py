from database import SESSIONS


def create_token(username: str) -> str:
    token = f"token-{username}"
    SESSIONS[token] = username
    return token


def resolve_token(token: str):
    """Returns the username for a token, or None if invalid."""
    return SESSIONS.get(token)
