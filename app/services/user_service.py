from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def create_user(self, db: Session, user_data: UserCreate) -> User:

        existing_user = user_repository.get_by_email(db, user_data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

        hashed_password = hash_password(user_data.password)

        user = User(
            name=user_data.name, email=user_data.email, password_hash=hashed_password
        )

        try:
            return user_repository.create(db, user)

        except IntegrityError:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

    def get_all_users(self, db: Session) -> list[User]:

        return user_repository.get_all(db)

    def get_user(self, db: Session, user_id: int) -> User:

        user = user_repository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> User:

        user = user_repository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = user_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        return user_repository.update(db, user)

    def delete_user(self, db: Session, user_id: int) -> None:

        user = user_repository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_repository.delete(db, user)


user_service = UserService()
