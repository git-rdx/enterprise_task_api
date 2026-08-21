from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.oauth import (
    consume_google_oauth_transaction,
    create_google_oauth_transaction,
)
from app.core.security import hash_token
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.rate_limit import rate_limit
from app.models.user import User
from app.repositories.email_verification_repository import (
    email_verification_repository,
)
from app.repositories.user_repository import user_repository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services.auth_service import auth_service
from app.services.google_oauth_service import google_oauth_service
from app.services.refresh_service import refresh_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):

    auth_service.register(db, data.name, data.email, data.password)

    return {"message": ("Registration successful. Please verify your email.")}


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: Annotated[Session, Depends(get_db)]):

    token_hash = hash_token(token)

    verification_token = email_verification_repository.get_by_hash(db, token_hash)

    if not verification_token:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if verification_token.used_at is not None:
        raise HTTPException(status_code=400, detail="Verification token already used")

    if verification_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token expired")

    user = user_repository.get_by_id(db, verification_token.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True

    verification_token.used_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Email verified successfully"}


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(limit=5, window=60))],
)
def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    return auth_service.login(db, data.email, data.password)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit(limit=3, window=60))],
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):

    return auth_service.forgot_password(db, data.email)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):

    return auth_service.reset_password(db, data.token, data.new_password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(limit=10, window=60))],
)
def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):

    return refresh_service.refresh(db, data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(data: RefreshTokenRequest, db: Annotated[Session, Depends(get_db)]):

    return auth_service.logout(db, data.refresh_token)


@router.get("/google/login")
def google_login():

    transaction = create_google_oauth_transaction(flow="login")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        # CSRF
        "state": transaction["state"],
        # OIDC replay protection
        "nonce": transaction["nonce"],
        # PKCE
        "code_challenge": transaction["code_challenge"],
        "code_challenge_method": "S256",
    }

    google_authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    )

    return RedirectResponse(google_authorization_url)


@router.get("/google/callback")
def google_callback(
    db: Annotated[Session, Depends(get_db)],
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):

    # ---------------------------------
    # 1. Validate + consume transaction
    # ---------------------------------

    transaction = consume_google_oauth_transaction(state)

    # ---------------------------------
    # 2. Google authorization error
    # ---------------------------------

    if error:
        if error == "access_denied":
            raise HTTPException(
                status_code=400, detail=("Google authorization was cancelled")
            )

        raise HTTPException(status_code=400, detail="Google authorization failed")

    if not code:
        raise HTTPException(status_code=400, detail="Google authorization code missing")

    # ---------------------------------
    # 3. Authorization-code exchange
    # ---------------------------------

    token_data = google_oauth_service.exchange_code(code, transaction["code_verifier"])

    google_id_token = token_data.get("id_token")

    if not google_id_token:
        raise HTTPException(status_code=400, detail="Google ID token missing")

    # ---------------------------------
    # 4. Verify ID token + nonce
    # ---------------------------------

    google_identity = google_oauth_service.verify_id_token(
        google_id_token, transaction["nonce"]
    )

    # ---------------------------------
    # 5. LOGIN or LINK
    # ---------------------------------

    if transaction["flow"] == "link":
        return google_oauth_service.link_account(
            db, transaction["user_id"], google_identity
        )

    return google_oauth_service.login_or_create_user(db, google_identity)


@router.get("/google/link")
def google_link(current_user: Annotated[User, Depends(get_current_user)]):

    google_url = google_oauth_service.create_link_url(current_user)

    return RedirectResponse(google_url)


@router.delete("/google/unlink")
def google_unlink(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):

    return google_oauth_service.unlink_google_account(db, current_user)
