from typing import Optional

from pydantic import BaseModel, Field

from ._types import SortByOrder


class BaseSort(BaseModel):
    """A base class for creating pydantic-based filters."""

    sort_by: Optional[str] = None
    """Field to sort by"""

    sort_by_order: SortByOrder = Field(SortByOrder.asc)
    """Sorting order"""
