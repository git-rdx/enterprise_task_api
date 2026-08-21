from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.task import Task


class TaskRepository:
    def create(self, db: Session, task: Task) -> Task:

        try:
            db.add(task)
            db.commit()
            db.refresh(task)

            return task

        except Exception:
            db.rollback()
            raise

    def get_by_id(self, db: Session, task_id: int) -> Task | None:

        statement = select(Task).where(Task.id == task_id)

        return db.scalar(statement)

    def get_by_id_and_project(
        self, db: Session, task_id: int, project_id: int
    ) -> Task | None:

        statement = select(Task).where(
            Task.id == task_id, Task.project_id == project_id
        )

        return db.scalar(statement)

    def list_tasks(
        self,
        db: Session,
        project_id: int,
        page: int,
        page_size: int,
        status=None,
        priority=None,
        assignee_id: int | None = None,
        search: str | None = None,
    ):

        statement = (
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.project_id == project_id)
        )

        if status is not None:
            statement = statement.where(Task.status == status)

        if priority is not None:
            statement = statement.where(Task.priority == priority)

        if assignee_id is not None:
            statement = statement.where(Task.assignee_id == assignee_id)

        if search:
            statement = statement.where(Task.title.ilike(f"%{search}%"))

        statement = statement.order_by(Task.id.desc())

        offset = (page - 1) * page_size

        statement = statement.offset(offset).limit(page_size)

        count_statement = (
            select(func.count()).select_from(Task).where(Task.project_id == project_id)
        )

        if status is not None:
            count_statement = count_statement.where(Task.status == status)

        if priority is not None:
            count_statement = count_statement.where(Task.priority == priority)

        if assignee_id is not None:
            count_statement = count_statement.where(Task.assignee_id == assignee_id)

        if search:
            count_statement = count_statement.where(Task.title.ilike(f"%{search}%"))

        total = db.scalar(count_statement) or 0

        return {
            "items": list(db.scalars(statement).all()),
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def update(self, db: Session, task: Task) -> Task:

        try:
            db.commit()
            db.refresh(task)

            return task

        except Exception:
            db.rollback()
            raise

    def delete(self, db: Session, task: Task) -> None:

        try:
            db.delete(task)
            db.commit()

        except Exception:
            db.rollback()
            raise


task_repository = TaskRepository()
