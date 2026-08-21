from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_permission
from app.dependencies.database import get_db
from app.dependencies.permissions import Permission
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import user_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Annotated[Session, Depends(get_db)]):

    return user_service.create_user(db, user_data)


@router.get("/", response_model=list[UserResponse])
def get_users(db: Annotated[Session, Depends(get_db)]):

    return user_service.get_all_users(db)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: Annotated[User, Depends(get_current_user)]):

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):

    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, user_data: UserUpdate, db: Annotated[Session, Depends(get_db)]
):

    return user_service.update_user(db, user_id, user_data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    current_user: Annotated[User, Depends(require_permission(Permission.USER_DELETE))],
):

    user_service.delete_user(db, user_id)

    return None
