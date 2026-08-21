from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File


class FileRepository:
    def create(self, db: Session, file: File) -> File:

        try:
            db.add(file)
            db.commit()
            db.refresh(file)

            return file

        except Exception:
            db.rollback()
            raise

    def get_by_id(self, db: Session, file_id: int) -> File | None:

        statement = select(File).where(File.id == file_id)

        return db.scalar(statement)

    def delete(self, db: Session, file: File) -> None:

        try:
            db.delete(file)
            db.commit()

        except Exception:
            db.rollback()
            raise


file_repository = FileRepository()
