from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def create(self, db: Session, refresh_token: RefreshToken) -> RefreshToken:

        try:
            db.add(refresh_token)
            db.commit()
            db.refresh(refresh_token)

            return refresh_token

        except Exception:
            db.rollback()
            raise

    def get_by_hash(self, db: Session, token_hash: str) -> RefreshToken | None:

        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)

        return db.scalar(statement)

    def revoke(self, db: Session, refresh_token: RefreshToken) -> RefreshToken:

        refresh_token.revoked_at = datetime.now(timezone.utc)

        try:
            db.commit()
            db.refresh(refresh_token)

            return refresh_token

        except Exception:
            db.rollback()
            raise

    def revoke_family(self, db: Session, family_id):
        statement = select(RefreshToken).where(
            RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
        )

        tokens = db.scalars(statement).all()

        now = datetime.now(timezone.utc)

        for token in tokens:
            token.revoked_at = now

        return tokens

    def update(self, db: Session, refresh_token: RefreshToken) -> RefreshToken:

        try:
            db.commit()
            db.refresh(refresh_token)

            return refresh_token

        except Exception:
            db.rollback()
            raise


refresh_token_repository = RefreshTokenRepository()
