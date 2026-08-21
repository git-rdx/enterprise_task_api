import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.dependencies.rate_limit as rate_limit_module
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.database.connection import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole

test_engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True)


TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db():

    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db):

    def override_get_db():

        try:
            yield db

        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):

    monkeypatch.setattr(
        rate_limit_module, "check_rate_limit", lambda *args, **kwargs: None
    )


@pytest.fixture()
def verified_user(db):

    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def unverified_user(db):

    user = User(
        name="Unverified User",
        email="unverified@example.com",
        password_hash=hash_password("TestPassword123!"),
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def auth_headers(client, verified_user):

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    assert response.status_code == 200

    access_token = response.json()["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture()
def auth_header_for():

    def _create(user):

        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

        return {"Authorization": f"Bearer {token}"}

    return _create


@pytest.fixture()
def admin_user(db):

    user = User(
        name="Admin User",
        email="admin@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def manager_user(db):

    user = User(
        name="Manager User",
        email="manager@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.MANAGER,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def employee_user(db):

    user = User(
        name="Employee User",
        email="employee@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.EMPLOYEE,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def unrelated_user(db):

    user = User(
        name="Unrelated User",
        email="unrelated@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.EMPLOYEE,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def project_with_member(db, manager_user, employee_user):

    project = Project(
        name="Private Project",
        description="Authorization test project",
        owner_id=manager_user.id,
    )

    project.members.append(manager_user)

    project.members.append(employee_user)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@pytest.fixture()
def task_project(db, manager_user, employee_user, unrelated_user):
    project = Project(
        name="Task Authorization Project",
        description="Task auth tests",
        owner_id=manager_user.id,
    )

    project.members.append(manager_user)
    project.members.append(employee_user)
    project.members.append(unrelated_user)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@pytest.fixture()
def assigned_task(db, task_project, employee_user):
    task = Task(
        title="Assigned Task",
        description="Task authorization test",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        project_id=task_project.id,
        assignee_id=employee_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
