from pydantic import BaseModel, Field

__all__ = (
    "BasePagination",
)


class BasePagination(BaseModel):
    limit: int = Field(None, ge=0)
    offset: int = Field(0, ge=0)
