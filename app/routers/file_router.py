from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    status,
)
from fastapi import (
    File as FastAPIFile,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.file import FileResponse
from app.services.file_service import file_service

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    upload_file: Annotated[UploadFile, FastAPIFile(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    project_id: int | None = None,
    task_id: int | None = None,
):

    return await file_service.upload_file(
        db, upload_file, current_user, project_id, task_id
    )


@router.get("/{file_id}")
def download_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    file = file_service.get_file(db, file_id, current_user)

    return FastAPIFileResponse(
        path=file.storage_path,
        media_type=file.content_type,
        filename=file.original_filename,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    file_service.delete_file(db, file_id, current_user)

    return None
