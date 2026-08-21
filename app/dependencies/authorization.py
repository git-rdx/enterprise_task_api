from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.permissions import ROLE_PERMISSIONS, Permission
from app.models.user import User, UserRole
from app.repositories.project_repository import project_repository
from app.repositories.task_repository import task_repository


def require_role(*allowed_roles: UserRole):

    def dependency(current_user: Annotated[User, Depends(get_current_user)]):

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return current_user

    return dependency


def require_permission(permission: Permission):

    def dependency(current_user: Annotated[User, Depends(get_current_user)]):

        permissions = ROLE_PERMISSIONS.get(current_user.role, set())

        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Permission denied")

        return current_user

    return dependency


def check_project_access(project, current_user):

    if current_user.role == UserRole.ADMIN:
        return True

    if project.owner_id == current_user.id:
        return True

    if current_user in project.members:
        return True

    raise HTTPException(status_code=403, detail="You cannot access this project")


def check_project_management_access(project, current_user):
    if current_user.role == UserRole.ADMIN:
        return True

    if project.owner_id == current_user.id:
        return True

    raise HTTPException(
        status_code=403, detail="Only project owner or admin can manage members"
    )


def check_task_update_access(task, project, current_user):

    if current_user.role == UserRole.ADMIN:
        return True

    if current_user.role == UserRole.MANAGER:
        if project.owner_id == current_user.id:
            return True

        if current_user in project.members:
            return True

    if current_user.role == UserRole.EMPLOYEE and task.assignee_id == current_user.id:
        return True

    raise HTTPException(status_code=403, detail="You cannot update this task")


def check_task_delete_access(project, current_user):

    if current_user.role == UserRole.ADMIN:
        return True

    if current_user.role == UserRole.MANAGER:
        if project.owner_id == current_user.id:
            return True

        if current_user in project.members:
            return True

    raise HTTPException(status_code=403, detail="You cannot delete this task")


def check_file_access(db: Session, file, current_user):

    if file.project_id is not None:
        project = project_repository.get_by_id(db, file.project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        return

    if file.task_id is not None:
        task = task_repository.get_by_id(db, file.task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        project = project_repository.get_by_id(db, task.project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        return

    # File is not attached to a project/task.
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot access this file")
