from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.auth import TokenResponse
from app.schemas.refresh_token import RefreshTokenRequest
from app.services.refresh_service import refresh_service

router = APIRouter()


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return refresh_service.refresh(
        db,
        data.refresh_token,
    )
