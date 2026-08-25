from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.redis import redis_client
from app.database.connection import SessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():

    return {"status": "healthy"}


@router.get("/ready")
def readiness_check():

    database_status = "healthy"
    redis_status = "healthy"

    # PostgreSQL
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

    except Exception:
        database_status = "unhealthy"

    finally:
        db.close()

    # Redis
    try:
        redis_client.ping()

    except Exception:
        redis_status = "unhealthy"

    overall_status = (
        "healthy"
        if (database_status == "healthy" and redis_status == "healthy")
        else "unhealthy"
    )

    if overall_status == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail={
                "status": overall_status,
                "database": database_status,
                "redis": redis_status,
            },
        )

    return {
        "status": overall_status,
        "database": database_status,
        "redis": redis_status,
    }
