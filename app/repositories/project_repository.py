from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


class ProjectRepository:
    def create(self, db: Session, project: Project) -> Project:

        try:
            db.add(project)
            db.commit()
            db.refresh(project)

            return project

        except Exception:
            db.rollback()
            raise

    def get_by_id(self, db: Session, project_id: int) -> Project | None:

        statement = select(Project).where(Project.id == project_id)

        return db.scalar(statement)

    def list_projects(
        self,
        db: Session,
        user_id: int,
        is_admin: bool,
        page: int,
        page_size: int,
    ):
        statement = select(Project)

        if not is_admin:
            statement = statement.where(
                or_(
                    Project.owner_id == user_id, Project.members.any(User.id == user_id)
                )
            )

        offset = (page - 1) * page_size

        statement = (
            statement.order_by(Project.id.desc()).offset(offset).limit(page_size)
        )

        count_statement = select(func.count()).select_from(Project)

        if not is_admin:
            count_statement = count_statement.where(
                or_(
                    Project.owner_id == user_id, Project.members.any(User.id == user_id)
                )
            )

        total = db.scalar(count_statement) or 0

        return {
            "items": list(db.scalars(statement).all()),
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def update(self, db: Session, project: Project) -> Project:

        try:
            db.commit()
            db.refresh(project)

            return project

        except Exception:
            db.rollback()
            raise

    def delete(self, db: Session, project: Project) -> None:

        try:
            db.delete(project)
            db.commit()

        except Exception:
            db.rollback()
            raise


project_repository = ProjectRepository()
