from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken


class EmailVerificationRepository:
    def create(
        self, db: Session, token: EmailVerificationToken
    ) -> EmailVerificationToken:

        try:
            db.add(token)
            db.commit()
            db.refresh(token)

            return token

        except Exception:
            db.rollback()
            raise

    def get_by_hash(
        self, db: Session, token_hash: str
    ) -> EmailVerificationToken | None:

        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )

        return db.scalar(statement)

    def update(
        self, db: Session, token: EmailVerificationToken
    ) -> EmailVerificationToken:

        try:
            db.commit()
            db.refresh(token)

            return token

        except Exception:
            db.rollback()
            raise


email_verification_repository = EmailVerificationRepository()
