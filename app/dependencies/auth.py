from typing import Annotated

from fastapi import Depends, HTTPException

# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import user_repository

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="/api/v1/auth/login/oauth2"
# )


# def get_current_user(
#     db: Annotated[Session, Depends(get_db)],
#     token: str = Depends(oauth2_scheme),
# ) -> User:

#     user_id = decode_access_token(token)

#     user = user_repository.get_by_id(
#         db,
#         user_id
#     )

#     if not user:

#         raise HTTPException(
#             status_code=401,
#             detail="User not found"
#         )

#     return user

security = HTTPBearer()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:

    token = credentials.credentials

    user_id = decode_access_token(token)

    user = user_repository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
