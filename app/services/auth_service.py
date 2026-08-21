from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.email_verification_repository import (
    email_verification_repository,
)
from app.repositories.password_reset_repository import (
    password_reset_repository,
)
from app.repositories.refresh_token_repository import (
    refresh_token_repository,
)
from app.repositories.user_repository import user_repository
from app.tasks.email_tasks import send_password_reset_email, send_verification_email


class AuthService:
    def register(self, db: Session, name: str, email: str, password: str) -> User:

        existing_user = user_repository.get_by_email(db, email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_verified=False,
        )

        user = user_repository.create(db, user)

        raw_token = generate_secure_token(32)

        token_hash = hash_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

        verification_token = EmailVerificationToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )

        email_verification_repository.create(db, verification_token)

        send_verification_email.delay(user.email, raw_token)

        return user

    def login(self, db: Session, email: str, password: str):

        user = user_repository.get_by_email(db, email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if user.password_hash is None:
            raise HTTPException(
                status_code=401,
                detail=(
                    "This account uses Google sign-in. Please continue with Google."
                ),
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email first",
            )

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        raw_refresh_token = generate_secure_token(64)

        family_id = uuid4()

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            family_id=family_id,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ),
            created_at=datetime.now(timezone.utc),
        )

        refresh_token_repository.create(db, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
        }

    def logout(self, db: Session, raw_token: str):

        token_hash = hash_token(raw_token)

        stored_token = refresh_token_repository.get_by_hash(db, token_hash)

        if stored_token and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(timezone.utc)

            db.commit()

        return {"message": "Logged out successfully"}

    def forgot_password(self, db: Session, email: str):

        user = user_repository.get_by_email(db, email)

        if not user:
            return {
                "message": (
                    "If an account exists for this email, "
                    "a password reset link has been sent."
                )
            }

        raw_token = generate_secure_token(64)

        token_hash = hash_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )

        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )

        password_reset_repository.create(db, reset_token)

        send_password_reset_email.delay(user.email, raw_token)

        return {
            "message": (
                "If an account exists for this email, "
                "a password reset link has been sent."
            )
        }

    def reset_password(self, db: Session, raw_token: str, new_password: str):

        token_hash = hash_token(raw_token)

        reset_token = password_reset_repository.get_by_hash(db, token_hash)

        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid password reset token")

        now = datetime.now(timezone.utc)

        if reset_token.used_at is not None:
            raise HTTPException(
                status_code=400, detail="Password reset token already used"
            )

        if reset_token.expires_at <= now:
            raise HTTPException(status_code=400, detail="Password reset token expired")

        user = user_repository.get_by_id(db, reset_token.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password_hash = hash_password(new_password)

        reset_token.used_at = now

        # Invalidate all refresh sessions
        for refresh_token in user.refresh_tokens:
            if refresh_token.revoked_at is None:
                refresh_token.revoked_at = now

        try:
            db.commit()

        except Exception:
            db.rollback()
            raise

        return {"message": "Password reset successfully"}


auth_service = AuthService()
