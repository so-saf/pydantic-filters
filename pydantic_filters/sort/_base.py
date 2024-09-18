from typing import Optional

from pydantic import BaseModel, Field

from ._types import SortByOrder


class BaseSort(BaseModel):
    sort_by: Optional[str] = None
    sort_by_order: SortByOrder = Field(SortByOrder.asc)
