from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.project_member import ProjectMemberListResponse, ProjectMemberResponse
from app.services.project_member_service import project_member_service

router = APIRouter(prefix="/projects/{project_id}/members", tags=["Project Members"])


@router.post(
    "/{user_id}",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    project_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    return project_member_service.add_member(db, project_id, user_id, current_user)


@router.get("", response_model=ProjectMemberListResponse)
def get_project_members(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    members = project_member_service.get_members(db, project_id, current_user)

    return {"items": members}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    project_member_service.remove_member(db, project_id, user_id, current_user)

    return None
