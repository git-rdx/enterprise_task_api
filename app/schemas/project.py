from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)

    description: str | None = None

    member_ids: list[int] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]

    page: int
    page_size: int
    total: int


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)

    description: str | None = None

    @property
    def updates(self) -> dict:
        """Return a dict of fields explicitly set on the model."""
        return self.model_dump(exclude_unset=True)
