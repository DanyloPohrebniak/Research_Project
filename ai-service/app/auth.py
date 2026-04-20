import os
import httpx
from fastapi import Header, HTTPException

LMS_URL = os.getenv("LMS_URL", "http://lms:8000")


async def validate_lms_session(
    session_id: str,
    user_id: str
) -> bool:
    """
    Validate user session against Open edX LMS.
    Returns True if session is valid.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LMS_URL}/api/user/v1/me",
                headers={"Cookie": f"sessionid={session_id}"},
                timeout=5.0
            )
            return response.status_code == 200
    except Exception:
        return False


async def get_current_user(
    x_user_id: str = Header(default="anonymous"),
    x_session_id: str = Header(default=""),
) -> dict:
    """
    FastAPI dependency — extracts user from LMS headers.
    In development mode skips validation.
    """
    dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"

    if dev_mode:
        return {"user_id": x_user_id, "session_id": x_session_id}

    if not x_session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    is_valid = await validate_lms_session(x_session_id, x_user_id)
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return {"user_id": x_user_id, "session_id": x_session_id}