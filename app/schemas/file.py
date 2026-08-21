from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str
    file_size: int
    project_id: int | None
    task_id: int | None
    uploaded_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
