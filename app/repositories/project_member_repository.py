from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


class ProjectMemberRepository:
    def get_user(self, db: Session, user_id: int) -> User | None:

        statement = select(User).where(User.id == user_id)

        return db.scalar(statement)

    def get_project(self, db: Session, project_id: int) -> Project | None:

        statement = select(Project).where(Project.id == project_id)

        return db.scalar(statement)

    def add_member(self, db: Session, project: Project, user: User) -> Project:

        project.members.append(user)

        try:
            db.commit()
            db.refresh(project)

            return project

        except Exception:
            db.rollback()
            raise

    def remove_member(self, db: Session, project: Project, user: User) -> Project:

        project.members.remove(user)

        try:
            db.commit()
            db.refresh(project)

            return project

        except Exception:
            db.rollback()
            raise

    def get_members(self, db: Session, project_id: int) -> list[User]:

        project = self.get_project(db, project_id)

        if not project:
            return []

        return project.members


project_member_repository = ProjectMemberRepository()
