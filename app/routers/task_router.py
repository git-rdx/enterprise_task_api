from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_permission
from app.dependencies.database import get_db
from app.dependencies.permissions import Permission
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    data: TaskCreate,
    current_user: Annotated[User, Depends(require_permission(Permission.TASK_CREATE))],
    db: Annotated[Session, Depends(get_db)],
):

    return task_service.create_task(db, project_id, data, current_user)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    assignee_id: Annotated[int | None, Query(ge=1)] = None,
    search: Annotated[str | None, Query()] = None,
):

    return task_service.list_tasks(
        db,
        project_id,
        current_user,
        page,
        page_size,
        status,
        priority,
        assignee_id,
        search,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    return task_service.get_task(db, project_id, task_id, current_user)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    current_user: Annotated[User, Depends(require_permission(Permission.TASK_UPDATE))],
    db: Annotated[Session, Depends(get_db)],
):

    return task_service.update_task(db, project_id, task_id, data, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(require_permission(Permission.TASK_DELETE))],
    db: Annotated[Session, Depends(get_db)],
):

    task_service.delete_task(db, project_id, task_id, current_user)
