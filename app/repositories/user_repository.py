from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:

        statement = select(User).where(User.id == user_id)

        return db.scalars(statement).first()

    def get_by_email(self, db: Session, email: str) -> User | None:

        statement = select(User).where(User.email == email)

        return db.scalars(statement).first()

    def get_all(self, db: Session) -> list[User]:

        statement = select(User)

        return list(db.scalars(statement).all())

    def create(self, db: Session, user: User) -> User:

        try:
            db.add(user)
            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            raise

    def update(self, db: Session, user: User) -> User:

        try:
            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            raise

    def delete(self, db: Session, user: User) -> None:

        try:
            db.delete(user)
            db.commit()

        except Exception:
            db.rollback()
            raise


user_repository = UserRepository()
