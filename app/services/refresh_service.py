from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, generate_secure_token, hash_token
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.user_repository import user_repository


class RefreshService:
    def refresh(self, db: Session, raw_token: str):

        token_hash = hash_token(raw_token)

        stored_token = refresh_token_repository.get_by_hash(db, token_hash)

        if not stored_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        now = datetime.now(timezone.utc)

        # Detect reuse of an already-rotated token
        if stored_token.revoked_at is not None:
            if stored_token.replaced_by is not None:
                refresh_token_repository.revoke_family(db, stored_token.family_id)

                db.commit()

                raise HTTPException(
                    status_code=401, detail="Refresh token reuse detected"
                )

            raise HTTPException(status_code=401, detail="Refresh token revoked")

        if stored_token.expires_at <= now:
            raise HTTPException(status_code=401, detail="Refresh token expired")

        user = user_repository.get_by_id(db, stored_token.user_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        new_raw_token = generate_secure_token(64)

        new_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_raw_token),
            family_id=stored_token.family_id,
            expires_at=(now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)),
            created_at=now,
        )

        db.add(new_token)

        db.flush()

        stored_token.revoked_at = now
        stored_token.replaced_by = new_token.id

        db.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_raw_token,
            "token_type": "bearer",
        }


refresh_service = RefreshService()
