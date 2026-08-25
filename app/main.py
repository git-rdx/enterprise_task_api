from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException
from app.core.logging_config import setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import (
    auth,
    file_router,
    health_router,
    project_member_router,
    project_router,
    task_router,
    user_router,
)

setup_logging()


app = FastAPI(title="Enterprise Task Management API", version="1.0.0")

app.add_exception_handler(AppException, cast(Any, app_exception_handler))
app.add_exception_handler(HTTPException, cast(Any, http_exception_handler))
app.add_exception_handler(RequestValidationError, cast(Any, validation_exception_handler))
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(user_router.router)
app.include_router(auth.router)
app.include_router(project_router.router)
app.include_router(project_member_router.router)
app.include_router(task_router.router)
app.include_router(file_router.router)
app.include_router(health_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID", "Retry-After"],
)

app.add_middleware(SecurityHeadersMiddleware)


@app.get("/")
def home():
    return {"message": "Enterprise Task Management API"}
