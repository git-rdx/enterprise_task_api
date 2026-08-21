from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.cache import (
    delete_cache,
    get_cache,
    get_cache_version,
    increment_cache_version,
    set_cache,
)
from app.dependencies.authorization import check_project_access
from app.models.project import Project
from app.models.user import UserRole
from app.repositories.project_repository import project_repository
from app.repositories.user_repository import user_repository
from app.schemas.project import ProjectUpdate


class ProjectService:
    def create_project(self, db: Session, data, current_user):

        project = Project(
            name=data.name, description=data.description, owner_id=current_user.id
        )

        # Owner is always a project member
        project.members.append(current_user)

        # Add requested members
        for member_id in set(data.member_ids):
            if member_id == current_user.id:
                continue

            user = user_repository.get_by_id(db, member_id)

            if not user:
                raise HTTPException(
                    status_code=404, detail=f"User {member_id} not found"
                )

            project.members.append(user)

        project = project_repository.create(db, project)

        increment_cache_version("projects:version")

        return project

    def get_project(self, db: Session, project_id: int, current_user):

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        return project

    def list_projects(self, db: Session, current_user, page: int, page_size: int):
        version = get_cache_version("projects:version")

        cache_key = (
            f"projects:list:"
            f"user:{current_user.id}:"
            f"v:{version}:"
            f"page:{page}:"
            f"size:{page_size}"
        )

        cached = get_cache(cache_key)

        if cached is not None:
            return cached

        result = project_repository.list_projects(
            db, current_user.id, current_user.role == UserRole.ADMIN, page, page_size
        )

        cache_data = {
            "items": [
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                }
                for project in result["items"]
            ],
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
        }

        set_cache(cache_key, cache_data, ttl=300)

        return cache_data

    def update_project(
        self, db: Session, project_id: int, project_data: ProjectUpdate, current_user
    ) -> Project:

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        update_data = project_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(project, field, value)

        project = project_repository.update(db, project)

        increment_cache_version("projects:version")

        delete_cache(f"project:{project_id}")

        return project

    def delete_project(self, db: Session, project_id: int, current_user) -> None:

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        project_repository.delete(db, project)

        increment_cache_version("projects:version")

        delete_cache(f"project:{project_id}")


project_service = ProjectService()
