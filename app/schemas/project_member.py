from pydantic import BaseModel


class ProjectMemberResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class ProjectMemberListResponse(BaseModel):
    items: list[ProjectMemberResponse]
