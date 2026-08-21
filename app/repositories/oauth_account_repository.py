from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_account import OAuthAccount


class OAuthAccountRepository:
    def get_by_provider_account_id(
        self, db: Session, provider: str, provider_account_id: str
    ) -> OAuthAccount | None:

        statement = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )

        return db.scalar(statement)

    def get_by_user_and_provider(
        self, db: Session, user_id: int, provider: str
    ) -> OAuthAccount | None:

        statement = select(OAuthAccount).where(
            OAuthAccount.user_id == user_id, OAuthAccount.provider == provider
        )

        return db.scalar(statement)

    def create(self, db: Session, oauth_account: OAuthAccount) -> OAuthAccount:

        db.add(oauth_account)
        db.commit()
        db.refresh(oauth_account)

        return oauth_account

    def delete(self, db: Session, oauth_account: OAuthAccount) -> None:

        try:
            db.delete(oauth_account)
            db.commit()

        except Exception:
            db.rollback()
            raise


oauth_account_repository = OAuthAccountRepository()
