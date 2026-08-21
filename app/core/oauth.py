import base64
import hashlib
import json
import secrets

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.core.redis import redis_client

GOOGLE_OAUTH_TTL = 300


def _create_pkce_pair() -> tuple[str, str]:

    code_verifier = secrets.token_urlsafe(64)

    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()

    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")

    return code_verifier, code_challenge


def create_google_oauth_transaction(flow: str, user_id: int | None = None) -> dict:

    if flow not in {"login", "link"}:
        raise ValueError("Invalid OAuth flow")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    code_verifier, code_challenge = _create_pkce_pair()

    data = {
        "flow": flow,
        "user_id": user_id,
        "code_verifier": code_verifier,
        "nonce": nonce,
    }

    key = f"oauth:google:txn:{state}"

    try:
        redis_client.setex(key, GOOGLE_OAUTH_TTL, json.dumps(data))

    except RedisError:
        # OAuth security state should fail closed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth service temporarily unavailable",
        )

    return {"state": state, "nonce": nonce, "code_challenge": code_challenge}


def consume_google_oauth_transaction(state: str) -> dict:

    key = f"oauth:google:txn:{state}"

    try:
        raw_data = redis_client.getdel(key)

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth service temporarily unavailable",
        )

    if raw_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )

    return json.loads(raw_data)
