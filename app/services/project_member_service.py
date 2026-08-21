from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import increment_cache_version
from app.dependencies.authorization import (
    check_project_access,
    check_project_management_access,
)
from app.models.user import User
from app.repositories.project_member_repository import (
    project_member_repository,
)


class ProjectMemberService:
    def add_member(
        self, db: Session, project_id: int, user_id: int, current_user: User
    ):

        project = project_member_repository.get_project(db, project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # User must have access to the project
        check_project_management_access(project, current_user)

        user = project_member_repository.get_user(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user in project.members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a project member",
            )

        project_member_repository.add_member(db, project, user)

        increment_cache_version("projects:version")

        return user

    def remove_member(
        self, db: Session, project_id: int, user_id: int, current_user: User
    ):

        project = project_member_repository.get_project(db, project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        check_project_management_access(project, current_user)

        user = project_member_repository.get_user(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user not in project.members:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a project member",
            )

        # Don't allow removing the project owner
        if user.id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project owner cannot be removed",
            )

        project_member_repository.remove_member(db, project, user)

        increment_cache_version("projects:version")

        return {"message": "Project member removed successfully"}

    def get_members(self, db: Session, project_id: int, current_user: User):

        project = project_member_repository.get_project(db, project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        check_project_access(project, current_user)

        return project_member_repository.get_members(db, project_id)


project_member_service = ProjectMemberService()
