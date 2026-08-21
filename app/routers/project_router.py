from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_permission
from app.dependencies.database import get_db
from app.dependencies.permissions import Permission
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import project_service

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    current_user: Annotated[
        User, Depends(require_permission(Permission.PROJECT_CREATE))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    return project_service.create_project(db, data, current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return project_service.get_project(db, project_id, current_user)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return project_service.list_projects(db, current_user, page, page_size)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: Annotated[
        User, Depends(require_permission(Permission.PROJECT_UPDATE))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    return project_service.update_project(db, project_id, data, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: Annotated[
        User, Depends(require_permission(Permission.PROJECT_DELETE))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    project_service.delete_project(db, project_id, current_user)
