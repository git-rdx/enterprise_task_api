from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO, nullable=False)

    priority: Mapped[TaskPriority] = mapped_column(
        default=TaskPriority.MEDIUM, nullable=False
    )

    assignee_id: Mapped[int | None] = mapped_column(  # task.assignee_id -> returns user
        ForeignKey("users.id"), nullable=True, index=True
    )

    project_id: Mapped[int] = mapped_column(  # task.project_id -> returns project
        ForeignKey("projects.id"), nullable=False, index=True
    )

    project: Mapped["Project"] = relationship(  # task.project -> returns project
        back_populates="tasks"
    )

    assignee: Mapped["User | None"] = relationship(  # task.assignee -> returns user
        back_populates="assigned_tasks"
    )

    # Indexes for optimizing queries based on project_id and status/priority
    __table_args__ = (
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_project_priority", "project_id", "priority"),
    )
