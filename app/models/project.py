from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.project_member import project_members

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[int] = mapped_column(  # project.owner_id -> returns user
        ForeignKey("users.id"), nullable=False, index=True
    )

    tasks: Mapped[list["Task"]] = relationship(  # project.tasks -> returns tasks
        back_populates="project", cascade="all, delete-orphan"
    )

    members: Mapped[list["User"]] = relationship(  # project.members -> returns users
        secondary=project_members, back_populates="projects"
    )
