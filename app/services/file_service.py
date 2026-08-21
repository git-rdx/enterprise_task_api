from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.file_storage import delete_stored_file, save_upload_file
from app.dependencies.authorization import check_file_access, check_project_access
from app.models.file import File
from app.repositories.file_repository import file_repository
from app.repositories.project_repository import project_repository
from app.repositories.task_repository import task_repository


class FileService:
    async def upload_file(
        self,
        db: Session,
        upload_file: UploadFile,
        current_user,
        project_id: int | None = None,
        task_id: int | None = None,
    ) -> File:

        # -------------------------
        # 1. Validate content type
        # -------------------------

        allowed_types = {
            content_type.strip()
            for content_type in settings.ALLOWED_FILE_TYPES.split(",")
        }

        if upload_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type is not allowed",
            )

        # -------------------------
        # 2. Read and validate size
        # -------------------------

        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        file_content = await upload_file.read()

        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(f"File size cannot exceed {settings.MAX_FILE_SIZE_MB} MB"),
            )

        # -------------------------
        # 3. Ownership Validation
        # -------------------------

        if project_id is not None:
            project = project_repository.get_by_id(db, project_id)

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            check_project_access(project, current_user)

        if task_id is not None:
            task = task_repository.get_by_id(db, task_id)

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            if project_id is not None and task.project_id != project_id:
                raise HTTPException(
                    status_code=400, detail="Task does not belong to this project"
                )

            task_project = project_repository.get_by_id(db, task.project_id)

            if not task_project:
                raise HTTPException(status_code=404, detail="Project not found")

            check_project_access(task_project, current_user)

            # If task_id is supplied without project_id,
            # associate the file with the task's project.
            if project_id is None:
                project_id = task.project_id

        saved_file_path = None

        try:
            (original_filename, stored_filename, file_size) = await save_upload_file(
                upload_file
            )

            saved_file_path = str(Path(settings.UPLOAD_DIR) / stored_filename)

            file_record = File(
                original_filename=original_filename,
                stored_filename=stored_filename,
                content_type=upload_file.content_type,
                file_size=file_size,
                storage_path=saved_file_path,
                project_id=project_id,
                task_id=task_id,
                uploaded_by=current_user.id,
            )

            return file_repository.create(db, file_record)

        except Exception:
            if saved_file_path:
                delete_stored_file(saved_file_path)

            raise

    def get_file(self, db: Session, file_id: int, current_user):

        file = file_repository.get_by_id(db, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        check_file_access(db, file, current_user)

        return file

    def delete_file(self, db: Session, file_id: int, current_user):

        file = file_repository.get_by_id(db, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.project_id is not None:
            project = project_repository.get_by_id(db, file.project_id)

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            check_project_access(project, current_user)

        storage_path = file.storage_path

        file_repository.delete(db, file)

        delete_stored_file(storage_path)


file_service = FileService()
