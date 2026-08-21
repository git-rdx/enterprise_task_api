from enum import Enum

from app.models.user import UserRole


class Permission(str, Enum):
    USER_CREATE = "user:create"
    USER_DELETE = "user:delete"

    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"


ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        Permission.USER_CREATE,
        Permission.USER_DELETE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
    },
    UserRole.MANAGER: {
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
    },
    UserRole.EMPLOYEE: {
        Permission.TASK_UPDATE,
    },
}
