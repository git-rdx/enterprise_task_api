from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


async def save_upload_file(file: UploadFile) -> tuple[str, str, int]:

    upload_dir = Path(settings.UPLOAD_DIR)

    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = (file.filename or "unknown").strip()

    extension = Path(original_filename).suffix.lower()

    stored_filename = f"{uuid4()}{extension}"

    file_path = upload_dir / stored_filename

    content = await file.read()

    file_path.write_bytes(content)

    return (original_filename, stored_filename, len(content))


def delete_stored_file(storage_path: str) -> None:

    file_path = Path(storage_path)

    if file_path.exists():
        file_path.unlink()
