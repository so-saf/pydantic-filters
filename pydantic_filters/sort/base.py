from pydantic import BaseModel, Field

from ._meta import SortMetaclass
from .misc import SortByOrder

__all__ = (
    "BaseSort",
)


class BaseSort(BaseModel, metaclass=SortMetaclass):
    sort_by: str
    sort_by_order: SortByOrder = Field(SortByOrder.asc)
