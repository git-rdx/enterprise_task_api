from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.oauth import create_google_oauth_transaction
from app.core.security import create_access_token, generate_secure_token, hash_token
from app.models.oauth_account import OAuthAccount
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.oauth_account_repository import oauth_account_repository
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.user_repository import user_repository

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleOAuthService:
    def exchange_code(self, code: str, code_verifier: str) -> dict:

        response = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
                # PKCE
                "code_verifier": code_verifier,
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Failed to exchange Google authorization code"),
            )

        return response.json()

    def verify_id_token(self, raw_id_token: str, expected_nonce: str) -> dict:

        try:
            id_info = id_token.verify_oauth2_token(
                raw_id_token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token",
            )

        received_nonce = id_info.get("nonce")

        if received_nonce != expected_nonce:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google OAuth nonce",
            )

        return id_info

    def _issue_app_tokens(self, db: Session, user: User):

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        raw_refresh_token = generate_secure_token(64)

        now = datetime.now(timezone.utc)

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            family_id=uuid4(),
            expires_at=(now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)),
            created_at=now,
        )

        refresh_token_repository.create(db, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
        }

    def login_or_create_user(self, db: Session, google_identity: dict):
        google_id = google_identity.get("sub")
        email = google_identity.get("email")
        name = google_identity.get("name") or "Google User"
        email_verified = google_identity.get("email_verified")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Incomplete Google identity")

        if email_verified is not True:
            raise HTTPException(status_code=400, detail="Google email is not verified")

        # --------------------------------
        # 1. Is this Google account
        #    already linked?
        # --------------------------------

        oauth_account = oauth_account_repository.get_by_provider_account_id(
            db, "google", google_id
        )

        if oauth_account:
            user = user_repository.get_by_id(db, oauth_account.user_id)

            if not user:
                raise HTTPException(status_code=404, detail="Linked user not found")

            return self._issue_app_tokens(db, user)

        # --------------------------------
        # 2. Does a LOCAL account already
        #    exist with this email?
        # --------------------------------

        existing_user = user_repository.get_by_email(db, email)

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An account with this email already exists. "
                    "Login with your existing account and "
                    "link Google from your account."
                ),
            )

        # --------------------------------
        # 3. Completely new Google user
        # --------------------------------

        user = User(name=name, email=email, password_hash=None, is_verified=True)

        user = user_repository.create(db, user)

        oauth_account = OAuthAccount(
            user_id=user.id, provider="google", provider_account_id=google_id
        )

        oauth_account_repository.create(db, oauth_account)

        return self._issue_app_tokens(db, user)

    def create_link_url(self, current_user: User):

        transaction = create_google_oauth_transaction(
            flow="link", user_id=current_user.id
        )

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": transaction["state"],
            "nonce": transaction["nonce"],
            "code_challenge": transaction["code_challenge"],
            "code_challenge_method": "S256",
            # Useful for explicit linking
            "prompt": "select_account",
        }

        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

        return url

    def link_account(self, db: Session, user_id: int, google_identity: dict):

        google_id = google_identity.get("sub")

        if not google_id:
            raise HTTPException(status_code=400, detail="Google account ID missing")

        user = user_repository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_google_account = oauth_account_repository.get_by_user_and_provider(
            db, user.id, "google"
        )

        if current_google_account:
            if current_google_account.provider_account_id == google_id:
                raise HTTPException(
                    status_code=409, detail=("Google account is already linked")
                )

            raise HTTPException(
                status_code=409,
                detail=("A different Google account is already linked to this user"),
            )

        existing_google_account = oauth_account_repository.get_by_provider_account_id(
            db, "google", google_id
        )

        if existing_google_account:
            if existing_google_account.user_id == user.id:
                raise HTTPException(
                    status_code=409, detail="Google account is already linked"
                )

            raise HTTPException(
                status_code=409,
                detail=("Google account is already linked to another user"),
            )

        oauth_account = OAuthAccount(
            user_id=user.id, provider="google", provider_account_id=google_id
        )

        oauth_account_repository.create(db, oauth_account)

        return {"message": "Google account linked successfully"}

    def unlink_google_account(self, db: Session, current_user: User):

        oauth_account = oauth_account_repository.get_by_user_and_provider(
            db, current_user.id, "google"
        )

        if not oauth_account:
            raise HTTPException(status_code=404, detail="Google account is not linked")

        # Don't lock a Google-only user out
        if current_user.password_hash is None:
            raise HTTPException(
                status_code=400, detail=("Set a password before unlinking Google")
            )

        oauth_account_repository.delete(db, oauth_account)

        return {"message": "Google account unlinked successfully"}


google_oauth_service = GoogleOAuthService()
