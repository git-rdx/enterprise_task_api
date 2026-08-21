from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    def create(self, db: Session, token: PasswordResetToken) -> PasswordResetToken:

        try:
            db.add(token)
            db.commit()
            db.refresh(token)

            return token

        except Exception:
            db.rollback()
            raise

    def get_by_hash(self, db: Session, token_hash: str) -> PasswordResetToken | None:

        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )

        return db.scalar(statement)

    def mark_as_used(
        self, db: Session, token: PasswordResetToken
    ) -> PasswordResetToken:

        token.used_at = datetime.now(timezone.utc)

        try:
            db.commit()
            db.refresh(token)

            return token

        except Exception:
            db.rollback()
            raise


password_reset_repository = PasswordResetRepository()
