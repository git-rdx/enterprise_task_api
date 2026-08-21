from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies.authorization import (
    check_project_access,
    check_task_delete_access,
    check_task_update_access,
)
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.project_repository import project_repository
from app.repositories.task_repository import task_repository
from app.repositories.user_repository import user_repository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def create_task(self, db: Session, project_id: int, data: TaskCreate, current_user):

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        if data.assignee_id is not None:
            assignee = user_repository.get_by_id(db, data.assignee_id)

            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")

            if assignee not in project.members:
                raise HTTPException(
                    status_code=400, detail="User is not a member of this project"
                )

        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            assignee_id=data.assignee_id,
            project_id=project_id,
        )

        return task_repository.create(db, task)

    def get_task(self, db: Session, project_id: int, task_id: int, current_user):

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        task = task_repository.get_by_id_and_project(db, task_id, project_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    def list_tasks(
        self,
        db: Session,
        project_id: int,
        current_user,
        page: int,
        page_size: int,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assignee_id: int | None,
        search: str | None,
    ):

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_project_access(project, current_user)

        return task_repository.list_tasks(
            db, project_id, page, page_size, status, priority, assignee_id, search
        )

    def update_task(
        self, db: Session, project_id: int, task_id: int, data: TaskUpdate, current_user
    ):

        task = self.get_task(db, project_id, task_id, current_user)

        project = project_repository.get_by_id(db, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        check_task_update_access(task, project, current_user)

        update_data = data.model_dump(exclude_unset=True)

        if "assignee_id" in update_data:
            assignee_id = update_data["assignee_id"]

            if assignee_id is not None:
                assignee = user_repository.get_by_id(db, assignee_id)

                if not assignee:
                    raise HTTPException(status_code=404, detail="Assignee not found")

                if assignee not in project.members:
                    raise HTTPException(
                        status_code=400, detail=("User is not a member of this project")
                    )

        for field, value in update_data.items():
            setattr(task, field, value)

        return task_repository.update(db, task)

    def delete_task(self, db: Session, project_id: int, task_id: int, current_user):

        task = self.get_task(db, project_id, task_id, current_user)

        project = project_repository.get_by_id(db, project_id)

        check_task_delete_access(project, current_user)

        task_repository.delete(db, task)


task_service = TaskService()
